#!/usr/bin/env python3
"""D5 deliberately bounded CPU preflight: original second expression for toy algebra.

Neither this nor a future billion-case GPU run solves transient current, PV arcs,
failed components, inverter energy or physical IEC insulation coordination.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
from billion_case_space import (
    TOTAL, AXES, KINDS, CODES, classify, case_at, review_sample, fibonacci_index,
    explicit_corner_ids,
)

SCHEMA="ventus.v11.pv.d5.cpu-preflight.v1"

def independent_check(case):
    """Separate named-value expression rather than reusing classify's offsets."""
    voltage=float(case["imposed_device_diff_v"])
    output_switch=case["architecture"].startswith("module_output")
    if voltage >= (1700.0 if output_switch else 80.0):
        return 1
    if case["component_state"]!="healthy":
        return 3
    temperature=float(case["cell_temp_c"])
    sun=float(case["irradiance_w_m2"])
    available=18.402067*(sun/1000.0)*(1.0+0.0005*(temperature-25.0))
    bypass_current=max(0.0,17.31-available)
    passive=case["architecture"] in ("passive_bypass","sensing_only")
    series_current=17.31 if output_switch else bypass_current
    dissipation=(0.0 if passive else (series_current*series_current)*case["hot_pair_path_r_mohm"]/1000.0)
    if dissipation > 3.3:
        return 2
    if passive and 0.8*bypass_current > 3.3:
        return 4
    return 0

def indices():
    """Adjacent decoder cases, all 512 extremes and diverse Fibonacci traversal."""
    seen=set()
    for i in range(32768):
        seen.add(i)
    seen.update(explicit_corner_ids())
    for j in range(32768):
        seen.add(fibonacci_index(j))
    return sorted(seen)

def audit(out):
    chosen=indices()
    mismatch=[]
    counts=Counter()
    for index in chosen:
        via_named=independent_check(case_at(index))
        via_offsets=classify(index)
        counts[via_named]+=1
        if via_offsets != via_named:
            mismatch.append({"case_id":index,"direct":via_offsets,"independent":via_named})
            if len(mismatch)>20:
                break
    if mismatch:
        raise AssertionError("Independent CPU model disagreement: "+repr(mismatch))
    if len(chosen)<65000 or len(chosen)!=len(set(chosen)):
        raise AssertionError("CPU audit skipped samples or reused IDs")
    # Deliberately inject a wrong verdict into the comparator and prove detection.
    exemplar=chosen[0]
    planted=(independent_check(case_at(exemplar))+1)%5
    injection_caught=planted!=classify(exemplar)
    if not injection_caught: raise AssertionError("control injection not detected")
    receipt={
        "schema":SCHEMA,
        "status":"ACTUAL_CPU_PRECHECK_ONLY_IF_SCRIPT_EXECUTED",
        "declared_distinct_input_space":TOTAL,
        "distinct_cpu_cases_evaluated":len(chosen),
        "explicit_corners_included":len(explicit_corner_ids()),
        "fibonacci_probe_requested":32768,
        "contiguous_prefix_requested":32768,
        "two_cpu_expressions_agree":True,
        "mismatches":0,
        "planted_mismatch_caught":injection_caught,
        "counts":{str(k):counts[k] for k in CODES},
        "inert_preflight_inputs":["fault_class","response_latency_us","inverter_coupling_hypothesis"],
        "claim_limit":"NOT SPICE, NOT CUDA, NOT DEVICE MODEL, NOT 1B EXECUTED, NOT IEC APPROVAL",
        "source_equations":"assumed substring photocurrent and nominal-voltage/hot-resistance screens only",
        "licensed_IEC_content_present":False,
    }
    digest=hashlib.sha256(json.dumps(receipt,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    receipt["digest_sha256"]=digest
    dest=Path(out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return receipt

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    r=audit(args.out)
    print(json.dumps({"cpu_cases":r["distinct_cpu_cases_evaluated"],
                      "planted_mismatch_detected":r["planted_mismatch_caught"],
                      "bin_counts":r["counts"],"no_cuda_claim":True},indent=2))
if __name__=="__main__":
    main()
