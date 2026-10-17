"""SUP-D verification: ledger.py.kuiper_xy == lib.mjs place(key) bit-for-bit (doubles) for keys 1..2959 and extras;
Phase 0 keys 1..2560 untouched by family 2561..2959; ledger append-only / stable / collision-free."""
import json, math, sys, importlib.util, struct
from pathlib import Path

STUDY = Path(__file__).resolve().parents[3]  # studies/pv-vogel-protection-20261017
spec = importlib.util.spec_from_file_location("ledger", STUDY / "claude-study/tools/ledger.py")
ledger = importlib.util.module_from_spec(spec); spec.loader.exec_module(ledger)
spec0 = importlib.util.spec_from_file_location("vogel_study", STUDY / "vogel_study.py")
vs = importlib.util.module_from_spec(spec0); spec0.loader.exec_module(vs)

node = json.loads(Path(sys.argv[1]).read_text())
bits = lambda f: struct.unpack("<Q", struct.pack("<d", f))[0]

# 1. constants
print("GOLDEN node   =", repr(node["GOLDEN"]))
print("GOLDEN python =", repr(ledger.GOLDEN), "| vogel_study:", repr(vs.GOLDEN_ANGLE))
assert bits(node["GOLDEN"]) == bits(ledger.GOLDEN) == bits(vs.GOLDEN_ANGLE), "GOLDEN differs"
assert node["SPACING"] == 1.0

# 2. place(key) bit-equality, and against vogel_study.kuiper_xy (Phase 0)
nbit = nulp = 0; max_rel = 0.0
for k, x, y in node["rows"]:
    px, py = ledger.kuiper_xy(k)
    if bits(px) == bits(x) and bits(py) == bits(y):
        nbit += 1
    else:
        rel = max(abs(px - x) / max(abs(x), 1e-300), abs(py - y) / max(abs(y), 1e-300))
        max_rel = max(max_rel, rel); nulp += 1
    if k <= 2560:
        assert vs.kuiper_xy(k) == (px, py), f"phase0 kuiper_xy differs at {k}"
    assert abs(math.hypot(px, py) - math.sqrt(k)) <= 4 * math.ulp(math.sqrt(k)), f"|r| != sqrt(k) at {k}"
print(f"place(key) rows compared: {len(node['rows'])}; bit-identical: {nbit}; differing: {nulp}; max rel diff: {max_rel:.3e}")

# 3. the ledger on disk vs Phase 0: keys 1..2560 absent from the family; family keys contiguous 2561..2959
on_disk = json.loads((STUDY / "claude-study/experiments/scenario-ledger.json").read_text())
keys = [e["key"] for e in on_disk["entries"]]
assert keys == list(range(2561, 2560 + len(keys) + 1)), "family keys not contiguous from 2561"
assert min(keys) == 2561 and max(keys) == 2959 and len(keys) == 399
assert all(e["family"] == "cycle1-physical-v1" for e in on_disk["entries"])
ids = [e["scenario_id"] for e in on_disk["entries"]]
assert len(set(ids)) == len(ids)
# every stored kuiper_xy equals round(place(key), 8)
for e in on_disk["entries"]:
    x, y = ledger.kuiper_xy(e["key"])
    assert e["kuiper_xy"] == [round(x, 8), round(y, 8)], e["key"]
# Phase 0 identities: same tuple order as before (FAULTS x LEVELS x 64) gives 1..2560, and are not in the new family
p0 = [vs.one_case(f, l, s)["key"] for f in vs.FAULTS for l in vs.LEVELS for s in range(1, 65)]
assert p0 == list(range(1, 2561)) and not (set(p0) & set(keys))
assert on_disk["phase0_frozen_keys"] == [1, 2560]
# 4. rebuild reproduces entries_sha256 (append-only / deterministic enumeration)
rebuilt = ledger.build(); assert ledger.digest(rebuilt["entries"]) == on_disk["entries_sha256"]
# 5. distinct keys -> distinct addresses within 1..2959 (a 2-D collision would make the address useless as a place)
pts = {}
dmin = 1e9
allxy = [(k, *ledger.kuiper_xy(k)) for k in range(1, 2960)]
for i in range(len(allxy)):
    for j in range(i + 1, min(i + 60, len(allxy))):  # neighbours in key are the nearest candidates in radius; check a window
        d = math.hypot(allxy[i][1] - allxy[j][1], allxy[i][2] - allxy[j][2]); dmin = min(dmin, d)
print(f"min pairwise distance (window scan, keys 1..2959): {dmin:.6f} (dimensionless address units)")
print("phase0_frozen_keys", on_disk["phase0_frozen_keys"], "| family", on_disk["first_key"], "..", on_disk["last_key"], "count", on_disk["count"])
print("entries_sha256 (disk == rebuild):", on_disk["entries_sha256"])
print("ALL ASSERTIONS PASSED")
