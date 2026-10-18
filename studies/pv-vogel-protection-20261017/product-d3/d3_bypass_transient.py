#!/usr/bin/env python3
"""D3 ngspice research: transient switching of a PV substring active bypass.

All source, diode, MOSFET and gate-drive parameters are illustrative. This is
NOT a validated component, a vendor MOSFET model, arc quenching, junction-box
thermal modelling, or insulation qualification. Does not copy IEC content.

Crucial comparison: SINGLE MOSFET with body diode vs back-to-back MOSFET pair.
A lone MOSFET connected for active bypass may conduct through its body diode
when supposedly OFF, robbing normally illuminated substring generation.

Usage: python d3_bypass_transient.py --run --out results
Requires ngspice; use without --run to generate publicly reviewable decks.
"""
import argparse
import csv
import json
import math
import re
import subprocess
from pathlib import Path

STUDY_ID="V11-D3-ACTIVE-BYPASS-TRANSIENT-ILLUSTRATIVE"
ROOT=Path(__file__).resolve().parent
SAMPLE_US=(20,100,200)
IDS=[
    ("pair_shaded", "pair",100.,"normal","normal"),
    ("pair_full_sun", "pair",1000.,"normal","normal"),
    ("pair_dark_bypass_open", "pair",0.,"open","normal"),
    ("pair_shaded_bypass_open", "pair",100.,"open","normal"),
    ("pair_shaded_gate_lost", "pair",100.,"normal","gate_lost"),
    ("pair_fullsun_stuck_short", "pair",1000.,"normal","stuck_short"),
    ("pair_shaded_bypass_short", "pair",100.,"short","normal"),
    ("single_fullsun_off_body_diode", "single",1000.,"normal","gate_lost"),
    ("single_shaded_gate_pulse", "single",100.,"normal","normal"),
]

MEASURE_KEYS=("vsub_off","vsub_on","vsub_after",
              "ibyp_off","ibyp_on","ibyp_after",
              "isw_off","isw_on","isw_after",
              "vgs_off","vgs_on","vgs_after",
              "vds1_off","vds1_on","vds1_after",
              "vds2_off","vds2_on","vds2_after",
              "sw_power_on","diode_power_on","peak_overshoot_v")
NUMBER=r"[-+]?(?:(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?|nan|NaN)"
MEAS=re.compile(r"^\s*("+("|".join(MEASURE_KEYS))+r")\s*=\s*("+NUMBER+r")\b",re.M|re.I)

def netlist(case):
    cid, topology, g, bypass_failure, control_fault=case
    if bypass_failure not in ("normal","open","short"):raise ValueError(bypass_failure)
    if control_fault not in ("normal","gate_lost","stuck_short"):raise ValueError(control_fault)
    assert topology in ("pair","single")
    diode={
        "normal":"DBYP b_anode plus DBY",
        "open":"ROPEN b_anode plus 1e12",
        "short":"RSHORT b_anode plus .001",
    }[bypass_failure]
    if topology=="pair":
        # Both sources share a floating gate reference on the common SOURCE node.
        # When OFF, their opposing internal body diodes prevent either direction.
        # In this normalised MOS model, body diode is bulk-to-drain; W/L/KP
        # are a parametric toy, NOT a manufacturable device or fit to datasheet.
        transistor="""VSW1 0 d1 DC 0
VSW2 plus d2 DC 0
M1 d1 gate mid mid NTOY W=1 L=1
M2 d2 gate mid mid NTOY W=1 L=1
VDRIVE drv mid PULSE(0 12 40u 100n 100n 100u 500u)
Rgate drv gate 5
Cgate gate mid 10n
Cgd1 gate d1 1n
Cgd2 gate d2 1n
"""
        if control_fault in ("gate_lost","stuck_short"):
            transistor=transistor.replace(
                "VDRIVE drv mid PULSE(0 12 40u 100n 100n 100u 500u)",
                "VDRIVE drv mid DC 0")
        vgs="v(gate,mid)"
        vds1="v(d1,mid)"
        vds2="v(d2,mid)"
    else:
        # Intentionally compare the improper single FET orientation. Its
        # source/body at plus makes its body diode bypass illuminated PV when OFF.
        transistor="""VSW1 0 d1 DC 0
M1 d1 gate plus plus NTOY W=1 L=1
VDRIVE drv plus PULSE(0 12 40u 100n 100n 100u 500u)
Rgate drv gate 5
Cgate gate plus 10n
Cgd1 gate d1 1n
"""
        if control_fault=="gate_lost":
            transistor=transistor.replace(
                "VDRIVE drv plus PULSE(0 12 40u 100n 100n 100u 500u)",
                "VDRIVE drv plus DC 0")
        vgs="v(gate,plus)"
        vds1="v(d1,plus)"
        vds2="v(plus,plus)"  # zero, no second FET
    welded="RFAILED plus 0 .005" if control_fault=="stuck_short" else ""
    Iph=18.402067*g/1000.0
    expr={
       "vsub":"v(plus)",
       "ibyp":"i(VDBS)",
       "isw":"i(VSW1)",
       "vgs":vgs,
       "vds1":vds1,
       "vds2":vds2,
    }
    measures=[]
    for suffix,t in (("off",20),("on",100),("after",200)):
        for name,e in expr.items():
            measures.append(f"meas tran {name}_{suffix} FIND {e} AT={t}u")
    # Signed switch current can be negative in full sun: energy value from
    # computed terminal drop x current is positive for passive shunt flow.
    # The two ideal 0V sense sources do not represent shunt sensing hardware.
    measures+= [
       "let p_shunt_screen = -v(plus)*i(vsw1)",
       "let p_diode_screen = -v(plus)*i(vdbs)",
       "meas tran sw_power_on FIND p_shunt_screen AT=100u",
       "meas tran diode_power_on FIND p_diode_screen AT=100u",
       "meas tran peak_overshoot_v MAX v(plus) FROM=40u TO=140u",
    ]
    return f"""* {STUDY_ID}: {cid}
* DO NOT USE FOR ELECTRICAL HARDWARE OR FIELD PV INSTALLATION
* PV source and diode are D2 research assumptions, MOSFET generic L1 surrogate.
* ILOAD enforces 17.31 A through single substring (NOT full 30-module string).
IPH 0 cell DC {Iph:.10f}
DCELL cell 0 DCELL
RSH cell 0 219.017492
RS cell plus .0246039952
VDBS 0 b_anode DC 0
{diode}
ILOAD plus 0 DC 17.31
{transistor}
{welded}
.model DCELL D(Is=1.778242293090851e-8 N=28.6)
.model DBY D(Is=1e-8 N=1.2 Rs=.01)
.model NTOY NMOS (LEVEL=1 VTO=2 KP=40 LAMBDA=.001 IS=1e-12)
.control
set noaskquit
tran 0.05u 240u 0 0.05u
{chr(10).join(measures)}
quit
.endc
.end
"""

def manifest(path):
    path.mkdir(parents=True,exist_ok=True)
    items=[]
    for c in IDS:
        cid,topology,g,by,drive=c
        fn=f"D3-{cid}.cir"
        (path/fn).write_text(netlist(c),encoding="utf8")
        items.append({"id":cid,"netlist":fn,"topology":topology,
                      "irradiance_w_m2":g,"diode":by,"drive":drive,
                      "model_grade":"generic_SPICE_surrogate_unverified"})
    data={"study":STUDY_ID,"cases":items,
          "licensed_iec_content_in_repo":False,
          "excluded":["arc plasma","real MOSFET model or safe operating area",
               "junction-box thermal dynamics","whole-string insulation",
               "converter/DC link and cable transients","gate-power isolation",
               "calibrated bypass diode thermal and recovery",
               "real module IV","actual spontaneous fault detection",
               "field reliability and IEC qualification"]}
    (path/"cases.json").write_text(json.dumps(data,indent=2)+"\n",encoding="utf8")
    return items

def parse(s):
    res={key.lower():float(v) for key,v in MEAS.findall(s)}
    if len(res)!=len(MEASURE_KEYS):
        raise ValueError(f"ngspice missing metrics: {sorted(set(MEASURE_KEYS)-set(res))}; excerpt: {s[-1900:]}")
    if not all(math.isfinite(v) for v in res.values()):
        raise ValueError("unphysical floating NaN result")
    return res

def run(items,path):
    result=[]
    for c in items:
        proc=subprocess.run(["ngspice","-b",c["netlist"]],cwd=path,timeout=45,
                            text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (path/f"D3-{c['id']}.log").write_text(proc.stdout,encoding="utf8")
        if proc.returncode!=0 or "Error:" in proc.stdout:
            raise RuntimeError(f"SPICE failed: {c['id']}: {proc.stdout[-2400:]}")
        values=parse(proc.stdout)
        result.append({**c,"measurements":values})
    return result

def evaluate(records):
    by={r["id"]:r["measurements"] for r in records}
    pair=by["pair_full_sun"]
    single=by["single_fullsun_off_body_diode"]
    shaded=by["pair_shaded"]
    if pair["vsub_off"]<5:
        raise AssertionError("back-to-back FETs must leave sunlit substring productive while OFF")
    if single["vsub_off"]>1.5:
        raise AssertionError("single MOSFET body diode should improperly shunt illuminated substring")
    if not (shaded["isw_on"] > 10 and shaded["diode_power_on"] < shaded["diode_power_off"] if "diode_power_off" in shaded else shaded["isw_on"]>10):
        raise AssertionError("paired MOS must redirect shaded bypass current")
    if shaded["vgs_on"]<8:
        raise AssertionError("gate drive not fully on for toy model")
    return {"single_fet_off_full_sun_v":single["vsub_off"],
            "pair_fets_off_full_sun_v":pair["vsub_off"],
            "pair_shaded_switch_a_at_100us":shaded["isw_on"],
            "pair_shaded_switch_loss_w_at_100us":shaded["sw_power_on"],
            "pair_shaded_diode_loss_w_at_100us":shaded["diode_power_on"],
            "interpretation":"Topology screening only; not a validated protection MOSFET"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--run",action="store_true")
    ap.add_argument("--out",default="results")
    args=ap.parse_args()
    folder=Path(args.out)
    c=manifest(folder)
    print(f"Generated {len(c)} executable generic-MOSFET SPICE transient decks.")
    if not args.run:
        print("NOT EXECUTED: use --run when ngspice is installed")
        return
    cases=run(c,folder)
    result=evaluate(cases)
    with (folder/"transient-results.json").open("w",encoding="utf8") as fp:
        json.dump({"study":STUDY_ID,"status":"ACTUAL_SPICE_RUN_GENERIC_SURROGATES_NOT_HARDWARE",
                   "cases":cases,"decision_screen":result},fp,indent=2)
    print(json.dumps(result,indent=2))
if __name__=="__main__":
    main()
