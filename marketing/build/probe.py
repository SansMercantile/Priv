import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw  # noqa: E402

import brand as B  # noqa: E402
import poster_specs  # noqa: E402
import posters  # noqa: E402


def probe(slug, fmt):
    spec = poster_specs.POSTERS[slug]
    w, h = posters.FORMATS[fmt]
    scale = min(w, h) / 1080.0
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov, "RGBA")
    m = int(min(w, h) * spec.get("margin", 0.062))
    cw = w - m * 2
    y = m + int(54 * scale)
    hy, _ = posters.headline(ov, m, y, cw, spec["headline"],
                             int(spec.get("hsize", 96) * scale))
    y = hy + int(24 * scale)
    if spec.get("sub"):
        y = posters.subhead(ov, d, m, y, cw, spec["sub"], int(34 * scale)) + int(34 * scale)
    lm = int(min(w, h) * 0.055)
    footer_top = h - m - int(26 * scale) - lm // 2
    cta_h = (int(int(34 * scale) * 1.5) + 2 * int(int(34 * scale) * 0.62)) \
        if spec.get("cta") else 0
    avail = int(footer_top - cta_h - int(56 * scale) - y)
    body = spec.get(f"body_{fmt}") or spec.get("body")
    body = dict(body, _max_h=max(int(90 * scale), avail))
    print(f"{slug}/{fmt}: body_top={y:.0f} avail={avail} "
          f"body_h_avail_end={y + avail:.0f} footer={footer_top}")

    if body["kind"] == "signal":
        ch_ = min(int(cw * 0.50), avail)
        pad = int(min(cw * 0.045, ch_ * 0.07))
        fy = y + pad
        f_buy = B.font("mono", int(min(cw * 0.036, ch_ * 0.07)))
        hdr_bottom = fy + int(ch_ * 0.115) + sum(f_buy.getmetrics())
        cols = 4 if cw / max(1, ch_) > 2.8 else 2
        colw = (cw - pad * 2) / cols
        n_rows = (len(range(4)) + cols - 1) // cols
        f_lab = B.font("mono", int(min(cw * 0.028, ch_ * 0.055, colw * 0.115)))
        sym = int(min(cw * 0.055, ch_ * 0.135, colw * 0.19))
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
        last_bottom = ry + (n_rows - 1) * pitch + lab_h + gap_lv + val_h
        card_bottom = y + ch_
        print(f"    signal card {y:.0f}..{card_bottom:.0f}  rows {ry:.0f}..{last_bottom:.0f}"
              f"  cols={cols} n_rows={n_rows} sym={sym}")
        assert last_bottom <= card_bottom, "signal rows overflow card"
        assert ry >= hdr_bottom, "signal rows collide header"
        assert n_rows == 1 or pitch >= lab_h + gap_lv + val_h, "row pitch too small"

    if body["kind"] == "tiers":
        tiers = body["tiers"]
        n = len(tiers)
        gap = int(cw * 0.028)
        tw = (cw - gap * (n - 1)) / n
        ch = int(tw * (1.75 if n <= 3 else 1.5))
        ch = max(int(min(cw, avail) * 0.5), min(ch, avail))
        print(f"    tiers cw={tw:.0f} ch={ch} avail={avail} "
              f"card {y:.0f}..{y + ch:.0f}")
        assert y + ch <= y + avail, "tier card overflows"


for slug, spec in poster_specs.POSTERS.items():
    body = spec.get("body_feed") or spec.get("body")
    if body and body.get("kind") in ("signal", "tiers"):
        for fmt in spec["formats"]:
            probe(slug, fmt)
print("probe ok")
