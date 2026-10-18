#!/usr/bin/env python3
"""V11 D6 deterministic bounded learning loop: Iterations -> Kuiper log ->
evidence-aware algorithms -> new distinct iterations -> repeat.

This is a *research controller* using the D5 synthetic algebraic case space,
NOT 1 billion solved DC circuits. It imports the existing D5 source, never
duplicates the global Kuiper key registry, and can optionally link real D6
ngspice resistor/forced-current evidence. CPU is default and independently
checked. CuPy GPU is explicit opt-in on the OWNER'S separate CUDA machine.
No licensed IEC standard text is included or loaded.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys

D5=Path(__file__).resolve().parents[1]/"product-d5"
sys.path.insert(0,str(D5))
from billion_case_space import (TOTAL,AXES,RADICES,IRRADIANCE,CELL_TEMP,
    KINDS,FAILURES,CODES,explicit_corner_ids,fibonacci_index,
    decode_offsets,encode_offsets,case_at,classify,case_tag,live_kuiper_xy)

VERSION="ventus.v11.pv.d6.adaptive-kuiper-loop.v1"
PREV_GENESIS="0"*64
FAULT_HOT=6
PRIORITIES={1:0,3:1,2:2,4:3,0:4}
INERT_AXES=("fault_class","response_latency_us","inverter_coupling_hypothesis")

def canonical(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False)

def digest(x):
    return hashlib.sha256(canonical(x).encode("utf8")).hexdigest()

def independent_code(index):
    """Named-field arithmetic, independently expressed from D5 offset classifier."""
    c=case_at(index)
    module_switch=c["architecture"].startswith("module_output")
    rating=1700.0 if module_switch else 80.0
    if c["imposed_device_diff_v"]>=rating:return 1
    if c["component_state"]!="healthy":return 3
    irradiance=c["irradiance_w_m2"]
    temperature=c["cell_temp_c"]
    ipv=18.402067*irradiance/1000*(1+.0005*(temperature-25))
    bypass=max(0.,17.31-ipv)
    current=17.31 if module_switch else bypass
    active=c["architecture"] not in ("passive_bypass","sensing_only")
    watts=(current**2)*(c["hot_pair_path_r_mohm"]/1000) if active else 0
    if watts>3.3:return 2
    if not active and bypass*.8>3.3:return 4
    return 0

def evaluate_ids(ids,backend,approve_gpu=False):
    if backend=="cpu":
        results=[classify(i) for i in ids]
    elif backend=="gpu":
        if not approve_gpu or os.environ.get("V11_GPU_APPROVED")!="1":
            raise RuntimeError("real GPU use requires --approve-gpu and V11_GPU_APPROVED=1")
        try:
            import cupy as cp
            from cupy_furnace import RAW_CUDA,graph_codes
            if cp.cuda.runtime.getDeviceCount()<1:
                raise RuntimeError("no actual CUDA device")
            a=cp.arange(8,dtype=cp.float64)
            if int(cp.sum(a).get())!=28:raise RuntimeError("CUDA smoke kernel failed")
            ar=[cp.asarray(values,dtype=cp.float64) for name,values in AXES
                if name in ("irradiance_w_m2","cell_temp_c",
                            "hot_pair_path_r_mohm","imposed_device_diff_v")]
            g=cp.asarray(ids,dtype=cp.int64)
            k=cp.RawKernel(RAW_CUDA,"d5_screen")
            target=cp.empty(len(ids),dtype=cp.uint8)
            k(((len(ids)+255)//256,),(256,),(g,len(ids),*ar,target))
            independent_gpu=graph_codes(cp,g,ar)
            cp.cuda.Stream.null.synchronize()
            u=cp.asnumpy(target).tolist()
            v=cp.asnumpy(independent_gpu).tolist()
            if u!=v:raise AssertionError("fused CUDA and independent CuPy graph disagree")
            results=[int(x) for x in u]
        except Exception as exc:
            raise RuntimeError(f"GPU not executed: {exc}") from exc
    else:
        raise ValueError("backend must be cpu or gpu")
    for idx,code in zip(ids,results):
        if independent_code(idx)!=code:
            raise AssertionError(f"synthetic model expressions disagree at {idx}")
    return results

def physical_receipt(file):
    if file is None:
        return {"status":"MISSING_REAL_SPICE_INPUT",
                "fault_zones_validated":False,"no_external_isolation_evidence":False}
    data=json.loads(Path(file).read_text(encoding="utf8"))
    if (data.get("status")!="NGSPICE_GENERIC_OHMIC_FAULT_ZONE_SCREEN_NOT_ARC_TEST"
        or data.get("cases_executed")!=12 or len(data.get("paired_findings",[]))!=6):
        raise ValueError("unexpected D6 ngspice input; refuse to promote")
    outside=[p for p in data["paired_findings"] if p["fault_zone"]=="outside_module"]
    if len(outside)!=2 or not all(p["external_connector_not_isolated"] for p in outside):
        raise AssertionError("external fault must remain outside active substring cut-set")
    for row in outside:
        e1=row["energy_external_on_j"];e0=row["energy_external_off_j"]
        expected=17.31**2*.2*(200-60)*1e-6
        if abs(e1-expected)>expected*.01 or abs(e0-expected)>expected*.01:
            raise AssertionError("D6 external I squared R expected heat mismatch")
        if abs(e1-e0)>expected*.001:
            raise AssertionError("false module bypass isolation claim in D6 evidence")
    return {"status":"REAL_NGSPICE_OHMIC_FIXED_CURRENT_NOT_ARC",
            "cases_executed":12,"external_fault_energy_j_per_case":outside[0]["energy_external_on_j"],
            "no_external_isolation_evidence":True,
            "source_sha256":hashlib.sha256(Path(file).read_bytes()).hexdigest(),
            "source_ref":"V11 D6 ngspice results / 12 actual model circuits",
            "conditions":"forced 17.31 A; 0.2-ohm external connector; NOT arc; not an inverter",
            "fault_zones_validated":False}

def anchors():
    """Source-connected, high-priority local hypotheses, not lab results."""
    chosen=list(explicit_corner_ids())  # 512 compulsory adversarial corners
    # Explicitly target the actual D6 external hot connector fault label,
    # despite D5 fault label being an INERT axis at first approximation.
    for topo in (0,3,4,6,7):
      for fail in (0,1,3,4):
       for irr in (0,4,13,15):
        offsets=[topo,FAULT_HOT,fail,irr,7,6,10,5,0]
        chosen.append(encode_offsets(offsets))
    return list(dict.fromkeys(chosen))

def variants(index,code):
    """Phase II one-factor counterexample searches around screened boundaries."""
    offsets=list(decode_offsets(index))
    targeted={1:(6,5),3:(2,0),2:(5,3),4:(3,0),0:(1,8)}
    axis,target=targeted[code]
    tests=[]
    for next_k in (target, max(0,offsets[axis]-1),min(RADICES[axis]-1,offsets[axis]+1)):
        o=offsets.copy()
        o[axis]=min(RADICES[axis]-1,next_k)
        if tuple(o)!=tuple(offsets):
            tests.append((encode_offsets(o),"phase2_counterexample_axis_"+AXES[axis][0]))
    return tests

def select_next(iteration,budget,seen,previous,step):
    if not isinstance(budget,int) or not 512<=budget<=16384:raise ValueError("budget outside bounded CPU/GPU iteration interval")
    if not isinstance(iteration,int) or not 0<=iteration<=32:raise ValueError("iteration outside bounded range")
    proposed=[]
    if iteration==0:
        proposed.extend((x,"explicit_corner_or_physical_D6_anchor") for x in anchors())
    else:
        # At most half budget is chosen by high-priority counterexamples; the
        # remainder is new coprime Fibonacci exploration across the full grid.
        candidates=sorted(previous,key=lambda p:(PRIORITIES[p["code"]],p["index"]))
        for prior in candidates:
            for index,why in variants(prior["index"],prior["code"]):
                proposed.append((index,why))
                if len(proposed)>budget*2:break
            if len(proposed)>budget*2:break
    result=[]
    local=set()
    adaptive_limit=budget if iteration==0 else budget//2
    for idx,why in proposed:
        if idx not in seen and idx not in local and len(result)<adaptive_limit:
            result.append((idx,why));local.add(idx)
    guard=0
    while len(result)<budget:
        idx=fibonacci_index(step)
        step+=1;guard+=1
        if idx not in seen and idx not in local:
            result.append((idx,"coprime_fibonacci_exploration"));local.add(idx)
        if guard>budget*100+10000:
            raise AssertionError("selection stalled before unique quota completed")
    return result,step

def append_log(path,rows,previous_hash):
    with Path(path).open("a",encoding="utf8") as fp:
        for item in rows:
            body={"schema":VERSION,"sequence":item["sequence"],
                  "iteration":item["iteration"],
                  "case_index":item["index"],"case_id":case_tag(item["index"]),
                  "code":item["code"],"selection_reason":item["reason"],
                  "kuiper_namespace":"D6_LOCAL_CASE_ONLY_NO_GLOBAL_KEYS",
                  "xy_live":tuple(round(x,7) for x in live_kuiper_xy(item["index"])),
                  "prev_sha256":previous_hash}
            sha=digest(body)
            body["entry_sha256"]=sha
            fp.write(canonical(body)+"\n")
            previous_hash=sha
    return previous_hash

def verify_log(path):
    previous=PREV_GENESIS
    seen=set();cycles=[];count=0
    with Path(path).open("r",encoding="utf8") as fp:
        for line in fp:
            item=json.loads(line)
            sha=item.pop("entry_sha256")
            if sha!=digest(item) or item["prev_sha256"]!=previous:
                raise ValueError("Kuiper evidence log chain corrupted")
            if item["sequence"]!=count:
                raise ValueError("sequence not append-only")
            case=item["case_index"]
            if case in seen or item["case_id"]!=case_tag(case):
                raise ValueError("duplicate case or incorrect identity")
            if item["kuiper_namespace"]!="D6_LOCAL_CASE_ONLY_NO_GLOBAL_KEYS":
                raise ValueError("unexpected global key allocation")
            previous=sha;seen.add(case);count+=1;cycles.append(item["iteration"])
    if not cycles or any(b<a or b-a>1 for a,b in zip(cycles,cycles[1:])):
        raise ValueError("bad iteration ordering")
    return {"hash":previous,"unique_cases":len(seen),
            "iterations":max(cycles)+1,"duplicates":0}

def loop(output,iterations=3,batch=768,backend="cpu",approve_gpu=False,spice_file=None):
    if not isinstance(iterations,int) or not 1<=iterations<=8:
        raise ValueError("bounded 1..8 iterations only")
    target=Path(output)
    if target.exists() and any(target.iterdir()):
        raise FileExistsError("refusing to overwrite append-only Kuiper evidence; use a new run path")
    target.mkdir(parents=True,exist_ok=True)
    evidence=physical_receipt(spice_file)
    seen=set();previous=[];step=0;hash_head=PREV_GENESIS;cycles=[]
    ledger=target/"kuiper-evidence.jsonl"
    for iteration in range(iterations):
        planned,step=select_next(iteration,batch,seen,previous,step)
        ids=[idx for idx,why in planned]
        if len(ids)!=len(set(ids)) or seen.intersection(ids):
            raise AssertionError("iteration repeated any case identifier")
        labels=evaluate_ids(ids,backend,approve_gpu)
        rows=[]
        counts={str(i):0 for i in range(5)}
        for idx,code in zip(ids,labels):
            counts[str(code)]+=1
            rows.append({"index":idx,"code":code,"reason":dict(planned)[idx],
                        "sequence":len(seen)+len(rows),"iteration":iteration})
        hash_head=append_log(ledger,rows,hash_head)
        cycle={
           "iteration":iteration+1,"evaluated_distinct_cases":len(ids),
           "observed_counts":counts,"selection_evidence":"previous_iteration_priority_and_fibonacci",
           "kuiper_log_tip_sha256":hash_head,
           "priority_examples":[case_tag(p["index"]) for p in
              sorted(rows,key=lambda r:(PRIORITIES[r["code"]],r["index"]))[:12]],
           "independent_cpu_per_case_checks":len(ids),
           "GPU_executed":backend=="gpu",
           "real_SPICE_performed_this_iteration":0,
           "not_proven":"DC arc clearing, physical risk reduction, dielectric compliance"}
        cycles.append(cycle)
        previous=rows;seen.update(ids)
        # Phase II algorithms adapt NEXT iteration while preserving all history.
        (target/f"iteration-{iteration+1:02d}.json").write_text(
            json.dumps(cycle,indent=2)+"\n",encoding="utf8")
    verification=verify_log(ledger)
    if verification["unique_cases"]!=batch*iterations or verification["hash"]!=hash_head:
        raise AssertionError("append-only ledger verification failed")
    record={
      "schema":VERSION,"status":"COMPLETED_BOUNDED_RESEARCH_LOOP",
      "backend_actually_executed":backend,
      "CuPy_GPU_executed":backend=="gpu",
      "physical_D6_spice":evidence,
      "iterations":iterations,"cases_per_iteration":batch,
      "actually_evaluated_distinct_synthetic_cases":len(seen),
      "original_D5_possible_input_tuples":TOTAL,
      "repeated_cases":0,"hashed_kuiper_ledger":verification,
      "cycles":cycles,"inert_axes_in_screen":list(INERT_AXES),
      "physical_netlists_run_by_this_loop":0,
      "algorithm":"severity-ranked one-axis counterexamples + Fibonacci exploration",
      "global_Kuiper_keys_allocated":0,
      "no_IEC_licensed_content":True,
      "next_physical_tests":[
        {"hypothesis":"Active substring bypass isolates heat at external connector",
         "finding":"REFUTED by D6 fixed-current resistor ngspice" if evidence["no_external_isolation_evidence"] else "NOT EVALUATED",
         "action":"test actual external arc source paths with calibrated PV/MPPT and diode"},
        {"hypothesis":"Improved bypass prevents internal fault energy",
         "finding":"UNPROVEN; I2R model may move current rather than extinguish arc",
         "action":"compute named arc electrode current and source joules with verified MOSFET and arc models"}]}
    (target/"loop-receipt.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf8")
    return record

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True)
    ap.add_argument("--iterations",type=int,default=3)
    ap.add_argument("--cases-per-iteration",type=int,default=768)
    ap.add_argument("--backend",choices=["cpu","gpu"],default="cpu")
    ap.add_argument("--approve-gpu",action="store_true")
    ap.add_argument("--spice-results",default=None)
    a=ap.parse_args()
    r=loop(a.out,a.iterations,a.cases_per_iteration,a.backend,a.approve_gpu,a.spice_results)
    print(json.dumps({"backend":r["backend_actually_executed"],
       "completed_iterations":r["iterations"],
       "unique_screened_cases":r["actually_evaluated_distinct_synthetic_cases"],
       "ledger_tip":r["hashed_kuiper_ledger"]["hash"],
       "SPICE_cases_reused":r["physical_D6_spice"].get("cases_executed",0),
       "NEW_GPU_RUN":r["CuPy_GPU_executed"],
       "not_arc_validation":True},indent=2))
if __name__=="__main__":main()
