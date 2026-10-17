#!/usr/bin/env python3
"""Illustrative, UNCALIBRATED static DC-arc law for the V11 cycle-1 study (worker W07, Track E).

Run from claude-study/:  python3 models/arc_model.py        -> deterministic JSON verification summary on stdout
Tests:                   python3 -m unittest -v models.test_arc_model

What this module is
- The fixture's static V-I law (fixture/system-fixture.json -> arc_model.static_vi_law), PARSED from the fixture text:
      |v| = (va0 + va1*gap_mm) * |i|**nexp      for |i| >= i_min        (Stokes-Oppenlander form, ASSUMED)
  with the fixture's minimum sustaining current i_min and ignition voltage.
- The fixture's constant-resistance alternative (R_arc in {1, 2, 5} ohm), cross-check only.
- Below i_min: a C1 odd-quadratic continuation  v = ca*i + cb*i*|i|  -> NUMERICAL, NOT PHYSICAL. It only keeps
  Newton iterations well posed (|i|**0.12 has an infinite slope at i = 0). A real arc is extinguished there.
- A post-processing extinction criterion: |i| < i_min continuously for longer than HOLD_S (ASSUMED 100 us).
- ngspice batch verification of models/arc_model.lib (ARC_SERIES, ARC_PARALLEL) against these functions.

What it is not
- Not a validated arc-plasma model. Python law values are evidence grade `algebra`; ngspice values are
  `illustrative_simulation`. Any extinction statement derived from them is ILLUSTRATIVE.
- Not modelled: arc ignition physics, HF noise signature, gap dynamics/electrode erosion, arc column cooling
  (time constants), ambient pressure/humidity, polarity asymmetry, re-ignition, plasma radiation and fire ignition.
- Outside the relayed Stokes-Oppenlander data range for gap < 5 mm and for |i| < 10 + 0.2*gap_mm (see validity_flags).
"""
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
FIXTURE = STUDY / "fixture" / "system-fixture.json"
LIB = HERE / "arc_model.lib"

# ---- values introduced by this worker (to be appended to assumptions.json by the orchestrator) ----------------------
HOLD_S = 1e-4            # ASSUMED (W07 task brief): extinction hold time
R_SHORT_OHM = 1e-6       # ASSUMED numerical (W07 task brief): intact-conductor resistance of ARC_SERIES before ignition
R_OFF_OHM = 1e9          # ASSUMED numerical: intact-insulation resistance of ARC_PARALLEL before ignition / open gap
TRAMP_S = 1e-7           # ASSUMED numerical: switching ramp of ignite/extinguish in arc_model.lib
# Literature range of the Stokes-Oppenlander data, RELAYED by Ammerman et al. 2010 (register L02); primary not read.
SO_GAP_RANGE_MM = (5.0, 500.0)
SO_TRANSITION_A0, SO_TRANSITION_A1 = 10.0, 0.2   # I_t = 10 + 0.2*gap_mm (A), relayed (L01/L02); law form valid above I_t

LAW_REGION = "FIXTURE_LAW_ASSUMED_UNCALIBRATED"
CONT_REGION = "NUMERICAL_CONTINUATION_NOT_PHYSICAL"


def _load_fixture():
    fx = json.loads(FIXTURE.read_text())
    am = fx["arc_model"]
    m = re.search(r"\(\s*([0-9.]+)\s*\+\s*([0-9.]+)\s*\*\s*gap_mm\s*\)\s*\*\s*I\^([0-9.]+)", am["static_vi_law"])
    if not m:
        raise ValueError("fixture arc_model.static_vi_law is not in the expected (a + b*gap_mm)*I^n form")
    m2 = re.search(r"\{([^}]*)\}\s*ohm", am["alternative"])
    if not m2:
        raise ValueError("fixture arc_model.alternative does not list R_arc values as {..} ohm")
    va0, va1, nexp = (float(x) for x in m.groups())
    return {
        "fixture_id": fx["fixture_id"],
        "arc_model_label": am["label"],
        "va0_v": va0, "va1_v_per_mm": va1, "nexp": nexp,
        "gap_mm_variants": tuple(float(g) for g in am["gap_mm_variants"]),
        "i_min_a": float(am["minimum_sustaining_current_a"]["value"]),
        "i_min_label": am["minimum_sustaining_current_a"]["label"],
        "v_ignition_v": float(am["ignition_voltage_v"]["value"]),
        "v_ignition_label": am["ignition_voltage_v"]["label"],
        "r_arc_alt_ohm": tuple(float(x) for x in m2.group(1).split(",")),
        "impp_a": float(fx["module"]["impp_a"]),
        "isc_a": float(fx["module"]["isc_a"]),
        "vmpp_string_v": float(fx["plant"]["string_derived"]["vmpp_string_v"]),
        "voc_string_stc_v": float(fx["plant"]["string_derived"]["voc_string_stc_v"]),
    }


FIX = _load_fixture()


def _out(x):
    x = np.asarray(x, dtype=float)
    return float(x) if x.ndim == 0 else x


def _imin(i_min_a):
    imin = FIX["i_min_a"] if i_min_a is None else float(i_min_a)
    if not imin > 0:
        raise ValueError("i_min_a must be > 0")
    return imin


def k_v(gap_mm):
    """Gap factor K = va0 + va1*gap_mm (V/A^nexp). gap_mm in mm (fixture naming)."""
    if gap_mm < 0:
        raise ValueError("gap_mm must be >= 0")
    return FIX["va0_v"] + FIX["va1_v_per_mm"] * gap_mm


def v_min_v(gap_mm, i_min_a=None):
    """Law voltage at the minimum sustaining current (V)."""
    imin = _imin(i_min_a)
    return k_v(gap_mm) * imin ** FIX["nexp"]


def continuation_coefficients(gap_mm, i_min_a=None):
    """(ca, cb) of the NUMERICAL continuation v = ca*i + cb*i*|i| for |i| < i_min.
    Matches value and slope of the law at |i| = i_min; v(0) = 0; dv/di > 0 on [0, i_min]."""
    imin, n = _imin(i_min_a), FIX["nexp"]
    vm = v_min_v(gap_mm, imin)
    return (2.0 - n) * vm / imin, -(1.0 - n) * vm / imin ** 2


def v_arc(i_a, gap_mm, i_min_a=None):
    """Arc voltage (V) for arc current i_a (A); odd, strictly increasing, C1 in i.
    |i| >= i_min: sign(i)*K(gap)*|i|^nexp   (fixture law, ASSUMED, uncalibrated)
    |i| <  i_min: ca*i + cb*i*|i|            (NUMERICAL CONTINUATION, NOT PHYSICAL)"""
    imin = _imin(i_min_a)
    i = np.asarray(i_a, dtype=float)
    a = np.abs(i)
    law = np.sign(i) * k_v(gap_mm) * np.power(np.maximum(a, imin), FIX["nexp"])
    ca, cb = continuation_coefficients(gap_mm, imin)
    return _out(np.where(a >= imin, law, ca * i + cb * i * a))


def dv_di(i_a, gap_mm, i_min_a=None):
    """Incremental resistance dv/di (ohm) of v_arc."""
    imin, n = _imin(i_min_a), FIX["nexp"]
    a = np.abs(np.asarray(i_a, dtype=float))
    ca, cb = continuation_coefficients(gap_mm, imin)
    law = n * k_v(gap_mm) * np.power(np.maximum(a, imin), n - 1.0)
    return _out(np.where(a >= imin, law, ca + 2.0 * cb * a))


def v_arc_resistive(i_a, r_arc_ohm):
    """Constant-resistance alternative (fixture cross-check only): v = R_arc * i."""
    if not r_arc_ohm > 0:
        raise ValueError("r_arc_ohm must be > 0")
    return _out(r_arc_ohm * np.asarray(i_a, dtype=float))


def region(i_a, i_min_a=None):
    return LAW_REGION if abs(float(i_a)) >= _imin(i_min_a) else CONT_REGION


def validity_flags(i_a, gap_mm, i_min_a=None):
    """Flags where (i, gap) lies outside the relayed Stokes-Oppenlander data (literature register L01/L02)."""
    a, flags = abs(float(i_a)), []
    if a < _imin(i_min_a):
        flags.append("BELOW_I_MIN_NUMERICAL_CONTINUATION_NOT_PHYSICAL")
    if gap_mm < SO_GAP_RANGE_MM[0] or gap_mm > SO_GAP_RANGE_MM[1]:
        flags.append("GAP_OUTSIDE_SO_DATA_5_TO_500_MM")
    if a < SO_TRANSITION_A0 + SO_TRANSITION_A1 * gap_mm:
        flags.append("BELOW_SO_TRANSITION_CURRENT_LAW_FORM_EXTRAPOLATED")
    return flags


def so_max_gap_mm(i_a):
    """Largest gap for which current i_a is still above the S-O transition current (mm)."""
    return (abs(float(i_a)) - SO_TRANSITION_A0) / SO_TRANSITION_A1


def series_operating_point(v_source_v, r_series_ohm, gap_mm, i_min_a=None, v_ignition_v=None):
    """Static intersection of a linear Thevenin source with the fixture law (ILLUSTRATIVE screening only).
    v_source_v is the open-circuit voltage the network presents across the separating contacts."""
    imin = _imin(i_min_a)
    vign = FIX["v_ignition_v"] if v_ignition_v is None else float(v_ignition_v)
    if not r_series_ohm > 0:
        raise ValueError("r_series_ohm must be > 0")
    res = {"v_source_v": v_source_v, "r_series_ohm": r_series_ohm, "gap_mm": gap_mm, "i_min_a": imin,
           "v_ignition_v": vign, "i_a": 0.0, "v_arc_v": 0.0, "p_arc_w": 0.0}
    if abs(v_source_v) < vign:
        res["status"] = "NO_IGNITION_SOURCE_BELOW_IGNITION_VOLTAGE_ILLUSTRATIVE"
        return res
    s, vs = math.copysign(1.0, v_source_v), abs(v_source_v)
    f = lambda i: vs - r_series_ohm * i - v_arc(i, gap_mm, imin)
    if f(imin) < 0:
        res["status"] = "NO_STATIC_ARC_POINT_ABOVE_I_MIN_ILLUSTRATIVE"
        return res
    i = brentq(f, imin, vs / r_series_ohm, xtol=1e-14, rtol=1e-14, maxiter=200)
    v = v_arc(i, gap_mm, imin)
    res.update(status="ARC_SUSTAINED_STATIC_POINT_ILLUSTRATIVE", i_a=s * i, v_arc_v=s * v, p_arc_w=i * v,
               validity_flags=validity_flags(i, gap_mm, imin))
    return res


def parallel_operating_point(i_source_a, gap_mm, r_fault_series_ohm=0.0, r_shunt_ohm=math.inf, i_min_a=None,
                             v_ignition_v=None):
    """Norton source (i_source_a in parallel with r_shunt_ohm) feeding a shunt arc whose fault path has an optional
    series resistance r_fault_series_ohm (ILLUSTRATIVE). Returns the arc current, arc voltage and terminal voltage."""
    imin = _imin(i_min_a)
    vign = FIX["v_ignition_v"] if v_ignition_v is None else float(v_ignition_v)
    if i_source_a <= 0 or r_fault_series_ohm < 0 or not r_shunt_ohm > 0:
        raise ValueError("invalid Norton source or fault path")
    res = {"i_source_a": i_source_a, "r_shunt_ohm": r_shunt_ohm, "r_fault_series_ohm": r_fault_series_ohm,
           "gap_mm": gap_mm, "i_arc_a": 0.0, "v_arc_v": 0.0, "v_terminal_v": 0.0, "p_arc_w": 0.0}
    if math.isfinite(r_shunt_ohm) and i_source_a * r_shunt_ohm < vign:
        res["status"] = "NO_IGNITION_SOURCE_BELOW_IGNITION_VOLTAGE_ILLUSTRATIVE"
        return res
    if math.isinf(r_shunt_ohm):
        i = i_source_a
    else:
        g = lambda x: (i_source_a - x) * r_shunt_ohm - v_arc(x, gap_mm, imin) - r_fault_series_ohm * x
        if i_source_a < imin or g(imin) < 0:
            res["status"] = "NO_STATIC_ARC_POINT_ABOVE_I_MIN_ILLUSTRATIVE"
            return res
        i = brentq(g, imin, i_source_a, xtol=1e-14, rtol=1e-14, maxiter=200)
    if i < imin:
        res["status"] = "NO_STATIC_ARC_POINT_ABOVE_I_MIN_ILLUSTRATIVE"
        return res
    v = v_arc(i, gap_mm, imin)
    res.update(status="ARC_SUSTAINED_STATIC_POINT_ILLUSTRATIVE", i_arc_a=i, v_arc_v=v,
               v_terminal_v=v + r_fault_series_ohm * i, p_arc_w=v * i, validity_flags=validity_flags(i, gap_mm, imin))
    return res


def extinction(t_s, i_a, i_min_a=None, hold_s=HOLD_S, t_ignite_s=None):
    """Post-processing extinction criterion (ILLUSTRATIVE; hold time ASSUMED 100 us).

    The arc is declared extinguished at t_x = t0 + hold_s, where t0 is the start of the first interval at or after
    t_ignite_s during which |i| < i_min continuously and whose duration is strictly longer than hold_s.
    t0 (and the end of an interval) are located by linear interpolation of the crossing of |i| through i_min; an
    interval already in progress at the start of the window starts at the first window sample. A sample with
    |i| == i_min is not below. Energy to the fault should be integrated up to t_x (arc_energy_j); quantities after
    t_x from the same run are invalid (the element keeps conducting through the numerical continuation): re-run
    with ARC_* parameter extinguish = t_x (two-pass method) for post-extinction node voltages.
    """
    t, i = np.asarray(t_s, dtype=float), np.abs(np.asarray(i_a, dtype=float))
    if t.ndim != 1 or t.shape != i.shape or t.size < 2 or np.any(np.diff(t) <= 0):
        raise ValueError("t_s must be strictly increasing and the same length as i_a (>= 2 samples)")
    if not hold_s > 0:
        raise ValueError("hold_s must be > 0")
    imin = _imin(i_min_a)
    k0 = 0 if t_ignite_s is None else int(np.searchsorted(t, t_ignite_s, side="left"))
    res = {"status": "NOT_EXTINGUISHED_IN_RECORD_ILLUSTRATIVE", "t_extinct_s": None, "t_below_start_s": None,
           "longest_below_s": 0.0, "i_min_a": imin, "hold_s": hold_s, "criterion": "|i| < i_min for longer than hold_s"}
    if k0 >= t.size:
        res["status"] = "UNDETERMINED_NO_SAMPLES_AFTER_IGNITION"
        return res
    below = i < imin
    n, k = t.size, k0
    while k < n:
        if not below[k]:
            k += 1
            continue
        s = k
        if s == k0:
            t0 = t[s]
        else:
            t0 = t[s - 1] + (i[s - 1] - imin) / (i[s - 1] - i[s]) * (t[s] - t[s - 1])
        while k < n and below[k]:
            k += 1
        e = k - 1
        if e == n - 1:
            t1, open_end = t[-1], True
        else:
            t1, open_end = t[e] + (imin - i[e]) / (i[e + 1] - i[e]) * (t[e + 1] - t[e]), False
        dur = t1 - t0
        res["longest_below_s"] = max(res["longest_below_s"], dur)
        if dur > hold_s:
            res.update(status="EXTINGUISHED_ILLUSTRATIVE", t_extinct_s=t0 + hold_s, t_below_start_s=t0)
            return res
        if open_end:
            res.update(status="UNDETERMINED_RECORD_ENDS_DURING_HOLD", t_below_start_s=t0)
            return res
    return res


def arc_energy_j(t_s, v_v, i_a, t_start_s, t_stop_s):
    """Energy delivered to the arc (J): trapezoidal integral of v*i from t_start_s to t_stop_s, with linear
    interpolation of the power at both bounds."""
    t = np.asarray(t_s, dtype=float)
    p = np.asarray(v_v, dtype=float) * np.asarray(i_a, dtype=float)
    if not t[0] <= t_start_s < t_stop_s <= t[-1]:
        raise ValueError("integration bounds outside the record")
    inner = (t > t_start_s) & (t < t_stop_s)
    tt = np.concatenate(([t_start_s], t[inner], [t_stop_s]))
    pp = np.concatenate(([np.interp(t_start_s, t, p)], p[inner], [np.interp(t_stop_s, t, p)]))
    return float(np.sum(0.5 * (pp[1:] + pp[:-1]) * np.diff(tt)))


# ---------------------------------------------------------------------------------------------------- ngspice ------
def ngspice_version():
    exe = shutil.which("ngspice")
    if not exe:
        return None
    r = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=60)
    for line in (r.stdout + r.stderr).splitlines():
        if "ngspice-" in line:
            return line.strip("* \t")
    return "ngspice (version line not found)"


def _law_params():
    return f"va0={FIX['va0_v']!r} va1={FIX['va1_v_per_mm']!r} nexp={FIX['nexp']!r} i_min={FIX['i_min_a']!r}"


def run_ngspice(body, vectors, analysis):
    """Run one batch ngspice job with arc_model.lib included; return (sweep_or_time, [vector arrays])."""
    exe = shutil.which("ngspice")
    if not exe:
        raise RuntimeError("ngspice not found on PATH")
    with tempfile.TemporaryDirectory(prefix="w07_arc_") as d:
        dp = Path(d)
        shutil.copyfile(LIB, dp / "arc_model.lib")
        net = "\n".join([
            "* W07 arc_model verification job (generated by models/arc_model.py)",
            ".include arc_model.lib", body.strip(),
            ".options reltol=1e-6 abstol=1e-12 vntol=1e-9",
            ".control", "set wr_singlescale", "set wr_vecnames", "option numdgt=12",
            analysis, "wrdata out.dat " + " ".join(vectors), ".endc", ".end", ""])
        (dp / "case.cir").write_text(net)
        r = subprocess.run([exe, "-b", "case.cir"], cwd=d, capture_output=True, text=True, timeout=600)
        log = r.stdout + r.stderr
        errs = [ln for ln in log.splitlines() if ln.strip().lower().startswith("error")]
        if r.returncode != 0 or errs or not (dp / "out.dat").exists():
            raise RuntimeError("ngspice failed: rc=%s %s" % (r.returncode, "; ".join(errs[:5])))
        data = np.loadtxt(dp / "out.dat", skiprows=1, ndmin=2)
    if data.shape[1] != len(vectors) + 1:
        raise RuntimeError("unexpected wrdata column count")
    return data[:, 0], [data[:, k + 1] for k in range(len(vectors))]


def _rel(a, b):
    return abs(a - b) / abs(b)


def _sig(x, n=9):
    return float(f"{x:.{n}g}")


T_IGN_S = 1e-4   # verification ignition time (ASSUMED test value)


def verify_series(gaps=None, v_source_v=1144.0, r_series_ohm=60.0):
    """ARC_SERIES in a 1144 V / 60 ohm test loop (task-brief test circuit, NOT a PV source)."""
    gaps = FIX["gap_mm_variants"] if gaps is None else gaps
    body, vecs = [], []
    for k, g in enumerate(gaps):
        body += [f"Vs{k} s{k} 0 DC {v_source_v!r}", f"Rs{k} s{k} a{k} {r_series_ohm!r}",
                 f"Xa{k} a{k} 0 ARC_SERIES gap_mm={g!r} ignite={T_IGN_S!r} {_law_params()}"]
        vecs += [f"v(a{k})", f"i(v.xa{k}.vsense)"]
    t, cols = run_ngspice("\n".join(body), vecs, "tran 1e-7 1e-3 0 1e-6")
    k_pre = int(np.searchsorted(t, 0.5 * T_IGN_S))
    rows = []
    for k, g in enumerate(gaps):
        v, i = cols[2 * k], cols[2 * k + 1]
        py = series_operating_point(v_source_v, r_series_ohm, g)
        i_pre_py = v_source_v / (r_series_ohm + R_SHORT_OHM)
        rows.append({"gap_mm": g, "v_source_v": v_source_v, "r_series_ohm": r_series_ohm,
                     "i_pre_ignition_spice_a": _sig(i[k_pre]), "i_pre_ignition_python_a": _sig(i_pre_py),
                     "i_arc_spice_a": _sig(i[-1]), "i_arc_python_a": _sig(py["i_a"]),
                     "v_arc_spice_v": _sig(v[-1]), "v_arc_python_v": _sig(py["v_arc_v"]),
                     "p_arc_python_w": _sig(py["p_arc_w"]),
                     "rel_err_i": _sig(_rel(i[-1], py["i_a"]), 3), "rel_err_v": _sig(_rel(v[-1], py["v_arc_v"]), 3),
                     "pass_within_1pct": bool(_rel(i[-1], py["i_a"]) < 0.01 and _rel(v[-1], py["v_arc_v"]) < 0.01
                                              and _rel(i[k_pre], i_pre_py) < 0.01),
                     "validity_flags": py["validity_flags"],
                     "label": "DERIVED", "grade": "illustrative_simulation"})
    return rows


def verify_dc_sweep(i_max_a=20.0, step_a=0.01, gap_mm=3.0):
    """DC current sweep through both elements: ngspice lib vs Python v_arc (incl. continuation and sign)."""
    body = "\n".join([
        "Isw 0 n1 DC 0", f"Xs n1 0 ARC_SERIES gap_mm={gap_mm!r} ignite=0 {_law_params()}",
        "Isw2 0 n2 DC 0", f"Xp n2 0 ARC_PARALLEL gap_mm={gap_mm!r} ignite=0 {_law_params()}"])
    # Isw2 is swept by a second job (ngspice .dc sweeps one source per job here for clarity)
    out = {}
    for name, node, src in (("ARC_SERIES", "n1", "Isw"), ("ARC_PARALLEL", "n2", "Isw2")):
        sw, (v, i) = run_ngspice(body, [f"v({node})", f"i(v.x{'s' if node == 'n1' else 'p'}.vsense)"],
                                 f"dc {src} {-i_max_a!r} {i_max_a!r} {step_a!r}")
        v_py = v_arc(i, gap_mm) + 1e-6 * i     # r_short (series) and r_on (parallel) are both 1 uOhm by default
        err = np.abs(v - v_py)
        out[name] = {"points": int(sw.size), "i_range_a": [_sig(float(i.min())), _sig(float(i.max()))],
                     "max_abs_err_v": _sig(float(err.max()), 3),
                     "max_rel_err_where_abs_v_gt_1v": _sig(float(np.max(err[np.abs(v_py) > 1] / np.abs(v_py[np.abs(v_py) > 1]))), 3),
                     "current_matches_sweep": bool(np.allclose(i, sw, rtol=1e-6, atol=1e-9))}
    return {"gap_mm": gap_mm, "results": out, "label": "DERIVED", "grade": "illustrative_simulation"}


def verify_parallel(i_source_a=None, r_series_extra_ohm=0.1):
    """ARC_PARALLEL across an ideal current source = fixture module/string Isc (18.4 A): V_arc vs gap table, the
    constant-resistance alternatives and one row with an ASSUMED 0.1 ohm fault-path series resistance."""
    isrc = FIX["isc_a"] if i_source_a is None else i_source_a
    cases = [("SO", g, 0.0, None) for g in FIX["gap_mm_variants"]]
    cases += [("SO", 3.0, r_series_extra_ohm, None)]
    cases += [("R", None, 0.0, r) for r in FIX["r_arc_alt_ohm"]]
    body, vecs = [], []
    for k, (law, g, rs, r) in enumerate(cases):
        extra = f"law=1 r_arc={r!r}" if law == "R" else f"gap_mm={g!r}"
        body += [f"Ip{k} 0 p{k} DC {isrc!r}", f"Xp{k} p{k} 0 ARC_PARALLEL {extra} r_series={rs!r} ignite=0 {_law_params()}"]
        vecs += [f"v(p{k})", f"i(v.xp{k}.vsense)"]
    _, cols = run_ngspice("\n".join(body), vecs, "tran 1e-6 1e-4 0 1e-6")
    rows = []
    for k, (law, g, rs, r) in enumerate(cases):
        v, i = cols[2 * k][-1], cols[2 * k + 1][-1]
        if law == "R":
            v_py, flags = float(v_arc_resistive(isrc, r)), ["CONSTANT_RESISTANCE_CROSS_CHECK_ONLY"]
            if v_py < FIX["v_ignition_v"]:
                flags.append("ARC_VOLTAGE_BELOW_FIXTURE_15V_MINIMUM_INCONSISTENT")
            row = {"law": f"constant_resistance_r_arc_{r:g}_ohm", "gap_mm": None}
        else:
            py = parallel_operating_point(isrc, g, r_fault_series_ohm=rs)
            v_py, flags = py["v_terminal_v"], py["validity_flags"]
            row = {"law": "fixture_stokes_oppenlander_form", "gap_mm": g}
        row.update({"i_source_a": isrc, "r_fault_series_ohm": rs, "i_arc_spice_a": _sig(i),
                    "v_terminal_spice_v": _sig(v), "v_terminal_python_v": _sig(v_py),
                    "p_fault_python_w": _sig(v_py * isrc), "rel_err_v": _sig(_rel(v, v_py), 3),
                    "pass_within_1pct": bool(_rel(v, v_py) < 0.01 and _rel(i, isrc) < 0.01),
                    "validity_flags": flags, "label": "DERIVED", "grade": "illustrative_simulation"})
        rows.append(row)
    return rows


def verify_parallel_ignition(gap_mm=3.0):
    """ARC_PARALLEL switched in at T_IGN_S across a linear Norton stand-in (Isc || Voc_string_stc/Isc).
    The Norton source is NOT a PV model (illustrative stand-in that lets the pre-ignition voltage exist)."""
    isc, r_n = FIX["isc_a"], FIX["voc_string_stc_v"] / FIX["isc_a"]
    body = f"In 0 pn DC {isc!r}\nRn pn 0 {r_n!r}\nXn pn 0 ARC_PARALLEL gap_mm={gap_mm!r} ignite={T_IGN_S!r} {_law_params()}"
    t, (v, i) = run_ngspice(body, ["v(pn)", "i(v.xn.vsense)"], "tran 1e-7 1e-3 0 1e-6")
    k_pre = int(np.searchsorted(t, 0.5 * T_IGN_S))
    py = parallel_operating_point(isc, gap_mm, r_shunt_ohm=r_n)
    v_pre_py = isc * (r_n * R_OFF_OHM / (r_n + R_OFF_OHM))
    return {"gap_mm": gap_mm, "i_norton_a": isc, "r_norton_ohm": _sig(r_n), "ignite_s": T_IGN_S,
            "v_pre_ignition_spice_v": _sig(v[k_pre]), "v_pre_ignition_python_v": _sig(v_pre_py),
            "i_arc_spice_a": _sig(i[-1]), "i_arc_python_a": _sig(py["i_arc_a"]),
            "v_arc_spice_v": _sig(v[-1]), "v_arc_python_v": _sig(py["v_arc_v"]),
            "pass_within_1pct": bool(_rel(v[k_pre], v_pre_py) < 0.01 and _rel(i[-1], py["i_arc_a"]) < 0.01
                                     and _rel(v[-1], py["v_arc_v"]) < 0.01),
            "label": "DERIVED", "grade": "illustrative_simulation",
            "note": "r_norton = voc_string_stc_v / isc_a (DERIVED); linear stand-in, not a PV IV curve"}


def verify_two_pass_extinction(gap_mm=3.0, r_series_ohm=60.0, v_high_v=1144.0, v_low_v=40.0):
    """Demonstrates the post-processing criterion and the two-pass method on a test loop whose source is ramped
    down (ASSUMED test waveform) until no static arc point above i_min exists. ILLUSTRATIVE only."""
    pwl = f"PWL(0 {v_high_v!r} 2e-4 {v_high_v!r} 3e-4 {v_low_v!r} 2e-3 {v_low_v!r})"
    base = f"Vs s 0 {pwl}\nRs s a {r_series_ohm!r}\nXa a 0 ARC_SERIES gap_mm={gap_mm!r} ignite={T_IGN_S!r} {_law_params()}"
    t1, (v1, i1) = run_ngspice(base, ["v(a)", "i(v.xa.vsense)"], "tran 1e-7 1e-3 0 1e-6")
    ext = extinction(t1, i1, t_ignite_s=T_IGN_S)
    out = {"gap_mm": gap_mm, "source": pwl, "r_series_ohm": r_series_ohm, "hold_s": HOLD_S,
           "pass1_extinction": {k: (_sig(v) if isinstance(v, float) else v) for k, v in ext.items()},
           "label": "DERIVED", "grade": "illustrative_simulation",
           "statement": "illustrative only: uncalibrated law, assumed i_min and hold time"}
    # analytic crossing: v_source(t) = r*i_min + v_min  on the ramp
    v_cross = r_series_ohm * FIX["i_min_a"] + v_min_v(gap_mm)
    t_cross = 2e-4 + (v_high_v - v_cross) / (v_high_v - v_low_v) * 1e-4
    out["t_below_start_analytic_s"] = _sig(t_cross)
    if ext["t_extinct_s"] is None:
        return out
    tx = ext["t_extinct_s"]
    out["e_arc_ignite_to_extinct_j"] = _sig(arc_energy_j(t1, v1, i1, T_IGN_S, tx))
    t2, (v2, i2) = run_ngspice(base.replace(f"ignite={T_IGN_S!r}", f"ignite={T_IGN_S!r} extinguish={tx!r}"),
                               ["v(a)", "i(v.xa.vsense)", "v(s)"], "tran 1e-7 1e-3 0 1e-6")[0], \
        run_ngspice(base.replace(f"ignite={T_IGN_S!r}", f"ignite={T_IGN_S!r} extinguish={tx!r}"),
                    ["v(a)", "i(v.xa.vsense)"], "tran 1e-7 1e-3 0 1e-6")[1]
    k_chk = int(np.searchsorted(t2, tx - 1e-6)) - 1
    out["pass2"] = {"extinguish_s": _sig(tx), "i_end_a": _sig(i2[-1], 4), "v_gap_end_v": _sig(v2[-1]),
                    "pass1_pass2_current_match_before_tx": bool(abs(np.interp(t2[k_chk], t1, i1) - i2[k_chk]) < 1e-6),
                    "e_arc_ignite_to_extinct_pass2_j": _sig(arc_energy_j(t2, v2, i2, T_IGN_S, tx)),
                    "note": "after extinguish the gap is a 1 GOhm open: full source voltage appears across it"}
    return out


def literature_spot_checks():
    """Fixture law vs public data points (literature register IDs). Conditions are NOT matched: magnitude check only,
    DERIVED, illustrative; NOT a calibration."""
    x17 = FIX["impp_a"]
    paukert_5mm = 71.39 * x17 ** -0.186     # L03 via L04 (5 mm form relayed by Najam et al. 2020)
    so5 = float(v_arc(x17, 5.0))
    nrel_v, nrel_i = 75.0, 18.0             # L08: ~75 V average at ~18 A (gap not reported per test)
    zmax = so_max_gap_mm(nrel_i)
    return [
        {"source_id": "L03/L04", "what": "Paukert 5 mm form 71.39*I^-0.186 at Impp vs fixture law at 5 mm",
         "paukert_v": _sig(paukert_5mm, 5), "fixture_law_v": _sig(so5, 5), "ratio": _sig(paukert_5mm / so5, 4)},
        {"source_id": "L05", "what": "Sandia 2012 sustained parallel arcs 18-22 V at 1.8-8.1 A (gap uncontrolled)",
         "fixture_law_gap0_v": [_sig(float(v_arc(1.8, 0.0)), 4), _sig(float(v_arc(8.1, 0.0)), 4)],
         "fixture_law_gap1_v": [_sig(float(v_arc(1.8, 1.0)), 4), _sig(float(v_arc(8.1, 1.0)), 4)]},
        {"source_id": "L04", "what": "Najam 2020 relay arcs: initial arc voltage 11-13 V (Cu), 0.5-20 A",
         "fixture_law_gap0_v": [_sig(float(v_arc(0.5, 0.0)), 4), _sig(float(v_arc(20.0, 0.0)), 4)]},
        {"source_id": "L08", "what": "NREL 2019 PV arc ~75 V at ~18 A vs largest fixture-law voltage inside S-O window",
         "so_window_max_gap_mm_at_18a": _sig(zmax, 4), "fixture_law_max_in_window_v": _sig(float(v_arc(nrel_i, zmax)), 4),
         "measured_v": nrel_v, "ratio_measured_to_window_max": _sig(nrel_v / float(v_arc(nrel_i, zmax)), 4)},
    ]


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def summary():
    x17 = FIX["impp_a"]
    out = {
        "status": "ILLUSTRATIVE_UNCALIBRATED_ARC_LAW_VERIFICATION",
        "fixture_id": FIX["fixture_id"], "fixture_arc_model_label": FIX["arc_model_label"],
        "law": {"form": "|v| = (va0 + va1*gap_mm)*|i|^nexp for |i| >= i_min", "va0_v": FIX["va0_v"],
                "va1_v_per_mm": FIX["va1_v_per_mm"], "nexp": FIX["nexp"], "i_min_a": FIX["i_min_a"],
                "i_min_label": FIX["i_min_label"], "v_ignition_v": FIX["v_ignition_v"],
                "v_ignition_label": FIX["v_ignition_label"], "r_arc_alt_ohm": list(FIX["r_arc_alt_ohm"]),
                "continuation": "v = ca*i + cb*i*|i| for |i| < i_min; C1; NUMERICAL_NOT_PHYSICAL",
                "extinction": "|i| < i_min continuously for longer than hold_s; hold_s ASSUMED",
                "hold_s": HOLD_S},
        "assumptions_added": [
            {"name": "arc_extinction_hold_s", "value": HOLD_S, "label": "ASSUMED"},
            {"name": "arc_series_r_short_ohm", "value": R_SHORT_OHM, "label": "ASSUMED_numerical"},
            {"name": "arc_r_off_and_r_open_ohm", "value": R_OFF_OHM, "label": "ASSUMED_numerical"},
            {"name": "arc_r_on_ohm", "value": 1e-6, "label": "ASSUMED_numerical"},
            {"name": "arc_switch_ramp_s", "value": TRAMP_S, "label": "ASSUMED_numerical"}],
        "python_law_at_impp": [],
        "so_validity_window_at_fixture_currents": {
            "rule": "gap 5-500 mm and |i| >= 10 + 0.2*gap_mm (relayed, literature L01/L02)",
            "max_gap_mm_at_impp": _sig(so_max_gap_mm(x17), 5), "max_gap_mm_at_isc": _sig(so_max_gap_mm(FIX["isc_a"]), 5),
            "transition_current_a_for_fixture_gaps": {str(g): SO_TRANSITION_A0 + SO_TRANSITION_A1 * g
                                                      for g in FIX["gap_mm_variants"]},
            "i_min_to_transition_ratio_gap1": _sig(FIX["i_min_a"] / (SO_TRANSITION_A0 + SO_TRANSITION_A1), 4)},
        "literature_spot_checks": literature_spot_checks(),
    }
    for g in FIX["gap_mm_variants"]:
        v = float(v_arc(x17, g))
        out["python_law_at_impp"].append({"gap_mm": g, "i_a": x17, "v_arc_v": _sig(v), "p_arc_w": _sig(v * x17),
                                          "v_at_i_min_v": _sig(v_min_v(g)), "region": region(x17),
                                          "validity_flags": validity_flags(x17, g), "label": "DERIVED", "grade": "algebra"})
    ver = ngspice_version()
    out["ngspice"] = ver if ver else "NOT_AVAILABLE"
    if ver:
        out["series_verification_1144v_60ohm"] = verify_series()
        out["lib_vs_python_dc_sweep"] = verify_dc_sweep()
        out["parallel_table_isc_current_source"] = verify_parallel()
        out["parallel_ignition_norton"] = verify_parallel_ignition()
        out["two_pass_extinction_demo"] = verify_two_pass_extinction()
    out["not_modelled"] = ["arc ignition physics (ignition imposed at 'ignite')", "HF noise signature",
                           "gap dynamics / electrode erosion / contact evolution", "arc column thermal time constants",
                           "ambient pressure, humidity, electrode material", "polarity asymmetry", "re-ignition",
                           "radiation, plasma heating of polymers, fire ignition", "below-I_t inverse V-I characteristic"]
    out["files"] = {"claude-study/models/arc_model.py": sha256_file(__file__),
                    "claude-study/models/arc_model.lib": sha256_file(LIB),
                    "claude-study/fixture/system-fixture.json": sha256_file(FIXTURE)}
    return out


if __name__ == "__main__":
    s = summary()
    print(json.dumps(s, indent=1))
    checks = []
    for key in ("series_verification_1144v_60ohm", "parallel_table_isc_current_source"):
        checks += [r["pass_within_1pct"] for r in s.get(key, [])]
    if "parallel_ignition_norton" in s:
        checks.append(s["parallel_ignition_norton"]["pass_within_1pct"])
    sys.exit(0 if all(checks) else 1)
