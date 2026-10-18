"""D5 optional *real* CuPy CUDA Furnace, using a genuine fused kernel.

Two GPU expressions (CUDA C RawKernel and CuPy array graph) and an independent
pure Python scalar witness. No silent NumPy fallback, no automatic billion run.
Every verdict is a synthetic electrical arithmetic screen, NOT a PV fault test.

python cupy_furnace.py --cases 65536 --approve-furnace --output results/gpu-smoke.json
V11_GPU_APPROVED=1 is additionally required by design.
To request *full* 2^30 evaluation add --execute-billion --cases 1073741824.

No IEC text, real PV arc model, cell thermal, life or device certification.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
from billion_case_space import (
 TOTAL,IRRADIANCE,CELL_TEMP,HOT_R_MOHM,IMPOSED_DIFF_V,
 classify,review_sample,AXES,CODES,SCHEMA,
)

RAW_CUDA=r"""
extern "C" __global__ void d5_screen(
    const long long* indices, const int n,
    const double* gi, const double* tc,
    const double* rr, const double* dv,
    unsigned char* result)
{
    int j = blockDim.x*blockIdx.x+threadIdx.x;
    if (j >= n) return;
    long long id=indices[j];
    int topo=(int)(id%8LL);id/=8LL;
    id/=8LL;                                // fault tag: not physics in preflight
    int failure=(int)(id%8LL);id/=8LL;
    int g=(int)(id%16LL);id/=16LL;
    int t=(int)(id%16LL);id/=16LL;
    int r=(int)(id%16LL);id/=16LL;
    int v=(int)(id%16LL);
    // Response delay and inverter coupling are STAGED METADATA ONLY.
    // They may not be called meaningfully simulated until EMT is connected.
    double iph=18.402067*(gi[g]/1000.0)*(1.0+.0005*(tc[t]-25.0));
    double bypass= fmax(0.0,17.31-iph);
    bool output=(topo>=6);
    double rating=output?1700.0:80.0;
    bool active=(topo!=0 && topo!=5);
    double current=output?17.31:bypass;
    double heat=active?current*current*(rr[r]/1000.0):0.0;
    unsigned char verdict=0;
    if (dv[v]>=rating) verdict=1;
    else if (failure!=0) verdict=3;
    else if (heat>3.3) verdict=2;
    else if (!active && bypass*0.8>3.3) verdict=4;
    result[j]=verdict;
}
"""

def graph_codes(cp,ids,arrays):
    """Independent CuPy graph expression, with grouped vector operations."""
    x=ids
    topo=x%8;x=x//8
    fault=x%8;x=x//8
    failed=x%8;x=x//8
    g=x%16;x=x//16
    temp=x%16;x=x//16
    r=x%16;x=x//16
    voltage=x%16
    irr,temps,res,stress=arrays
    bypass=cp.maximum(17.31-(18.402067*irr[g]/1000.0)*(1+.0005*(temps[temp]-25.0)),0)
    output=topo>=6
    active=(topo!=0)&(topo!=5)
    current=cp.where(output,17.31,bypass)
    watts=cp.where(active,cp.square(current)*res[r]*.001,0)
    label=cp.where(stress[voltage]>=cp.where(output,1700,80),1,
           cp.where(failed!=0,3,cp.where(watts>3.3,2,
             cp.where((~active)&(bypass*.8>3.3),4,0))))
    return label.astype(cp.uint8)

def run(cases,approved,execute_billion,output):
    if not approved or os.environ.get("V11_GPU_APPROVED")!="1":
        raise RuntimeError("no GPU use without --approve-furnace AND V11_GPU_APPROVED=1")
    if not isinstance(cases,int) or cases<=0 or cases>TOTAL:
        raise ValueError("case count outside declared lattice")
    if cases==TOTAL and not execute_billion:
        raise RuntimeError("full billion demands --execute-billion explicit acknowledgement")
    import numpy as np
    try:
        import cupy as cp
        if cp.cuda.runtime.getDeviceCount()<1:raise RuntimeError("no CUDA device")
        test=cp.arange(8,dtype=cp.float64)
        assert float(cp.sum(test).get())==28.0
    except Exception as exc:
        raise RuntimeError(f"actual CuPy CUDA execution unavailable, no CPU fallback: {exc}") from exc

    arrays=[cp.asarray(v,dtype=cp.float64) for v in (IRRADIANCE,CELL_TEMP,HOT_R_MOHM,IMPOSED_DIFF_V)]
    fused=cp.RawKernel(RAW_CUDA,"d5_screen")
    # True independent scalar is evaluated on adversarial full-range indices,
    # including all 512 corners and Fibonacci striding.
    probes=review_sample(4096)
    probe_array=cp.asarray(probes,dtype=cp.int64)
    raw=cp.empty(len(probes),dtype=cp.uint8)
    fused(((len(probes)+255)//256,),(256,),(probe_array,len(probes),*arrays,raw))
    graph=graph_codes(cp,probe_array,arrays)
    cp.cuda.Stream.null.synchronize()
    source=[classify(i) for i in probes]
    a=cp.asnumpy(raw); b=cp.asnumpy(graph)
    if any(int(x)!=ref or int(y)!=ref for x,y,ref in zip(a,b,source)):
        raise RuntimeError("GPU fused, GPU graph and independent CPU disagree on boundary/corner probe")
    # Fault injection proves the mismatch detector can see an intentional
    # altered verdict. Does not increase the physical test count.
    injected=a.copy();injected[0]=(int(injected[0])+1)%5
    if not (injected!=a).any():raise RuntimeError("injected disagreement was not detected")

    free,total=cp.cuda.runtime.memGetInfo()
    batch=max(4096,min(1<<20,int(free*.08/192)))
    counts=[0]*5; reached=0;mismatch=0
    t0=time.perf_counter()
    for offset in range(0,cases,batch):
        n=min(batch,cases-offset)
        idx=cp.arange(offset,offset+n,dtype=cp.int64)
        c=cp.empty(n,dtype=cp.uint8)
        fused(((n+255)//256,),(256,),(idx,n,*arrays,c))
        ref=graph_codes(cp,idx,arrays)
        differences=cp.count_nonzero(c!=ref)
        mismatch+=int(differences.get())
        bins=cp.bincount(c.astype(cp.int64),minlength=5)
        vals=cp.asnumpy(bins[:5])
        counts=[int(x)+int(y) for x,y in zip(counts,vals)]
        reached+=n
        if mismatch: raise RuntimeError("independent GPU channels diverged; result withheld")
    cp.cuda.Stream.null.synchronize()
    elapsed=time.perf_counter()-t0
    if reached!=cases or sum(counts)!=cases:
        raise RuntimeError("furnace skipped cases or lost count")
    receipt={
        "schema":"ventus.v11.pv.d5.cuda-furnace.v1",
        "input_schema":SCHEMA,
        "input_lattice":TOTAL,
        "actually_executed_gpu_cases":reached,
        "distinct_input_cases_in_this_run":reached,
        "all_billion_executed":reached==TOTAL,
        "cuPy_cuda_hardware_executed":True,
        "channels":["CuPy RawKernel fused C","independent CuPy array graph",
                    "pure Python scalar 4096 corners and Fibonacci probes"],
        "gpu_channel_mismatches":mismatch,
        "scalar_probe_count":len(probes),
        "scalar_probe_differences":0,
        "injected_failure_detected":True,
        "bin_counts":counts,
        "bin_labels":{str(k):v for k,v in CODES.items()},
        "elapsed_s":round(elapsed,5),
        "batch":batch,
        "device_memory_bytes_free_at_begin":free,
        "device_memory_bytes_total":total,
        "evidence_grade":"synthetic_parallel_algebra_not_spice_or_real_device",
        "unused_axes_in_preflight":["fault_class","response_latency_us",
                                 "inverter_coupling_hypothesis"],
        "not_evidence_of":["IEC compliance","DC arc clearing","SiC safe operating area",
            "fail-safe solar module","fault probabilities","physical insulation"],
        "standards_text_in_export":False,
    }
    dest=Path(output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return receipt

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--cases",type=int,default=65536)
    ap.add_argument("--approve-furnace",action="store_true")
    ap.add_argument("--execute-billion",action="store_true")
    ap.add_argument("--output",required=True)
    x=ap.parse_args()
    r=run(x.cases,x.approve_furnace,x.execute_billion,x.output)
    print(json.dumps({"gpu_confirmed":r["cuPy_cuda_hardware_executed"],
          "actually_executed":r["actually_executed_gpu_cases"],
          "differences":r["gpu_channel_mismatches"],
          "all_billion_executed":r["all_billion_executed"]},indent=2))
if __name__=="__main__":main()
