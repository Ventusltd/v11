#!/usr/bin/env python3
"""V11 D4 Phase-II proof-of-contract: Stars/Faraday-shaped replay candidates.

NOT deployed into historical Stars or Faraday repos. Data built ONLY from
bounded independent CPU static-case pilot, never mislabelled SPICE or lab tests.
No machine learning, no live event replay, no claims about real-world risks.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from billion_case_contract import (
    MODEL_STATUS,SCHEMA,SIZE,scheme_sha256,pilot_keys,simple_arithmetic_screen,
)

STAR_SCHEMA="v11.pv.phase2.case-star/1"
GRAPH_SCHEMA="v11.pv.phase2.review-graph/1"
FARADAY_SCHEMA="v11.pv.phase2.faraday-proposal/1"

# Priority is a RESEARCH FOLLOW-UP ORDER, not severity or risk probability.
PRIORITY={
 "PHYSICALLY_INCONSISTENT_CURRENT_WITHOUT_DECLARED_SOURCE":100,
 "FORCED_CONTACT_CURRENT_MAY_VIOLATE_SOURCE_VOLTAGE":95,
 "OUTPUT_SWITCH_BIDIRECTIONAL_STRING_CLASS_STRESS":90,
 "CONTROL_FAULT_NEEDS_FULL_NETLIST":85,
 "BYPASS_ELEMENT_UNVERIFIED_FAILURE":80,
 "ILLUSTRATIVE_COLD_STRING_ABOVE_1500":75,
 "SHUNT_I2R_ABOVE_RESEARCH_BUDGET_WHEN_ON":70,
 "HYPOTHETICAL_MPPT_CAP_STORED_ENERGY_GT_100J":65,
 "EXTERNALLY_FORCED_CURRENT_EXCEEDS_PROVISIONAL_ISC":60,
 "SUBSTRING_SHUNT_OUTSIDE_FAULT_ZONE_OR_UNKNOWN":45,
 "ARC_PLASMA_AND_REAL_SOURCE_TO_FAULT_UNMODELLED":20,
}
BLOCKING={
 "PHYSICALLY_INCONSISTENT_CURRENT_WITHOUT_DECLARED_SOURCE",
 "FORCED_CONTACT_CURRENT_MAY_VIOLATE_SOURCE_VOLTAGE",
}
def research_priority(case):
    tags=case["model_rejection_flags"]
    return max(PRIORITY[t] for t in tags) if tags else 0

def star_id(key):
    s=scheme_sha256()+":v11-phase2-v1:"+str(key)
    return "pvstar:"+hashlib.sha256(s.encode("utf8")).hexdigest()[:20]

def select_witnesses(pilot_n=2048,limit=48):
    if limit<=0 or pilot_n<limit:raise ValueError("invalid shortlist bound")
    allcases=[simple_arithmetic_screen(k) for k in pilot_keys(pilot_n)]
    allcases.sort(key=lambda c:(-research_priority(c),c["case_index"]))
    # Guarantee architecture/fault-zone diversity where available.
    selected=[];keys=set();per_group=Counter()
    for case in allcases:
        c=case["scenario"];group=(c["architecture"],c["fault_zone"])
        if per_group[group]>=2:continue
        selected.append(case);keys.add(case["case_index"]);per_group[group]+=1
        if len(selected)>=limit:break
    return selected

def _reason(case):
    x=case["scenario"]
    return "Synthetic electrical case: "+x["architecture"]+" / "+x["fault_zone"]+". " +(
      "Input contradicts an explicit source assumption; model must REFUSE." if
      BLOCKING.intersection(case["model_rejection_flags"]) else
      "Requires physically appropriate SPICE/OEM model to evaluate."
    )

def graph_and_experiments(pilot_n=2048,limit=48):
    witnesses=select_witnesses(pilot_n,limit)
    nodes={};edges=[];stars=[];experiments=[]
    def node(id,label,typ,reason):
        if id not in nodes:
            nodes[id]={"id":id,"label":label,"type":typ,
                       "rag":"amber" if typ=="case" else "grey","reason":reason}
    def wire(fr,to,typ):
        if fr not in nodes or to not in nodes:raise AssertionError("dangling graph edge")
        edges.append({"from":fr,"to":to,"type":typ})
    schemehash=scheme_sha256()
    root="source:"+schemehash[:12]
    node(root,"D4 schema verified","assumption","Hashed synthetic v1 case lattice, NOT OEM verified")
    for rank,case in enumerate(witnesses,1):
        key=case["case_index"];c=case["scenario"];sid=star_id(key)
        status="INPUT_CONTRADICTION" if BLOCKING.intersection(case["model_rejection_flags"]) else "NUMERIC_ONLY"
        arch="arch:"+c["architecture"]
        fault="fault:"+c["fault_zone"]
        node(arch,c["architecture"],"architecture","Circuit family; topology still unvalidated")
        node(fault,c["fault_zone"],"fault","Fault site with no calibrated plasma data")
        node(sid,"Case "+str(key),"case",_reason(case))
        wire(sid,arch,"proposes");wire(sid,fault,"locates");wire(sid,root,"assumes")
        stars.append({
            "schema":STAR_SCHEMA,"id":sid,"ordinal_rank_for_followup":rank,
            "case_index":key,"virtual_key":case["virtual_key"],
            "input_schema_sha256":schemehash,
            "status":status,"electrical_evidence":"PURE_STATIC_ALGEBRA_AND_TOPOLOGY_WARNINGS",
            "followup_priority_not_risk_score":research_priority(case),
            "assumptions":c,"reported_numeric_inventory":case["electrical_screen"],
            "flags":case["model_rejection_flags"],
            "source":"billion_case_contract.py",
            "requires":"real module/diode/semiconductor/inverter netlist + qualified lab",
            "not_claimed":["arc quenching","certified insulation","physical probability","real CUDA"]})
        experiments.append({
            "schema":FARADAY_SCHEMA,
            "experiment_id":"V11-PV-D4-FARADAY-PROPOSAL-"+f"{rank:04d}",
            "case_star_id":sid,"case_index":key,
            "question":"Can an independently solved source-to-fault network eliminate these static inconsistencies and produce a valid fault-energy bound?",
            "apparatus":"Original V11 deterministic CPU static lattice, not a high-voltage experiment",
            "action_performed":"Decoded synthetic case and checked source/energy arithmetic",
            "observation":{"flags":case["model_rejection_flags"],
                           "numeric_inventory":case["electrical_screen"]},
            "verdict":"UNRESOLVED__NEEDS_PHYSICAL_SIMULATION",
            "falsification":"Recompute same case with measured OEM PV I-V, bypass diode, FET SOA, source graph and validated ngspice transient; reject if source paths or energy balances disagree.",
            "laboratory_test_performed":False,
            "append_only_namespace":"V11 only; does not alter Ventusltd/faraday historical ledger"})
    return {
      "graph":{"schema":GRAPH_SCHEMA,"status":"PROPOSED_FOLLOWUP_ONLY",
               "pilot_cases_seen":pilot_n,"distinct_stars":len(stars),
               "nodes":list(nodes.values()),"edges":edges},
      "stars":stars,"faraday_proposals":experiments,
      "receipt":{"schema":"v11.pv.phase2.replay-shortlist/1",
                 "lattice_sha256":schemehash,
                 "virtual_lattice_size_not_executed":SIZE,
                 "actually_pilot_screened":pilot_n,
                 "replay_candidates":len(stars),"real_cuda_executed":False,
                 "actual_spice_in_this_workflow":False,
                 "no_risk_probabilities":True,
                 "source_reuse":["Ventusltd/stars/modular-star/decisions.mjs",
                     "Ventusltd/star-maker/machinery/bench/starmaker.mjs",
                     "Ventusltd/faraday/bench/tests.py",
                     "Ventusltd/ventus-grid-engine/engine/network-topology.js"],
                 "status":"RESEARCH_PROPOSALS_NOT_REAL_FAULT_VERDICTS"}
    }

def write(out,pilot_n=2048,limit=48):
    dest=Path(out);dest.mkdir(parents=True,exist_ok=True)
    d=graph_and_experiments(pilot_n,limit)
    for key,obj in (("graph.json",d["graph"]),("stars.json",d["stars"]),
                    ("faraday-proposals.json",d["faraday_proposals"]),
                    ("phase2-receipt.json",d["receipt"])):
        (dest/key).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return d

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="results/phase2")
    p.add_argument("--pilot",type=int,default=2048)
    p.add_argument("--stars",type=int,default=48)
    a=p.parse_args()
    d=write(a.out,a.pilot,a.stars)
    print(json.dumps(d["receipt"],indent=2))
