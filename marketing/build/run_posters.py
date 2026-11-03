import os
import sys

import poster_specs
import posters

ONLY = sys.argv[1:] or None

made = []
for slug, spec in poster_specs.POSTERS.items():
    if ONLY and slug not in ONLY:
        continue
    for fmt in spec["formats"]:
        path = os.path.join(posters.OUT, fmt, f"priv-{slug}-{fmt}.jpg")
        posters.render(spec, fmt, path)
        made.append(path)
        print("ok", os.path.relpath(path, posters.OUT))

print(f"\n{len(made)} posters written to {posters.OUT}")
