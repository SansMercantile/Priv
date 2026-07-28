import os, re, json

ROOT = "/home/mpeti/workspace/constellation/shared_resources"
STUB_PATTERNS = re.compile(r'\bNotImplementedError\b|\bTODO\b|\bplaceholder\b|\bmock\b|\bsimulate[ds]?\b|\bdummy\b|\bstub\b', re.I)

results = {}
for entry in sorted(os.listdir(ROOT)):
    full = os.path.join(ROOT, entry)
    if not os.path.isdir(full) or entry == "__pycache__":
        continue
    total_lines = 0
    total_files = 0
    stub_hits = 0
    trivial_files = 0  # < 25 lines
    has_tests = False
    for dirpath, dirnames, filenames in os.walk(full):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        if "test" in dirpath.lower():
            has_tests = True
        for fn in filenames:
            if fn.endswith(".py"):
                fp = os.path.join(dirpath, fn)
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                except Exception:
                    continue
                lines = content.count("\n") + 1
                total_lines += lines
                total_files += 1
                if lines < 25:
                    trivial_files += 1
                stub_hits += len(STUB_PATTERNS.findall(content))
    if total_files == 0:
        continue
    results[entry] = {
        "files": total_files,
        "lines": total_lines,
        "avg_lines": round(total_lines / total_files, 1),
        "trivial_pct": round(100 * trivial_files / total_files, 1),
        "stub_hits": stub_hits,
        "stub_per_100_lines": round(100 * stub_hits / max(total_lines, 1), 2),
        "has_tests": has_tests,
    }

# Sort by lines descending
for k, v in sorted(results.items(), key=lambda x: -x[1]["lines"]):
    print(f"{k:30s} files={v['files']:4d} lines={v['lines']:6d} avg={v['avg_lines']:6.1f} trivial%={v['trivial_pct']:5.1f} stub/100L={v['stub_per_100_lines']:5.2f} tests={v['has_tests']}")
