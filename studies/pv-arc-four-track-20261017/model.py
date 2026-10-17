"""Exploratory PV -> grid screening. NOT a validated transient/protection model."""
import argparse, json, math
from pathlib import Path

def analyse(c):
    m, d, e = c["module"], c["switch"], c["network"]
    out = []
    for x in c["cases"]:
        n, s, g = x["strings"], x["modules_per_string"], x["strings_per_mppt"]
        if not(n > 0 and s > 0 and g > 0 and n % g == 0):
            raise ValueError("invalid topology")
        vmp = s * m["vmpp_v"]
        voc = s * m["voc_v"] * m["cold_multiplier"]
        pdc = n * vmp * m["impp_a"]
        pac = min(x["inverter_ac_kw"]*1000, pdc * e["inverter_efficiency"])
        lv = pac / (math.sqrt(3)*e["lv_v_ll"]*e["power_factor"])
        hv = pac*e["transformer_efficiency"] / (math.sqrt(3)*e["hv_v_ll"]*e["power_factor"])
        # Two devices + equal resistors, mismatched leakage as sensitivity, not a guarantee.
        high_v = voc/2 + d["balance_ohm"]*d["leakage_difference_a"]/2
        ripple = [{"L_uH": L*1e6, "unclamped_delta_v": round(
            L*m["impp_a"]/e["opening_s"], 3)} for L in e["loop_L_h"]]
        out.append({
            "case": x["name"],
            "chain": ["module", "series string", "parallel MPPT group", "DC link",
                      "inverter", "690V LV AC", "transformer", "33kV grid"],
            "topology": {"modules": n*s, "strings": n, "mppt_groups": n//g,
                         "strings_per_mppt": g, "switch_count": 2*n*s},
            "steady": {"Vmp_string_v": round(vmp,2), "cold_Voc_string_v": round(voc,2),
                       "array_peak_kw": round(pdc/1000,2), "output_ac_kw": round(pac/1000,2),
                       "LV_line_a": round(lv,2), "HV_line_a": round(hv,2)},
            "fault_envelopes": {
                "same_MPPT_group_other_strings_Isc_a": round((g-1)*m["isc_a"],2),
                "all_strings_ideal_parallel_other_Isc_a": round((n-1)*m["isc_a"],2),
                "assumed_DC_link_energy_j": round(0.5*x["dc_link_C_f"]*voc**2,2),
                "unclamped_L_di_dt": ripple
            },
            "switch_screen": {
                "rated_v_per_part": d["rated_v"],
                "ideal_v_each": round(voc/2,2),
                "mismatch_high_v": round(high_v,2),
                "ideal_rating_pass": voc/2 <= d["rated_v"],
                "mismatch_rating_pass": high_v <= d["rated_v"],
                "one_short_rating_pass": voc <= d["rated_v"],
                "pair_w_at_Impp": round(2*m["impp_a"]**2*d["rds_ohm"],3),
                "shunt_w_at_Impp": round(m["impp_a"]**2*d["shunt_ohm"],3),
                "shunt_rating_pass": m["impp_a"]**2*d["shunt_ohm"] <= d["shunt_rating_w"]
            },
            "not_modelled": ["true I-V/PV cells", "body diode orientation", "arc plasma",
                "mutual L/C cable geometry", "actual inverter control/MPPT or DC-link boundary",
                "dynamic MOSFET voltage share", "transient surge clamps/thermal SOA",
                "grid Thevenin/fault model", "protection coordination"]
        })
    return {"status":"ILLUSTRATIVE_SCREENING_NOT_FULL_SYSTEM_VALIDATION",
            "input_id":c["id"],"cases":out}

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",default=str(Path(__file__).with_name("illustrative-input.json")))
    ap.add_argument("--output")
    a=ap.parse_args()
    res=json.dumps(analyse(json.loads(Path(a.input).read_text())),indent=2)+"\n"
    if a.output: Path(a.output).write_text(res)
    else: print(res,end="")
