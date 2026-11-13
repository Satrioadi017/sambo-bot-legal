"""
Generator GIF untuk game fishing Sambo Bot.
Jalankan:  pip install pillow && python generate_gifs.py
Output: fish_*.gif di folder ini (upload ke repo kamu).
"""
import math, random, os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

W, H, S = 480, 200, 2          # ukuran logis & super-sampling
HZ = 108                       # garis cakrawala / permukaan air
TARGET = (300, HZ + 14)        # tempat pelampung jatuh
OUT = os.path.dirname(os.path.abspath(__file__))

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]
def font(size):
    for p in FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, int(size * S))
    return ImageFont.load_default()

RARITY = {
    "common":    dict(col=(178, 190, 205), text="COMMON"),
    "uncommon":  dict(col=(110, 205, 120), text="UNCOMMON"),
    "rare":      dict(col=(90, 160, 250),  text="RARE!"),
    "epic":      dict(col=(190, 110, 240), text="EPIC!!"),
    "legendary": dict(col=(255, 205, 70),  text="LEGENDARY!!!"),
}

def lerp(a, b, t): return a + (b - a) * t
def lerpc(c1, c2, t): return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))
def ease(t): return t * t * (3 - 2 * t)
def u(v): return int(round(v * S))

# ---------------------------------------------------------------- helpers
class G:
    """Wrapper ImageDraw dengan koordinat logis."""
    def __init__(self, im): self.im, self.d = im, ImageDraw.Draw(im)
    def ellipse(self, cx, cy, rx, ry, fill=None, outline=None, width=1):
        self.d.ellipse([u(cx-rx), u(cy-ry), u(cx+rx), u(cy+ry)], fill=fill, outline=outline, width=max(1, u(width)) if outline else 0)
    def line(self, pts, fill, width=1):
        self.d.line([(u(x), u(y)) for x, y in pts], fill=fill, width=max(1, u(width)), joint="curve")
    def poly(self, pts, fill): self.d.polygon([(u(x), u(y)) for x, y in pts], fill=fill)
    def text(self, x, y, s, size, fill, outline=(20, 20, 30), ow=2):
        f = font(size)
        for dx in range(-ow, ow + 1):
            for dy in range(-ow, ow + 1):
                if dx or dy:
                    self.d.text((u(x) + dx * S // 1, u(y) + dy * S // 1), s, font=f, fill=outline, anchor="mm")
        self.d.text((u(x), u(y)), s, font=f, fill=fill, anchor="mm")

def layer(): return Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
def comp(base, lay): return Image.alpha_composite(base, lay)

def build_background():
    im = Image.new("RGBA", (W * S, H * S))
    g = G(im)
    top, mid, hz = (34, 40, 96), (190, 96, 130), (255, 176, 108)
    for y in range(HZ * S):
        t = y / (HZ * S)
        c = lerpc(top, mid, t / 0.65) if t < 0.65 else lerpc(mid, hz, (t - 0.65) / 0.35)
        g.d.line([(0, y), (W * S, y)], fill=c)
    g.ellipse(372, HZ - 6, 34, 34, fill=(255, 226, 150))          # matahari
    g.ellipse(372, HZ - 6, 46, 46, outline=(255, 200, 140), width=1)
    g.poly([(0, HZ), (0, HZ-18), (60, HZ-30), (130, HZ-14), (210, HZ-26), (270, HZ-10), (330, HZ), ], (70, 52, 100))
    g.poly([(260, HZ), (330, HZ-14), (410, HZ-30), (480, HZ-12), (480, HZ)], (58, 44, 92))
    for y in range(HZ * S, H * S):
        t = (y - HZ * S) / ((H - HZ) * S)
        g.d.line([(0, y), (W * S, y)], fill=lerpc((38, 120, 150), (14, 44, 84), t))
    return im
BG = build_background()

def water(frame_idx=0, period=24):
    """Frame baru dengan gelombang beranimasi (loop mulus berdasarkan period)."""
    im = BG.copy(); g = G(im)
    ph = 2 * math.pi * frame_idx / period
    for k in range(7):
        y0 = HZ + 7 + k * 13
        pts = [(x, y0 + (1.4 + k * 0.25) * math.sin(x / (22 - k) + ph + k)) for x in range(0, W + 8, 8)]
        g.line(pts, lerpc((120, 210, 225), (60, 130, 170), k / 7), 1.2)
    for j in range(7):                                                # pantulan matahari
        yy = HZ + 6 + j * 9
        w = 30 - j * 2 + 4 * math.sin(ph + j)
        g.line([(372 - w, yy), (372 + w, yy)], (255, 214, 150), 1.6)
    return im

def fish_sprite(L=30, h=12, col=(190, 200, 215), alpha=255, facing=1):
    w, hh = u(2.7 * L + 14), u(2 * h + 12)
    im = Image.new("RGBA", (w, hh), (0, 0, 0, 0)); g = G(im)
    cx, cy = 1.7 * L + 6, hh / S / 2
    belly = tuple(min(255, c + 45) for c in col); fin = tuple(max(0, c - 40) for c in col)
    g.poly([(cx - L + 5, cy), (cx - 1.65 * L, cy - h * .95), (cx - 1.5 * L, cy), (cx - 1.65 * L, cy + h * .95)], fin + (alpha,))
    g.poly([(cx - L * .25, cy - h * .8), (cx + L * .1, cy - h * 1.5), (cx + L * .45, cy - h * .7)], fin + (alpha,))
    g.ellipse(cx, cy, L, h, fill=col + (alpha,))
    g.d.pieslice([u(cx - L + 1), u(cy - h + 1), u(cx + L - 1), u(cy + h - 1)], 10, 170, fill=belly + (alpha,))
    g.ellipse(cx + L * .55, cy - h * .2, 3.2, 3.2, fill=(255, 255, 255, alpha))
    g.ellipse(cx + L * .6, cy - h * .2, 1.6, 1.6, fill=(20, 20, 30, alpha))
    g.line([(cx + L * .3, cy - h * .6), (cx + L * .22, cy + h * .6)], fin + (alpha,), 1.2)
    return im.transpose(Image.FLIP_LEFT_RIGHT) if facing < 0 else im

def paste_center(base, sprite, x, y, angle=0, scale=1.0):
    if scale != 1.0:
        sprite = sprite.resize((int(sprite.width * scale), int(sprite.height * scale)), Image.LANCZOS)
    if angle: sprite = sprite.rotate(angle, expand=True, resample=Image.BICUBIC)
    base.paste(sprite, (u(x) - sprite.width // 2, u(y) - sprite.height // 2), sprite)

def rod_and_line(im, tip, bob, sag=10, line_col=(250, 250, 255), rod_end=(-6, 176)):
    g = G(im)
    g.line([rod_end, tip], (92, 58, 34), 4.2)
    g.line([(rod_end[0] + (tip[0]-rod_end[0]) * .55, rod_end[1] + (tip[1]-rod_end[1]) * .55), tip], (140, 96, 60), 2.4)
    if bob is None: return
    mx, my = (tip[0] + bob[0]) / 2, (tip[1] + bob[1]) / 2 + sag
    pts = [((1-t)**2*tip[0] + 2*(1-t)*t*mx + t*t*bob[0], (1-t)**2*tip[1] + 2*(1-t)*t*my + t*t*bob[1]) for t in [i/16 for i in range(17)]]
    g.line(pts, line_col, 1.1)

def bobber(im, x, y):
    g = G(im)
    g.ellipse(x, y, 6, 6, fill=(235, 60, 60))
    g.d.pieslice([u(x-6), u(y-6), u(x+6), u(y+6)], 0, 180, fill=(250, 250, 250))
    g.ellipse(x, y, 6, 6, outline=(60, 20, 20), width=0.8)
    g.line([(x, y - 6), (x, y - 11)], (240, 240, 240), 1.4)

def ripples(base, x, y, ts, col=(235, 250, 255)):
    lay = layer(); g = G(lay)
    for t in ts:
        if 0 < t < 1:
            r = 4 + 34 * t
            g.ellipse(x, y, r, r * .28, outline=col + (int(210 * (1 - t)),), width=1.6)
    return comp(base, lay)

def droplets(base, x, y, t, n=12, seed=1, power=1.0):
    lay = layer(); g = G(lay); rnd = random.Random(seed)
    for _ in range(n):
        a = rnd.uniform(math.radians(55), math.radians(125)); v = rnd.uniform(60, 120) * power
        px = x + math.cos(a) * v * t * 1.1 + rnd.uniform(-4, 4)
        py = y - math.sin(a) * v * t + 150 * t * t
        if py < HZ + 12 and 0 < t < 1:
            g.ellipse(px, py, 2.2, 2.2, fill=(235, 250, 255, int(230 * (1 - t * .6))))
    return comp(base, lay)

def star4(g, x, y, r, col):
    g.poly([(x, y - r), (x + r * .28, y - r * .28), (x + r, y), (x + r * .28, y + r * .28),
            (x, y + r), (x - r * .28, y + r * .28), (x - r, y), (x - r * .28, y - r * .28)], col)

def sparkles(base, cx, cy, f, col, n=10, spread=95, seed=3):
    lay = layer(); g = G(lay); rnd = random.Random(seed)
    for i in range(n):
        x = cx + rnd.uniform(-spread * 1.5, spread * 1.5); y = cy + rnd.uniform(-spread * .8, spread * .6)
        ph = (f * .35 + i * .9) % (2 * math.pi)
        r = max(0, math.sin(ph)) * rnd.uniform(5, 11)
        if r > 1: star4(g, x, y, r, col + (230,))
    return comp(base, lay)

def rays(base, cx, cy, rot, col, n=14, alpha=70):
    lay = layer(); g = G(lay)
    for i in range(n):
        a0 = math.radians(rot + i * 360 / n); hw = math.radians(5.5)
        g.poly([(cx, cy), (cx + 320 * math.cos(a0 - hw), cy + 320 * math.sin(a0 - hw)),
                (cx + 320 * math.cos(a0 + hw), cy + 320 * math.sin(a0 + hw))], col + (alpha,))
    return comp(base, lay)

def vignette_flash(base, col, a):
    lay = Image.new("RGBA", base.size, col + (int(a),)); return comp(base, lay)

def finalize(im): return im.resize((W, H), Image.LANCZOS).convert("RGB")

def save_gif(frames, durs, name):
    sample = Image.new("RGB", (W, H * min(6, len(frames))))
    step = max(1, len(frames) // 6)
    for i, f in enumerate(frames[::step][:6]): sample.paste(f, (0, i * H))
    pal = sample.quantize(colors=250, method=Image.Quantize.MEDIANCUT)
    q = [f.quantize(palette=pal, dither=Image.Dither.FLOYDSTEINBERG) for f in frames]
    path = os.path.join(OUT, name)
    q[0].save(path, save_all=True, append_images=q[1:], duration=durs, loop=0, disposal=1, optimize=False)
    print(f"{name:28s} {len(frames):2d} frame  {os.path.getsize(path)/1024:6.0f} KB")

# ---------------------------------------------------------------- animasi
def gif_cast():
    frames, durs = [], []
    N = 26
    for f in range(N):
        im = water(f, 24)
        if f < 7:                                  # ayun ke belakang
            p = ease(f / 6); tip = (lerp(62, 36, p), lerp(42, 22, p)); bob = (tip[0] - 4 * p, tip[1] + 40 - 6 * p); sag = 4
        elif f < 17:                               # lempar
            p = (f - 7) / 9; pe = ease(min(1, p)); tip = (lerp(36, 86, min(1, p * 2.2)), lerp(22, 50, min(1, p * 2.2)))
            bob = (lerp(tip[0], TARGET[0], pe), lerp(tip[1] + 24, TARGET[1], pe) - 78 * math.sin(math.pi * min(1, p)))
            sag = 14 * (1 - pe)
        else:
            tip = (84, 48); k = f - 17; bob = (TARGET[0], TARGET[1] + 1.8 * math.sin(k * .9) * math.exp(-k * .15)); sag = 8
        rod_and_line(im, tip, bob, sag)
        if f >= 16:
            k = (f - 16) / 9
            im = droplets(im, TARGET[0], TARGET[1], k, seed=4)
            im = ripples(im, TARGET[0], TARGET[1] + 3, [k, k - .25, k - .5])
        bobber(im, *bob)
        frames.append(finalize(im)); durs.append(55 if f < N - 1 else 900)
    save_gif(frames, durs, "fish_cast.gif")

def gif_wait():
    frames, N = [], 24
    for f in range(N):
        im = water(f, N); a = 2 * math.pi * f / N
        lay = layer()
        fx, fy = TARGET[0] + 95 * math.cos(a), HZ + 62 + 14 * math.sin(a)       # bayangan ikan berputar
        paste_center(lay, fish_sprite(24, 9, (10, 30, 50), 95, 1 if -math.sin(a) > 0 else -1), fx, fy, 0)
        im = comp(im, lay)
        bob = (TARGET[0], TARGET[1] + 2.2 * math.sin(a * 2))
        rod_and_line(im, (84, 48), bob, 9 + 2 * math.sin(a * 2))
        im = ripples(im, TARGET[0], TARGET[1] + 3, [(f / N) % 1, (f / N + .5) % 1])
        bobber(im, *bob); frames.append(finalize(im))
    save_gif(frames, [80] * N, "fish_wait.gif")

def gif_bite():
    frames, N = [], 18
    dip = [0, 3, 10, 18, 9, 17, 6, 15, 8, 17, 9, 14, 7, 12, 8, 12, 7, 11]
    for f in range(N):
        im = water(f, 18); a = f / N
        lay = layer()
        paste_center(lay, fish_sprite(26, 10, (8, 24, 44), 130, -1), TARGET[0] - 8 + 3 * math.sin(f), HZ + 44 + dip[f] * .5, 12 * math.sin(f * 1.3))
        im = comp(im, lay)
        bob = (TARGET[0] + 1.5 * math.sin(f * 2), TARGET[1] + dip[f])
        tip = (84, 48 + min(10, dip[f] * .6))
        rod_and_line(im, tip, bob, sag=0)
        im = ripples(im, TARGET[0], TARGET[1] + 3, [a * 1.3 % 1, (a * 1.3 + .4) % 1, (a * 1.3 + .75) % 1])
        im = droplets(im, TARGET[0], TARGET[1], (f % 6) / 6, seed=f, power=.8)
        bobber(im, *bob)
        s = min(1, f / 4); pop = 1 + .18 * math.sin(f * 1.4)                      # gelembung "!"
        g = G(im); bx, by = TARGET[0] + 30, TARGET[1] - 52
        g.ellipse(bx, by, 17 * s * pop, 17 * s * pop, fill=(255, 70, 70), outline=(255, 255, 255), width=2)
        if s > .6: g.text(bx, by, "!", 22 * pop, (255, 255, 255), ow=1)
        if f % 4 < 2: im = vignette_flash(im, (255, 255, 255), 28)
        frames.append(finalize(im))
    save_gif(frames, [60] * N, "fish_bite.gif")

def gif_catch(rarity):
    info = RARITY[rarity]; col = info["col"]; big = rarity in ("rare", "epic", "legendary")
    frames, durs = [], []
    spr = fish_sprite(30, 12, col, 255, 1)
    N1, N2 = 16, 14
    for f in range(N1):                                           # tarik + ikan melompat
        im = water(f, 24)
        if f < 5:
            p = f / 4; fx, fy = 258, HZ + 26 - 6 * p; tip = (84, 48 + 9 * (1 - p)); ang = 0
            im = ripples(im, fx, HZ + 12, [p, p - .3])
            im = droplets(im, fx, HZ + 12, p, seed=9, power=1.3)
            bob = None
            rod_and_line(im, tip, (fx, fy), sag=0)
            paste_center(im, spr, fx, fy, 0, .9)
        else:
            p = (f - 5) / (N1 - 6); fx = lerp(258, 150, ease(p)); fy = HZ + 12 - 96 * math.sin(math.pi * p)
            ang = lerp(40, -50, p); tip = (84, 48)
            rod_and_line(im, tip, (fx + 26 * math.cos(math.radians(ang)), fy - 26 * math.sin(math.radians(ang))), sag=2)
            paste_center(im, spr, fx, fy, ang, 1.0)
            if p < .4: im = droplets(im, 258, HZ + 12, p * 2.2, seed=11, power=1.5)
            if big: im = sparkles(im, fx, fy, f, col, n=6, spread=50, seed=2)
        frames.append(finalize(im)); durs.append(55)
    for k in range(N2):                                           # reveal
        im = water(k, 24)
        im = vignette_flash(im, (10, 10, 30), 120)
        if big: im = rays(im, 240, 100, k * 4, col, alpha=60 if rarity != "legendary" else 85)
        pop = min(1, (k + 1) / 4); bounce = 1 + .06 * math.sin(k * .8)
        lay = layer(); g = G(lay)
        g.ellipse(240, 100, 62 * pop, 62 * pop, fill=col + (60,))
        im = comp(im, lay)
        paste_center(im, spr, 240, 100 + 3 * math.sin(k * .7), 8 * math.sin(k * .5), 1.9 * pop * bounce)
        im = sparkles(im, 240, 100, k, col, n=12 if big else 6, spread=100, seed=5)
        g = G(im)
        g.text(240, 160, info["text"], 24 * min(1, .5 + pop), col, ow=2)
        frames.append(finalize(im)); durs.append(70 if k < N2 - 1 else 2000)
    save_gif(frames, durs, f"fish_catch_{rarity}.gif")

def gif_fail():
    frames, N = [], 20
    for f in range(N):
        im = water(f, 20); p = f / (N - 1)
        lay = layer()
        fx = lerp(TARGET[0], 520, ease(min(1, p * 1.2))); fy = HZ + 40 + 8 * math.sin(f * .9)
        paste_center(lay, fish_sprite(26, 10, (8, 24, 44), 140, 1), fx, fy, 0)
        im = comp(im, lay)
        bob = (TARGET[0] + 2 * p, TARGET[1] + 1.5 * math.sin(f * .6))
        rod_and_line(im, (84, 48 - 5 * min(1, p * 3)), bob, sag=18 * min(1, p * 3), line_col=(200, 200, 210))
        im = ripples(im, TARGET[0], TARGET[1] + 3, [(p * 1.5) % 1])
        bobber(im, *bob)
        im = ImageEnhance.Color(im.convert("RGB")).enhance(1 - .55 * min(1, p * 2)).convert("RGBA")
        g = G(im)
        if p > .3: g.text(240, 52, "KABUR...", 26 * min(1, (p - .3) * 6), (255, 130, 130), ow=2)
        frames.append(finalize(im))
    save_gif(frames, [70] * (N - 1) + [1800], "fish_fail.gif")

def gif_junk():
    frames, N = [], 22
    boot = Image.new("RGBA", (u(60), u(60)), (0, 0, 0, 0)); g = G(boot)
    g.poly([(18, 6), (34, 6), (34, 34), (54, 40), (56, 52), (14, 52), (14, 34)], (110, 74, 44, 255))
    g.poly([(14, 46), (56, 46), (56, 52), (14, 52)], (60, 40, 26, 255))
    g.line([(18, 14), (34, 14)], (150, 110, 70, 255), 2)
    g.line([(18, 22), (34, 22)], (150, 110, 70, 255), 2)
    for f in range(N):
        im = water(f, 22); p = min(1, f / 14)
        bx, by = lerp(TARGET[0], 170, ease(p)), lerp(HZ + 20, 70, ease(p)) - 40 * math.sin(math.pi * p)
        rod_and_line(im, (84, 48), (bx, by - 22), sag=6 * (1 - p))
        im = droplets(im, TARGET[0], HZ + 14, min(1, f / 10), seed=6)
        paste_center(im, boot, bx, by, 18 * math.sin(f * .6) * (1 - p * .3))
        g = G(im)
        for k in range(3):                                            # rumput laut menggantung
            g.line([(bx - 6 + k * 6, by + 20), (bx - 8 + k * 6 + 3 * math.sin(f * .8 + k), by + 36)], (70, 150, 70), 2.2)
        if f > 10: g.text(300, 50, "ZONK!", 26 * min(1, (f - 10) / 4), (230, 210, 170), ow=2)
        frames.append(finalize(im))
    save_gif(frames, [65] * (N - 1) + [1800], "fish_junk.gif")

if __name__ == "__main__":
    gif_cast(); gif_wait(); gif_bite(); gif_fail(); gif_junk()
    for r in RARITY: gif_catch(r)
