"""Verify tools/ledger.py kuiper_core_xy against the live shell's keyPlace evaluated under Node (JSON on argv[1])."""
import json, struct, sys, importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location("ledger", Path(__file__).resolve().parents[1] / "tools" / "ledger.py")
ledger = importlib.util.module_from_spec(spec); spec.loader.exec_module(ledger)
node = json.loads(Path(sys.argv[1]).read_text())
bits = lambda f: struct.unpack("<Q", struct.pack("<d", f))[0]
same = ulp = 0; worst = 0.0
for k, x, y in node["rows"]:
    px, py = ledger.kuiper_core_xy(k)
    if bits(px) == bits(x) and bits(py) == bits(y): same += 1
    else:
        ulp += 1; worst = max(worst, abs(px - x) / max(abs(x), 1e-300), abs(py - y) / max(abs(y), 1e-300))
        assert worst < 1e-12, (k, px, x, py, y)
    assert [round(px, 8), round(py, 8)] == [round(x, 8), round(y, 8)], k
print(f"core law: {same} bit-identical, {ulp} within {worst:.2e} relative, 0 differences after round(.,8); keys checked {len(node['rows'])}")
led = json.loads((Path(__file__).resolve().parents[1] / "experiments" / "scenario-ledger.json").read_text())
for e in led["entries"]:
    cx, cy = ledger.kuiper_core_xy(e["key"]); assert e["kuiper_core_xy"] == [round(cx, 8), round(cy, 8)]
    lx, ly = ledger.kuiper_xy(e["key"]); assert e["kuiper_xy"] == [round(lx, 8), round(ly, 8)]
print("ledger: every entry carries both addresses; keys", led["first_key"], "..", led["last_key"], "ALL ASSERTIONS PASSED")
