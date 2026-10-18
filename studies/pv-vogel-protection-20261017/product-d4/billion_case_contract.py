#!/usr/bin/env python3
"""One-billion-index module-level PV research LATTICE and source-pinned Kuiper law.

Virtual cases, NOT 1bn SPICE simulations; no CUDA execution in this module.
No IEC content copied. This is a deterministic indexed parameter namespace.
Original live Kuiper source: kuiper-belt/learn-the-kuiper/202610050010/
kuiper-law.js, blob c506a252f27fa8b80e849eb63bbb6699eaf674f0.
"""
from __future__ import annotations
import hashlib
import json
import math
from collections import Counter

SCHEMA="v11.pv.module-protection.billion/1"
VIRTUAL_NAMESPACE="v11.pv.d4-billion/v1"
KUIPER_LAW="kuiper-belt/learn-the-kuiper/202610050010/kuiper-law.js"
KUIPER_BLOB="c506a252f27fa8b80e849eb63bbb6699eaf674f0"
G32=2654435769
TWO32=1<<32

# Readable, immutable v1 mixed-radix order (FASTEST axis first).
# Values are assumption categories, not input to actual ngspice or OEM facts.
AXES=(
 ("architecture",("passive_baseline","active_substring_pair","module_output_pair","hybrid_pair")),
 ("fault_zone",("cell_series","substring_ribbon","bypass_diode","junction_solder",
                 "positive_connector","negative_connector","lead_parallel_short",
                 "string_cable_parallel","quiet_hot_contact","module_to_frame_leakage")),
 ("passive_bypass_state",("healthy","failed_open","failed_short","high_series_r","high_reverse_leak")),
 ("irradiance_profile",("full_1000","middle_10_percent","middle_dark","uniform_100","all_dark")),
 ("cell_temperature_c",(-30,-10,25,65,85)),
 ("externally_forced_current_a",(0.,3.,10.,17.31,25.)),
 ("assumed_hot_pair_r_ohm",(.002,.005,.02,.05)),
 ("assumed_mppt_input_c_f",(0.,.00005,.00015,.0005,.001)),
 ("assumed_trip_latency_s",(.000002,.00002,.0002,.002,.02)),
 ("assumed_bus_state",("isolated","mppt_1143_9_v","collapsed_0_v","backfed_1500_v","reversed_source_1500_v")),
 ("controller_state",("healthy","lost_gate_power","stuck_on","nuisance_command")),
 ("fault_resistance_proxy_ohm",(.05,.075,.1,.15,.2,.3,.5,.8,1.,1.5,2.,3.,5.,8.,12.,20.,30.,50.,80.,120.)),
)
NAMES=tuple(a[0] for a in AXES)
RADICES=tuple(len(a[1]) for a in AXES)
SIZE=math.prod(RADICES)
assert SIZE==1_000_000_000, SIZE
MODEL_STATUS="NOT_A_VALIDATED_ARC_OR_DIELECTRIC_MODEL"
CURRENT_BASELINE_IMPP_A=17.31
ADDED_PATH_LOSS_TARGET_W=3.3
PROVISIONAL_MODULE_VOC_V=45.75
PROVISIONAL_VOC_BETA_FRAC_PER_K=-.0024
# Only two assumed live DC node values. When bus is disconnected/collapsed,
# initial MPPT-side capacitive energy is unknown or not applicable, NOT measured.
BUS_V={"isolated":None,"mppt_1143_9_v":1143.9,
       "collapsed_0_v":0.0,"backfed_1500_v":1500.0,
       "reversed_source_1500_v":1500.0}
IRRADIANCE={
 "full_1000":(1000,1000,1000),
 "middle_10_percent":(1000,100,1000),
 "middle_dark":(1000,0,1000),
 "uniform_100":(100,100,100),
 "all_dark":(0,0,0),
}
CONTACT_ZONES=frozenset(("junction_solder","positive_connector","negative_connector","quiet_hot_contact"))
SHUNT_ARCH=frozenset(("active_substring_pair","hybrid_pair"))
OUTPUT_ARCH=frozenset(("module_output_pair","hybrid_pair"))

def scheme():
    return {"schema":SCHEMA,"namespace":VIRTUAL_NAMESPACE,"size":SIZE,
            "axes":[{"name":n,"values":list(v)} for n,v in AXES],
            "kuiper_math":{"G32":G32,"angle":"2*pi*((key*G32) mod 2^32)/2^32",
                           "radius":"sqrt(key+0.5)", "source_blob":KUIPER_BLOB},
            "evidence_grade":MODEL_STATUS}

def scheme_sha256():
    return hashlib.sha256(json.dumps(scheme(),sort_keys=True,
                  separators=(",",":"),allow_nan=False).encode("utf-8")).hexdigest()

def decode_indices(case_index):
    if not isinstance(case_index,int) or not 0<=case_index<SIZE:
        raise ValueError("case_index outside the immutable billion-case virtual namespace")
    digits=[]
    remaining=case_index
    for radix in RADICES:
        digits.append(remaining%radix)
        remaining//=radix
    if remaining!=0:raise ArithmeticError("mixed-radix overflow")
    return tuple(digits)

def encode_indices(digits):
    if len(digits)!=len(RADICES):raise ValueError("wrong number of axes")
    key=0
    factor=1
    for value,radix in zip(digits,RADICES):
        if not isinstance(value,int) or value<0 or value>=radix:
            raise ValueError("out-of-range axis digit")
        key+=value*factor
        factor*=radix
    return key

def decode_case(key):
    return {name:values[digit] for (name,values),digit
            in zip(AXES,decode_indices(key))}

def virtual_key(key):
    decode_indices(key)
    return f"{VIRTUAL_NAMESPACE}/{key}"

def kuiper_position(key):
    """Exact live JS integer angle law in Python double arithmetic, not shader f32."""
    if not isinstance(key,int) or key<0 or key>2**53-1:
        raise ValueError("Kuiper key must be nonnegative safe JS integer")
    m=((key%TWO32)*G32)&(TWO32-1)
    th=(math.tau*m)/TWO32
    radius=math.sqrt(key+.5)
    return {"key":key,"angle_word_u32":m,"turns":m/TWO32,
            "radius":radius,"x":radius*math.cos(th),"y":radius*math.sin(th)}

def simple_arithmetic_screen(key):
    """A bounded input-relevance/sizing inventory, NOT circuit behaviour.

    Does not use fault-resistance proxies as plasma arcs, claim actual fault
    energy or mark designs safe. 'Not applicable' means physically not tied
    to an active circuit element, not that the fault is impossible.
    """
    x=decode_case(key)
    tags=[]
    arch=x["architecture"]
    i=x["externally_forced_current_a"]
    r=x["assumed_hot_pair_r_ohm"]
    t=x["cell_temperature_c"]
    cap=x["assumed_mppt_input_c_f"]
    bus=BUS_V[x["assumed_bus_state"]]
    subp=IRRADIANCE[x["irradiance_profile"]]
    if x["passive_bypass_state"]!="healthy":tags.append("BYPASS_ELEMENT_UNVERIFIED_FAILURE")
    if x["controller_state"]!="healthy":tags.append("CONTROL_FAULT_NEEDS_FULL_NETLIST")
    if sum(subp)==0 and i>0 and bus is None:
        tags.append("PHYSICALLY_INCONSISTENT_CURRENT_WITHOUT_DECLARED_SOURCE")
    if i>18.4 and bus is None:
        tags.append("EXTERNALLY_FORCED_CURRENT_EXCEEDS_PROVISIONAL_ISC")
    cold_voc=30*PROVISIONAL_MODULE_VOC_V*(1+PROVISIONAL_VOC_BETA_FRAC_PER_K*(t-25))
    if cold_voc>1500:tags.append("ILLUSTRATIVE_COLD_STRING_ABOVE_1500")
    shunt_w=(i*i*r) if arch in SHUNT_ARCH else None
    if shunt_w is not None and shunt_w>ADDED_PATH_LOSS_TARGET_W:
        tags.append("SHUNT_I2R_ABOVE_RESEARCH_BUDGET_WHEN_ON")
    # Capacitive inventory only. Not all energy necessarily reaches this fault.
    cap_stored_j=(.5*cap*bus*bus) if bus is not None else None
    if cap_stored_j is not None and cap_stored_j>100:
        tags.append("HYPOTHETICAL_MPPT_CAP_STORED_ENERGY_GT_100J")
    forced_contact_w=(i*i*x["fault_resistance_proxy_ohm"]) if x["fault_zone"] in CONTACT_ZONES else None
    if forced_contact_w is not None and i*x["fault_resistance_proxy_ohm"]>1500:
        tags.append("FORCED_CONTACT_CURRENT_MAY_VIOLATE_SOURCE_VOLTAGE")
    if x["fault_zone"] not in ("cell_series","substring_ribbon","bypass_diode"):
        tags.append("SUBSTRING_SHUNT_OUTSIDE_FAULT_ZONE_OR_UNKNOWN")
    if arch in OUTPUT_ARCH and x["assumed_bus_state"] in ("backfed_1500_v","reversed_source_1500_v"):
        tags.append("OUTPUT_SWITCH_BIDIRECTIONAL_STRING_CLASS_STRESS")
    tags.append("ARC_PLASMA_AND_REAL_SOURCE_TO_FAULT_UNMODELLED")
    return {
      "case_index":key,"virtual_key":virtual_key(key),
      "provenance":"assumed_v11_d4_lattice_not_OEM_or_IEC",
      "evidence_grade":"PURE_STATIC_ALGEBRA_AND_TOPOLOGY_WARNINGS",
      "scenario":x,
      "source_inventory":{"30_module_voc_linear_assumption_v":round(cold_voc,6),
                          "mppt_assumed_voltage_v":bus},
      "electrical_screen":{
        "shunt_on_resistive_loss_w":None if shunt_w is None else round(shunt_w,9),
        "contact_forced_i2r_w":None if forced_contact_w is None else round(forced_contact_w,6),
        "input_cap_stored_energy_j_not_fault_energy":None if cap_stored_j is None else round(cap_stored_j,6),
      },
      "model_rejection_flags":tags,
      "unproven":["fault-site energy","detect/interrupt arc","real converter source",
                  "hot connector resistance under nonconstant I","FET SOA",
                  "insulation-to-frame","IEC qualification"]}

def coprime_stride():
    s=1_000_003
    while math.gcd(s,SIZE)!=1:s+=2
    return s

def pilot_keys(count=2048):
    if count<1 or count>SIZE:raise ValueError("invalid pilot count")
    # Include exact extreme index witnesses and separately coprime-strided cases.
    seen=set()
    anchors=[0,SIZE-1,1,2,SIZE//2,999_999_999]
    for k in anchors:
        if len(seen)==count:break
        seen.add(k)
    step=coprime_stride()
    j=0
    while len(seen)<count:
        seen.add((j*step)%SIZE)
        j+=1
    return sorted(seen)

def pilot_receipt(count=2048):
    keys=pilot_keys(count)
    flags=Counter()
    sample=[]
    for key in keys:
        r=simple_arithmetic_screen(key)
        flags.update(r["model_rejection_flags"])
        if len(sample)<24:
            sample.append({"case_index":key,"tags":r["model_rejection_flags"],
                           "architecture":r["scenario"]["architecture"],
                           "fault_zone":r["scenario"]["fault_zone"]})
    return {"schema":"v11.pv.d4.billion-pilot/1",
            "lattice_sha256":scheme_sha256(),
            "declared_unique_cases":SIZE,
            "actually_examined_distinct_cases":len(keys),
            "cpu_pilot_only":True,"cuda_cases_executed":0,
            "ngspice_cases_executed_in_this_pilot":0,
            "first_cases":sample,
            "flags_not_failures_or_probabilities":dict(sorted(flags.items())),
            "limit":"Static hand-auditable screens only; no real circuit solver"}
if __name__=="__main__":
    import argparse
    from pathlib import Path
    p=argparse.ArgumentParser()
    p.add_argument("--pilot",type=int,default=2048)
    p.add_argument("--receipt",required=True)
    args=p.parse_args()
    body=pilot_receipt(args.pilot)
    dest=Path(args.receipt); dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(body,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps({"schema_hash":body["lattice_sha256"],"declared":SIZE,
                      "examined":body["actually_examined_distinct_cases"],
                      "CUDA_run":False,"NGSPICE_run":False},indent=2))
