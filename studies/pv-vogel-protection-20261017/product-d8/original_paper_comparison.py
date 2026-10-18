#!/usr/bin/env python3
"""D8 comparative STATIC screening against original June 2025 Ventus disclosure.

Original public disclosure: Ventusltd/pv-arc-protection-circuit
  Open-Hardware-Disclosure.md v1.3.2.1, commit
  a9649d2c7d8733ecf5803b94c384206d101460df, CERN-OHL-S-2.0.
A1: original *proposed* series switches + passive substring bypass.
A2: NEW hypothetical actively commanded whole-module 5 milliohm shunt.
Not electrically equivalent, not OEM-validated, NOT DC ARC EXTINCTION.
Public V11 provisional 660Wp fixture only. NO private inverter or IEC data.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

MODULES=30
VOC=45.75
VMPP=38.13
IMPP=17.31
ISC=18.4
ORIGINAL_SENSE_OHM=.1
ORIGINAL_TWO_MOSFETS_OHM=.054
ACTUAL_NAMED_FET_RATING_V=650   # Infineon original IMZA65R027M1H
ACTIVE_MODULE_SHUNT_OHM=.005     # hypothesis; not an identified product
CU_PER_CONDUCTOR_OHM_PER_M=.00308 # assumed 6mm2 copper at 20C
LENGTHS=(16,50,100,200,300)
STUDY_TARGET_W=3.3              # voluntary 0.5%*660W, NOT normative
STUDY_ID="v11.d8.original-paper-active-whole-module-bypass.static.v1"

def pv_module_iv(i, shape=1.0):
    """Uncalibrated three-point Voc/Mpp/Isc interpolant, forward-current ONLY."""
    if not 0<=i<=ISC or shape<=0:raise ValueError("PV surrogate outside characterised domain")
    if i<=IMPP:
        return VOC-(VOC-VMPP)*i/IMPP
    return VMPP*((ISC-i)/(ISC-IMPP))**shape

def paper_loss(i):
    """Conditional: original sensing shunt and both series FETs carry same i."""
    return {"current_a":i,"shunt_w":i*i*ORIGINAL_SENSE_OHM,
       "fet_pair_w":i*i*ORIGINAL_TWO_MOSFETS_OHM,
       "total_per_module_w":i*i*(ORIGINAL_SENSE_OHM+ORIGINAL_TWO_MOSFETS_OHM)}

def whole_string_bypass_ocv(bypassed_modules=MODULES):
    """No inverter and no parallel peer: residual module current through shunts."""
    if not 0<=bypassed_modules<=MODULES:raise ValueError("modules outside string")
    return ((MODULES-bypassed_modules)*VOC+
             bypassed_modules*ISC*ACTIVE_MODULE_SHUNT_OHM)

def peer_backfeed(length_m,shape=1.0,r_on=ACTIVE_MODULE_SHUNT_OHM):
    """Two strings on ONE MPPT, no inverter load/capacitor.
    First string generates at current i. Second string is ALL bypassed
    and receives reversed i. Paired equal-length two-core copper routes.
    The current through EACH bypass shunt is ISC + i, not merely i.
    """
    if length_m<0 or r_on<=0:raise ValueError("invalid physical input")
    r_cable=2*length_m*CU_PER_CONDUCTOR_OHM_PER_M
    def residual(i):
        healthy_v=MODULES*pv_module_iv(i,shape)-i*r_cable
        faulted_v=MODULES*r_on*(ISC+i)+i*r_cable
        return healthy_v-faulted_v
    low,high=0.,ISC
    if residual(low)<=0 or residual(high)>=0:raise AssertionError("model brackets missing")
    for _ in range(100):
        i=.5*(low+high)
        if residual(i)>0:low=i
        else:high=i
    i=.5*(low+high)
    shunt_current=ISC+i
    return {"distance_m_one_way":length_m,"pv_reshape_exponent":shape,
        "one_string_cable_loop_ohm":r_cable,
        "inter_string_backfeed_a":i,
        "each_bypass_path_current_a":shunt_current,
        "each_bypassed_module_heat_w":r_on*shunt_current**2,
        "all_30_bypass_heat_w":MODULES*r_on*shunt_current**2,
        "paired_cables_heat_w":2*i*i*r_cable,
        "mppt_bus_v":MODULES*r_on*shunt_current+i*r_cable,
        "power_residual_w":i*residual(i)}

def capacitor_stored_energy_j(cap_f,volts):
    if cap_f<0 or volts<0:raise ValueError("invalid RLC placeholder")
    return .5*cap_f*volts*volts

def report():
    data={
     "schema":STUDY_ID,
     "source_original":"https://github.com/Ventusltd/pv-arc-protection-circuit/blob/main/Open-Hardware-Disclosure.md",
     "source_original_sha":"a9649d2c7d8733ecf5803b94c384206d101460df",
     "original_vs_revised":{
       "2025":"two original series SiC FETs, passive bypass, analogue detection; opens upon fault/power loss (claim, unqualified)",
       "D8":"hypothetical controlled WHOLE-module shunt on EACH of 30 modules, coordinated, all at once",
       "not_equivalent":"passive substring bypass diode does not force healthy illuminated full-module shunt",
       "fet_original_datasheet":"Infineon IMZA65R027M1H is 650V, 27mohm typical at 25C, not for new design; not 1700V",
       "series_voltage_sharing":"two series FETs do not automatically guarantee 1300V/2kV withstand"
     },
     "source_and_hypothesis_parameters":{
       "n":MODULES,"voc_stc_v":VOC,"vmpp_stc_v":VMPP,"impp_a":IMPP,"isc_a":ISC,
       "r_shunt_orig_ohm":ORIGINAL_SENSE_OHM,
       "r_two_fets_orig_ohm":ORIGINAL_TWO_MOSFETS_OHM,
       "r_active_shunt_assumption_ohm":ACTIVE_MODULE_SHUNT_OHM,
       "copper_6mm2_ohm_per_m_one_conductor_20c":CU_PER_CONDUCTOR_OHM_PER_M,
       "mppt_pairing":"generic two-string same-MPPT pair, not a common 24-string DC bus",
       "pv_curve":"UNCALIBRATED piecewise IV through Voc/Mpp/Isc; no reverse cell breakdown"
     },
     "original_losses_at_impp":paper_loss(IMPP),
     "original_losses_at_20a":paper_loss(20),
     "30_module_healthy_voc_v":MODULES*VOC,
     "30_module_healthy_mpp_v":MODULES*VMPP,
     "all_modules_active_bypass_oc_v_isolated":whole_string_bypass_ocv(),
     "one_of_30_bypasses_fails_open_oc_v_isolated":whole_string_bypass_ocv(MODULES-1),
     "peer_connected_results":[peer_backfeed(l) for l in LENGTHS],
     "iv_uncertainty_results_300m":[peer_backfeed(300,shape=x) for x in (.35,.7,1.,1.5,2.5)],
     "assumed_150uf_bus_energy_j":{
       "at_stc_mpp_v":capacitor_stored_energy_j(150e-6,MODULES*VMPP),
       "at_1500v":capacitor_stored_energy_j(150e-6,1500),
       "CAUTION":"150uF is a hypothetical V11 study fixture, NOT OEM inverter measurement"
     },
     "not_validated":[
       "actual DC series/parallel arc and Joules delivered to electrodes",
       "actual module shunt FET, diode, gate control or SOA",
       "real inverter reverse blocking, MPPT current control or boost input capacitance",
       "actual cable inductance, snubbers, transient overload, hot copper resistance",
       "real 30-module distributed command or loss-of-power safe state",
       "IEC/UL certification, humidity, creepage or insulation"],
     "priority_test":"both strings on ONE MPPT must be controlled or reverse-blocked before commanding only one string low-impedance bypass",
     "copyright_policy":"No proprietary IEC or inverter documents included; original public paper attributed."
    }
    payload=json.dumps(data,sort_keys=True,separators=(',',':'),allow_nan=False)
    data["inputs_results_sha256"]=hashlib.sha256(payload.encode()).hexdigest()
    return data

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--output",required=True)
    args=a.parse_args()
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    r=report()
    path.write_text(json.dumps(r,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"original_loss_w":r["original_losses_at_impp"]["total_per_module_w"],
     "all_bypassed_oc_v":r["all_modules_active_bypass_oc_v_isolated"],
     "failed_one_oc_v":r["one_of_30_bypasses_fails_open_oc_v_isolated"],
     "peer_backfeed_16m_a":r["peer_connected_results"][0]["inter_string_backfeed_a"],
     "peer_backfeed_300m_a":r["peer_connected_results"][-1]["inter_string_backfeed_a"],
     "physical_arc_extinction_proved":False},indent=2))

if __name__=="__main__":
    main()
