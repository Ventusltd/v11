"""A second accounting path for C2 quasi-static source -> wire -> fault energy.

This is an algebraic conservation check, not independent physical evidence:
the fixed fault voltage, synthetic PV IV and steady currents are assumed.
"""
import math
from b1_network import c2_illustration, fixture

def energy_ledger(location, action, f=None, fault_v=30.0, horizon_s=5.0):
    f = fixture() if f is None else f
    if horizon_s < 0 or fault_v < 0:
        raise ValueError("negative parameters")
    result = c2_illustration(location, action, f, fault_v, horizon_s)
    conductor_heat_j, pv_source_j, contributions = 0.0, 0.0, {}
    for name, p in result["pv_sources"].items():
        if not p["sustained_path"]:
            contributions[name] = {"pv_j": 0.0, "wire_j": 0.0, "fault_j": 0.0}
            continue
        i = result["source_currents_a"][name]
        r = p["loop_resistance_ohm_20c"]
        cable_power = i*i*r
        fault_power = i*fault_v
        source_power = i*(fault_v+i*r)
        conductor_heat_j += cable_power*horizon_s
        pv_source_j += source_power*horizon_s
        contributions[name] = {
            "pv_j": round(source_power*horizon_s, 5),
            "wire_j": round(cable_power*horizon_s, 5),
            "fault_j": round(fault_power*horizon_s, 5),
        }
    fault_j = result["source_feed_current_a"]*fault_v*horizon_s
    err = pv_source_j-(fault_j+conductor_heat_j)
    if abs(err) > 1e-6 + pv_source_j*1e-8:
        raise AssertionError("source-energy ledger fails")
    return {
        "fault":location, "action":action, "sources":contributions,
        "pv_source_energy_j":round(pv_source_j, 4),
        "copper_heat_j":round(conductor_heat_j, 4),
        "fault_energy_j":round(fault_j, 4),
        "conservation_residual_j":round(err, 7),
        "not_accounted_for": [
            "input and line capacitors", "semiconductor switching/clamps",
            "thermal transients of conductors", "dynamic irradiance",
            "arc plasma", "inductive energy", "inverter-side boost/bus state"],
        "interpretation":"CONDITIONAL algebraic accounting of two STC PV sources under a fixed V_fault. NOT absolute arc energy."}
