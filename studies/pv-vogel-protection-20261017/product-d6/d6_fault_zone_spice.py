#!/usr/bin/env python3
"""D6: a module-level *electrical* falsification test of active bypass zones.

Three explicit PV substrings, anti-parallel diodes, a middle-substring
back-to-back MOSFET bypass, an internal series hot spot and an EXTERNAL
module-lead hot connector. Real ngspice switching and I^2R energy integrals.

HARD LIMITS: forced ideal 17.31 A load, synthetic PV I-V and MOSFET models,
ohmic connectors (NOT arcs), no inverter/backfeed, insulation-to-frame,
validated junction thermal, real diode or FET SOA, nor IEC qualification.
No IEC licensed content or vendor copyrighted simulation model included.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

STUDY="V11_D6_MODULE_FAULT_ZONE_RESISTOR_TRANSIENT_v1"
I_STC=17.31
R_CLEAN=.00035
R_FAULT=.2
G_SUN=1000.
G_SHADE=100.
T_START_US=60.
T_END_US=200.
MEAS_NAMES=("e_inside_j","e_external_j","e_shunt_j","e_passive_bypass_j",
            "i_inside_a","i_external_a","i_shunt_a","i_bypass_a",
            "v_substring_v","v_module_v","v_gs_v","v_ds1_max_v","v_ds1_min_v",
            "v_ds2_max_v","v_ds2_min_v")
FLOAT=r"[-+]?(?:(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?)"
RECORD=re.compile(r"^\s*("+"|".join(MEAS_NAMES)+r")\s*=\s*("+FLOAT+r")(?=\s|$)",re.I|re.M)

@dataclass(frozen=True)
class Case:
    name:str
    fault_zone:str
    irradiance_ss2_w_m2:float
    shunt_on:bool
    def __post_init__(self):
        if self.fault_zone not in ("inside_substring","outside_module","clean_control"):
            raise ValueError("invalid fault-zone identifier")
        if self.irradiance_ss2_w_m2 not in (G_SUN,G_SHADE):
            raise ValueError("only explicit irradiance points supported")
        if not isinstance(self.shunt_on,bool):raise TypeError("shunt_on must be boolean")

def experiment_cases():
    # Every named state gets an identically forced-current OFF/ON comparison.
    return tuple(Case(f"{zone}__g{int(g)}__{'shunt_on' if turn else 'shunt_off'}",
                      zone,g,turn)
          for zone in ("inside_substring","outside_module","clean_control")
          for g in (G_SUN,G_SHADE) for turn in (False,True))

def circuit(case:Case):
    """Physical branches, with external connector beyond ALL bypass loops."""
    if not isinstance(case,Case):raise TypeError("Case required")
    ri=R_FAULT if case.fault_zone=="inside_substring" else R_CLEAN
    rext=R_FAULT if case.fault_zone=="outside_module" else R_CLEAN
    sources=[]
    for i in range(1,4):
        neg=("0","n1","n2")[i-1]
        pos=("n1","n2","n3")[i-1]
        g=case.irradiance_ss2_w_m2 if i==2 else G_SUN
        rh=ri if i==2 else R_CLEAN
        vhot=(f"VHOT2 h2 sense2 DC 0\nRHOT2 sense2 {pos} {rh:.12g}"
              if i==2 else f"RHOT{i} h{i} {pos} {rh:.12g}")
        bypass=("VDB2 n1 dbtap2 DC 0\nDBY2 dbtap2 n2 DBY"
                if i==2 else f"DBY{i} {neg} {pos} DBY")
        sources.append(f"""* Substring {i} negative={neg} positive={pos} irradiance={g:g}
IPH{i} {neg} c{i} DC {18.402067*g/1000:.10g}
DCELL{i} c{i} {neg} DCELL
RSH{i} c{i} {neg} 219.017492
RS{i} c{i} h{i} .0246039952
{vhot}
{bypass}
""")
    drive=("VDRIVE drv mid PULSE(0 12 40u 100n 100n 250u 500u)"
           if case.shunt_on else "VDRIVE drv mid DC 0")
    return f"""* {STUDY} {case.name}
* NOT A CALIBRATED PV ARC MODEL OR APPROVED PV PROTECTION CIRCUIT.
* Source: V11 provisional module fixture, D1/D2 PV, D3 generic MOSFET.
{''.join(sources)}
* External hot connector is downstream of all three bypass paths.
VEXT n3 conntap DC 0
REXT conntap out {rext:.12g}
* Forced 17.31 A ideal load: NOT a real loaded MPPT!
ILOAD out 0 DC {I_STC:.12g}
* Two generic opposed-body-diode NMOS, shunt across S2 only.
VSW1 n1 d1 DC 0
VSW2 n2 d2 DC 0
M1 d1 gate mid mid NTOY W=1 L=1
M2 d2 gate mid mid NTOY W=1 L=1
{drive}
RGATE drv gate 5
CGATE gate mid 10n
CGD1 gate d1 1n
CGD2 gate d2 1n
.model DCELL D(Is=1.778242293090851e-8 N=28.6)
.model DBY D(Is=1e-8 N=1.2 Rs=.01)
.model NTOY NMOS(LEVEL=1 VTO=2 KP=40 LAMBDA=.001 IS=1e-12)
.control
set noaskquit
tran .05u 240u 0 .05u
let ihot = i(vhot2)
let iext = i(vext)
let ishunt = i(vsw1)
let ipassive = i(vdb2)
let vsub = v(n2)-v(n1)
let rhot_power = ihot*ihot*{ri:.12g}
let rext_power = iext*iext*{rext:.12g}
let shunt_power = -vsub*ishunt
let diode_power = -vsub*ipassive
let vg = v(gate)-v(mid)
let vd1 = v(d1)-v(mid)
let vd2 = v(d2)-v(mid)
meas tran e_inside_j INTEG rhot_power FROM={T_START_US}u TO={T_END_US}u
meas tran e_external_j INTEG rext_power FROM={T_START_US}u TO={T_END_US}u
meas tran e_shunt_j INTEG shunt_power FROM={T_START_US}u TO={T_END_US}u
meas tran e_passive_bypass_j INTEG diode_power FROM={T_START_US}u TO={T_END_US}u
meas tran i_inside_a FIND ihot AT=100u
meas tran i_external_a FIND iext AT=100u
meas tran i_shunt_a FIND ishunt AT=100u
meas tran i_bypass_a FIND ipassive AT=100u
meas tran v_substring_v FIND vsub AT=100u
meas tran v_module_v FIND v(out) AT=100u
meas tran v_gs_v FIND vg AT=100u
meas tran v_ds1_max_v MAX vd1 FROM=20u TO=200u
meas tran v_ds1_min_v MIN vd1 FROM=20u TO=200u
meas tran v_ds2_max_v MAX vd2 FROM=20u TO=200u
meas tran v_ds2_min_v MIN vd2 FROM=20u TO=200u
quit
.endc
.end
"""

def parse_output(log):
    found={k.lower():float(v) for k,v in RECORD.findall(log)}
    missing=set(MEAS_NAMES)-set(found)
    if missing:raise ValueError(f"missing measured vectors {sorted(missing)}: {log[-1900:]}")
    if not all(math.isfinite(x) for x in found.values()):
        raise ValueError("non-finite simulator result")
    return found

def prepare(out):
    folder=Path(out);folder.mkdir(parents=True,exist_ok=True)
    records=[]
    for case in experiment_cases():
        deck=circuit(case)
        fname=case.name+".cir"
        (folder/fname).write_text(deck,encoding="utf8")
        records.append(asdict(case)|{"file":fname,
                      "sha256":hashlib.sha256(deck.encode("utf8")).hexdigest()})
    manifest={
      "study":STUDY,"status":"GENERATED_NOT_EXECUTED",
      "source":"V11 provisional OEM-UNVERIFIED 660Wp three-substring PV model",
      "zone_definition":"inside S2 photovoltaic series branch vs outside ALL module bypass paths",
      "external_current":"ideal 17.31 A imposed, no inverter/MPPT feedback",
      "fault_device":"0.2 ohm resistor, NOT an electric arc",
      "measurement_window_s":[T_START_US*1e-6,T_END_US*1e-6],
      "case_count":len(records),"cases":records,
      "no_IEC_copyright_content":True,
      "not_modelled":["arc plasma","two-pole cable","parallel string backfeed",
          "inverter capacitor","temperature feedback","real MOSFET/diode",
          "gate supply insulation","IEC creepage/clearance"]}
    (folder/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf8")
    return manifest

def verify_physics(records):
    named={r["name"]:r["measurements"] for r in records}
    findings=[]
    for g in (G_SUN,G_SHADE):
        for zone in ("inside_substring","outside_module","clean_control"):
            off=named[f"{zone}__g{int(g)}__shunt_off"]
            on=named[f"{zone}__g{int(g)}__shunt_on"]
            for q in (on,off):
                if abs(abs(q["i_external_a"])-I_STC)>.05:
                    raise AssertionError("ideal forced external current no longer holds")
                if min(q["e_inside_j"],q["e_external_j"])< -1e-7:
                    raise AssertionError("negative energy dissipated by resistor")
            if zone=="outside_module":
                expected=I_STC**2*R_FAULT*(T_END_US-T_START_US)*1e-6
                if any(abs(q["e_external_j"]-expected)>max(1e-7,expected*.01)
                       for q in (on,off)):
                    raise AssertionError("external hot connector energy does not match I^2R")
                if abs(on["e_external_j"]-off["e_external_j"])>max(1e-7,expected*.001):
                    raise AssertionError("substring bypass falsely appears to isolate external connector")
            findings.append({
              "fault_zone":zone,"irradiance_ss2_w_m2":g,
              "energy_internal_off_j":off["e_inside_j"],
              "energy_internal_on_j":on["e_inside_j"],
              "energy_external_off_j":off["e_external_j"],
              "energy_external_on_j":on["e_external_j"],
              "passive_bypass_off_j":off["e_passive_bypass_j"],
              "passive_bypass_on_j":on["e_passive_bypass_j"],
              "switch_on_j":on["e_shunt_j"],
              "external_connector_not_isolated":zone=="outside_module"})
    return findings

def execute(folder):
    path=Path(folder);manifest=prepare(path);records=[]
    for case in manifest["cases"]:
        p=subprocess.run(["ngspice","-b",case["file"]],cwd=path,text=True,
              stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=45)
        (path/(case["name"]+".log")).write_text(p.stdout,encoding="utf8")
        if p.returncode or "Error:" in p.stdout:
            raise RuntimeError(f"ngspice {case['name']} failed: {p.stdout[-2500:]}")
        records.append({"name":case["name"],"sha256":case["sha256"],
                        "measurements":parse_output(p.stdout)})
    finding=verify_physics(records)
    output={
      "study":STUDY,"status":"NGSPICE_GENERIC_OHMIC_FAULT_ZONE_SCREEN_NOT_ARC_TEST",
      "cases_executed":len(records),"arc_extinction_demonstrated":False,
      "mppt_behaviour_modelled":False,"dielectric_qualified":False,
      "case_results":records,"paired_findings":finding}
    (path/"observed-spice-results.json").write_text(json.dumps(output,indent=2)+"\n",encoding="utf8")
    return output

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--run",action="store_true")
    ap.add_argument("--out",default="results")
    args=ap.parse_args()
    if args.run:
        r=execute(args.out)
        print(json.dumps({"cases_executed":r["cases_executed"],
           "interpretation":r["status"]},indent=2))
    else:
        p=prepare(args.out)
        print(f"Generated {p['case_count']} decks, NO SPICE tests executed.")
if __name__=="__main__":
    main()
