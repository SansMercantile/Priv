"""Layout audit: dry-runs every poster spec and reports vertical gaps/overlaps."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw  # noqa: E402

import brand as B  # noqa: E402
import poster_specs  # noqa: E402
import posters  # noqa: E402

SCALE_REF = 1080.0
problems = []


def audit(slug, spec, fmt):
    w, h = posters.FORMATS[fmt]
    scale = min(w, h) / SCALE_REF
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov, "RGBA")
    issues = []
    m = int(min(w, h) * spec.get("margin", 0.062))
    content_w = w - m * 2
    y = m
    boxes = []

    if spec.get("eyebrow"):
        f = B.font("mono", int(34 * scale))
        y += int(54 * scale)
        boxes.append(("eyebrow", y - int(54 * scale), y))

    hy, _ = posters.headline(ov, m, y, content_w, spec["headline"],
                             int(spec.get("hsize", 96) * scale))
    boxes.append(("headline", y, hy))
    y = hy + int(24 * scale)

    if spec.get("sub"):
        sub_top = y
        sub_end = posters.subhead(ov, d, m, y, content_w, spec["sub"], int(34 * scale))
        boxes.append(("sub", sub_top, sub_end))
        y = sub_end + int(34 * scale)

    show_logo = spec.get("show_logo", True)
    cta = spec.get("cta")
    f_cta = int(34 * scale)
    lm = int(min(w, h) * 0.055)
    footer_top = (h - m - int(26 * scale) - lm // 2) if show_logo else h - m
    cta_h = int(f_cta * 1.5) + 2 * int(f_cta * 0.62) if cta else 0
    avail = int(footer_top - cta_h - int(56 * scale) - y)

    body = spec.get(f"body_{fmt}") or spec.get("body")
    if body:
        body = dict(body, _max_h=max(int(90 * scale), avail))
        b_top = y
        b_end = posters.BODIES[body["kind"]](ov, d, m, y, content_w, body)
        boxes.append(("body", b_top, b_end))
        if b_end - b_top > avail + 1:
            issues.append(f"body overflows available height by "
                          f"{b_end - b_top - avail:.0f}px")
        y = b_end + int(38 * scale)

    boxes.append(("cta", y, y + cta_h))
    boxes.append(("footer", footer_top, footer_top + int(min(w, h) * 0.055)))

    for i in range(len(boxes) - 1):
        name, top, bot = boxes[i]
        nxt = boxes[i + 1]
        gap = nxt[1] - bot
        if gap < -1:
            issues.append(f"{name}->{nxt[0]} OVERLAP {gap:+.0f}px")
        elif gap < 10 * scale and name in ("headline", "sub"):
            issues.append(f"{name}->{nxt[0]} tight {gap:+.0f}px")
    last = boxes[-2] if len(boxes) >= 2 else boxes[-1]
    if last[2] > footer_top + 1:
        issues.append(f"{last[0]} runs {last[2] - footer_top:.0f}px into footer")

    tag = f"{slug}/{fmt} {w}x{h}"
    if issues:
        problems.append((tag, issues))
        print("FAIL", tag)
        for it in issues:
            print("      ", it)
    else:
        print("  ok", tag)
        for name, top, bot in boxes:
            print(f"        {name:9s} {top:6.0f} -> {bot:6.0f}")


for slug, spec in poster_specs.POSTERS.items():
    for fmt in spec["formats"]:
        audit(slug, spec, fmt)

print("\n" + ("ALL CLEAR" if not problems else f"{len(problems)} specs with issues"))
