// commands/fishing.js  —  Game fishing animasi untuk Sambo Bot (discord.js v14, CommonJS)
//
// Alur game (mirip bot UwU):
//   1. "lagi lempar kail..."   -> animasi lempar + nunggu (tombol Tarik nonaktif)
//   2. "ada yang nyantol!"     -> progress bar naik, pencet Tarik tepat di ZONA PAS
//   3. Hasil                   -> rarity, bintang, berat, hadiah coin (atau kabur / zonk)
//
// Pakai sebagai slash command:  /fishing taruhan:20
// Pakai sebagai prefix command: (lihat bagian paling bawah: executePrefix)

const {
  SlashCommandBuilder, EmbedBuilder, ActionRowBuilder, ButtonBuilder,
  ButtonStyle, ComponentType, MessageFlags,
} = require('discord.js');

// ============================================================================
// 1) KONFIGURASI
// ============================================================================

// Lokasi GIF. Upload semua fish_*.gif ke repo, lalu pakai URL raw GitHub:
const GIF_BASE = process.env.FISH_GIF_BASE
  || 'https://raw.githubusercontent.com/Satrioadi017/sambo-bot-legal/main/';
const gif = (f) => (GIF_BASE ? GIF_BASE + f : null);

const CFG = {
  minBet: 10,
  maxBet: 5000,
  defaultBet: 20,
  cooldownMs: 10_000,
  castFrames: 4,          // jumlah frame animasi lempar
  frameMs: 1000,          // jeda tiap edit pesan (aman dari rate limit)
  waitMin: 2500,          // nunggu ikan nyantol (ms)
  waitMax: 6000,
  biteWindowMs: 5000,     // waktu untuk pencet Tarik setelah ikan nyantol
  zoneStart: 0.40,        // zona PAS (0..1 dari waktu bite)
  zoneEnd: 0.70,
};

// ============================================================================
// 2) EKONOMI  — GANTI bagian ini dengan database botmu
// ============================================================================
const _mem = new Map(); // sementara, hilang saat bot restart
const economy = {
  async getBalance(userId) { return _mem.get(userId) ?? 1000; },
  async addCoins(userId, amount) {        // amount boleh negatif
    const next = (await this.getBalance(userId)) + amount;
    _mem.set(userId, next);
    return next;
  },
};

// ============================================================================
// 3) DATA IKAN
// ============================================================================
const RARITIES = {
  junk:      { label: 'Zonk',      icon: '🗑️', color: 0x7f8c8d, mult: 0,   weight: 8,   gif: 'fish_junk.gif' },
  common:    { label: 'Common',    icon: '⬜', color: 0xb2bece, mult: 0.9, weight: 50,  gif: 'fish_catch_common.gif' },
  uncommon:  { label: 'Uncommon',  icon: '🟩', color: 0x6ecd78, mult: 1.6, weight: 25,  gif: 'fish_catch_uncommon.gif' },
  rare:      { label: 'Rare',      icon: '🟦', color: 0x5aa0fa, mult: 3,   weight: 11,  gif: 'fish_catch_rare.gif' },
  epic:      { label: 'Epic',      icon: '🟪', color: 0xbe6ef0, mult: 7,   weight: 4.5, gif: 'fish_catch_epic.gif' },
  legendary: { label: 'Legendary', icon: '🟨', color: 0xffcd46, mult: 18,  weight: 1.5, gif: 'fish_catch_legendary.gif' },
};

// [nama, emoji, berat min kg, berat max kg]
const POOL = {
  junk: [
    ['Sepatu Butut', '🥾', 0.3, 0.8], ['Kaleng Bekas', '🥫', 0.1, 0.3],
    ['Ban Bocor', '🛞', 2, 6],        ['Rumput Laut Kusut', '🌿', 0.1, 0.5],
  ],
  common: [
    ['Ikan Teri Perak', '🐟', 0.1, 0.5], ['Ikan Lele', '🐟', 0.5, 2],
    ['Ikan Nila', '🐟', 0.4, 1.5],       ['Ikan Mujair', '🐟', 0.3, 1.2],
  ],
  uncommon: [
    ['Ikan Mas', '🐠', 1, 3.5], ['Ikan Gurame', '🐠', 1.5, 5], ['Ikan Bawal', '🐠', 1, 4],
  ],
  rare: [
    ['Ikan Kakap Merah', '🐡', 3, 9], ['Ikan Kerapu', '🐡', 4, 12], ['Cumi Raksasa', '🦑', 3, 10],
  ],
  epic: [
    ['Tuna Sirip Biru', '🐋', 20, 60], ['Ikan Todak', '🦈', 25, 70], ['Gurita Samudra', '🐙', 15, 45],
  ],
  legendary: [
    ['Hiu Putih Agung', '🦈', 120, 300], ['Paus Emas', '🐳', 500, 1200], ['Naga Laut', '🐉', 300, 900],
  ],
};

// ============================================================================
// 4) HELPER LOGIKA
// ============================================================================
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const rand = (a, b) => a + Math.random() * (b - a);
const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];

/** q: 0..1 = seberapa pas timing pencet Tarik (1 = tepat di tengah zona) */
function timingQuality(t) {
  const center = (CFG.zoneStart + CFG.zoneEnd) / 2;
  return Math.max(0, 1 - Math.abs(t - center) / center);
}
function timingLabel(t) {
  if (t >= CFG.zoneStart && t <= CFG.zoneEnd) return '🎯 PERFECT';
  return t < CFG.zoneStart ? '⚡ Kecepetan' : '🐢 Telat dikit';
}

function rollRarity(q) {
  const w = {};
  for (const [k, r] of Object.entries(RARITIES)) {
    w[k] = r.weight;
    if (['rare', 'epic', 'legendary'].includes(k)) w[k] *= 0.4 + 1.6 * q; // timing bagus = lebih hoki
    if (k === 'junk') w[k] *= 1.5 - q;
  }
  let roll = Math.random() * Object.values(w).reduce((a, b) => a + b, 0);
  for (const [k, v] of Object.entries(w)) { if ((roll -= v) <= 0) return k; }
  return 'common';
}

function rollCatch(bet, t) {
  const q = timingQuality(t);
  const rarityKey = rollRarity(q);
  const [name, emoji, min, max] = pick(POOL[rarityKey]);
  const kg = +rand(min, max).toFixed(rarityKey === 'legendary' ? 0 : 1);
  const stars = 1 + Math.min(4, Math.floor(((kg - min) / (max - min || 1)) * 5));
  const mult = +(RARITIES[rarityKey].mult * (0.6 + 0.8 * q) * rand(0.9, 1.1)).toFixed(2);
  const reward = Math.floor(bet * mult);
  return { rarityKey, name, emoji, kg, stars, mult, reward, q };
}

const starBar = (n) => '⭐'.repeat(n) + '☆'.repeat(5 - n);

// ============================================================================
// 5) RENDER ANIMASI TEKS (scene ASCII yang ikut bergerak)
// ============================================================================
const SCENE_W = 30;

function waveRow(offset, row) {
  const pat = row % 2 ? '~-~^' : '^~~-';
  let s = '';
  for (let i = 0; i < SCENE_W; i++) s += pat[(i + offset + row) % pat.length];
  return s;
}

/**
 * Gambar scene: joran di kiri-atas, senar diagonal, air di bawah.
 * opts: { lineRows (0-3), bobY (0|1|2), wave, fish: {col,row}|null, bang }
 */
function renderScene({ lineRows = 3, bobDip = 0, wave = 0, fish = null, bang = false }) {
  const rows = Array.from({ length: 7 }, () => Array(SCENE_W).fill(' '));
  const surface = 3;
  // senar diagonal
  for (let r = 0; r < Math.min(lineRows, 3); r++) { rows[r][1 + r * 2] = '\\'; rows[r][2 + r * 2] = ' '; }
  const bobCol = 7;
  // air
  for (let r = surface; r < 7; r++) {
    const w = waveRow(wave, r);
    for (let c = 0; c < SCENE_W; c++) rows[r][c] = r === surface ? w[c] : (r < 5 ? w[c] : ' ');
  }
  if (lineRows >= 3) {
    if (bobDip === 0) rows[surface][bobCol] = 'o';
    else {
      rows[surface][bobCol - 1] = '('; rows[surface][bobCol] = ' '; rows[surface][bobCol + 1] = ')';
      rows[surface + bobDip][bobCol] = 'o';
      for (let r = surface + 1; r < surface + bobDip; r++) rows[r][bobCol] = '|';
    }
  }
  if (fish) {
    const f = '<><';
    for (let i = 0; i < f.length; i++) if (fish.col + i < SCENE_W) rows[fish.row][fish.col + i] = f[i];
  }
  if (bang) { rows[0][bobCol + 3] = '!'; rows[1][bobCol + 3] = '!'; }
  return rows.map((r) => r.join('').replace(/\s+$/, '')).join('\n');
}

function renderBar(progress) {
  const cells = 10;
  const filled = Math.min(cells, Math.floor(progress * cells));
  const zs = Math.floor(CFG.zoneStart * cells), ze = Math.ceil(CFG.zoneEnd * cells);
  const bar = Array.from({ length: cells }, (_, i) => (i < filled ? '▰' : '▱')).join('');
  const marker = ' '.repeat(zs + 1) + '▲'.repeat(ze - zs) + ' ← zona pas';
  return `[${bar}]\n${marker}`;
}

// ============================================================================
// 6) EMBED & TOMBOL
// ============================================================================
function btn({ enabled, label = 'Tarik', style = ButtonStyle.Success }) {
  return new ActionRowBuilder().addComponents(
    new ButtonBuilder().setCustomId('fish_pull').setLabel(label).setEmoji('🎣')
      .setStyle(enabled ? style : ButtonStyle.Secondary).setDisabled(!enabled),
  );
}

function baseEmbed(user, bet, color) {
  return new EmbedBuilder().setColor(color).setAuthor({
    name: user.username, iconURL: user.displayAvatarURL({ size: 64 }),
  }).setFooter({ text: `Taruhan ${bet} 🪙` });
}

function castEmbed(user, bet, scene, note, gifFile) {
  const e = baseEmbed(user, bet, 0x3498db)
    .setTitle(`🎣 @${user.username} lagi lempar kail...`)
    .setDescription('```\n' + scene + '\n```' + note);
  if (gif(gifFile)) e.setImage(gif(gifFile));
  return e;
}

function biteEmbed(user, bet, scene, progress) {
  const e = baseEmbed(user, bet, 0x2ecc71)
    .setTitle(`🎣 @${user.username} — ada yang nyantol!`)
    .setDescription('```\n' + scene + '\n```\n```\n' + renderBar(progress) + '\n```\n'
      + 'Pencet **Tarik** pas di zona `▲` buat nyangkutin!');
  if (gif('fish_bite.gif')) e.setImage(gif('fish_bite.gif'));
  return e;
}

function resultEmbed(user, bet, c, t, balance) {
  const r = RARITIES[c.rarityKey];
  const e = baseEmbed(user, bet, r.color);
  if (c.rarityKey === 'junk') {
    e.setTitle(`🎣 @${user.username} dapat zonk...`)
      .setDescription(`${r.icon} **${r.label}**\n\n${c.emoji} **${c.name}**\n${c.kg} KG\n\u200b`)
      .addFields({ name: 'Hadiah', value: '🪙 **+0 Coins** (sabar ya)', inline: false });
  } else {
    e.setTitle(`🎣 @${user.username} dapat`)
      .setDescription(`${r.icon} **${r.label}**\n\n${c.emoji} ${c.name}\n${starBar(c.stars)}\n${c.kg} KG`)
      .addFields(
        { name: 'Hadiah', value: `🪙 **+${c.reward} Coins**`, inline: true },
        { name: 'Timing', value: timingLabel(t), inline: true },
      );
  }
  e.setFooter({ text: `Taruhan ${bet} · ${c.mult}x · Saldo ${balance} 🪙` });
  if (gif(r.gif)) e.setImage(gif(r.gif));
  return e;
}

function failEmbed(user, bet, balance) {
  const e = baseEmbed(user, bet, 0xe74c3c)
    .setTitle(`🎣 @${user.username} — ikannya kabur!`)
    .setDescription('Kelamaan narik, ikannya lepas dari kail. 😭')
    .addFields({ name: 'Hadiah', value: '🪙 **+0 Coins**' })
    .setFooter({ text: `Taruhan ${bet} · 0x · Saldo ${balance} 🪙` });
  if (gif('fish_fail.gif')) e.setImage(gif('fish_fail.gif'));
  return e;
}

// ============================================================================
// 7) GAME UTAMA
// ============================================================================
const cooldowns = new Map();

/**
 * @param {import('discord.js').User} user
 * @param {number} bet
 * @param {(payload) => Promise<import('discord.js').Message>} sendFirst  kirim pesan pertama
 * @param {(text:string)=>Promise<any>} sendError  balas error (ephemeral kalau slash)
 */
async function runFishing(user, bet, sendFirst, sendError) {
  // --- validasi
  const last = cooldowns.get(user.id) ?? 0;
  const left = last + CFG.cooldownMs - Date.now();
  if (left > 0) return sendError(`⏳ Tunggu **${(left / 1000).toFixed(1)}s** lagi sebelum mancing lagi.`);
  if (!Number.isInteger(bet) || bet < CFG.minBet || bet > CFG.maxBet)
    return sendError(`Taruhan harus **${CFG.minBet}–${CFG.maxBet}** coins.`);
  const bal = await economy.getBalance(user.id);
  if (bal < bet) return sendError(`Saldo kurang. Kamu punya **${bal}** 🪙, taruhan **${bet}**.`);

  cooldowns.set(user.id, Date.now());
  await economy.addCoins(user.id, -bet); // taruhan dipotong di awal

  // --- FASE 1: lempar kail
  const msg = await sendFirst({
    embeds: [castEmbed(user, bet, renderScene({ lineRows: 0 }), '\nNunggu ada yang nyantol...', 'fish_cast.gif')],
    components: [btn({ enabled: false })],
  });

  try {
    for (let i = 1; i <= CFG.castFrames; i++) {
      await sleep(CFG.frameMs);
      await msg.edit({
        embeds: [castEmbed(user, bet, renderScene({ lineRows: Math.min(i, 3), wave: i }),
          '\nNunggu ada yang nyantol...', 'fish_cast.gif')],
        components: [btn({ enabled: false })],
      });
    }

    // --- nunggu ikan (ikan mendekat tiap frame)
    const waitMs = rand(CFG.waitMin, CFG.waitMax);
    const steps = Math.max(1, Math.round(waitMs / CFG.frameMs));
    for (let i = 0; i < steps; i++) {
      await sleep(CFG.frameMs);
      const fishCol = Math.max(8, 24 - Math.round((i / steps) * 16));
      await msg.edit({
        embeds: [castEmbed(user, bet,
          renderScene({ lineRows: 3, wave: i + CFG.castFrames, bobDip: i % 2 && i > steps - 3 ? 1 : 0, fish: { col: fishCol, row: 6 } }),
          '\nNunggu ada yang nyantol...', 'fish_wait.gif')],
        components: [btn({ enabled: false })],
      });
    }

    // --- FASE 2: ikan nyantol!
    const biteAt = Date.now();
    let finished = false;
    await msg.edit({
      embeds: [biteEmbed(user, bet, renderScene({ lineRows: 3, bobDip: 2, bang: true, fish: { col: 6, row: 6 } }), 0)],
      components: [btn({ enabled: true })],
    });

    // loop update progress bar (jalan paralel dengan penunggu tombol)
    const ticker = (async () => {
      let n = 0;
      while (!finished) {
        await sleep(CFG.frameMs);
        if (finished) break;
        const t = Math.min(1, (Date.now() - biteAt) / CFG.biteWindowMs);
        if (t >= 1) break;
        n++;
        await msg.edit({
          embeds: [biteEmbed(user, bet,
            renderScene({ lineRows: 3, wave: n, bobDip: n % 2 ? 2 : 1, bang: true, fish: { col: 5 + (n % 3), row: 6 } }), t)],
          components: [btn({ enabled: true })],
        }).catch(() => {});
      }
    })();

    let pressed = null;
    try {
      pressed = await msg.awaitMessageComponent({
        componentType: ComponentType.Button,
        time: CFG.biteWindowMs,
        filter: (i) => {
          if (i.user.id === user.id) return true;
          i.reply({ content: 'Ini bukan pancinganmu 🎣', flags: MessageFlags.Ephemeral }).catch(() => {});
          return false;
        },
      });
    } catch { /* timeout */ }
    finished = true;
    await ticker;

    // --- FASE 3: hasil
    if (!pressed) {
      const balance = await economy.getBalance(user.id);
      return msg.edit({ embeds: [failEmbed(user, bet, balance)], components: [btn({ enabled: false, label: 'Kabur' })] });
    }
    const t = Math.min(1, (Date.now() - biteAt) / CFG.biteWindowMs);
    const c = rollCatch(bet, t);
    const balance = await economy.addCoins(user.id, c.reward);
    await pressed.update({
      embeds: [resultEmbed(user, bet, c, t, balance)],
      components: [btn({ enabled: false, label: 'Tarik' })],
    });
  } catch (err) {
    console.error('[fishing] error:', err);
    await economy.addCoins(user.id, bet).catch(() => {}); // refund kalau error
    cooldowns.delete(user.id);
    msg.edit({ content: '⚠️ Ada error, taruhanmu dikembalikan.', embeds: [], components: [] }).catch(() => {});
  }
}

// ============================================================================
// 8) EXPORT — slash command
// ============================================================================
module.exports = {
  data: new SlashCommandBuilder()
    .setName('fishing')
    .setDescription('Mancing ikan! Pencet Tarik di waktu yang pas buat dapet ikan langka.')
    .addIntegerOption((o) => o.setName('taruhan').setDescription(`Taruhan coin (${CFG.minBet}-${CFG.maxBet})`)
      .setMinValue(CFG.minBet).setMaxValue(CFG.maxBet)),

  async execute(interaction) {
    const bet = interaction.options.getInteger('taruhan') ?? CFG.defaultBet;
    await runFishing(
      interaction.user, bet,
      async (payload) => { await interaction.reply(payload); return interaction.fetchReply(); },
      (text) => interaction.reply({ content: text, flags: MessageFlags.Ephemeral }),
    );
  },

  // ---- opsional: prefix command, mis. "uf 20" / "uwu fish 20" -----------------
  // Di handler messageCreate kamu:
  //   if (['uf','fish','fishing'].includes(cmd)) return require('./commands/fishing').executePrefix(message, args);
  async executePrefix(message, args) {
    const bet = args[0] ? parseInt(args[0], 10) : CFG.defaultBet;
    await runFishing(
      message.author, bet,
      (payload) => message.reply(payload),
      (text) => message.reply(text),
    );
  },
};
