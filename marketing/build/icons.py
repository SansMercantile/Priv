"""brand/priv-mark.png -> app icons (PNG sizes, multi-size favicon.ico, favicon.svg).

Run from anywhere:  python marketing/build/icons.py

Geometry and gradient stops are measured from priv-mark.png (512 x 512,
L1 half-diagonal bands from centre 256,256):

    pink ring   128 .. 208     transparent gap 108 .. 127
    gold ring    56 .. 107     transparent gap  39 .. 55
    white core    0 ..  38
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))     # .../Priv
MARKETING = os.path.join(ROOT, "marketing")
SRC = os.path.join(MARKETING, "assets", "brand", "priv-mark.png")
PUB = os.path.join(ROOT, "public")
DESKTOP_ICON = os.path.join(
    ROOT, "desktop-shell", "release", "__appImage-x64", "usr", "share",
    "icons", "hicolor", "0x0", "apps", "priv-core.png")

PNG_SIZES = [512, 192, 180]          # manifest + apple-touch (180 is the Apple size)
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]

# --- measured geometry, in a 100-unit viewBox -------------------------------
D_PINK_OUT, D_PINK_IN = 40.625, 25.0        # 208 and 128 of 512
D_GOLD_OUT, D_GOLD_IN = 20.9, 10.9375       # 107 and 56
D_WHITE = 7.52                              # 38.5
PINK = ("#FE296C", "#D41552")               # light -> dark, TL to BR
GOLD = ("#977F6F", "#755F50")


def _d(d):
    return (f"M50,{50 - d:g} L{50 + d:g},50 L50,{50 + d:g} L{50 - d:g},50 Z")


def svg_mark():
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" '
        'width="100" height="100" role="img" aria-label="Priv">\n'
        "  <defs>\n"
        f'    <linearGradient id="pk" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{PINK[0]}"/>'
        f'<stop offset="1" stop-color="{PINK[1]}"/></linearGradient>\n'
        f'    <linearGradient id="gd" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{GOLD[0]}"/>'
        f'<stop offset="1" stop-color="{GOLD[1]}"/></linearGradient>\n'
        "  </defs>\n"
        f'  <path fill="url(#pk)" fill-rule="evenodd" '
        f'd="{_d(D_PINK_OUT)} {_d(D_PINK_IN)}"/>\n'
        f'  <path fill="url(#gd)" fill-rule="evenodd" '
        f'd="{_d(D_GOLD_OUT)} {_d(D_GOLD_IN)}"/>\n'
        f'  <path fill="#FFFFFF" d="{_d(D_WHITE)}"/>\n'
        "</svg>\n"
    )


def main():
    if not os.path.exists(SRC):
        sys.exit(f"mark not found: {SRC}")
    src = Image.open(SRC).convert("RGBA")
    if src.size != (512, 512):
        src = src.resize((512, 512), Image.LANCZOS)

    written = []
    for s in PNG_SIZES:
        out = os.path.join(PUB, f"priv-icon-{s}.png")
        (src if s == 512 else src.resize((s, s), Image.LANCZOS)).save(out)
        written.append(out)

    ico = os.path.join(PUB, "favicon.ico")
    src.save(ico, format="ICO", sizes=[(s, s) for s in ICO_SIZES])
    written.append(ico)

    sv = os.path.join(PUB, "favicon.svg")
    with open(sv, "w", encoding="utf-8") as fh:
        fh.write(svg_mark())
    written.append(sv)

    if os.path.isdir(os.path.dirname(DESKTOP_ICON)):
        src.save(DESKTOP_ICON)
        written.append(DESKTOP_ICON)

    for p in written:
        if p.endswith(".svg"):
            print(f"  {os.path.relpath(p, ROOT):70} SVG "
                  f"{os.path.getsize(p)}B")
            continue
        im = Image.open(p)
        extra = ""
        if im.format == "ICO":
            extra = f"  sizes={sorted(im.info.get('sizes'))}"
        print(f"  {os.path.relpath(p, ROOT):70} {im.size} {im.format}{extra}")
    print(f"{len(written)} files written from {os.path.relpath(SRC, ROOT)}")


if __name__ == "__main__":
    main()
