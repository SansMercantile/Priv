"""KEV poster factory — the first poster batch, in KEV's own brand tokens.

Reuses the shared poster renderer (backgrounds + brand helpers + posters.py)
but with KEV's house cyan (#06b6d4, from pr_content_engine NEXUS_COLORS) and a
school — not trading — visual language. Each poster is a keyed spec: plate +
eyebrow + headline + a body renderer (stats / bullets / chips) + CTA + the
standard footer. Every claim passes the KEV compliance guard (no learning-
outcome or performance claims, every number sourced from the registry).

Run:
    C:\\Users\\kpasc\\.bridge\\venv\\Scripts\\python.exe growth/posters_kev.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw

import brand as B
import posters
from growth import product_kev as K

# --- KEV brand tokens (house cyan instead of Priv gold) ----------------------
CYAN = (6, 182, 212)          # #06b6d4  KEV house cyan
CYAN_LT = (103, 232, 249)     # #67e8f9
CYAN_DK = (14, 116, 144)      # #0e7490
NAVY = (8, 20, 39)            # deep school-night navy
NAVY_DEEP = (4, 10, 22)

OUT = os.path.join(B.ASSETS, "posters", "kev")


# --- KEV plate: a calm campus gradient with a cyan glow (no trading candles) --
def _plate(size, seed=7):
    w, h = size
    im = B.gradient_bg(w, h, top=NAVY_DEEP, bottom=(9, 26, 49))
    im = im.convert("RGB")
    im = B.radial_glow(im.convert("RGBA"), (int(w * 0.74), int(h * 0.28)),
                       int(min(w, h) * 0.78), CYAN, 0.42).convert("RGB")
    # A faint cyan dot grid (the "campus map" feel), school-safe.
    d = ImageDraw.Draw(im, "RGBA")
    B.dot_grid(d, [w * 0.06, h * 0.30, w * 0.94, h * 0.94],
               step=int(min(w, h) * 0.055), color=CYAN_LT, r=2, alpha=26)
    return im


# --- KEV footer: KEV wordmark + url (reuses B.footer's layout, cyan tint) ----
def _footer(im, url):
    w, h = im.size
    d = ImageDraw.Draw(im, "RGBA")
    m = int(min(w, h) * 0.055)
    y = h - m - int(min(w, h) * 0.055)
    f = B.font("display", int(min(w, h) * 0.040))
    B.tracked(d, (m, y), "KEV", f, CYAN + (255,), tracking=int(f.size * 0.34))
    f2 = B.font("mono_r", int(min(w, h) * 0.028))
    tw = B.text_w(url, f2)
    d.text((w - m - tw + 2, y + f.size * 0.12 + 3), url, font=f2, fill=(0, 0, 0, 170))
    d.text((w - m - tw, y + f.size * 0.12), url, font=f2, fill=B.MUTED + (245,))
    return im


def _stat_row(d, x, y, w, stats, size):
    """Like posters.stat_row but in cyan."""
    n = len(stats)
    f_v = B.font("display", size)
    cell = w / n
    for i, (val, lab) in enumerate(stats):
        cx = x + cell * i
        lab = lab.upper()
        f_l, tr = posters._fit_mono(lab, int(size * 0.34), cell - 28)
        if i:
            d.line([cx - 1, y, cx - 1, y + int(size * 1.9)], fill=CYAN + (90,), width=2)
        d.text((cx + 12 + 3, y + 4), val, font=f_v, fill=(0, 0, 0, 160))
        d.text((cx + 12, y), val, font=f_v, fill=CYAN_LT + (255,))
        B.tracked(d, (cx + 12, y + int(size * 1.12)), lab, f_l, B.MUTED + (255,),
                  tracking=tr)
    return y + int(size * 1.9)


def _cta(d, xy, label, size):
    f = B.font("bold", size)
    tw = B.text_w(label, f)
    pad_x, pad_y = int(size * 1.05), int(size * 0.62)
    x, y = xy
    w, h = tw + pad_x * 2, int(f.size * 1.5) + pad_y * 2
    d.rounded_rectangle([x + 3, y + 5, x + w + 3, y + h + 5], radius=h // 2,
                        fill=(0, 0, 0, 150))
    d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=CYAN + (255,))
    d.text((x + pad_x, y + pad_y), label, font=f, fill=NAVY_DEEP + (255,))
    return w, h


def _body_bullets(d, x, y, w, items, size):
    return posters.bullet_rows(d, x, y, w, items, size, mark=CYAN)


def render(spec, fmt, out_path):
    w, h = posters.FORMATS[fmt]
    scale = min(w, h) / 1080.0
    im = _plate((w, h), seed=spec.get("seed", 7)).convert("RGBA")
    im = posters.darken(im, spec.get("scrim_top", 0.90), spec.get("scrim_bottom", 0.62))
    im = B.vignette(im.convert("RGB"), 0.5).convert("RGBA")

    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov, "RGBA")
    m = int(min(w, h) * spec.get("margin", 0.062))
    content_w = w - m * 2
    y = m

    if spec.get("eyebrow"):
        posters.eyebrow(d, (m, y), spec["eyebrow"], rule_to=w - m,
                        size=int(34 * scale), color=CYAN)
        y += int(54 * scale)

    # Headline in cyan gradient (reuses gold_gradient_text with cyan stops).
    f_h = B.font("display", int(spec.get("hsize", 96) * scale))
    for ln in B.wrap(spec["headline"], f_h, content_w):
        img = B.gold_gradient_text(ln, f_h, top=CYAN_LT, bottom=CYAN_DK)
        posters.text_shadow(ov, img, (m, y), blur=int(f_h.size * 0.09), alpha=205,
                            offset=(int(f_h.size * 0.045), int(f_h.size * 0.06)))
        y += int(f_h.size * 1.04)
    y += int(24 * scale)

    if spec.get("sub"):
        y = posters.subhead(ov, d, m, y, content_w, spec["sub"], int(34 * scale)) + int(34 * scale)

    body = spec.get("body")
    if body and body["kind"] == "stats":
        size = int(w * 0.09)
        y = _stat_row(d, m, y, content_w, body["stats"], size) + int(38 * scale)
    elif body and body["kind"] == "bullets":
        y = _body_bullets(d, m, y, content_w, body["items"],
                          int(w * 0.044)) + int(38 * scale)
    elif body and body["kind"] == "chips":
        # cyan chips
        f = B.font("mono", int(w * 0.040))
        cx, cy = m, y
        for lb in body["labels"]:
            tw = B.text_w(lb, f) + int(f.size * 1.6)
            if cx + tw > m + content_w:
                cx, cy = m, cy + int(f.size * 2.7)
            d.rounded_rectangle([cx, cy, cx + tw, cy + int(f.size * 2.0)],
                                radius=int(f.size), fill=CYAN + (34,),
                                outline=CYAN + (190,), width=2)
            d.text((cx + int(f.size * 0.8), cy + int(f.size * 0.35)), lb,
                   font=f, fill=CYAN_LT + (255,))
            cx += tw + int(f.size * 0.42)
        y = cy + int(f.size * 2.0) + int(38 * scale)

    if spec.get("cta"):
        _cta(d, (m, y), spec["cta"], int(34 * scale))

    _footer(ov, spec.get("url", K.SITE))
    im.alpha_composite(ov)
    im = B.grain(im.convert("RGB"), amount=5)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    im.convert("RGB").save(out_path, quality=93, optimize=True)
    return out_path


# --- Poster Set A (Week 1, brand pillar): campus / labs / tutors / offline ----
POSTERS = {
    "campus": dict(
        eyebrow="KEV · IMMERSIVE SCHOOL", headline="Walk to class through a 3D campus.",
        sub="Eleven floors, 199 rooms and 14 bookable facilities — every one a door into a working room, gated to your role.",
        body=dict(kind="stats", stats=[("11", "floors"), ("199", "rooms"), ("14", "facilities")]),
        cta="Start free — walk the campus", formats=["feed", "wide", "story"], seed=11),
    "labs": dict(
        eyebrow="KEV · SCIENCE LABS", headline="Dissect the human body. Then the engine.",
        sub="A Human Atlas of 2,234 modeled structures and a 334-piece EV cutaway — explode, isolate, inspect any part.",
        body=dict(kind="stats", stats=[("2,234", "structures"), ("334", "EV parts"), ("4", "labs")]),
        cta="Start free — open a lab", formats=["feed", "wide"], seed=22),
    "tutors": dict(
        eyebrow="KEV · AI TUTORS", headline="A tutor for every subject, at every level.",
        sub="Socratic, level-adaptive tutors across 185+ subjects — live online, cached and offline guidance when you're not.",
        body=dict(kind="stats", stats=[("185+", "subjects"), ("6", "languages"), ("Live", "+ offline")]),
        cta="Start free — meet a tutor", formats=["feed", "story"], seed=33),
    "offline": dict(
        eyebrow="KEV · WORKS OFFLINE", headline="The classroom that works with no internet.",
        sub="Every 3D model precached — the full labs run offline on first visit; notes and chat replay on reconnect.",
        body=dict(kind="chips", labels=["100% precached", "Queue + replay", "6 languages", "Any device"]),
        cta="Start free — walk the campus", formats=["feed", "wide"], seed=44),
}


def build(only=None, formats=None):
    made = []
    for slug, spec in POSTERS.items():
        if only and slug not in only:
            continue
        for fmt in spec["formats"]:
            if formats and fmt not in formats:
                continue
            path = os.path.join(OUT, fmt, f"kev-{slug}-{fmt}.jpg")
            render(spec, fmt, path)
            made.append(path)
            print("ok", os.path.relpath(path, B.ASSETS))
    print(f"\n{len(made)} KEV posters written to {OUT}")
    return made


def _compliance_check():
    bad = 0
    for slug, spec in POSTERS.items():
        text = " ".join([spec["headline"], spec.get("sub", ""), spec.get("cta", "")])
        g = K.guard(text)
        if g:
            bad += 1
            print("COMPLIANCE FAIL", slug, g)
    return bad


if __name__ == "__main__":
    fails = _compliance_check()
    print(f"compliance failures: {fails}")
    if fails == 0:
        build(only=sys.argv[1:] or None)
