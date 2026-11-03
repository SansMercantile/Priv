"""Priv campaign design system: brand tokens, fonts, and drawing helpers."""
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
BRAND_DIR = os.path.join(ROOT, "brand")

# --- Brand tokens (sansmercantile-nexus/tailwind.config.ts "System colors") --
GOLD = (212, 175, 55)          # #d4af37  priv-primary / nexus-gold
GOLD_LT = (240, 214, 122)      # #f0d67a
GOLD_DK = (138, 109, 31)       # #8a6d1f
NAVY = (10, 14, 39)            # #0a0e27  nexus-dark
NAVY_DEEP = (5, 7, 21)
CYAN = (0, 212, 255)           # #00d4ff  nexus-accent
PURPLE = (124, 58, 237)        # #7c3aed  nexus-purple
WHITE = (255, 255, 255)
MUTED = (148, 163, 184)
GREEN = (52, 211, 153)
ROSE = (251, 113, 133)
CRIMSON = (178, 34, 52)        # flower mark reference

FONTS = {
    "display": [r"C:\Windows\Fonts\seguibl.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    "display_alt": [r"C:\Windows\Fonts\bahnschrift.ttf",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    "semi": [r"C:\Windows\Fonts\seguisb.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "bold": [r"C:\Windows\Fonts\segoeuib.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "body": [r"C:\Windows\Fonts\segoeui.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    "mono": [r"C:\Windows\Fonts\consolab.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"],
    "mono_r": [r"C:\Windows\Fonts\consola.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"],
    "serif": [r"C:\Windows\Fonts\georgiab.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"],
}
_FONT_DEFAULT = ["C:/Windows/Fonts/segoeui.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]

LOGO_MARK = os.path.join(ASSETS, "brand", "priv-mark.png")      # canonical mark
LOGO_CARNATION = r"C:\Users\kpasc\source\repos\Priv\public\priv-icon-512.png"
LOGO_512 = LOGO_MARK if os.path.exists(LOGO_MARK) else LOGO_CARNATION
LOGO_192 = r"C:\Users\kpasc\source\repos\Priv\public\priv-icon-192.png"
LOGO_HI = r"C:\Users\kpasc\source\repos\constellation\priv\website\logo.png"
AVATAR_ART = (
    r"C:\Users\kpasc\source\repos\Priv\src\assets\images"
    r"\chat_avatar_1779278082106.png"
)

SITE = "priv.sansmercantile.com"
SITE_FULL = "https://priv.sansmercantile.com"
DOWNLOADS = "https://www.sansmercantile.com/priv"

_font_cache = {}


def font(kind, size):
    key = (kind, size)
    if key not in _font_cache:
        candidates = FONTS.get(kind, _FONT_DEFAULT)
        if isinstance(candidates, str):
            candidates = [candidates]
        path = next((p for p in candidates if os.path.exists(p)), candidates[-1])
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


def measure(draw, text, fnt):
    b = draw.textbbox((0, 0), text, font=fnt)
    return b[2] - b[0], b[3] - b[1]


def text_w(text, fnt):
    im = Image.new("L", (8, 8))
    d = ImageDraw.Draw(im)
    return measure(d, text, fnt)[0]


def tracked(draw, xy, text, fnt, fill, tracking=0, anchor="la"):
    """Draw text with letter-spacing. Returns total width."""
    x, y = xy
    widths = [text_w(ch, fnt) for ch in text]
    total = sum(widths) + tracking * max(0, len(text) - 1)
    if anchor[0] == "m":
        x -= total / 2
    elif anchor[0] == "r":
        x -= total
    if anchor[1] == "m":
        ascent, descent = fnt.getmetrics()
        y -= (ascent + descent) / 2
    elif anchor[1] == "d":
        ascent, descent = fnt.getmetrics()
        y -= ascent + descent
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += w + tracking
    return total


def wrap(text, fnt, max_width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_w(trial, fnt) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# --- backgrounds ------------------------------------------------------------
def gradient_bg(w, h, top=NAVY_DEEP, bottom=(13, 17, 49), vertical=True):
    base = Image.new("RGB", (w, h))
    px = base.load()
    n = h if vertical else w
    for i in range(n):
        t = i / max(1, n - 1)
        c = tuple(int(top[k] + (bottom[k] - top[k]) * t) for k in range(3))
        if vertical:
            for x in range(w):
                px[x, i] = c
        else:
            for y in range(h):
                px[i, y] = c
    return base


def radial_glow(im, center, radius, color, strength=0.55):
    """Additive gold bloom in RGB space (alpha-safe: ignores im alpha)."""
    w, h = im.size
    mode = im.mode
    base = im.convert("RGB")
    layer = Image.new("RGB", (w, h), (0, 0, 0))
    d = ImageDraw.Draw(layer)
    steps = 46
    for i in range(steps, 0, -1):
        r = radius * i / steps
        f = (1 - i / steps) ** 2
        c = tuple(int(color[k] * f * strength) for k in range(3))
        d.ellipse([center[0] - r, center[1] - r, center[0] + r, center[1] + r], fill=c)
    layer = layer.filter(ImageFilter.GaussianBlur(max(1, radius / 14)))
    from PIL import ImageChops

    out = ImageChops.add(base, layer)
    return out.convert(mode)


def vignette(im, strength=0.55):
    w, h = im.size
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    pad = int(min(w, h) * 0.06)
    d.rounded_rectangle([pad, pad, w - pad, h - pad], radius=int(min(w, h) * 0.06), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(min(w, h) * 0.12))
    dark = Image.new("RGB", (w, h), (0, 0, 0))
    return Image.composite(im, Image.blend(im, dark, strength), mask)


def grain(im, amount=7, seed=3):
    """Add ±amount luminance noise (mean-preserving)."""
    import random

    rnd = random.Random(seed)
    w, h = im.size
    noise = Image.new("L", (w // 2, h // 2))
    noise.putdata([128 + rnd.randint(-amount, amount) for _ in range((w // 2) * (h // 2))])
    noise = noise.resize((w, h))
    from PIL import ImageChops

    # add(im, noise, scale=1, offset=-128) == im + (noise - 128)
    return ImageChops.add(im, Image.merge("RGB", (noise, noise, noise)), 1.0, -128)


def gold_gradient_text(text, fnt, top=GOLD_LT, bottom=GOLD_DK):
    """Render text into an RGBA image with a vertical gold gradient."""
    tmp = Image.new("L", (4, 4))
    d = ImageDraw.Draw(tmp)
    w, h = measure(d, text, fnt)
    asc, desc = fnt.getmetrics()
    box = Image.new("L", (w + 8, asc + desc + 8), 0)
    ImageDraw.Draw(box).text((4, 4), text, font=fnt, fill=255)
    grad = Image.new("RGB", box.size)
    px = grad.load()
    for y in range(box.size[1]):
        t = y / max(1, box.size[1] - 1)
        c = tuple(int(top[k] + (bottom[k] - top[k]) * t) for k in range(3))
        for x in range(box.size[0]):
            px[x, y] = c
    out = Image.new("RGBA", box.size, (0, 0, 0, 0))
    out.paste(grad, (0, 0), box)
    return out


def _mark_source():
    """Canonical mark, transparent margins trimmed and re-centred."""
    src = Image.open(LOGO_512).convert("RGBA")
    box = src.split()[-1].getbbox()
    if box:
        src = src.crop(box)
    side = max(src.size)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.alpha_composite(src, ((side - src.width) // 2,
                                 (side - src.height) // 2))
    return square


def logo_mark(size, halo=True, ring=True):
    """Priv mark, optionally on a gold halo + ring."""
    mark = _mark_source().resize((size, size), Image.LANCZOS)
    if not halo:
        return mark
    pad = int(size * 0.16)
    canvas = Image.new("RGBA", (size + pad * 2, size + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    cx = cy = (size + pad * 2) / 2
    if ring:
        for i, col in enumerate([GOLD_DK, GOLD, GOLD_LT]):
            r = size / 2 + pad * (0.62 - i * 0.06)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col + (255,), width=max(1, size // 90))
    canvas.alpha_composite(mark, (pad, pad))
    return canvas


def wordmark(fnt, color=GOLD, sub_color=MUTED, tagline=None, tracking=400):
    """PRIV wordmark (+ optional tagline) rendered as RGBA."""
    text = "PRIV"
    tmp = Image.new("L", (4, 4))
    d = ImageDraw.Draw(tmp)
    asc, desc = fnt.getmetrics()
    w = text_w(text[0], fnt) * 4 + tracking * 3
    h = asc + desc
    img = Image.new("RGBA", (int(w) + 12, h + 12), (0, 0, 0, 0))
    dd = ImageDraw.Draw(img)
    tracked(dd, (6, 6), text, fnt, color, tracking=tracking)
    return img


# --- decorative motifs ------------------------------------------------------
def gold_rule(draw, xy, width, height=3, alpha=255):
    x, y = xy
    for i in range(height):
        t = i / max(1, height - 1)
        c = GOLD_DK if t < 0.5 else GOLD_LT
        draw.line([x, y + i, x + width, y + i], fill=c + (alpha,))


def candle_series(w, h, seed=11, n=46, drift=0.35):
    import random

    rnd = random.Random(seed)
    pts, v = [], h * 0.62
    for i in range(n):
        delta = rnd.uniform(-1, 1) * h * 0.07 + drift * h * 0.006
        v = max(h * 0.12, min(h * 0.9, v - delta))
        pts.append((i * (w / (n - 1)), v))
    return pts


def draw_candles(draw, box, seed=11, n=40, up=CYAN, down=ROSE, wick=True):
    import random

    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    rnd = random.Random(seed)
    price = 0.5
    slot = w / n
    body_w = max(3, int(slot * 0.55))
    for i in range(n):
        open_ = price
        close = price + rnd.uniform(-0.11, 0.12) + 0.012
        close = max(0.05, min(0.95, close))
        high = max(open_, close) + rnd.uniform(0, 0.06)
        low = min(open_, close) - rnd.uniform(0, 0.06)
        cx = x0 + slot * i + slot / 2
        col = up if close >= open_ else down
        yt = y0 + (1 - high) * h
        yb = y0 + (1 - low) * h
        if wick:
            draw.line([cx, yt, cx, yb], fill=col, width=1)
        a = y0 + (1 - max(open_, close)) * h
        b = y0 + (1 - min(open_, close)) * h
        draw.rectangle([cx - body_w / 2, a, cx + body_w / 2, max(a + 2, b)], fill=col)
        price = close


def poly_path(points):
    return [(int(x), int(y)) for x, y in points]


def sparkline(draw, box, seed=5, n=34, color=GOLD, width=3):
    import random

    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    rnd = random.Random(seed)
    v, pts = 0.5, []
    for i in range(n):
        v = max(0.05, min(0.95, v + rnd.uniform(-0.16, 0.19)))
        pts.append((x0 + i * (w / (n - 1)), y0 + (1 - v) * h))
    draw.line(pts, fill=color, width=width, joint="curve")
    return pts


def dot_grid(draw, box, step=34, color=None, r=1, alpha=60):
    color = color or WHITE
    x0, y0, x1, y1 = box
    for x in range(int(x0), int(x1), step):
        for y in range(int(y0), int(y1), step):
            draw.ellipse([x - r, y - r, x + r, y + r], fill=color + (alpha,))


def arc_glow(im, center, radius, color=GOLD, width=3, start=200, end=340):
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.arc(
        [center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius],
        start, end, fill=color + (200,), width=width,
    )
    layer = layer.filter(ImageFilter.GaussianBlur(width))
    im.alpha_composite(layer)


def rounded_panel(im, box, radius=26, fill=(11, 16, 44, 210), outline=(212, 175, 55, 90), width=2):
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)
    return d


def pill(draw, xy, label, fnt, fg=NAVY_DEEP, bg=GOLD, pad_x=18, pad_y=8, tracking=120):
    x, y = xy
    asc, desc = fnt.getmetrics()
    tw = text_w(label, fnt) + tracking * (len(label) - 1)
    w = tw + pad_x * 2
    h = asc + desc + pad_y * 2
    draw.rounded_rectangle([x, y, x + w, y + h], radius=h / 2, fill=bg)
    tracked(draw, (x + pad_x, y + pad_y - 1), label, fnt, fg, tracking=tracking)
    return w, h


def footer(im, y=None, url=SITE, show_logo=True):
    """Standard campaign footer: mark + wordmark + url."""
    w, h = im.size
    d = ImageDraw.Draw(im, "RGBA")
    m = int(min(w, h) * 0.055)
    if y is None:
        y = h - m - int(min(w, h) * 0.055)
    lm = int(min(w, h) * 0.055)
    mark = logo_mark(lm, halo=True, ring=True)
    im.alpha_composite(mark, (m, y - lm // 2))
    f = font("display", int(min(w, h) * 0.036))
    tracked(d, (m + lm + int(lm * 0.55), y), "PRIV", f, (212, 175, 55, 255),
            tracking=int(f.size * 0.3))
    f2 = font("mono_r", int(min(w, h) * 0.028))
    tw = text_w(url, f2)
    d.text((w - m - tw + 2, y + f.size * 0.12 + 3), url, font=f2, fill=(0, 0, 0, 170))
    d.text((w - m - tw, y + f.size * 0.12), url, font=f2, fill=(148, 163, 184, 245))
    return im
