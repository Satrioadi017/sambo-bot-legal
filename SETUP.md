# Setup Fishing — Sambo Bot (discord.js v14)

1. Upload semua `fish_*.gif` ke root repo `sambo-bot-legal` (sama seperti coin_spin.gif, slot_*.gif).
2. Salin `fishing.js` ke folder commands bot kamu (mis. `commands/fishing.js`).
3. Ganti objek `economy` di bagian 2 `fishing.js` dengan fungsi database coin botmu
   (`getBalance(userId)` dan `addCoins(userId, amount)`).
4. Kalau repo/branch beda, ubah `GIF_BASE` atau set env `FISH_GIF_BASE=https://.../`.
5. Deploy ulang slash command (`/fishing taruhan:20`), restart bot.
6. Opsional prefix command: panggil `require('./commands/fishing').executePrefix(message, args)`.

Ubah GIF? Edit `generate_gifs.py` lalu `pip install pillow && python generate_gifs.py`.
