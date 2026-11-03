"""Priv campaign poster factory.

Each poster is a keyed spec: plate (AI background) + eyebrow + headline +
a body renderer (chips / bullets / cards / tiers / platforms / signal ticket)
+ CTA + the standard campaign footer.

Sizes are named so the same design can ship in every placement format.
"""
import os

from PIL import Image, ImageDraw, ImageFilter

import backgrounds
import brand as B

OUT = os.path.join(B.ASSETS, "posters")

FORMATS = {
    "feed": (1080, 1350),      # IG / LinkedIn feed  (4:5)
    "story": (1080, 1920),     # IG / WA / TikTok story (9:16)
    "wide": (1920, 1080),      # YouTube / display / X (16:9)
    "thumb": (1280, 720),      # YouTube thumbnail
    "link": (1200, 628),       # link preview card
}


def rgba(c, a=255):
    return (c[0], c[1], c[2], a)


# ---------------------------------------------------------------- primitives
def darken(im, top=0.86, bottom=0.55, flat=0.0):
    """Multiply a vertical scrim over the plate (keeps colour, kills glare)."""
    w, h = im.size
    ov = Image.new("L", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        v = top + (bottom - top) * t
        ov.putpixel((0, y), int(255 * (1 - (1 - flat) * v)))
    ov = ov.resize((w, h))
    black = Image.new("RGB", (w, h), (4, 6, 18))
    return Image.composite(black, im.convert("RGB"), ov).convert("RGBA")


def text_shadow(im, img, xy, blur=10, alpha=190, offset=(4, 6)):
    """Composite a blurred black copy of an RGBA glyph image behind it."""
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, alpha), (0, 0), img.split()[3])
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    im.alpha_composite(sh, (int(xy[0] + offset[0]), int(xy[1] + offset[1])))
    im.alpha_composite(img, (int(xy[0]), int(xy[1])))


def eyebrow(d, xy, label, rule_to=None, size=34, color=B.GOLD):
    f = B.font("mono", size)
    w = B.tracked(d, xy, label, f, rgba(color), tracking=int(f.size * 0.32))
    x, y = xy
    if rule_to:
        yl = y + f.size * 0.62
        d.line([x + w + f.size * 0.7, yl, rule_to, yl], fill=rgba(B.GOLD_DK, 150), width=2)
    return w


def headline(im, x, y, max_w, text, size, leading=1.04, align="l"):
    f = B.font("display", size)
    lines = B.wrap(text, f, max_w)
    for ln in lines:
        img = B.gold_gradient_text(ln, f)
        if align == "l":
            dx = x
        else:
            dx = x + (max_w - img.width) / 2
        text_shadow(im, img, (dx, y), blur=int(size * 0.09), alpha=205,
                    offset=(int(size * 0.045), int(size * 0.06)))
        y += int(f.size * leading)
    # true ink bottom of the last line (gold_gradient_text pads by 4px)
    tmp = ImageDraw.Draw(Image.new("L", (4, 4)))
    bb = tmp.textbbox((0, 0), lines[-1], font=f)
    return y - int(f.size * leading) + 4 + bb[3], len(lines)


def subhead(im, d, x, y, max_w, text, size, color=(226, 232, 240), leading=1.34, align="l"):
    f = B.font("body", size)
    lines = B.wrap(text, f, max_w)
    first = y
    for ln in lines:
        w = B.text_w(ln, f)
        dx = x if align == "l" else x + (max_w - w) / 2
        d.text((dx + 3, y + 4), ln, font=f, fill=(0, 0, 0, 150))
        d.text((dx, y), ln, font=f, fill=rgba(color, 245))
        y += int(f.size * leading)
    if not lines:
        return first
    last_top = first + int(f.size * leading) * (len(lines) - 1)
    tmp = ImageDraw.Draw(Image.new("L", (4, 4)))
    return last_top + tmp.textbbox((0, 0), lines[-1], font=f)[3]


def bullet_rows(d, x, y, w, items, size, gap=None, mark=B.GOLD):
    f = B.font("semi", size)
    gap = gap or int(size * 0.7)
    for it in items:
        d.ellipse([x, y + f.size * 0.36, x + f.size * 0.24, y + f.size * 0.36 + f.size * 0.24],
                  fill=rgba(mark))
        lines = B.wrap(it, f, w - int(f.size * 0.75))
        for ln in lines:
            d.text((x + f.size * 0.60 + 2, y + 3), ln, font=f, fill=(0, 0, 0, 140))
            d.text((x + f.size * 0.60, y), ln, font=f, fill=rgba((226, 232, 240), 245))
            y += int(f.size * 1.26)
        y += gap
    return y


def body_signal(im, d, x, y, w, s):
    ch_ = int(w * 0.50)
    if s.get("_max_h"):
        ch_ = min(ch_, int(s["_max_h"]))
    card_panel(im, [x, y, x + w, y + ch_])
    d = ImageDraw.Draw(im, "RGBA")
    pad = int(min(w * 0.045, ch_ * 0.07))
    fx, fy = x + pad, y + pad
    d.text((fx, fy), "VOLATILITY 100 INDEX",
           font=B.font("mono", int(min(w * 0.03, ch_ * 0.06))), fill=rgba(B.MUTED))
    f_buy = B.font("mono", int(min(w * 0.036, ch_ * 0.07)))
    buy_top = fy + int(ch_ * 0.115)
    B.tracked(d, (fx, buy_top), "BUY  ·  1H", f_buy, rgba(B.GREEN),
              tracking=int(w * 0.004))
    hdr_bottom = buy_top + sum(f_buy.getmetrics())
    pillh = int(ch_ * 0.14)
    pillw = max(int(w * 0.14), pillh * 2)
    px1 = x + w - pad
    d.rounded_rectangle([px1 - pillw, fy, px1, fy + pillh], radius=pillh // 2,
                        fill=rgba(B.GREEN, 60), outline=rgba(B.GREEN, 210), width=2)
    f_liv = B.font("mono", int(pillh * 0.52))
    lw = B.text_w("LIVE", f_liv)
    d.text((px1 - (pillw + lw) / 2, fy + (pillh - f_liv.size) / 2 - 2), "LIVE",
           font=f_liv, fill=rgba(B.GREEN))
    rows = [("ENTRY", "8 452.1", B.WHITE), ("TAKE PROFIT 1", "8 461.3", B.GREEN),
            ("TAKE PROFIT 2", "8 470.5", B.GREEN), ("STOP LOSS", "8 443.0", B.ROSE)]
    cols = 4 if w / max(1, ch_) > 2.8 else 2
    colw = (w - pad * 2) / cols
    n_rows = (len(rows) + cols - 1) // cols
    f_lab = B.font("mono", int(min(w * 0.028, ch_ * 0.055, colw * 0.115)))
    sym = int(min(w * 0.055, ch_ * 0.135, colw * 0.19))
    gap_lv = int(ch_ * 0.065)
    free = ch_ - pad - (hdr_bottom - y)
    for _ in range(8):
        f_sym = B.font("bold", sym)
        lab_h, val_h = sum(f_lab.getmetrics()), sum(f_sym.getmetrics())
        pitch = lab_h + gap_lv + val_h + int(ch_ * 0.055)
        block_h = (n_rows - 1) * pitch + lab_h + gap_lv + val_h
        if block_h <= free or sym <= int(ch_ * 0.08):
            break
        sym = int(sym * 0.94)
    ry = hdr_bottom + max(int(ch_ * 0.05), (free - block_h) / 2)
    for i, (lab, val, colr) in enumerate(rows):
        cx = fx + colw * (i % cols)
        cy = ry + (i // cols) * pitch
        B.tracked(d, (cx, cy), lab, f_lab, rgba(B.MUTED), tracking=int(f_lab.size * 0.16))
        d.text((cx, cy + lab_h + gap_lv), val, font=f_sym, fill=rgba(colr))
    return y + ch_


def body_chips(im, d, x, y, w, s):
    f = B.font("mono", s.get("chip_size", int(w * 0.040)))
    labels = s["chips"]
    cx, cy = x, y
    for lb in labels:
        tw = B.text_w(lb, f) + int(f.size * 1.6)
        if cx + tw > x + w:
            cx, cy = x, cy + int(f.size * 2.7)
        d.rounded_rectangle([cx, cy, cx + tw, cy + int(f.size * 2.0)], radius=int(f.size),
                            fill=rgba(B.GOLD, 34), outline=rgba(B.GOLD, 190), width=2)
        d.text((cx + int(f.size * 0.8), cy + int(f.size * 0.35)), lb, font=f,
               fill=rgba(B.GOLD_LT))
        cx += tw + int(f.size * 0.42)
    return cy + int(f.size * 2.0)


def body_bullets(im, d, x, y, w, s):
    size = s.get("size", int(w * 0.044))
    max_h = s.get("_max_h")
    if max_h:
        for _ in range(8):
            f = B.font("semi", size)
            total = sum(len(B.wrap(it, f, w - int(f.size * 0.75))) * int(f.size * 1.26)
                        for it in s["items"]) + int(size * 0.7) * (len(s["items"]) - 1)
            if total <= max_h or size <= int(w * 0.026):
                break
            size = int(size * 0.93)
    return bullet_rows(d, x, y, w, s["items"], size)


def _fit_mono(text, size, max_w, tracking_ratio=0.2):
    """Shrink a mono label until its tracked width fits max_w."""
    while size > 9:
        f = B.font("mono", size)
        t = int(size * tracking_ratio)
        total = sum(B.text_w(ch, f) for ch in text) + t * max(0, len(text) - 1)
        if total <= max_w:
            return f, t
        size -= 1
    f = B.font("mono", 9)
    return f, int(9 * tracking_ratio)


def stat_row(d, x, y, w, stats, size):
    n = len(stats)
    f_v = B.font("display", size)
    cell = w / n
    for i, (val, lab) in enumerate(stats):
        cx = x + cell * i
        lab = lab.upper()
        f_l, tr = _fit_mono(lab, int(size * 0.34), cell - 28)
        if i:
            d.line([cx - 1, y, cx - 1, y + int(size * 1.9)], fill=rgba(B.GOLD, 90), width=2)
        d.text((cx + 12 + 3, y + 4), val, font=f_v, fill=(0, 0, 0, 160))
        d.text((cx + 12, y), val, font=f_v, fill=rgba(B.GOLD))
        B.tracked(d, (cx + 12, y + int(size * 1.12)), lab, f_l, rgba(B.MUTED),
                  tracking=tr)
    return y + int(size * 1.9)


def body_stats(im, d, x, y, w, s):
    size = s.get("size", int(w * 0.09))
    if s.get("_max_h"):
        size = max(int(s["_max_h"] / 1.9), int(w * 0.05))
        size = min(size, int(w * 0.09))
    return stat_row(d, x, y, w, s["stats"], size)


def card_panel(im, box, radius=24, alpha=232, outline_alpha=120):
    d = ImageDraw.Draw(im, "RGBA")
    d.rounded_rectangle(box, radius=radius, fill=(7, 10, 30, alpha),
                        outline=rgba(B.GOLD, outline_alpha), width=2)
    return d


def cta_button(d, xy, label, size, kind="solid"):
    f = B.font("bold", size)
    tw = B.text_w(label, f)
    pad_x, pad_y = int(size * 1.05), int(size * 0.62)
    x, y = xy
    w, h = tw + pad_x * 2, int(f.size * 1.5) + pad_y * 2
    if kind == "solid":
        d.rounded_rectangle([x + 3, y + 5, x + w + 3, y + h + 5], radius=h // 2,
                            fill=(0, 0, 0, 150))
        d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=rgba(B.GOLD))
        d.text((x + pad_x, y + pad_y), label, font=f, fill=rgba(B.NAVY_DEEP))
    else:
        d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, outline=rgba(B.GOLD, 235),
                            width=3, fill=rgba(B.GOLD, 30))
        d.text((x + pad_x, y + pad_y), label, font=f, fill=rgba(B.GOLD))
    return w, h


def body_tiers(im, d, x, y, w, s):
    tiers = s["tiers"]
    n = len(tiers)
    gap = int(w * 0.028)
    cw = (w - gap * (n - 1)) / n
    ch = int(cw * (1.75 if n <= 3 else 1.5))
    if s.get("_max_h"):
        ch = max(int(min(w, s["_max_h"]) * 0.5), min(ch, int(s["_max_h"])))

    for i, t in enumerate(tiers):
        cx = x + (cw + gap) * i
        hi = t.get("featured")
        card_panel(im, [cx, y, cx + cw, y + ch], radius=20,
                   alpha=248 if hi else 218, outline_alpha=235 if hi else 90)
        d = ImageDraw.Draw(im, "RGBA")
        if hi:
            d.rounded_rectangle([cx, y, cx + cw, y + ch], radius=20,
                                outline=rgba(B.GOLD), width=3)
            B.tracked(d, (cx + cw * 0.5, y + int(ch * 0.028)), "MOST POPULAR",
                      B.font("mono", int(min(cw * 0.075, ch * 0.05))), rgba(B.GOLD),
                      tracking=int(cw * 0.01), anchor="ma")

        reserve_cta = bool(hi and ch >= cw * 1.3)
        top = y + int(ch * 0.10)

        f_n = B.font("semi", int(min(cw * 0.13, ch * 0.085)))
        name_w = B.text_w(t["name"], f_n)
        d.text((cx + (cw - name_w) / 2, top), t["name"], font=f_n, fill=rgba(B.WHITE))
        cur = top + f_n.getmetrics()[0] + f_n.getmetrics()[1] + int(ch * 0.018)

        f_p = B.font("display", int(min(cw * 0.30, ch * 0.21)))
        asc_p, desc_p = f_p.getmetrics()
        pw = B.text_w(t["price"], f_p)
        im.alpha_composite(B.gold_gradient_text(t["price"], f_p),
                           (int(cx + (cw - pw) / 2), int(cur)))
        cur += asc_p + desc_p + int(ch * 0.008)

        f_per = B.font("mono", int(min(cw * 0.085, ch * 0.055)))
        per = t.get("per", "/ month")
        ppw = B.text_w(per, f_per)
        d.text((cx + (cw - ppw) / 2, cur), per, font=f_per, fill=rgba(B.MUTED))
        cur += f_per.getmetrics()[0] + f_per.getmetrics()[1] + int(ch * 0.03)

        cta_h = 0
        f_cta = int(min(cw * 0.095, ch * 0.07))
        if reserve_cta:
            cta_h = int(f_cta * 1.5) + 2 * int(f_cta * 0.62)
            cur = min(cur, y + ch - cta_h - int(ch * 0.075) - int(ch * 0.03))
        bottom = y + ch - (cta_h + int(ch * 0.075) if reserve_cta else int(ch * 0.055))

        lines = t["lines"]
        while len(lines) > 2:
            fs = int(min(cw * 0.085, ch * 0.06,
                         (bottom - cur) / (1.45 * len(lines))))
            if fs >= min(cw, ch) * 0.062:
                break
            lines = lines[:-1]
        fs = max(int(min(cw * 0.085, ch * 0.06, (bottom - cur) / (1.45 * len(lines)))),
                 int(min(cw, ch) * 0.048))
        f_b = B.font("body", fs)
        lh = int(fs * 1.45)
        for line in lines:
            lw = B.text_w(line, f_b)
            d.text((cx + (cw - lw) / 2, cur), line, font=f_b,
                   fill=rgba((203, 213, 225) if not hi else (226, 232, 240), 245))
            cur += lh
        if reserve_cta:
            label, f_cta2 = "START FREE", B.font("bold", f_cta)
            bw = B.text_w(label, f_cta2) + 2 * int(f_cta * 1.05)
            cta_button(d, (cx + (cw - bw) / 2, y + ch - cta_h - int(ch * 0.075)),
                       label, f_cta)
    return y + ch


def body_platforms(im, d, x, y, w, s):
    plats = s["platforms"]
    per_row = 3 if len(plats) > 4 else len(plats)
    rows = (len(plats) + per_row - 1) // per_row
    gap = int(w * 0.022)
    cw = (w - gap * (per_row - 1)) / per_row
    chh = int(cw * 0.52)
    if s.get("_max_h"):
        fit = (s["_max_h"] - gap * (rows - 1)) / rows
        if fit < chh:
            chh = int(fit)
    f_n = B.font("semi", int(min(cw * 0.17, chh * 0.34)))
    f_s = B.font("mono", int(min(cw * 0.105, chh * 0.21)))
    for i, p in enumerate(plats):
        r, c = divmod(i, per_row)
        cx = x + (cw + gap) * c
        cy = y + (chh + gap) * r
        card_panel(im, [cx, cy, cx + cw, cy + chh], radius=18, alpha=222)
        d = ImageDraw.Draw(im, "RGBA")
        nw = B.text_w(p["name"], f_n)
        d.text((cx + (cw - nw) / 2, cy + chh * 0.5 - (f_n.size * 1.3 + f_s.size * 1.4) / 2),
               p["name"], font=f_n, fill=rgba(B.GOLD))
        sw = B.text_w(p["meta"], f_s)
        d.text((cx + (cw - sw) / 2, cy + chh * 0.5 - f_s.size * 1.4 / 2 + f_n.size * 1.3),
               p["meta"], font=f_s, fill=rgba(B.MUTED))
    return y + rows * chh + (rows - 1) * gap


def body_agents(im, d, x, y, w, s):
    agents = s["agents"]
    n = len(agents)
    gap = int(w * 0.02)
    rowh = int(w * 0.112)
    if s.get("_max_h"):
        fit = (s["_max_h"] - gap * (n - 1)) / n
        if fit < rowh:
            rowh = int(fit)
    f_n = B.font("semi", int(min(w * 0.044, rowh * 0.36)))
    f_v = B.font("mono", int(min(w * 0.038, rowh * 0.32)))
    f_r = B.font("mono", int(min(w * 0.030, rowh * 0.26)))
    for i, (name, vote, reason) in enumerate(agents):
        ry = y + (rowh + gap) * i
        card_panel(im, [x, ry, x + w, ry + rowh], radius=16, alpha=222)
        d = ImageDraw.Draw(im, "RGBA")
        dot = int(rowh * 0.34)
        d.ellipse([x + int(w * 0.03), ry + rowh * 0.33,
                   x + int(w * 0.03) + dot, ry + rowh * 0.33 + dot], fill=rgba(B.GOLD))
        d.text((x + int(w * 0.10), ry + int(rowh * 0.14)), name, font=f_n,
               fill=rgba(B.WHITE))
        d.text((x + int(w * 0.10), ry + int(rowh * 0.56)), reason, font=f_r,
               fill=rgba(B.MUTED))
        vw = B.text_w(vote, f_v)
        d.text((x + w - int(w * 0.03) - vw, ry + int(rowh * 0.34)), vote, font=f_v,
               fill=rgba(B.GREEN if vote == "BUY" else B.GOLD))
    return y + n * rowh + (n - 1) * gap


def body_notify(im, d, x, y, w, s):
    items = s["items"]
    n = len(items)
    gap = int(w * 0.022)
    rowh = int(w * 0.15)
    if s.get("_max_h"):
        fit = (s["_max_h"] - gap * (n - 1)) / n
        if fit < rowh:
            rowh = int(fit)
    f_h = B.font("semi", int(min(w * 0.044, rowh * 0.30)))
    f_m = B.font("mono", int(min(w * 0.031, rowh * 0.22)))
    for i, (channel, head, meta) in enumerate(items):
        ry = y + (rowh + gap) * i
        card_panel(im, [x, ry, x + w, ry + rowh], radius=18, alpha=224)
        d = ImageDraw.Draw(im, "RGBA")
        bx = x + int(w * 0.03)
        side = int(rowh * 0.60)
        by = ry + (rowh - side) // 2
        d.rounded_rectangle([bx, by, bx + side, by + side], radius=int(side * 0.26),
                            fill=rgba(B.GOLD, 40), outline=rgba(B.GOLD, 210), width=2)
        f_c = B.font("display", int(side * 0.5))
        cw_ = B.text_w(channel[0], f_c)
        d.text((bx + (side - cw_) / 2, by + side * 0.18), channel[0], font=f_c,
               fill=rgba(B.GOLD))
        tx = bx + side + int(w * 0.035)
        th = f_h.getmetrics()[0] + f_h.getmetrics()[1]
        tm = f_m.getmetrics()[0] + f_m.getmetrics()[1]
        ty = ry + (rowh - (th + int(rowh * 0.10) + tm)) / 2
        d.text((tx, ty), head, font=f_h, fill=rgba(B.WHITE))
        d.text((tx, ty + th + int(rowh * 0.10)), meta, font=f_m, fill=rgba(B.MUTED))
    return y + n * rowh + (n - 1) * gap


def body_well(im, x0, y0, x1, y1):
    """Soft dark content well behind body copy (for bright plates).

    Applied to the base plate, before the text overlay is composited, so the
    blur can never dim or erase glyphs.
    """
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(im.width - 1, x1), min(im.height - 1, y1)
    if x1 - x0 < 8 or y1 - y0 < 8:
        return
    mask = Image.new("L", im.size, 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([x0, y0, x1, y1],
                        radius=int(min(x1 - x0, y1 - y0) * 0.16), fill=215)
    mask = mask.filter(ImageFilter.GaussianBlur(max(10, int(min(im.size) * 0.032))))
    blended = Image.alpha_composite(im, Image.new("RGBA", im.size, (4, 6, 18, 255)))
    im.paste(blended, (0, 0), mask)


BODIES = {
    "signal": body_signal, "chips": body_chips, "bullets": body_bullets,
    "stats": body_stats, "tiers": body_tiers, "platforms": body_platforms,
    "agents": body_agents, "notify": body_notify,
}


# --------------------------------------------------------------------- render
def render(spec, fmt, out_path=None, force_size=None):
    w, h = force_size or FORMATS[fmt]
    scale = min(w, h) / 1080.0
    plate = backgrounds.load(spec["plate"], (w, h))
    im = plate.convert("RGBA")
    im = darken(im, spec.get("scrim_top", 0.90), spec.get("scrim_bottom", 0.62))
    im = B.radial_glow(im, (int(w * 0.78), int(h * 0.24)), int(min(w, h) * 0.85),
                       B.GOLD, 0.22)
    im = B.vignette(im.convert("RGB"), 0.5).convert("RGBA")

    # Everything below is drawn on a transparent overlay: PIL's "RGBA" draw
    # mode writes raw pixels (it does NOT alpha-blend on an RGBA image), so
    # translucent fills must be composited, not drawn straight onto the plate.
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov, "RGBA")

    m = int(min(w, h) * spec.get("margin", 0.062))
    content_w = w - m * 2
    y = m

    if spec.get("eyebrow"):
        eyebrow(d, (m, y), spec["eyebrow"], rule_to=w - m, size=int(34 * scale))
        y += int(54 * scale)

    hy, _n = headline(ov, m, y, content_w, spec["headline"],
                      int(spec.get("hsize", 96) * scale))
    y = hy + int(24 * scale)

    block_top = y
    if spec.get("sub"):
        y = subhead(ov, d, m, y, content_w, spec["sub"], int(34 * scale)) + int(34 * scale)

    show_logo = spec.get("show_logo", True)
    cta = spec.get("cta")
    f_cta = int(34 * scale)
    lm = int(min(w, h) * 0.055)
    footer_top = (h - m - int(26 * scale) - lm // 2) if show_logo else h - m
    cta_h = int(f_cta * 1.5) + 2 * int(f_cta * 0.62) if cta else 0
    avail = int(footer_top - cta_h - int(56 * scale) - y)

    body = spec.get(f"body_{fmt}") or spec.get("body")
    well_bottom = y - int(38 * scale)
    if body:
        body = dict(body, _max_h=max(int(90 * scale), avail))
        b_top = y
        b_ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        b_end = BODIES[body["kind"]](b_ov, ImageDraw.Draw(b_ov, "RGBA"),
                                     m, y, content_w, body)
        ov.alpha_composite(b_ov)
        y = b_end + int(38 * scale)
        well_bottom = b_end + int(40 * scale)

    if cta:
        cta_button(d, (m, y), spec["cta"], f_cta, kind=spec.get("cta_kind", "solid"))
        well_bottom = y + cta_h + int(16 * scale)

    if spec.get("body_well") and (body or cta):
        body_well(im, m - int(28 * scale), block_top - int(12 * scale),
                  w - m + int(28 * scale), well_bottom)

    if show_logo:
        B.footer(ov, y=h - m - int(26 * scale), url=spec.get("url", B.SITE))

    if spec.get("watermark_tag"):
        f = B.font("mono", int(24 * scale))
        B.tracked(d, (w - m, m), spec["watermark_tag"], f, rgba(B.GOLD, 170),
                  tracking=int(f.size * 0.3), anchor="ra")

    im.alpha_composite(ov)
    im = B.grain(im.convert("RGB"), amount=5)
    im = im.convert("RGBA")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    im.convert("RGB").save(out_path, quality=93, optimize=True)
    return out_path
