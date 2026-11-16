#!/usr/bin/env python3
"""ai-excited-01 -- a giant glass marble rolling down a rain-slicked
city street at dusk, the whole skyline refracted upside-down inside it.

Pure Python 3.13 standard library. No network, no files read, no
randomness except a fixed seed: two runs write identical bytes.

Writes entry.png (1024x1024) to $MAKEFUN_OUTPUT_DIR or /output.
"""

import math
import os
import random
import struct
import zlib

W = H = 1024
SEED = 20261116

# ---------------------------------------------------------------- framebuffer
buf = bytearray(W * H * 3)


def _idx(x, y):
    return (y * W + x) * 3


def put(x, y, r, g, b):
    if 0 <= x < W and 0 <= y < H:
        i = _idx(x, y)
        buf[i] = r
        buf[i + 1] = g
        buf[i + 2] = b


def blend(x, y, r, g, b, a):
    """Alpha-blend colour (r,g,b) over pixel (x,y); a in [0,1]."""
    if a <= 0.0 or not (0 <= x < W and 0 <= y < H):
        return
    if a >= 1.0:
        put(x, y, r, g, b)
        return
    i = _idx(x, y)
    buf[i] = int(buf[i] + (r - buf[i]) * a)
    buf[i + 1] = int(buf[i + 1] + (g - buf[i + 1]) * a)
    buf[i + 2] = int(buf[i + 2] + (b - buf[i + 2]) * a)


def get(x, y):
    x = max(0, min(W - 1, x))
    y = max(0, min(H - 1, y))
    i = _idx(x, y)
    return buf[i], buf[i + 1], buf[i + 2]


def lerp(a, b, t):
    return a + (b - a) * t


def lerp3(c1, c2, t):
    return (lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t))


def clamp255(v):
    return max(0, min(255, int(v)))


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def disc(cx, cy, rad, color, alpha=1.0):
    """Anti-aliased filled disc."""
    r0 = int(cx - rad - 2)
    r1 = int(cx + rad + 2)
    c0 = int(cy - rad - 2)
    c1 = int(cy + rad + 2)
    for y in range(max(0, c0), min(H, c1 + 1)):
        for x in range(max(0, r0), min(W, r1 + 1)):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            cov = 1.0 - smooth((d - (rad - 1.0)) / 1.5)
            if cov > 0.0:
                blend(x, y, color[0], color[1], color[2], alpha * cov)


def ellipse(cx, cy, rx, ry, color, alpha=1.0):
    r0 = int(cx - rx - 2)
    r1 = int(cx + rx + 2)
    c0 = int(cy - ry - 2)
    c1 = int(cy + ry + 2)
    for y in range(max(0, c0), min(H, c1 + 1)):
        for x in range(max(0, r0), min(W, r1 + 1)):
            d = math.hypot((x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry)
            cov = 1.0 - smooth((d - 0.94) / 0.06)
            if cov > 0.0:
                blend(x, y, color[0], color[1], color[2], alpha * cov)


def hline(x0, x1, y, color, alpha=1.0):
    for x in range(max(0, x0), min(W, x1 + 1)):
        blend(x, y, color[0], color[1], color[2], alpha)


def rect(x0, y0, x1, y1, color, alpha=1.0):
    for y in range(max(0, y0), min(H, y1 + 1)):
        for x in range(max(0, x0), min(W, x1 + 1)):
            blend(x, y, color[0], color[1], color[2], alpha)


# ---------------------------------------------------------------- scene
rng = random.Random(SEED)

SKY_TOP = (10, 8, 38)
SKY_MID = (44, 24, 88)
SKY_LOW = (150, 58, 110)
SKY_HOR = (255, 128, 58)
HORIZON = 660


def sky_color(y):
    t = y / HORIZON
    if t < 0.45:
        return lerp3(SKY_TOP, SKY_MID, t / 0.45)
    if t < 0.8:
        return lerp3(SKY_MID, SKY_LOW, (t - 0.45) / 0.35)
    return lerp3(SKY_LOW, SKY_HOR, (t - 0.8) / 0.2)


def draw_sky():
    for y in range(HORIZON + 1):
        c = sky_color(y)
        r, g, b = clamp255(c[0]), clamp255(c[1]), clamp255(c[2])
        base = y * W * 3
        for x in range(W):
            i = base + x * 3
            buf[i] = r
            buf[i + 1] = g
            buf[i + 2] = b
    # low sun glow on the horizon, left of the marble (the disc itself stays
    # hidden: every horizon gap there is behind a tower or the marble)
    sx, sy = 300, 645
    for y in range(380, HORIZON + 1):
        for x in range(0, 640):
            d = math.hypot(x - sx, (y - sy) * 1.6)
            glow = math.exp(-(d / 260.0) ** 2)
            if glow > 0.01:
                blend(x, y, 255, 170, 80, glow * 0.55)
    # stars, upper sky only
    for _ in range(170):
        x = rng.randrange(0, W)
        y = rng.randrange(0, 380)
        a = rng.uniform(0.25, 0.9) * (1.0 - y / 480.0)
        s = rng.choice([1, 1, 1, 2])
        if s == 1:
            blend(x, y, 235, 235, 255, a)
        else:
            blend(x, y, 235, 235, 255, a * 0.5)
            blend(x + 1, y, 235, 235, 255, a * 0.5)
            blend(x, y + 1, 235, 235, 255, a * 0.5)
            blend(x + 1, y + 1, 235, 235, 255, a * 0.5)


def draw_skyline(y_base, color, win_color, seed, min_h, max_h, lit_p):
    """Silhouette skyline with lit windows; returns list of (x0,x1,top)."""
    r = random.Random(seed)
    towers = []
    x = -20
    while x < W + 20:
        w = r.randrange(46, 120)
        h = r.randrange(min_h, max_h)
        top = y_base - h
        rect(x, top, x + w, y_base, color)
        # rooftop antenna on some towers
        if r.random() < 0.4:
            ax = x + w // 2
            rect(ax, top - r.randrange(14, 42), ax + 2, top, color)
            blend(ax + 1, top - r.randrange(14, 42), 255, 90, 90, 0.9)
        towers.append((x, x + w, top))
        # windows
        for wy in range(top + 12, y_base - 8, 14):
            for wx in range(x + 8, x + w - 6, 12):
                if r.random() < lit_p:
                    wc = win_color if r.random() < 0.85 else (150, 200, 255)
                    rect(wx, wy, wx + 4, wy + 6, wc, r.uniform(0.5, 1.0))
        x += w + r.randrange(2, 26)
    return towers


def draw_street():
    for y in range(HORIZON, H):
        t = (y - HORIZON) / (H - HORIZON)
        c = lerp3((26, 22, 40), (13, 11, 22), t)
        r, g, b = clamp255(c[0]), clamp255(c[1]), clamp255(c[2])
        base = y * W * 3
        for x in range(W):
            i = base + x * 3
            buf[i] = r
            buf[i + 1] = g
            buf[i + 2] = b
    # wet sheen: warm horizon light smeared down the centre-left of the road
    for y in range(HORIZON, H):
        t = (y - HORIZON) / (H - HORIZON)
        half = 50 + t * 200
        for x in range(int(300 - half), int(300 + half)):
            d = abs(x - 300) / half
            a = (1.0 - d) * (1.0 - d) * 0.34 * (0.4 + 0.6 * t)
            blend(x, y, 255, 130, 60, a)
    # cool sky reflection streaks, left side
    for y in range(HORIZON + 30, H, 7):
        x0 = rng.randrange(40, 420)
        ln = rng.randrange(30, 160)
        a = rng.uniform(0.05, 0.16)
        for x in range(x0, x0 + ln):
            blend(x, y, 120, 110, 220, a)
    # puddles: sky-coloured ellipses
    for (px_, py_, rx_, ry_) in [(300, 760, 150, 16), (820, 900, 190, 20),
                                 (180, 950, 170, 18), (620, 990, 220, 16)]:
        ellipse(px_, py_, rx_, ry_, (96, 84, 170), 0.35)
        ellipse(px_, py_, rx_ * 0.7, ry_ * 0.6, (200, 120, 110), 0.2)


def draw_speed_lines(cx, cy, r):
    """Horizontal motion streaks trailing behind (left of) the marble."""
    for _ in range(34):
        y = int(cy + rng.uniform(-r * 0.6, r * 0.6))
        x1 = int(cx - r * rng.uniform(0.55, 1.0))
        ln = rng.randrange(60, 200)
        x0 = max(120, x1 - ln)
        a = rng.uniform(0.08, 0.30)
        col = (255, 200, 140) if rng.random() < 0.4 else (180, 190, 255)
        for x in range(max(0, x0), x1):
            fade = (x - x0) / max(1, ln)
            blend(x, y, col[0], col[1], col[2], a * fade)
            blend(x, y + 1, col[0], col[1], col[2], a * fade * 0.6)


def draw_marble(cx, cy, r):
    # Snapshot the scene FIRST: the loop below overwrites buf as it goes,
    # and the ball's lower half samples scene rows the upper half already
    # painted. Sampling the live buffer feeds the ball its own output back
    # into itself (a bright pink wash below the equator). The snapshot is
    # the true scene.
    snap = bytes(buf)

    def sget(x, y):
        x = max(0, min(W - 1, x))
        y = max(0, min(H - 1, y))
        i = (y * W + x) * 3
        return snap[i], snap[i + 1], snap[i + 2]

    # contact shadow
    ellipse(cx + 10, cy + r + 14, int(r * 1.08), 26, (0, 0, 0), 0.55)
    ellipse(cx + 10, cy + r + 10, int(r * 0.8), 18, (0, 0, 0), 0.5)
    # glass body: sample the already-drawn scene, flipped and squeezed
    for y in range(cy - r - 2, cy + r + 3):
        for x in range(cx - r - 2, cx + r + 3):
            dx = (x + 0.5 - cx) / r
            dy = (y + 0.5 - cy) / r
            d = math.hypot(dx, dy)
            if d > 1.0:
                continue
            cov = 1.0 - smooth((d - 0.985) / 0.015)
            # fisheye refraction: centre samples a tight patch, edge a wide one
            k = 0.34 + 0.42 * d * d
            sx = int(cx + dx * r * k * 1.25)
            sy = int(cy - dy * r * k * 2.3)
            sr, sg, sb = sget(sx, sy)
            # glass tint + brightening: the ball gathers light, it must glow
            tint = 1.0 - 0.22 * d
            nr = clamp255(sr * 1.38 * tint + 30 * (1.0 - d))
            ng = clamp255(sg * 1.30 * tint + 32 * (1.0 - d))
            nb = clamp255(sb * 1.42 * tint + 44 * (1.0 - d))
            # warm dusk band refracted across the ball's middle (soft, wide)
            band = math.exp(-((dy + 0.05) / 0.5) ** 2) * (1.0 - d * 0.6)
            nr = clamp255(nr + 40 * band)
            ng = clamp255(ng + 22 * band)
            nb = clamp255(nb + 8 * band)
            # edge darkening (thick glass rim) except on the sun side
            ang = math.atan2(dy, dx)
            sun = max(0.0, math.cos(ang - 2.86))
            edge = smooth((d - 0.82) / 0.18)
            nr = clamp255(nr * (1.0 - 0.55 * edge) + 255 * 0.35 * edge * sun)
            ng = clamp255(ng * (1.0 - 0.55 * edge) + 190 * 0.30 * edge * sun)
            nb = clamp255(nb * (1.0 - 0.45 * edge) + 120 * 0.25 * edge * sun)
            blend(x, y, nr, ng, nb, cov)
    # crisp rim: bright arc on the sun side, thin dark outline elsewhere
    for i in range(720):
        ang = -math.pi + i * (2.0 * math.pi) / 720.0
        x = cx + math.cos(ang) * (r - 1)
        y = cy + math.sin(ang) * (r - 1)
        sun = max(0.0, math.cos(ang - 2.86))
        a = 0.25 + 0.75 * sun
        blend(int(x), int(y), 255, 235, 200, a)
        blend(int(x), int(y) + 1, 255, 235, 200, a * 0.5)
    # specular highlight, upper left
    hx, hy = cx - int(r * 0.38), cy - int(r * 0.42)
    for yy in range(hy - 90, hy + 90):
        for xx in range(hx - 110, hx + 110):
            d = math.hypot((xx - hx) / 105.0, (yy - hy) / 78.0)
            if d < 1.0:
                a = (1.0 - d) ** 2 * 0.85
                blend(xx, yy, 255, 255, 255, a)
    # small secondary sparkle, high on the ball
    disc(cx - int(r * 0.55), cy - int(r * 0.62), 7, (255, 250, 230), 0.7)
    disc(cx - int(r * 0.55), cy - int(r * 0.62), 3, (255, 255, 255), 0.9)


def draw_spray(cx, cy, r):
    """Water spray and droplets kicked up where the marble meets the road."""
    gy = cy + r
    for _ in range(90):
        ang = rng.uniform(-2.6, -0.4)
        dist = rng.uniform(0, 150)
        x = cx + math.cos(ang) * dist * 1.6 + rng.uniform(-30, 30)
        y = gy - abs(math.sin(ang)) * dist * 0.9 - rng.uniform(0, 26)
        s = rng.choice([1, 1, 2, 2, 3])
        a = rng.uniform(0.35, 0.9)
        col = (220, 230, 255) if rng.random() < 0.7 else (255, 210, 160)
        disc(int(x), int(y), s, col, a)
    # a low sheet of spray hugging the road behind the contact point
    for _ in range(60):
        x = int(cx - rng.uniform(40, 320))
        y = int(gy + rng.uniform(-14, 6))
        ln = rng.randrange(14, 60)
        a = rng.uniform(0.15, 0.5)
        for xx in range(x, x + ln):
            blend(xx, y, 210, 220, 255, a * (1.0 - (xx - x) / ln))


def draw_person():
    """One tiny umbrella figure at the kerb, dwarfed by the marble."""
    x, y = 232, 884  # feet
    col = (6, 5, 14)
    # umbrella (thicker arc)
    for i in range(48):
        ang = math.pi + i * math.pi / 48.0
        ux = x + math.cos(ang) * 26
        uy = (y - 80) + math.sin(ang) * 20
        for dy in (0, 1, 2):
            blend(int(ux), int(uy) + dy, col[0], col[1], col[2], 1.0)
    rect(x - 2, y - 80, x + 2, y - 54, col)
    disc(x, y - 78, 9, col)
    rect(x - 5, y - 70, x + 5, y - 34, col)
    rect(x - 5, y - 34, x - 2, y, col)
    rect(x + 2, y - 34, x + 5, y, col)
    # faint warm rim from the street light
    blend(x + 5, y - 70, 255, 170, 90, 0.7)
    blend(x + 6, y - 52, 255, 170, 90, 0.5)


def draw_rain():
    """Fine diagonal rain, barely there, mostly in the sky."""
    for _ in range(240):
        x = rng.randrange(0, W)
        y = rng.randrange(0, 700)
        ln = rng.randrange(8, 18)
        a = rng.uniform(0.05, 0.14)
        for i in range(ln):
            blend(x + i // 3, y + i, 200, 210, 255, a)


# ---------------------------------------------------------------- PNG encode
def png_bytes():
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        raw += buf[y * W * 3:(y + 1) * W * 3]
    comp = zlib.compress(bytes(raw), 6)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


def main():
    draw_sky()
    draw_skyline(HORIZON, (24, 18, 54), (255, 190, 110), seed=7,
                 min_h=90, max_h=260, lit_p=0.16)
    draw_skyline(HORIZON, (13, 9, 32), (255, 170, 90), seed=21,
                 min_h=200, max_h=430, lit_p=0.10)
    draw_street()
    cx, cy, r = 590, 560, 298
    draw_speed_lines(cx, cy, r)
    draw_marble(cx, cy, r)
    # faint warm light spilling from the ball onto the wet road
    ellipse(cx, cy + r + 16, int(r * 0.95), 14, (255, 140, 70), 0.12)
    draw_spray(cx, cy, r)
    draw_person()
    draw_rain()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(png_bytes())
    print("wrote", path)


if __name__ == "__main__":
    main()
