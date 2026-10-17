"""B1: minimal explicit PV circuit connectivity and bounded electrical envelopes.

Evidence grade: ALGEBRA / TOPOLOGY + ILLUSTRATIVE quasi-static I-V.
Not an EMT solver, physical arc-plasma law, qualified protective action, or safe design.
All fixture quantities are pinned in ../fixture/system-fixture.json (PR #7).
No assumption that opening a breaker removes illuminated-PV/cable capacitance.
"""
from __future__ import annotations
import json
import math
from collections import defaultdict, deque
from pathlib import Path

FIXTURE = Path(__file__).resolve().parents[1] / "fixture" / "system-fixture.json"
CASES = ("C1loop", "C1in", "C2-far", "C2-near", "C3")
ACTIONS = ("P0", "P1", "P1b", "P2", "P2b", "P3")
RATED_ARC_V = 30.0   # SCREENING LOAD ONLY, not a calibrated arc voltage


def fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _edges(protection: str, f: dict):
    if protection not in ACTIONS:
        raise ValueError("unknown action")
    # Only positive conductors carry the two explicitly drawn series switches.
    # minus conductors remain connected; residual voltage/dual earth faults unmodelled.
    arr_open = protection in ("P2b", "P3")
    inv_open = protection in ("P2", "P3")
    e = []
    for pole in ("p", "n"):
        # 936m array-to-inverter S20 conductor: 5m + 926m + 5m.
        lengths = ((f"S20{pole}", f"F20{pole}", 5.0, arr_open),
                   (f"F20{pole}", f"N20{pole}", 926.0, False),
                   (f"N20{pole}", f"MPPT{pole}", 5.0, inv_open))
        for a, b, length, is_open in lengths:
            if pole == "n" or not is_open:
                e.append((a, b, length, "wire"))
        # Paired S19 has separate assumed 600m home run to SAME MPPT node.
        e.append((f"S19{pole}", f"MPPT{pole}", 600.0, "wire"))
    return e


def _reachable(edges, start, target):
    adj = defaultdict(list)
    for a, b, length, typ in edges:
        adj[a].append((b, length))
        adj[b].append((a, length))
    if start == target:
        return True, 0.0
    # Existing paths here are single-path trees. Generic Dijkstra for future loops.
    import heapq
    seen, heap = set(), [(0.0, start)]
    while heap:
        d, u = heapq.heappop(heap)
        if u in seen:
            continue
        if u == target:
            return True, d
        seen.add(u)
        for v, length in adj[u]:
            if v not in seen:
                heapq.heappush(heap, (d + length, v))
    return False, math.inf


def parallel_fault_paths(location: str, action: str, f: dict | None = None):
    """Sustained PV source-loop reachability to a parallel fault on S20 home run.

    A source is topologically capable of feeding the fault only when its
    positive AND negative terminal each has a conductive path to the two fault
    nodes. This is necessary but not sufficient for positive current/arc.
    No capacitive feed is counted as sustained; finite stored energy remains.
    """
    f = fixture() if f is None else f
    if location not in ("C2-far", "C2-near"):
        raise ValueError("unsupported parallel fault")
    target = ("F20p", "F20n") if location == "C2-far" else ("N20p", "N20n")
    edges = _edges(action, f)
    area = f["conductors"]["field_cable"]["resistance_ohm_per_km_20c"] / 1000.0
    out = {}
    for src in ("S20", "S19"):
        okp, lp = _reachable(edges, src + "p", target[0])
        okn, ln = _reachable(edges, src + "n", target[1])
        alive = okp and okn
        out[src] = {
            "sustained_path": alive,
            "plus_length_m": round(lp, 4) if okp else None,
            "minus_length_m": round(ln, 4) if okn else None,
            "loop_resistance_ohm_20c": round((lp + ln) * area, 6) if alive else None,
        }
    # One capacitor at MPPT, not a sustained PV source; opening P2/P3
    # removes its positive reachability from the fault but does NOT prove
    # the isolated cable is discharged or free of line capacitance.
    cp, _ = _reachable(edges, "MPPTp", target[0])
    cn, _ = _reachable(edges, "MPPTn", target[1])
    return {"fault": location, "action": action, "pv_sources": out,
            "mppt_input_capacitor_has_path": cp and cn,
            "line_capacitive_energy": "UNKNOWN_NOT_MODELLED",
            "fault_interruption_proved": False}


def pv_current_for_terminal_voltage(v_terminal, f: dict):
    """Explicit synthetic monotonic STC I-V fit through Voc/Isc/Vmpp/Impp.

    NOTE: NOT a physical single-diode model and NOT adequate for arcs or
    fault interrupt ratings. Fits 4 nominal data points for positive voltages.
    """
    m, plant = f["module"], f["plant"]
    voc = m["voc_stc_v"] * plant["modules_per_string"]
    vmpp = m["vmpp_v"] * plant["modules_per_string"]
    imp, isc = m["impp_a"], m["isc_a"]
    n = math.log(1.0 - imp / isc) / math.log(vmpp / voc)
    if v_terminal <= 0:
        return isc
    if v_terminal >= voc:
        return 0.0
    return isc * (1.0 - (v_terminal / voc) ** n)


def illustrative_parallel_current(loop_r, fault_v, f: dict):
    """Solve PV I(Vfault + I*R) by bisection; fixed Vfault, not arc physics."""
    if loop_r < 0 or fault_v < 0:
        raise ValueError("nonnegative only")
    isc = f["module"]["isc_a"]
    low, high = 0.0, isc
    for _ in range(100):
        i = (low + high) / 2
        available = pv_current_for_terminal_voltage(fault_v + i * loop_r, f)
        if i > available:
            high = i
        else:
            low = i
    return (low + high) / 2


def c2_illustration(location, action, f=None, fault_v=RATED_ARC_V, horizon_s=5.0):
    """Idealised fixed-voltage fault energy conditional on assumed source IV.

    I_f = sum of available PV currents. W_fault = V_fault * I_f.
    No SPICE, plasma extinction, source capacitance, PV dynamic or true fault
    waveforms; the 5s integral assumes stationary sources and V_fault.
    """
    f = fixture() if f is None else f
    topology = parallel_fault_paths(location, action, f)
    currents = {}
    for src, path in topology["pv_sources"].items():
        currents[src] = (illustrative_parallel_current(path["loop_resistance_ohm_20c"], fault_v, f)
                         if path["sustained_path"] else 0.0)
    i_total = sum(currents.values())
    return {**topology, "fixed_fault_v_assumed": fault_v,
            "source_currents_a": {s: round(i, 5) for s, i in currents.items()},
            "source_feed_current_a": round(i_total, 5),
            "source_feed_power_w_at_fixed_fault_v": round(i_total * fault_v, 4),
            "source_feed_energy_j_if_constant_for_horizon": round(i_total * fault_v * horizon_s, 4),
            "horizon_s": horizon_s,
            "energy_exclusions": ["inverter capacitor", "line capacitance",
                                  "arc plasma", "switch transition", "thermal", "control delay"],
            "evidence_grade": "illustrative_quasistatic_numerical_only"}


def c1_loop_illustration(action, f=None):
    """Presence of series return path for the M15 outside-bypass C1loop.

    A 30-module string is a source requiring a closed inverter load loop.
    These are simplified cut-set propositions, NOT C1 arc-viability tests.
    Does not represent anti-parallel bypass branch for C1in.
    """
    f = fixture() if f is None else f
    loop_open = action in ("P1", "P2", "P2b", "P3")
    return {"fault": "C1loop", "action": action,
            "S20_series_source_load_loop_continuous": not loop_open,
            "S19_paired_source_feed_possible_if_other_path": "UNASSESSED",
            "clamp_capacitance_and_residual_energy": "UNASSESSED",
            "C1in_bypass_loop": "UNASSESSED_ALTERNATE_PATH",
            "evidence_grade": "algebraic_conditional_cutset_only"}


def c3_hot_connector(f=None, contact_r=0.2, current_a=None, ambient_c=35.0):
    """One-node initial thermal screen, constant current/thermal coefficients.
    Assumptions not calibrated; high temperatures invalidate fixed material R,
    heat transfer and connector survival; does not imply a safe setpoint.
    """
    f = fixture() if f is None else f
    x = f["priority_cases"]["C3"]["thermal"]
    current = f["module"]["impp_a"] if current_a is None else current_a
    cth = x["connector_thermal_mass_j_per_k"]["value"]
    h = x["connector_to_ambient_w_per_k"]["value"]
    watts = current**2 * contact_r
    return {"fault": "C3", "contact_r_ohm": contact_r,
            "current_a_assumed": current,
            "local_contact_heating_w_initial": round(watts, 4),
            "delta_v_across_contact_v": round(current * contact_r, 4),
            "illustrative_linear_T_steady_c": round(ambient_c + watts / h, 2),
            "thermal_time_constant_s": round(cth / h, 3),
            "material_survival": "UNKNOWN",
            "arc_noise": "NOT_REQUIRED_FOR_THIS_FAULT",
            "detection": "NOT_MODELLED",
            "evidence_grade": "algebraic_lumped_thermal_only"}


def report():
    f = fixture()
    sample = {}
    for location in ("C2-far", "C2-near"):
        sample[location] = {a: c2_illustration(location, a, f) for a in ("P0", "P2", "P2b", "P3")}
    return {
        "status": "B1_CONDITIONAL_TOPOLOGY_AND_QUASISTATIC_ONLY_NOT_PROTECTION_VALIDATION",
        "fixture_id": f["fixture_id"],
        "topology": "S20 936m two-wire pair; S19 separate 600m pair; common MPPT node",
        "what_is_not_inferred": ["arc extinction", "semiconductor ratings", "certification",
                                  "residual conductor voltage", "failure probabilities"],
        "cases": sample, "series_C1loop": {a: c1_loop_illustration(a, f) for a in ("P0", "P1", "P2", "P2b", "P3")},
        "hot_contact_C3": [c3_hot_connector(f, r) for r in (0.05, .2, 1.0)],
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True))
