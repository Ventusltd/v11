"""Sensitivity campaign for the conditional B2 electrical model.

Not a real arc, not a fault-occurrence model, not a device-response prediction.
Shows sensitivity to ideal-trip latency and UNVERIFIED source capacitances.
Outputs a machine-readable JSON research receipt.
"""
import json
from dataclasses import replace
from pv_rlc_time_domain import Config, run

DELAYS_S = (0.0, .0002, .001, .003, .007)
MPPT_CAP_F = (.00005, .00015, .0005)
PV_CAP_F = (.000002, .000020, .000100)

def timed_cases():
    results = {}
    for loc in ("C2-far","C2-near"):
        base=Config(location=loc,action="P0")
        ref=run(base).outcome
        rows=[]
        for d in DELAYS_S:
            c=run(replace(base,action="P3",trip_at_s=d)).outcome
            rows.append({
                "trip_at_s":d,
                "fault_resistor_energy_j":c["energy_fault_resistor_j"],
                "energy_fraction_of_baseline":round(
                    c["energy_fault_resistor_j"]/ref["energy_fault_resistor_j"],6),
                "energy_conservation_relative":c["energy_residual_relative"],
                "end_capacitor_energy_j":c["energy_cap_end_j"],
            })
        results[loc]={"baseline_energy_j":ref["energy_fault_resistor_j"],
                      "ideal_two_end_switch_timing":rows}
    return results

def capacitance_cases():
    out={}
    # Probe paired, same-location changes: do not pool across cases as statistics.
    for name,field,values,loc in (
        ("input_capacitance","mppt_input_capacitance_f",MPPT_CAP_F,"C2-near"),
        ("PV_terminal_capacitance","pv_output_capacitance_f",PV_CAP_F,"C2-far"),
    ):
        rows=[]
        for val in values:
            kwargs={field:val}
            cfg=Config(location=loc,**kwargs)
            p0=run(replace(cfg,action="P0")).outcome
            p3=run(replace(cfg,action="P3",trip_at_s=.003)).outcome
            rows.append({"capacitance_f_per_fixture_parameter":val,
                         "baseline_fault_energy_j":p0["energy_fault_resistor_j"],
                         "P3_fault_energy_j":p3["energy_fault_resistor_j"],
                         "P3_fraction":round(p3["energy_fault_resistor_j"]/p0["energy_fault_resistor_j"],6),
                         "worst_conservation_relative":max(p0["energy_residual_relative"],p3["energy_residual_relative"])})
        out[name]={"location":loc,"entries":rows}
    return out

def report():
    return {
      "status":"ILLUSTRATIVE_PV_RLC_PARAMETER_SENSITIVITY_NOT_ARC_VALIDATION",
      "evidence":"conditional numerical thought experiment with current-source PV fit and resistive fault",
      "timing_s":list(DELAYS_S),
      "initial_PV_feeder_state":"0 A into fault, source at open-circuit voltage",
      "fault_resistance_ohm":0.8,
      "reference_horizon_s":0.01,
      "model_exclusions":["true series or parallel arc plasma","inverter under load/MPPT dynamics","distribution line reflections","fault sensor latency",
        "real switching/clamp voltage and SOA","reverse current and grounding","OEM-verified field capacitance"],
      "timing":timed_cases(),
      "storage_uncertainty":capacitance_cases()
    }

if __name__=="__main__":
    print(json.dumps(report(),indent=2,sort_keys=True))
