#!/usr/bin/env python3
"""CTRL-01 second, independent integral for the C2-far C_in transient (bonus item B-C2-cin).

Runs ngspice 42 in batch on c2far_cin_transient.cir (lumped, illustrative_simulation, UNCALIBRATED arc law),
parses the in-simulator `meas` integrals and compares them with the scipy LSODA result in cleanroom-results.json.
Run from claude-study/:  python3 -I review/controls/CTRL-01/ctrl01_ngspice_check.py
Writes review/controls/CTRL-01/ngspice-check.json (deterministic; no waveform file is kept).
"""
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
cir = HERE / "c2far_cin_transient.cir"
out = subprocess.run(["ngspice", "-b", str(cir)], capture_output=True, text=True, timeout=60, cwd=HERE).stdout
meas = {k: float(v) for k, v in re.findall(r"^(earc50|earc10|iarcmax|vnodeend)\s*=\s*([-+0-9.eE]+)", out, re.M)}
ref = json.loads((HERE / "cleanroom-results.json").read_text())["B_bonus"]
p_ss = ref["c2_far_transient_ode_cin_150uF"]["p_steady_w"]
res = {
    "ngspice": meas,
    "ngspice_excess_over_steady_50ms_j": meas["earc50"] - p_ss * 0.05,
    "ngspice_excess_over_steady_10ms_j": meas["earc10"] - p_ss * 0.01,
    "scipy_e_arc_50ms_j": ref["c2_far_transient_ode_cin_150uF"]["e_arc_0_to_tend_j"],
    "scipy_e_arc_10ms_j": ref["c2_far_transient_ode_cin_150uF_first_10ms"]["e_arc_0_to_tend_j"],
}
res["rel_diff_50ms"] = meas["earc50"] / res["scipy_e_arc_50ms_j"] - 1.0
res["rel_diff_10ms"] = meas["earc10"] / res["scipy_e_arc_10ms_j"] - 1.0
res["within_A018_0p02"] = abs(res["rel_diff_50ms"]) <= 0.02 and abs(res["rel_diff_10ms"]) <= 0.02
assert res["within_A018_0p02"], res
(HERE / "ngspice-check.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
print(json.dumps(res, sort_keys=True))
