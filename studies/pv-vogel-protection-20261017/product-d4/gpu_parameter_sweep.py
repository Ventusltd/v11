#!/usr/bin/env python3
"""V11 D4: deterministic PV-substring parameter screens using existing Ventus Engine.

External runtime dependency (read-only, do NOT vendor here):
Ventusltd/gpu-drivers-for-global-grid/engine/ventus_engine.py
Pinned reference main commit bfdc344289c0f03093e0c65979487e9916ea1ef4.

Mathematical screen only: no ngspice time-domain solving on GPU, no thermal
qualification, no fault detection, arc extinction, IEC standard text, or
semiconductor manufacturer model. R values, duty and voltage bins are hypotheses.
CUDA is opt-in and MUST really execute: --backend gpu refuses absent CuPy/device.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
import pathlib
import sys

SCHEMA="v11.pv.d4.cupy-readiness/1"
GPU_ENGINE_REPO="Ventusltd/gpu-drivers-for-global-grid"
GPU_ENGINE_SHA="bfdc344289c0f03093e0c65979487e9916ea1ef4"
D3_SPICE_RUN="https://github.com/Ventusltd/v11/actions/runs/39133272452"
FURNACE_REFERENCE="https://github.com/Ventusltd/worlds-/blob/main/src/furnace.py"
LOSS_BUDGET_W=3.3  # engineering study target = 0.5% of unverified 660Wp, not IEC limit
AXES={
 "substring_shunt_current_a":(0.0,1.0,10.0,15.46965,17.31,20.0,25.0),
 "pair_r_hot_ohm":(.002,.005,.01,.02,.05),
 "active_duty":(0.0,.1,.5,1.0),
 "hypothetical_local_v_stress":(0.0,12.8,15.25,20.0,45.0,80.0,1500.0),
 "hypothetical_device_v_rating":(30.0,40.0,60.0,80.0,1200.0,1700.0),
 "assumed_bypass_diode_vf_v":(.4,.6,.8),
}
NAMES=tuple(AXES)
RADICES=tuple(len(AXES[name]) for name in NAMES)
SIZE=math.prod(RADICES)
LABELS={
 "0":"hypothesis: voltage below nominal rating, loss within target, and modelled shunt loss lower",
 "1":"modelled shunt electrical loss above user target",
 "2":"hypothetical local voltage at/over nominal device rating; NO transient margin",
 "3":"no modelled dissipative benefit over passive diode (includes 0-duty state)",
}
EXPECTED_D3_W=1.196517
D3_SHUNT_A=15.46965
D3_HYPOTHESIS_R=.005

def engine_import():
    base=os.environ.get("V11_GPU_ENGINE_DIR")
    if not base:
        raise RuntimeError("SET V11_GPU_ENGINE_DIR to READ-ONLY pinned gpu-drivers-for-global-grid/engine checkout")
    f=pathlib.Path(base).resolve()/"ventus_engine.py"
    if not f.is_file():
        raise RuntimeError("REQUIRED existing ventus_engine.py absent; refusing to invent replacement")
    if str(f.parent) not in sys.path:
        sys.path.insert(0,str(f.parent))
    from ventus_engine import Engine, Space, EngineError
    return Engine,Space,EngineError

def decode_scalar(index):
    if not 0<=index<SIZE: raise ValueError("case index outside grid")
    offsets=[]
    for radix in RADICES:
        index,rem=divmod(index,radix)
        offsets.append(rem)
    return tuple(AXES[name][value] for name,value in zip(NAMES,offsets))

def independent_scalar(index):
    """Scalar reviewer: explicit case decoding and factored power algebra."""
    current, r_hot, duty, v_stress, rating, vf=decode_scalar(index)
    if v_stress>=rating: return 2
    shunt_loss=math.pow(current*math.sqrt(r_hot),2)*duty
    if shunt_loss>LOSS_BUDGET_W: return 1
    passive_diode=(vf*current)*duty
    return 3 if shunt_loss>=passive_diode else 0

def kernel(xp, axes):
    """Reusable Engine contract: identical xp kernel for NumPy or CuPy.

    Compact 4-bin receipt. The stable case id is the integer mixed-radix index.
    No probability or IEC 'pass' labels can arise from these codes.
    """
    i,r,d,v,rated,vf=(
       xp.asarray(AXES[name],dtype=xp.float64)[axis]
       for name,axis in zip(NAMES,axes)
    )
    p=(i*i)*r*d
    diode_p=(i*vf)*d
    return xp.where(v>=rated,2,
                    xp.where(p>LOSS_BUDGET_W,1,
                             xp.where(p>=diode_p,3,0))).astype(xp.int64)

def closed_forms(np, space, fn):
    """Checks independent fixture arithmetic BEFORE engine's sweep."""
    assert space.size==SIZE==17640
    assert abs(D3_SHUNT_A*D3_SHUNT_A*D3_HYPOTHESIS_R-EXPECTED_D3_W)<.0001
    assert abs(3.3/(17.31*17.31)-.011013359204715321)<1e-14
    # Compare indexed scalar and xp for hand selected stress corners.
    idxs=[0,1,SIZE//3,SIZE//2,SIZE-1]
    a=np.array(idxs,dtype=np.int64)
    results=fn(np,space.decode(np,a))
    for j,idx in enumerate(idxs):
        assert int(results[j])==independent_scalar(idx),(idx,results[j])
    return True

def independent_counts():
    counts=[0,0,0,0]
    for idx in range(SIZE):
        counts[independent_scalar(idx)]+=1
    if sum(counts)!=SIZE: raise AssertionError("did not enumerate all distinct cases")
    return counts

def _canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False)

def run(backend,receipt_path):
    if backend not in ("cpu","gpu"):
        raise ValueError("Must explicitly request cpu or gpu; never silently auto-promote")
    scalar=independent_counts()
    Engine,Space,_=engine_import()
    eng=Engine(Space(RADICES,NAMES),kernel,bytes_per_case=128,prefer=backend)
    eng.assert_closed_forms(closed_forms)
    checked=eng.verify(n=SIZE,against="cpu")
    if not checked.passed:
        raise RuntimeError("CPU and requested backend DISAGREE on declared case grid")
    result=eng.run(nbins=4)
    if result.totals!=scalar:
        raise RuntimeError(f"Independent scalar oracle mismatch {scalar} != {result.totals}")
    # Hash assumptions and all verdict counts, but not wall-clock performance.
    evidence={
      "schema":SCHEMA,"evidence_grade":"synthetic_electrical_screen_only",
      "backend_actually_executed":eng.backend.name,
      "source_engine_repo":GPU_ENGINE_REPO,
      "source_engine_commit_pinned":GPU_ENGINE_SHA,
      "source_engine_file":"engine/ventus_engine.py",
      "d3_spice_source":D3_SPICE_RUN,
      "furnace_source":FURNACE_REFERENCE,
      "distinct_cases":SIZE,"repeated_evaluations_not_new_cases":0,
      "cpu_oracle_all_cases":SIZE,
      "backend_parity_cases":checked.n,
      "backend_parity_differences":checked.differ,
      "axes":[{"name":name,"values":list(AXES[name]),
               "provenance":"research assumption, NOT published PV device rating"}
              for name in NAMES],
      "electrical_loss_target_w":{"value":LOSS_BUDGET_W,
                "provenance":"provisional user research target 0.5 percent of 660W"},
      "verdict_counts":result.totals,
      "bin_definitions":LABELS,
      "licenses_respected":"No IEC standard text, table, image or licensed input",
      "not_proven":["real device SOA","reverse-bias cell thermal","MOSFET failure",
                    "actual substring voltage topology","Cgd switching transients",
                    "PV arc extinction","insulation coordination",
                    "30-year reliability","device cost","statistical efficacy"],
    }
    ehash=hashlib.sha256(_canonical(evidence).encode("utf-8")).hexdigest()
    evidence["input_and_verdict_digest_sha256"]=ehash
    evidence["measurement_not_in_digest"]={
       "elapsed_s":round(result.seconds,7),
       "sample_comparison_s":round(checked.seconds,7),
       "note":"No GPU rate, device-watts, or speed-up claimed from this small space",
    }
    path=pathlib.Path(receipt_path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return evidence

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--backend",choices=("cpu","gpu"),required=True)
    ap.add_argument("--receipt",required=True)
    args=ap.parse_args()
    a=run(args.backend,args.receipt)
    print(json.dumps({
        "backend":a["backend_actually_executed"],"distinct_cases":a["distinct_cases"],
        "zero_mismatches":a["backend_parity_differences"]==0,
        "totals":a["verdict_counts"],
        "receipt_digest":a["input_and_verdict_digest_sha256"],
        "NOT_PRODUCT_VALIDATION":True,
    },indent=2))
if __name__=="__main__":
    main()
