#!/usr/bin/env python3
"""Sky Jellyfish — procedural art for make.fun ai-excited-01.

Renders at 2048x2048 with PIL, downscales to 1024x1024, writes entry.png
beside this file. If the PNG exceeds 1 MiB, JPEG bytes (quality 90) are
written into entry.png instead (allowed by the rules: format is detected
by first bytes).
"""
import io
import math
import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

random.seed(11)
S = 2048
HERE = os.path.dirname(os.path.abspath(__file__))


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def screen(base, layer):
    return ImageChops.screen(base, layer)


def add_rgba(base, layer):
    base.alpha_composite(layer)


# ---------------------------------------------------------------- sky
def make_sky():
    top = (3, 3, 17)
    mid = (15, 8, 44)
    low = (40, 17, 76)
    hor = (22, 9, 44)
    img = Image.new("RGB", (S, S))
    d = ImageDraw.Draw(img)
    for y in range(S):
        t = y / S
        if t < 0.55:
            c = lerp(top, mid, t / 0.55)
        elif t < 0.85:
            c = lerp(mid, low, (t - 0.55) / 0.30)
        else:
            c = lerp(low, hor, (t - 0.85) / 0.15)
        d.line([(0, y), (S, y)], fill=c)
    return img


def glow_blob(img, center, radius, color, strength=1.0):
    layer = Image.new("RGB", (S, S), (0, 0, 0))
    d = ImageDraw.Draw(layer)
    x, y = center
    d.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color)
    layer = layer.filter(ImageFilter.GaussianBlur(radius * 0.55))
    if strength < 1.0:
        layer = layer.point(lambda v: int(v * strength))
    return screen(img, layer)


img = make_sky()

# ambient glows: main halo behind jellyfish + horizon glow (silhouette pop)
img = glow_blob(img, (1230, 700), 780, (26, 60, 92))
img = glow_blob(img, (1230, 640), 480, (52, 30, 96))
img = glow_blob(img, (1024, 1980), 900, (44, 18, 66), 0.8)
img = img.convert("RGBA")

# ---------------------------------------------------------------- stars
stars = Image.new("RGBA", (S, S), (0, 0, 0, 0))
sd = ImageDraw.Draw(stars)
for _ in range(520):
    x = random.uniform(0, S)
    y = random.uniform(0, S * 0.92)
    # fewer stars where the jellyfish will be
    if math.hypot(x - 1230, y - 700) < 620 and random.random() < 0.75:
        continue
    r = random.choice([1.2, 1.6, 2.0, 2.6, 3.4])
    a = random.randint(50, 210)
    tint = random.choice([(255, 255, 255), (190, 225, 255), (255, 240, 210)])
    sd.ellipse([x - r, y - r, x + r, y + r], fill=tint + (a,))
    if r > 3.0:  # tiny cross sparkle on the brightest
        sd.line([(x - 9, y), (x + 9, y)], fill=tint + (70,), width=2)
        sd.line([(x, y - 9), (x, y + 9)], fill=tint + (70,), width=2)
add_rgba(img, stars)

# ---------------------------------------------------------------- moon (top-left crescent)
moon_mask = Image.new("L", (S, S), 0)
md = ImageDraw.Draw(moon_mask)
mx, my, mr = 268, 252, 96
md.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=255)
md.ellipse([mx - mr + 74, my - mr - 34, mx + mr + 74, my + mr - 34], fill=0)
moon_mask = moon_mask.filter(ImageFilter.GaussianBlur(2))
moon = Image.new("RGBA", (S, S), (238, 240, 220, 0))
moon.putalpha(moon_mask.point(lambda v: int(v * 0.92)))
# soft halo behind moon
img = glow_blob(img.convert("RGB"), (mx, my), 190, (30, 32, 40), 0.9).convert("RGBA")
add_rgba(img, moon)

# ================================================================ JELLYFISH
CX, CY = 1235, 660          # bell centre
BW, BH = 565, 545           # bell half-width / dome height
BELLY = CY + 250            # bell bottom edge baseline
TILT = 0.11                 # right side higher: bell ascending to the upper-right

# ---------------------------------------------------------------- tentacles (behind bell)
def bezier(p0, p1, p2, p3, n=90):
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]
        pts.append((x, y))
    return pts


def draw_ribbon(layer, pts, w0, color, a0, a1, w1=1.5):
    d = ImageDraw.Draw(layer)
    n = len(pts)
    for i in range(n - 1):
        t = i / (n - 1)
        w = (w0 * (1 - t) + w1 * t) * (0.75 + 0.25 * math.sin(t * math.pi))
        a = int(a0 * (1 - t) + a1 * t)
        # segment quad using local tangent normal
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        dx, dy = x1 - x0, y1 - y0
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        hw = w / 2
        d.polygon([(x0 - nx * hw, y0 - ny * hw), (x0 + nx * hw, y0 + ny * hw),
                   (x1 + nx * hw, y1 + ny * hw), (x1 - nx * hw, y1 - ny * hw)],
                  fill=color + (a,))


tent_glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
tent = Image.new("RGBA", (S, S), (0, 0, 0, 0))

tent_specs = []
# long outer tentacles streaming down-left
for i in range(20):
    fx = (i / 19.0) * 2 - 1                      # -1 .. 1 across bell
    ox = CX + fx * BW * 0.82
    oy = BELLY - abs(fx) * 90 + random.uniform(-14, 14)
    oy = BELLY - (ox - CX) * TILT - abs(fx) * 90 + random.uniform(-14, 14)
    length = random.uniform(520, 1180) * (1.0 - abs(fx) * 0.15)
    drift = (random.uniform(280, 580) + fx * 60) * (1.0 - abs(fx) * 0.38)  # swept left, edges less
    sway = random.uniform(-170, 170)
    p0 = (ox, oy)
    p1 = (ox - drift * 0.10 + sway * 0.45, oy + length * 0.32)
    p2 = (ox - drift * 0.58 + sway, oy + length * 0.70)
    p3 = (ox - drift + sway * 0.35, oy + length)
    col = random.choice([(64, 210, 255), (120, 120, 255), (232, 90, 255),
                         (64, 230, 235), (170, 80, 255)])
    w = random.uniform(20, 38)
    tent_specs.append((p0, p1, p2, p3, col, w))

# thick wavy oral arms in the centre
arm_specs = []
for i in range(6):
    fx = (i / 5.0) * 2 - 1
    ox = CX + fx * BW * 0.38
    oy = BELLY - 30 - abs(fx) * 40
    length = random.uniform(520, 760)
    drift = random.uniform(240, 420)
    phase = random.uniform(0, 6.28)
    pts = []
    for j in range(91):
        t = j / 90
        x = ox - drift * t + math.sin(t * 7.0 + phase) * 34 * t
        y = oy + length * t
        pts.append((x, y))
    arm_specs.append((pts, random.choice([(255, 110, 235), (150, 90, 255), (90, 200, 255)])))

for (p0, p1, p2, p3, col, w) in tent_specs:
    pts = bezier(p0, p1, p2, p3)
    draw_ribbon(tent_glow, pts, w * 3.4, col, 60, 6)
    draw_ribbon(tent, pts, w, col, 185, 26)
    draw_ribbon(tent, pts, w * 0.38, (215, 250, 255), 150, 10)
for pts, col in arm_specs:
    draw_ribbon(tent_glow, pts, 120, col, 55, 8)
    draw_ribbon(tent, pts, 46, col, 130, 30)
    draw_ribbon(tent, pts, 18, (240, 235, 255), 120, 16)

add_rgba(img, tent_glow.filter(ImageFilter.GaussianBlur(16)))
add_rgba(img, tent)

# ---------------------------------------------------------------- bell
def dome_points(cx, cy_base, hw, hh, scallops=7, depth=26, shrink=1.0, dy=0.0):
    pts = []
    steps = 72
    for i in range(steps + 1):                    # top arc, left -> right
        ang = math.pi - (i / steps) * math.pi
        x = cx + math.cos(ang) * hw * shrink
        y = cy_base - math.sin(ang) * hh * shrink - (x - cx) * TILT + dy
        pts.append((x, y))
    for i in range(1, steps + 1):                 # bottom edge, right -> left, scalloped
        t = i / steps
        x = cx + hw * shrink - t * 2 * hw * shrink
        y = cy_base + math.sin(t * math.pi * scallops) * depth * shrink - (x - cx) * TILT + dy
        pts.append((x, y))
    return pts


bell = Image.new("RGBA", (S, S), (0, 0, 0, 0))
bd = ImageDraw.Draw(bell)
layers = [
    (1.00, (196, 52, 226, 165)),
    (0.92, (150, 62, 250, 180)),
    (0.82, (96, 96, 255, 195)),
    (0.70, (56, 168, 255, 205)),
    (0.57, (62, 208, 250, 215)),
    (0.43, (120, 232, 250, 220)),
]
for shrink, col in layers:
    # inner layers rise and drift slightly left so the gradient feels organic
    bd.polygon(dome_points(CX - (1 - shrink) * 60, BELLY, BW, BH,
                           shrink=shrink, dy=-(1 - shrink) * 46), fill=col)
bell = bell.filter(ImageFilter.GaussianBlur(5))
# bright off-centre core: a soft blob, not a concentric semicircle
core = Image.new("RGBA", (S, S), (0, 0, 0, 0))
ImageDraw.Draw(core).ellipse([CX - 255, CY - 170, CX + 185, CY + 195],
                             fill=(178, 243, 255, 185))
bell.alpha_composite(core.filter(ImageFilter.GaussianBlur(58)))

# clip inner detail to the bell mask
bell_mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(bell_mask).polygon(dome_points(CX, BELLY, BW, BH), fill=255)

detail = Image.new("RGBA", (S, S), (0, 0, 0, 0))
dd = ImageDraw.Draw(detail)
# inner filaments: independent strands from an inner arc down to the rim
for i in range(11):
    fx = (i / 10.0) * 2 - 1
    sx = CX + fx * BW * 0.52
    sy = BELLY - BH * 0.60 - (sx - CX) * TILT + abs(fx) * 120
    x_end = CX + fx * BW * 0.90
    y_end = BELLY - (x_end - CX) * TILT - abs(fx) * 55 + math.sin((fx + 1) * math.pi * 3.5) * 16
    bow = fx * 36 + random.uniform(-14, 14)
    pts = bezier((sx, sy),
                 (sx + bow, sy + (y_end - sy) * 0.36),
                 (x_end - bow * 0.5, sy + (y_end - sy) * 0.72),
                 (x_end, y_end), n=40)
    dd.line(pts, fill=(235, 255, 255, 70), width=4)
# inner glowing orbs
for _ in range(26):
    ang = random.uniform(0, 6.28)
    rr = random.uniform(0, 0.72)
    x = CX + math.cos(ang) * BW * rr
    y = CY - abs(math.sin(ang)) * BH * rr * 0.4 + BH * rr * 0.25
    if y > BELLY - 30:
        continue
    r = random.uniform(6, 20)
    c = random.choice([(255, 255, 255), (140, 240, 255), (255, 170, 245)])
    dd.ellipse([x - r, y - r, x + r, y + r], fill=c + (random.randint(70, 150),))
detail.putalpha(ImageChops.multiply(detail.getchannel("A"), bell_mask))
add_rgba(bell, detail)
add_rgba(img, bell)

# bell glow halo (screen-blended, behind rim crispness is kept by drawing rim after)
halo = Image.new("RGB", (S, S), (0, 0, 0))
hd = ImageDraw.Draw(halo)
hd.ellipse([CX - BW * 0.95, CY - BH * 0.95, CX + BW * 0.95, CY + BH * 0.8], fill=(30, 70, 86))
img = screen(img.convert("RGB"), halo.filter(ImageFilter.GaussianBlur(90))).convert("RGBA")
# re-composite a crisp bell copy so the halo doesn't wash it out
add_rgba(img, bell.filter(ImageFilter.GaussianBlur(1)))

# crisp rim light + scalloped bottom band
rim = Image.new("RGBA", (S, S), (0, 0, 0, 0))
rd = ImageDraw.Draw(rim)
arc_pts = []
for i in range(121):
    ang = math.pi - (i / 120) * math.pi
    ax = CX + math.cos(ang) * BW
    arc_pts.append((ax, BELLY - math.sin(ang) * BH - (ax - CX) * TILT))
rd.line(arc_pts, fill=(190, 250, 255, 235), width=10)
scallop_pts = []
for i in range(161):
    t = i / 160
    sx = CX - BW + t * 2 * BW
    scallop_pts.append((sx, BELLY + math.sin(t * math.pi * 7) * 26 - (sx - CX) * TILT))
rd.line(scallop_pts, fill=(255, 96, 235, 220), width=16)
rd.line([(x, y + 14) for x, y in scallop_pts], fill=(120, 235, 255, 160), width=7)
add_rgba(img, rim.filter(ImageFilter.GaussianBlur(2)))
add_rgba(img, rim)

# specular highlight near top of bell, clipped inside the bell
spec = Image.new("RGBA", (S, S), (0, 0, 0, 0))
ImageDraw.Draw(spec).ellipse([CX - 330, CY - BH + 30, CX + 30, CY - BH + 260],
                             fill=(255, 255, 255, 105))
spec = spec.filter(ImageFilter.GaussianBlur(38))
spec.putalpha(ImageChops.multiply(spec.getchannel("A"), bell_mask))
add_rgba(img, spec)

# ---------------------------------------------------------------- particles / bokeh
bokeh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
bk = ImageDraw.Draw(bokeh)
for _ in range(90):
    # trail down-left of the jellyfish + rising around it
    t = random.random()
    x = CX + random.uniform(-950, 620) - t * 260
    y = CY + random.uniform(-430, 980)
    r = random.uniform(8, 44)
    c = random.choice([(110, 225, 255), (255, 130, 240), (255, 205, 110), (170, 150, 255)])
    a = random.randint(18, 66)
    bk.ellipse([x - r, y - r, x + r, y + r], outline=c + (a,), width=3)
    bk.ellipse([x - r * 0.3, y - r * 0.3, x + r * 0.3, y + r * 0.3], fill=c + (a // 2,))
add_rgba(img, bokeh.filter(ImageFilter.GaussianBlur(6)))

dots = Image.new("RGBA", (S, S), (0, 0, 0, 0))
dk = ImageDraw.Draw(dots)
for _ in range(150):
    x = CX + random.uniform(-1050, 700)
    y = CY + random.uniform(-480, 1150)
    r = random.uniform(2.5, 8)
    c = random.choice([(160, 240, 255), (255, 180, 245), (255, 215, 130)])
    dk.ellipse([x - r, y - r, x + r, y + r], fill=c + (random.randint(90, 220),))
add_rgba(img, dots)

# ---------------------------------------------------------------- city skyline
city = Image.new("RGBA", (S, S), (0, 0, 0, 0))
cd = ImageDraw.Draw(city)
buildings = []
x = -20
while x < S + 20:
    w = random.randint(110, 240)
    h = random.randint(170, 430)
    buildings.append((x, w, h))
    x += w + random.randint(6, 30)
ROOF_X, ROOF_W = 600, 250
# force one hero building for the figures
buildings.append((ROOF_X, ROOF_W, 372))
for (bx, bw_, bh_) in buildings:
    cd.rectangle([bx, S - bh_, bx + bw_, S], fill=(4, 4, 11, 255))
    if random.random() < 0.4:
        cd.rectangle([bx + bw_ * 0.42, S - bh_ - 34, bx + bw_ * 0.52, S - bh_], fill=(4, 4, 11, 255))
# lit windows
for (bx, bw_, bh_) in buildings:
    for wx in range(int(bx) + 16, int(bx + bw_) - 16, 30):
        for wy in range(S - bh_ + 20, S - 18, 38):
            if random.random() < 0.30:
                warm = random.choice([(255, 196, 96), (255, 170, 80), (190, 220, 255)])
                cd.rectangle([wx, wy, wx + 11, wy + 15], fill=warm + (random.randint(120, 235),))
add_rgba(img, city)

# ---------------------------------------------------------------- rooftop figures (scale cue)
roof_y = S - 372
fig = Image.new("RGBA", (S, S), (0, 0, 0, 0))
fd = ImageDraw.Draw(fig)
INK = (2, 2, 6, 255)


def figure(cx, base, h, pointing=False):
    head_r = h * 0.11
    head_y = base - h + head_r
    fd.ellipse([cx - head_r, head_y - head_r, cx + head_r, head_y + head_r], fill=INK)
    shoulder = base - h * 0.78
    fd.polygon([(cx - h * 0.13, base), (cx - h * 0.10, shoulder),
                (cx + h * 0.10, shoulder), (cx + h * 0.13, base)], fill=INK)
    if pointing:  # one arm raised toward the jellyfish
        fd.line([(cx + h * 0.06, shoulder + 4), (cx + h * 0.42, shoulder - h * 0.34)],
                fill=INK, width=int(h * 0.07))
    else:
        fd.line([(cx - h * 0.08, shoulder + 4), (cx - h * 0.20, base - h * 0.38)],
                fill=INK, width=int(h * 0.06))


figure(ROOF_X + 52, roof_y, 112, pointing=True)
figure(ROOF_X + 132, roof_y, 96)
figure(ROOF_X + 198, roof_y, 78)
add_rgba(img, fig)

# ---------------------------------------------------------------- vignette + finish
vig = Image.new("L", (S, S), 0)
vd = ImageDraw.Draw(vig)
vd.ellipse([-S * 0.28, -S * 0.28, S * 1.28, S * 1.28], fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(260))
dark = Image.new("RGBA", (S, S), (2, 2, 8, 255))
img = Image.composite(img, dark, vig)

out = img.convert("RGB").resize((1024, 1024), Image.LANCZOS)
buf = io.BytesIO()
out.save(buf, "PNG", optimize=True)
data = buf.getvalue()
fmt = "PNG"
if len(data) > 1048576:
    buf = io.BytesIO()
    out.save(buf, "JPEG", quality=90)
    data = buf.getvalue()
    fmt = "JPEG"
with open(os.path.join(HERE, "entry.png"), "wb") as f:
    f.write(data)
print(f"wrote entry.png format={fmt} bytes={len(data)} size={out.size}")
