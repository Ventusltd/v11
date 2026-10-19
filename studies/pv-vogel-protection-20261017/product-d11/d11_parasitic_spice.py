#!/usr/bin/env python3
"""D11 ngspice: source-level shunt with datasheet-constrained component parasitics.

NOT an Infineon vendor transistor macro-model. Uses IPT015N10N5 real datasheet
RDS(on), Ciss, Coss, Crss as a SMALL-SIGNAL, fixed-C equivalent at Vds=50V,
plus an explicit controlled switch and a real PN body-diode *surrogate*.
The UCC27511A driver is a sourced candidate but NOT its vendor PSpice model;
Vdrive is a 10V source and finite drive resistance.
Module PV, insulation/frame and cable capacitances are unmeasured sweep axes.

No vendor library is redistributed and NO IEC/private Sungrow files are used.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path

STUDY="v11.d11.parasitic-capacitance-source-limited-ngspice.v1"
DATASHEET="https://www.infineon.com/part/IPT015N10N5"
DRIVER="https://www.ti.com/product/UCC27511A"
SOURCE="https://github.com/Ventusltd/pv-arc-protection-circuit/blob/main/Open-Hardware-Disclosure.md"
CISS_F=12_000e-12
COSS_F=1_800e-12
CRSS_F=80e-12
CGS_F=CISS_F-CRSS_F
CDS_F=COSS_F-CRSS_F
R_FET_TYP_EQUIV=.0015  # actual part datasheet MAX at 25C/VGS10; not a hot guarantee
R_LEAD_ASSUMED=.0035  # total nominal 5mOhm, NOT datasheet copper/bond rating
ISC=18.4
VOC=45.75
VMPP=38.13
IMPP=17.31
PV_A=2.6962262802947725
PV_N=PV_A/.025864 # illustrative 27C thermal Vt; ngspice .TEMP 27
PV_IS=7.863925882139147e-7
FLOAT=r"[-+]?(?:(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?)"
OBS=("v20_v","v80_v","v150_v","vg80_v","vg150_v",
     "peak_shunt_a","peak_short_w","heat_short_j","peak_drain_v")
PATTERN=re.compile(r"^\s*("+"|".join(OBS)+r")\s*=\s*("+FLOAT+r")(?=\s|$)",re.I|re.M)

@dataclass(frozen=True)
class Case:
    name:str
    pv_cap_f:float
    cable_diff_f:float
    frame_each_f:float
    board_l_h:float
    gate_ohm:float
    drive_mode:str="close"
    def __post_init__(self):
        if self.drive_mode not in ("close","off","power_loss"):
            raise ValueError("unsupported mode")
        if min(self.pv_cap_f,self.cable_diff_f,self.frame_each_f,
               self.board_l_h,self.gate_ohm)<0 or self.gate_ohm==0:
            raise ValueError("negative parasitic or gate fixture")

def cases():
    return (
        Case("01_open_control",1e-9,1e-9,1e-9,50e-9,5.,"off"),
        Case("02_close_small_charge",1e-9,1e-9,1e-9,50e-9,5.),
        Case("03_close_typical_hypothesis",1e-7,1e-8,1e-9,50e-9,5.),
        Case("04_close_medium_charge",1e-6,1e-7,1e-9,50e-9,5.),
        Case("05_close_large_charge",100e-6,1e-7,1e-9,50e-9,5.),
        Case("06_close_large_charge_slow_gate",100e-6,1e-7,1e-9,50e-9,100.),
        Case("07_close_large_charge_long_lead",100e-6,1e-7,1e-9,500e-9,5.),
        Case("08_close_large_charge_more_frame",100e-6,1e-7,100e-9,50e-9,5.),
        Case("09_power_loss_low_charge",1e-7,1e-8,1e-9,50e-9,5.,"power_loss"),
        Case("10_power_loss_large_charge",100e-6,1e-7,1e-9,50e-9,5.,"power_loss"),
    )

def declared_capacitance_energy_j(c_f,v=VMPP):
    if c_f<0 or v<0:raise ValueError("negative C or V")
    return .5*c_f*v*v

def netlist(c:Case):
    """Return a real ngspice deck; floating PV negative references frame ONLY
    via 1Gohm solver resistor and two distinct *capacitive* PE paths.
    PV current is NOT intentionally dumped to PE.
    """
    drives={
        "close":"PULSE(0 10 30u 100n 100n 1m 2m)",
        "off":"DC 0",
        "power_loss":"PWL(0 0 30u 0 33u 10 90u 10 92u 0 210u 0)",
    }
    return f"""* {STUDY} {c.name}
* Real sourced candidate IPT015N10N5 datasheet-constrained equivalent.
* NO manufacturer transistor macro model, NO measured module capacitance.
* TI UCC27511A candidate driver, NOT actual TI PSpice macro model.
* Original 2025 sunlight gate >15V is blind when PV terminals short.
.temp 27
.options reltol=0.001 abstol=1e-9 chgtol=1e-15
* PV source + idealised diode anchored at Voc, Vmpp, Impp, Isc.
IPH n p DC {ISC}
DPV p n DPV
.model DPV D(Is={PV_IS:.15g} N={PV_N:.9g})
* PV output resistive load anchored to MPP; not real inverter.
RLOAD p n {VMPP/IMPP:.12g}
* External and intrinsic lumped capacitance; all non-device values are test axes.
CPVCELL p n {c.pv_cap_f:.12g}
CCABLEDIF p n {c.cable_diff_f:.12g}
CFRAMEPLUS p 0 {c.frame_each_f:.12g}
CFRAMEMINUS n 0 {c.frame_each_f:.12g}
RFRAME_REF n 0 1000Meg
* IPT015N10N5: 100V, <=1.5mOhm @ 10V/25C test condition,
* Ciss 12000p, Coss 1800p, Crss 80p at 50V / 1MHz.
* Fixed capacitances Cgs=Ciss-Crss, Cds=Coss-Crss.
* Semiconductor nonlinear C(V), package L, body diode and SOA unverified.
RLEAD p lead {R_LEAD_ASSUMED:.12g}
LBOARD lead sense {c.board_l_h:.12g}
VSHSENSE sense fet_d DC 0
SFET fet_d fet_r gate n SMOS
RFET fet_r n {R_FET_TYP_EQUIV:.12g}
CBULKDS fet_d n {CDS_F:.12g}
CMILLER fet_d gate {CRSS_F:.12g}
CGATESRC gate n {CGS_F:.12g}
DBODY n fet_d DBODY
.model DBODY D(Is=1e-10 N=1.2 Rs=.015)
.model SMOS SW(Ron=.000001 Roff=1e10 Vt=4 Vh=.20)
* Candidate TI UCC27511A approximated ONLY as a finite-R 10V gate source.
VDRIVE drive n {drives[c.drive_mode]}
RGATE drive gate {c.gate_ohm:.12g}
RGATEPULL gate n 1Meg
.control
set noaskquit
set numdgt=9
tran .015u 210u 0 .015u
let ish = i(vshsense)
let vmod = v(p)-v(n)
let ps = vmod*ish
let vg = v(gate)-v(n)
let vd = v(fet_d)-v(n)
meas tran v20_v FIND vmod AT=20u
meas tran v80_v FIND vmod AT=80u
meas tran v150_v FIND vmod AT=150u
meas tran vg80_v FIND vg AT=80u
meas tran vg150_v FIND vg AT=150u
meas tran peak_shunt_a MAX ish FROM=30u TO=190u
meas tran peak_short_w MAX ps FROM=30u TO=190u
meas tran heat_short_j INTEG ps FROM=30u TO=190u
meas tran peak_drain_v MAX vd FROM=0u TO=190u
quit
.endc
.end
"""

def parse(log):
    vals={k.lower():float(v) for k,v in PATTERN.findall(log)}
    missing=set(OBS)-set(vals)
    if missing:raise ValueError(f"SPICE measures missing: {sorted(missing)} {log[-1600:]}")
    if any(not math.isfinite(z) for z in vals.values()):
        raise ValueError("non-finite ngspice measurement")
    return vals

def run(out="results", execute=True):
    folder=Path(out)
    folder.mkdir(parents=True,exist_ok=True)
    observed=[]
    for c in cases():
        deck=netlist(c)
        deckname=c.name+".cir"
        (folder/deckname).write_text(deck,encoding="utf8")
        row={"case":asdict(c),"deck":deckname,
             "deck_sha256":hashlib.sha256(deck.encode()).hexdigest(),
             "cap_source_energy_j":declared_capacitance_energy_j(c.pv_cap_f),
             "cap_cable_energy_j":declared_capacitance_energy_j(c.cable_diff_f),
             "fet_Coss_50V_f":COSS_F,
             "fet_gate_input_Ciss_50V_f":CISS_F}
        if execute:
            p=subprocess.run(["ngspice","-b",deckname],cwd=folder,text=True,
                             stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                             timeout=75,check=False)
            (folder/(c.name+".log")).write_text(p.stdout,encoding="utf8")
            if p.returncode or "Error:" in p.stdout:
                raise RuntimeError(f"{c.name} ngspice failed: {p.stdout[-2200:]}")
            row["observed"]=parse(p.stdout)
        observed.append(row)
    result={"study":STUDY,
       "status":"NGSPICE_TRANSIENT_DATASHEET_EQUIVALENT" if execute else "DECKS_PREPARED_NOT_EXECUTED",
       "case_count":len(observed),
       "real_candidate_parts":[
          {"part":"Infineon IPT015N10N5","source":DATASHEET,
            "physical_properties":"datasheet grounded capacitances and nominal-on resistance at stated test points; switch itself behavioural, not manufacturer macro"},
          {"part":"TI UCC27511A","source":DRIVER,
            "physical_properties":"driver example only; ideal 10V source plus selected gate resistance, NOT vendor macro"},
       ],
       "device_c_f":{
          "ciss_typ_at_50v_f":CISS_F,"coss_typ_at_50v_f":COSS_F,
          "crss_typ_at_50v_f":CRSS_F,
          "model_cgs_f":CGS_F,"model_cds_f":CDS_F,
       },
       "original_public_sun_logic":SOURCE,
       "provisional_660wp_module":{"voc":VOC,"vmpp":VMPP,"impp":IMPP,"isc":ISC},
       "actual_arc_simulated":False,
       "actual_transistor_soa_verified":False,
       "nonlinear_device_capacitance_modelled":False,
       "sunrise_bootstrap_demonstrated":False,
       "source_warning":"PV C, cable C, frame C, wiring L are hypothetical axes. Gate control externally driven for electrical screening. Not a real autonomously self-powered module.",
       "cases":observed,
    }
    txt=json.dumps(result,sort_keys=True,separators=(",",":"),allow_nan=False)
    result["sha256"]=hashlib.sha256(txt.encode()).hexdigest()
    (folder/"parasitic-spice-receipt.json").write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    return result

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--out",default="results")
    a.add_argument("--prepare-only",action="store_true")
    o=a.parse_args()
    r=run(out=o.out,execute=not o.prepare_only)
    print(json.dumps({"study":STUDY,"status":r["status"],"cases":r["case_count"],
         "observations":[{"case":x["case"]["name"],
              "v80":round(x["observed"]["v80_v"],4),
              "v150":round(x["observed"]["v150_v"],4),
              "peak_shunt_a":round(x["observed"]["peak_shunt_a"],4)}
              for x in r["cases"] if "observed" in x],
         "hash":r["sha256"]},indent=2))
