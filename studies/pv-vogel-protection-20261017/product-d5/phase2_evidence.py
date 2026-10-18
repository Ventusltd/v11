"""D5 Phase II: original evidence-aware, deterministic *study triage*.

Reads a compact Kuiper projection; emits bounded Stars-style relationship
evidence and Faraday-style falsifiable experiment proposals.
No physical test, classifier training or claim that plotted proximity implies
electrical causality. New permanent Faraday record numbers NOT allocated.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from collections import Counter,defaultdict
from pathlib import Path
from kuiper_projection import CHART_SCHEMA,build_projection

SCHEMA="ventus.v11.pv.d5.phase2-evidence.v1"
VOCAB=("depends-on","produces","checked-by","fails","concerns",
       "mixed-evidence","proven","run-of","triggers","unstable")
PRIORITY=(1,3,2,4,0) # triage: hypothetical voltage, failure, loss, diode, unflagged
MAX_FAMILIES=20

def analysis(projection,shortlist=48):
    if projection.get("schema")!=CHART_SCHEMA:
        raise ValueError("Not a V11 D5 original Kuiper projection")
    points=projection["points"]
    if len(points)>50000 or len(points)!=projection["distinct_projected"]:
        raise ValueError("projection count mismatch or excessive")
    keys=[p["local_case_id"] for p in points]
    if len(set(keys))!=len(keys):raise ValueError("duplicate case identity")
    if not projection.get("input_space_not_physically_simulated"):
        raise ValueError("refusing unstated physical validation in display artifact")
    if shortlist<1 or shortlist>500:raise ValueError("review list must be bounded")
    groups=defaultdict(list)
    for p in points:
        if not isinstance(p["screen_code"],int) or p["screen_code"] not in PRIORITY:
            raise ValueError("invalid numerical screen")
        groups[p["screen_code"]].append(p)
    # Maximal variety by fault and topology within the labelled sample, NOT
    # automatic determination of the safest architecture.
    selected=[];seen=set()
    for code in PRIORITY:
        rows=groups[code]
        rows=sorted(rows,key=lambda x:(x["fault"],x["arch"],x["local_index"]))
        by=defaultdict(list)
        for p in rows:by[(p["arch"],p["fault"])].append(p)
        while by and len(selected)<shortlist:
            for key in sorted(tuple(by)):
                if len(selected)>=shortlist:break
                candidate=by[key].pop(0)
                if not by[key]:del by[key]
                if candidate["local_case_id"] not in seen:
                    selected.append(candidate);seen.add(candidate["local_case_id"])
        if len(selected)>=shortlist:break
    bycode={str(c):len(groups[c]) for c in PRIORITY}
    nodes=[
        {"id":"study:D5","kind":"study","status":"synthetic_model_only"},
        {"id":"engine:VentusEngine","kind":"source","status":"prior_reference_read_only"},
        {"id":"model:D5static","kind":"model","status":"uncalibrated"},
        {"id":"display:KuiperLive","kind":"projection","status":"local_keys_unreserved"},
    ]
    edges=[["study:D5","engine:VentusEngine","depends-on"],
           ["study:D5","model:D5static","depends-on"],
           ["study:D5","display:KuiperLive","produces"]]
    for p in selected:
        id="case:"+p["local_case_id"]
        nodes.append({"id":id,"kind":"hypothesis_case","status":"NOT_PHYSICALLY_VALIDATED",
                      "screen_code":p["screen_code"],"local_index":p["local_index"]})
        edges.append([id,"model:D5static","checked-by"])
        edges.append([id,"study:D5","run-of"])
        if p["screen_code"] in (1,2,3,4):
            edges.append([id,"study:D5","concerns"])
        # No "proven" edge for uncalibrated algebra or model.
    journal=[
        {"local_proposed_id":"D5-EXP-001","question":"Can independent mixed-radix decoders detect any duplicated index or missed corner?",
         "apparatus":"CPU oracle, explicit 512 corners, Fibonacci coprime samples; real CUDA channel planned",
         "what_was_done":"LOCAL CPU scalar case IDs and projection screened, NOT full 1.073b GPU case run",
         "observation":"All 512 enumerated corners are in the bounded projection; full lattice enumeration not claimed",
         "refuted_if":"any duplicate index, lost corner, disagreement or change of permanent key",
         "result":"PROVISIONAL_SOFTWARE_EVIDENCE"},
        {"local_proposed_id":"D5-EXP-002","question":"Does a single-MOSFET substring shunt conduct undesirably through its body diode when OFF?",
         "apparatus":"V11 D3 generic ngspice model; require actual manufacturer model next",
         "what_was_done":"D3 pre-existing generic SPICE case execution, not recreated by D5",
         "observation":"D3 model screened a loss of healthy substring voltage; real device verification needed",
         "refuted_if":"qualified real device/orientation SPICE and measurements retain substring voltage with same circuit",
         "result":"UNVERIFIED_PHYSICAL_INFERENCE"},
        {"local_proposed_id":"D5-EXP-003","question":"Do analytic loss and hypothetical voltage bins predict vendor-SPICE stresses?",
         "apparatus":"D5 comparison to D3 and future OEM ngspice/CuPy corner traces",
         "what_was_done":"NOT RUN - no real manufacturer SPICE model supplied",
         "observation":"NO OBSERVATION",
         "refuted_if":"source-backed hot Rds, body diode, Vds or thermal behaviour falls outside screen",
         "result":"NOT_RUN"},
        {"local_proposed_id":"D5-EXP-004","question":"Can a local active substring shunt reduce energy into a named DC arc?",
         "apparatus":"Validated PV/diode/body-diode circuit, multiple source path and calibrated arc trace",
         "what_was_done":"NOT RUN - no calibrated fault-site energy circuit",
         "observation":"NO OBSERVATION",
         "refuted_if":"energy at the physically defined fault is unchanged or increased",
         "result":"NOT_RUN"},
    ]
    return {
       "schema":SCHEMA,"evidence_grade":"synthetic_triage_not_circuit_validation",
       "projection_sha256":projection.get("sha256"),
       "n_projected":len(points),"review_count":len(selected),
       "screen_counts_in_projection":bycode,
       "what_the_counts_are_not":["risk probabilities","real circuit fault clearance",
         "measured voltage safety margins","certification"],
       "graph":{"nodes":nodes,"edges":edges,"vocabulary_source":
            "Ventusltd/stars/modular-star/relate.mjs; original subset of typed links",
            "causal_edges_claimed":False},
       "review_cases":[{"case_id":p["local_case_id"],"index":p["local_index"],
                        "screen_code":p["screen_code"],"architecture":p["arch"],
                        "fault":p["fault"],"why":"unverified algebraic counterexample candidate"}
                        for p in selected],
       "faraday_style_proposals":journal,
       "global_faraday_numbers_assigned":False,
       "licensed_IEC_text_in_export":False,
       "next_gate":"manufacturer MOSFET/bypass diode/arc SPICE with source-resolved fault joules",
    }

def run(path,out,shortlist=48):
    p=json.loads(Path(path).read_text(encoding="utf-8"))
    q=analysis(p,shortlist)
    target=Path(out)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(q,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return q

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--projection",required=True)
    ap.add_argument("--output",required=True)
    ap.add_argument("--shortlist",type=int,default=48)
    args=ap.parse_args()
    r=run(args.projection,args.output,args.shortlist)
    print(f"Phase II: {r['review_count']} unverified study candidates linked into evidence graph; NO product safety claim.")
