import math, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

W, H, FPS = 1080, 1920, 24
GAP, TAIL = 0.45, 0.9

PALETTES = [  # (top, bottom, accent)
    ((18, 32, 74), (60, 40, 120), (255, 196, 61)),
    ((8, 60, 70), (20, 110, 110), (120, 255, 214)),
    ((70, 20, 60), (150, 50, 90), (255, 150, 170)),
    ((20, 40, 90), (30, 100, 170), (120, 200, 255)),
    ((50, 30, 90), (110, 50, 150), (255, 214, 102)),
    ((15, 50, 40), (30, 110, 70), (190, 255, 120)),
]


def fc(query, fallback):
    try:
        p = subprocess.check_output(["fc-match", "-f", "%{file}", query], text=True).strip()
        if p:
            return p
    except Exception:
        pass
    return fallback


AR_FONT = fc("Noto Naskh Arabic:bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
EN_FONT = fc("Noto Sans:bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")


def shape(t, ar):
    return get_display(arabic_reshaper.reshape(t)) if ar else t


def mix(a, b, f):
    return tuple(int(a[i] * (1 - f) + b[i] * f) for i in range(3))


def gradient(top, bot):
    t = np.linspace(0, 1, H)[:, None, None]
    arr = np.array(top) * (1 - t) + np.array(bot) * t
    arr = np.repeat(arr, W, axis=1).astype("uint8")
    return Image.fromarray(arr, "RGB")


def wrap(d, text, font, maxw, ar):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(shape(trial, ar), font=font) <= maxw:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def text_block(d, text, font, fill, y, maxw, ar, stroke=0):
    lh = int(font.size * 1.3)
    lines = wrap(d, text, font, maxw, ar)
    for i, ln in enumerate(lines):
        d.text((W / 2, y + i * lh), shape(ln, ar), font=font, fill=fill, anchor="ma",
               stroke_width=stroke, stroke_fill=(0, 0, 0, 170))
    return y + len(lines) * lh, len(lines), lh


def build_layer(title, sc, ar, accent, fonts):
    fcap, fnar, ftit = fonts
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    text_block(d, title, ftit, accent + (255,), 120, 900, ar)
    text_block(d, sc["caption"], fcap, (255, 255, 255, 255), 930, 920, ar, stroke=4)
    lines = wrap(d, sc["narration"], fnar, 880, ar)
    lh = int(fnar.size * 1.35)
    y0 = 1290
    d.rounded_rectangle([60, y0 - 30, W - 60, y0 + len(lines) * lh + 20], radius=40, fill=(0, 0, 0, 120))
    for i, ln in enumerate(lines):
        d.text((W / 2, y0 + i * lh), shape(ln, ar), font=fnar, fill=(240, 240, 255, 255), anchor="ma")
    return L


# ---------- 2D motion (Arabic reels) ----------
def draw_2d(d, t, si, accent, bgmid):
    rnd = random.Random(si * 97 + 5)
    for i in range(14):
        bx, by = rnd.randint(60, W - 60), rnd.randint(200, H - 200)
        x = bx + 60 * math.sin(t * 0.8 + i)
        y = by + 50 * math.cos(t * 0.6 + i * 1.3)
        r = 40 + 30 * ((i * 7) % 5)
        col = mix(bgmid, (255, 255, 255), 0.07 + 0.04 * (i % 3))
        if i % 2 == 0:
            d.ellipse([x - r, y - r, x + r, y + r], fill=col)
        else:
            d.rounded_rectangle([x - r, y - r, x + r, y + r], radius=r // 3, fill=col)
    cx, cy = W / 2, 560
    d.ellipse([cx - 60, cy - 60, cx + 60, cy + 60], fill=accent)
    for k in range(3):
        r = 150 + k * 80 + 10 * math.sin(t * 2 + k)
        d.ellipse([cx - r, cy - r * 0.55, cx + r, cy + r * 0.55] if k % 2 else [cx - r, cy - r, cx + r, cy + r],
                  outline=accent, width=7)
        a = t * (1.4 - 0.25 * k) + k * 2.1
        ox = cx + r * math.cos(a)
        oy = cy + (r * 0.55 if k % 2 else r) * math.sin(a)
        d.ellipse([ox - 22, oy - 22, ox + 22, oy + 22], fill=(255, 255, 255))


# ---------- 3D-projected hero (English reels) ----------
def fib(n):
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n)
    th = math.pi * (1 + 5 ** 0.5) * i
    return np.stack([np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)], 1)


def torus(nu=44, nv=14):
    u, v = np.meshgrid(np.linspace(0, 2 * math.pi, nu, endpoint=False),
                       np.linspace(0, 2 * math.pi, nv, endpoint=False))
    u, v = u.ravel(), v.ravel()
    return np.stack([(1 + 0.4 * np.cos(v)) * np.cos(u), 0.4 * np.sin(v), (1 + 0.4 * np.cos(v)) * np.sin(u)], 1)


SPH = fib(650)
TOR = torus()
_a = np.linspace(0, 2 * math.pi, 200, endpoint=False)
RING = np.stack([np.cos(_a) * 1.6, np.zeros_like(_a), np.sin(_a) * 1.6], 1)


def rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def project(P, cx, cy, scale):
    z = P[:, 2]
    f = 1 / (1.0 - 0.22 * z)
    return cx + P[:, 0] * scale * f, cy + P[:, 1] * scale * f, z


def dots(d, P, cx, cy, scale, color, bg, r0, r1):
    xs, ys, z = project(P, cx, cy, scale)
    for i in np.argsort(z):
        k = float(np.clip((z[i] + 1.8) / 3.6, 0, 1))
        r = r0 + (r1 - r0) * k
        d.ellipse([xs[i] - r, ys[i] - r, xs[i] + r, ys[i] + r], fill=mix(bg, color, 0.25 + 0.75 * k))


def draw_3d(d, t, si, accent, bgmid):
    cx, cy = W / 2, 570
    ang = t * 0.8 + si * 1.1
    pulse = 1 + 0.05 * math.sin(t * 2)
    kind = si % 3
    # soft floor shadow
    d.ellipse([cx - 260, cy + 340, cx + 260, cy + 385], fill=mix(bgmid, (0, 0, 0), 0.35))
    if kind == 0:
        dots(d, SPH @ (rx(0.4) @ ry(ang)).T, cx, cy, 280 * pulse, accent, bgmid, 3, 8)
        dots(d, RING @ (rx(0.4) @ rz(0.45) @ ry(ang * 1.4)).T, cx, cy, 250, (255, 255, 255), bgmid, 3, 7)
    elif kind == 1:
        dots(d, TOR @ (rx(0.9) @ ry(ang)).T, cx, cy, 215 * pulse, accent, bgmid, 3, 8)
        dots(d, SPH * 0.45 @ (rx(0.2) @ ry(-ang)).T, cx, cy, 250, (255, 255, 255), bgmid, 3, 6)
    else:  # DNA helix
        y = np.linspace(-1.45, 1.45, 46)
        a = y * 2.6 + ang * 1.5
        s1 = np.stack([0.8 * np.cos(a), y, 0.8 * np.sin(a)], 1)
        s2 = np.stack([0.8 * np.cos(a + math.pi), y, 0.8 * np.sin(a + math.pi)], 1)
        M = rx(0.25).T
        s1, s2 = s1 @ M, s2 @ M
        x1, y1, z1 = project(s1, cx, cy, 250 * pulse)
        x2, y2, z2 = project(s2, cx, cy, 250 * pulse)
        for i in range(0, 46, 3):
            d.line([x1[i], y1[i], x2[i], y2[i]], fill=mix(bgmid, (255, 255, 255), 0.45), width=5)
        dots(d, np.vstack([s1, s2]), cx, cy, 250 * pulse, accent, bgmid, 6, 13)


def read_wav(p):
    with wave.open(p) as w:
        return w.readframes(w.getnframes()), w.getframerate()


def render(lang, title, scenes, wavs, out_mp4, audio_path):
    ar = lang == "ar"
    path = AR_FONT if ar else EN_FONT
    fonts = (ImageFont.truetype(path, 118 if ar else 104),
             ImageFont.truetype(path, 54 if ar else 50),
             ImageFont.truetype(path, 56))

    # audio timeline
    pcm, starts, lens, rate = b"", [], [], 24000
    for i, wv in enumerate(wavs):
        data, rate = read_wav(wv)
        starts.append(len(pcm) / 2 / rate)
        extra = TAIL if i == len(wavs) - 1 else GAP
        pcm += data + b"\x00\x00" * int(rate * extra)
        lens.append(len(data) / 2 / rate + extra)
    with wave.open(audio_path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(pcm)
    total = sum(lens)

    bgs, layers = [], []
    for i, sc in enumerate(scenes):
        top, bot, acc = PALETTES[i % len(PALETTES)]
        bgs.append(gradient(top, bot))
        layers.append(build_layer(title, sc, ar, acc, fonts))

    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS),
         "-i", "-", "-i", audio_path, "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out_mp4],
        stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    n = int(total * FPS)
    si = 0
    for f in range(n):
        t = f / FPS
        while si < len(scenes) - 1 and t >= starts[si] + lens[si]:
            si += 1
        top, bot, acc = PALETTES[si % len(PALETTES)]
        img = bgs[si].copy()
        d = ImageDraw.Draw(img)
        mid = mix(top, bot, 0.5)
        (draw_2d if ar else draw_3d)(d, t, si, acc, mid)
        age = t - starts[si]
        a = min(1.0, age / 0.35)
        L = layers[si]
        if a >= 1:
            img.paste(L, (0, 0), L)
        else:
            m = L.getchannel("A").point(lambda p, a=a: int(p * a))
            img.paste(L, (0, int((1 - a) * 50)), m)
        d.rectangle([0, 0, int(W * t / total), 14], fill=acc)
        proc.stdin.write(img.tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg failed")
    return total
