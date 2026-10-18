"""D5: compact original Kuiper projection from reviewed *local* case indices.

One projection contains representative case IDs and their factual toy verdicts.
It is NOT an exhaustive 1.073 billion-point drawing or evidence of arc safety.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from collections import Counter
from billion_case_space import (
    SCHEMA,TOTAL,review_sample,case_evidence,live_kuiper_xy,
    legacy_wafer_xy,decode_offsets,AXES,CODES)

SOURCE_URL="https://github.com/Ventusltd/kuiper-belt/blob/main/learn-the-kuiper/202610042346/kuiper-law.js"
LEGACY_URL="https://github.com/Ventusltd/faraday/blob/main/apparatus/cells.mjs"
CHART_SCHEMA="ventus.v11.pv.d5.kuiper-projection.v1"
ALLOWED_LAWS=("live-kuiper-g32","legacy-golden-angle")

def build_projection(n=4096,law="live-kuiper-g32"):
    if not 512<=n<=50000 or not isinstance(n,int):
        raise ValueError("projection is capped at 50,000 and includes all 512 corners")
    if law not in ALLOWED_LAWS:raise ValueError("unknown coordinate law")
    selected=review_sample(n)
    point=[]
    counts=Counter()
    for idx in selected:
        row=case_evidence(idx)
        # Locally indexed points for teaching/review only, NOT globally allocated
        # permanent Kuiper keys. Never overwrite a key in user's global registry.
        key=idx if law=="live-kuiper-g32" else idx+1
        xy=(live_kuiper_xy(key) if law=="live-kuiper-g32"
            else legacy_wafer_xy(key))
        code=row["screen_code"];counts[code]+=1
        offsets=decode_offsets(idx)
        point.append({
          "local_case_id":row["case_id"],
          "local_index":idx,"local_plot_key":key,
          "x":round(xy[0],8),"y":round(xy[1],8),
          "screen_code":code,
          "arch":AXES[0][1][offsets[0]],
          "fault":AXES[1][1][offsets[1]],
          "failure":AXES[2][1][offsets[2]],
        })
    return {
      "schema":CHART_SCHEMA,"declared_input_space":TOTAL,
      "projected":n,"distinct_projected":len({p["local_index"] for p in point}),
      "source_case_schema":SCHEMA,
      "scope":"ONLY a deterministic projection with ALL 512 corners and Fibonacci-stride samples",
      "identity":"D5 LOCAL ONLY; owner must allocate collision-free permanent Kuiper keys",
      "coordinate_law":law,"source_law_url":SOURCE_URL if law=="live-kuiper-g32" else LEGACY_URL,
      "input_space_not_physically_simulated":True,
      "GPU_execution_claimed":False,
      "original_circuit_netlist_present":False,
      "sampled_verdict_counts":{str(i):counts[i] for i in range(5)},
      "screen_labels":{str(i):x for i,x in CODES.items()},
      "points":point
    }

def generate(out,n=4096,law="live-kuiper-g32"):
    a=build_projection(n,law)
    stable=json.dumps({k:v for k,v in a.items() if k!="sha256"},sort_keys=True,separators=(",",":"))
    a["sha256"]=hashlib.sha256(stable.encode("utf-8")).hexdigest()
    dest=Path(out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(a,separators=(",",":"))+"\n",encoding="utf-8")
    return a

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--n",type=int,default=4096)
    parser.add_argument("--law",choices=ALLOWED_LAWS,default="live-kuiper-g32")
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    result=generate(args.output,args.n,args.law)
    print(f"Projection {result['projected']}/{TOTAL} distinct hypothetical cases; "
          f"law={result['coordinate_law']}; NOT a billion-case GPU execution.")
if __name__=="__main__":main()
