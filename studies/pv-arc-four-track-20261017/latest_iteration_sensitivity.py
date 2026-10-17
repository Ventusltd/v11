"""Independent sensitivity calculations for the published PV arc circuit, NOT a safety model.

Reproduces a small set of V11 PR #3 provisional reference fixture values with provenance.
No claim that module switches ever see the full string voltage; example voltage exposures
are HYPOTHETICAL branches pending topology and verified device-stress waveforms.
"""
import json
import math
from pathlib import Path

INPUT = Path(__file__).with_name("v11-reference-facts.json")

def calculate(p):
    m, a, w = p["module"], p["plant"], p["what_if"]
    i, total = m["imp_a"], a["strings"]*a["modules_per_string"]
    factor=1+m["temp_coeff_voc_per_c"]*(w["min_cell_temp_c"]-25)
    v_module_cold=m["voc_stc_v"]*factor
    v_string_cold=v_module_cold*a["modules_per_string"]
    def p_fets(r): return i*i*(2*r)
    def p_shunt(r): return i*i*r
    rds_values={"published_typ_25C":w["rds_typ_ohm"],
                "published_typ_175C":w["rds_hot_typ_ohm"],
                "hypothetical_low_rds":w["alternate_rds_ohm"]}
    scenarios={}
    for label,rfet in rds_values.items():
        scenarios[label]={
          "fets_w_per_module":round(p_fets(rfet),4),
          "fets_w_720_modules":round(p_fets(rfet)*total,2),
          "fets_fraction_660wp":round(p_fets(rfet)/m["rated_wp"],5),
        }
    for label,rshunt in (("published_100milliohm",w["shunt_original_ohm"]),
                         ("research_0_5milliohm",w["shunt_research_ohm"])):
        scenarios[label]={
          "shunt_w_per_module":round(p_shunt(rshunt),4),
          "shunt_w_720_modules":round(p_shunt(rshunt)*total,2),
          "sense_mv_at_imp":round(i*rshunt*1000,3)
        }
    capacitor={}
    for c in w["snubber_cap_f"]:
        for v in w["snubber_v_scenarios"]:
            capacitor[f"{c*1e6:g}uF_at_{v}V_joule"]=round(0.5*c*v*v,6)
    raw_at_30k=1/math.sqrt(1+(2*math.pi*30000*1000*100e-9)**2)
    raw_at_100k=1/math.sqrt(1+(2*math.pi*100000*1000*100e-9)**2)
    return {
        "scope":"NUMERICAL_SENSITIVITY_ONLY_NOT_VALIDATED_HARDWARE",
        "derived_from":p["source"],
        "plant":{"module_total":total, "strings":a["strings"],
                 "mppt_groups":a["mppt_groups"],"dc_nameplate_kw":total*m["rated_wp"]/1000,
                 "string_vmp_v":round(m["vmpp_v"]*a["modules_per_string"],2),
                 "string_voc_stc_v":round(m["voc_stc_v"]*a["modules_per_string"],2),
                 "string_voc_cold_v":round(v_string_cold,2),
                 "module_voc_cold_v":round(v_module_cold,4),
                 "impp_a":i,
                 "backfeed_assuming_only_two_strings_parallel_a":m["isc_a"],
                 "all_23_strings_if_cross_connected_a":23*m["isc_a"]
                 },
        "dissipation_scenarios":scenarios,
        "published_fets_and_shunt_loss_kw_at_impp":round(
            total*(p_fets(w["rds_typ_ohm"])+p_shunt(w["shunt_original_ohm"]))/1000,3),
        "published_fets_and_shunt_loss_percent_dc_nameplate":round(
            100*(p_fets(w["rds_typ_ohm"])+p_shunt(w["shunt_original_ohm"]))/m["rated_wp"],3),
        "hypothetical_switch_exposure_screen":{
           "module_local_only_v":round(v_module_cold,3),
           "full_string_only_if_circuit_imposes_it_v":round(v_string_cold,2),
           "IMPORTANT":"switch Vds NOT automatically string Voc; solve actual nodal circuit"
        },
        "RC_1k_100nF":{"lowpass_cutoff_hz":round(1/(2*math.pi*1000*100e-9),1),
                       "amplitude_30kHz":round(raw_at_30k,5),
                       "amplitude_100kHz":round(raw_at_100k,5),
                       "NOTE":"If used directly as low-pass, arc-band signal attenuated"},
        "snubber_energy_j":capacitor,
        "not_modelled":["actual body diode placement","MOSFET SOA and gate circuitry",
          "EMT/transmission lines","arc plasma/ignition probability","PV I-V and partial shade",
          "module frame electrical environment","surge waveforms","PV module thermal fields"]
    }

if __name__ == "__main__":
    print(json.dumps(calculate(json.loads(INPUT.read_text())), indent=2,sort_keys=True))
