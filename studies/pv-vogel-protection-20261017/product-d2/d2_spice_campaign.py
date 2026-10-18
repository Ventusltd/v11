#!/usr/bin/env python3
"""PV D2: generate/run a bounded ngspice voltage, diode and bypass study.

This is research grade / illustrative physics only. SPICE cannot certify
creepage, clearance, solid insulation or safely interrupt a real PV DC arc.
All cases are named from fixed explicit assumptions, not random sampling.
Run: python3 d2_spice_campaign.py --run --out results
Requires: ngspice executable (only when --run is requested).
"""
import argparse
import csv
import json
import math
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent
STUDY_ID="V11-D2-SPICE-INSULATION-v1"
FIT="PROVISIONAL_OEM_UNVERIFIED"
V_OC_STC=45.75
V_OC_COLD_LINEAR=49.593
IMPP=17.31
# Independent voltage-boundary cases: prescribed source potentials are NOT
# a complete post-trip network solution and deliberately bracket stress.
OUTPUT_CASES=[
    ("stc_mpp","NORMAL_ESTIMATE",29*V_OC_STC,V_OC_STC,1143.9),
    ("stc_mppt_collapsed","INVERTER_INPUT_COLLAPSED",29*V_OC_STC,V_OC_STC,0.0),
    ("cold_mppt_collapsed","COLD_VOC_ESTIMATE",29*V_OC_COLD_LINEAR,V_OC_COLD_LINEAR,0.0),
    ("cold_mpp","COLD_VOC_MPP_NODE_ASSUMED",29*V_OC_COLD_LINEAR,V_OC_COLD_LINEAR,1143.9),
    ("dark_module_cold_rest_collapsed","DARK_MODULE_WITH_COLD_OTHERS",29*V_OC_COLD_LINEAR,0.0,0.0),
    ("reverse_feed_stress","INVERTER_OR_OTHER_BUS_HIGH",0.0,0.0,1500.0)
]
# V(panel_out) is relative to a circuit datum that models string- negative,
# not mechanically grounded chassis or exposed metal. Frame insulation is
# a separate barrier even if the local substring differential is 15 V.
BLOCKING_CASES=[
    ("night_high_bus",0.0,1500.0),
    ("module_low_bus_high",45.75,1500.0),
    ("module_nominal_bus",1143.9,1143.9),
    ("reverse_test_cold",0.0,1487.79)
]
BYPASS_CASES=[
    ("unshaded_normal",1000.,17.31,1e10,False),
    ("shaded_normal",100.,17.31,1e10,False),
    ("shaded_active_shunt",100.,17.31,.005,False),
    ("unshaded_active_shunt",1000.,17.31,.005,False),
    ("dark_active_shunt_diode_open",0.,17.31,.005,True)
]

def _output_deck(name,rest_v,module_v,mppt_v):
    return f"""* {STUDY_ID} output OPEN stress {name} - imposed DC source-node envelope ONLY
* 29 series PV modules and a 1-module source; modelled as independent DC
* boundary conditions. No arc, panel frame, switching waveform or rated FET.
VREST mid 0 DC {rest_v:.12g}
VMODULE mout mid DC {module_v:.12g}
VMPPT load 0 DC {mppt_v:.12g}
ROFF mout load 1e9
.control
set noaskquit
op
let vds = v(mout)-v(load)
let vcm = v(mout)
print vds
print vcm
quit
.endc
.end
"""

def _bypass_deck(name,g,load,rsw,diode_open):
    # The PV substring is an *illustrative* photo-source + recombination
    # diode + series/shunt resistance fitted from the V11 provisional D1 data.
    # The series switch is a resistor for now; no MOSFET body diode/driver.
    if diode_open:
        diode_branch="RBYP_OPEN b_anode pos 1e12"
    else:
        diode_branch="DBYP b_anode pos DBY"
    return f"""* {STUDY_ID} substring bypass {name}; NOT a semiconductor switching study
* Positive current flowing from a downstream 17.31A string is imposed by ILOAD.
* The diode anode is negative and cathode is positive to bypass a shaded substring.
IPH 0 cell DC {18.402067*g/1000:.12g}
DCELL cell 0 DCELL
RSH cell 0 219.017492
RS cell pos .0246039952
VDB 0 b_anode DC 0
{diode_branch}
VSW pos swmid DC 0
RSW swmid 0 {rsw:.12g}
ILOAD pos 0 DC {load:.12g}
.model DCELL D(Is=1.778242293090851e-8 N=28.6)
.model DBY D(Is=1e-8 N=1.2 Rs=.01)
.control
set noaskquit
op
let v_sub = v(pos)
let ibyp = i(vdb)
let isw = i(vsw)
let p_by = -v(pos)*i(vdb)
let p_sw = v(pos)*i(vsw)
print v_sub
print ibyp
print isw
print p_by
print p_sw
quit
.endc
.end
"""

def _blocking_deck(name,array_v,bus_v):
    return f"""* {STUDY_ID} series BLOCKING diode reverse screen: {name}
* Demonstrates VRRM boundary, not PV surge rating or avalanche survival.
* This diode is NOT a substring bypass diode.
VARRAY array 0 DC {array_v:.12g}
VBUS bus 0 DC {bus_v:.12g}
DBLOCK array bus D_BLOCK_PLACEHOLDER
.model D_BLOCK_PLACEHOLDER D(Is=1e-12 N=1.5 BV=1e5)
.control
set noaskquit
op
let vrblock = v(bus)-v(array)
print vrblock
quit
.endc
.end
"""

def cases():
    for id,tag,rest,mod,mppt in OUTPUT_CASES:
        yield {"case_id":"D2-OUTPUT-"+id,"kind":"output_open","tag":tag,
               "deck":_output_deck(id,rest,mod,mppt),
               "input":{"rest_v":rest,"module_v":mod,"mppt_v":mppt},
               "expected_vds_v":rest+mod-mppt}
    for id,array_v,bus_v in BLOCKING_CASES:
        yield {"case_id":"D2-BLOCK-"+id,"kind":"blocking_diode",
               "tag":"SERIES_STRING_BLOCKING_REVERSE_NOT_BYPASS",
               "deck":_blocking_deck(id,array_v,bus_v),
               "input":{"array_node_v":array_v,"bus_node_v":bus_v},
               "expected_vrblock_v":bus_v-array_v}
    for id,g,load,sw,opened in BYPASS_CASES:
        yield {"case_id":"D2-BYPASS-"+id,"kind":"substring_bypass",
               "tag":"UNVERIFIED_SUBSTRING",
               "deck":_bypass_deck(id,g,load,sw,opened),
               "input":{"irradiance_w_m2":g,"load_a":load,"shunt_r_ohm":sw,
                        "bypass_diode_open":opened}}

VALUES=("vds","vcm","vrblock","v_sub","ibyp","isw","p_by","p_sw")
PAT=re.compile(r"^\s*("+("|".join(VALUES))+r")\s*=\s*([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)\s*$",re.M)

def parse_log(log):
    out={k:float(v) for k,v in PAT.findall(log)}
    if not out:
        raise ValueError("no understood scalar .op results from ngspice")
    if not all(math.isfinite(x) for x in out.values()):
        raise ValueError("non-finite SPICE result")
    return out

def generate(out_dir:Path):
    out_dir.mkdir(parents=True,exist_ok=True)
    descriptions=[]
    for item in cases():
        filename=item["case_id"]+".cir"
        (out_dir/filename).write_text(item["deck"],encoding="utf8")
        descriptions.append({k:v for k,v in item.items() if k!="deck"} | {"netlist":filename})
    (out_dir/"case-manifest.json").write_text(json.dumps({
        "study_id":STUDY_ID,"evidence_grade":"illustrative_spice_simulation",
        "original_fixture":FIT,
        "model_exclusions":["calibrated arc plasma","MOSFET avalanche and SOA","whole-string PV IV",
            "real inverter/DC link topology","converter switching and cable RLC",
            "frame leakage/earth and galvanic barriers","actual diode VRRM/failure rating",
            "physical dielectric distances","PCB creepage and clearance"],
        "cases":descriptions},indent=2)+"\n",encoding="utf8")
    return descriptions

def run_ngspice(items,out_dir):
    records=[]
    for case in items:
        deck=out_dir/case["netlist"]
        p=subprocess.run(["ngspice","-b",str(deck.name)],cwd=out_dir,
                         text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                         check=False,timeout=30)
        (out_dir/(case["case_id"]+".log")).write_text(p.stdout,encoding="utf8")
        if p.returncode != 0 or "Error:" in p.stdout:
            raise RuntimeError(f"ngspice failed for {case['case_id']} code={p.returncode}: {p.stdout[-1200:]}")
        values=parse_log(p.stdout)
        if case["kind"]=="output_open":
            if set(values)!={"vds","vcm"}: raise ValueError(f"missing output vectors {values}")
            if abs(values["vds"]-case["expected_vds_v"])>0.05:
                raise AssertionError(f"open switch voltage deviates {case['case_id']} {values}")
        elif case["kind"]=="blocking_diode":
            if set(values)!={"vrblock"}: raise ValueError(f"missing blocking diode vector {values}")
            if abs(values["vrblock"]-case["expected_vrblock_v"])>0.05:
                raise AssertionError(f"series blocking diode VRRM screen deviates {case['case_id']} {values}")
        else:
            if set(values)!={"v_sub","ibyp","isw","p_by","p_sw"}:
                raise ValueError(f"missing bypass vectors {values}")
            if values["p_by"]<-1e-6 or values["p_sw"]<-1e-6:
                raise AssertionError(f"negative passive component dissipation {values}")
        records.append({k:case[k] for k in ("case_id","kind","tag","input")}
                       | {"values":values, "ngspice_run_status":"passed_voltage_and_energy_algebra_only"})
    return records

def insulation_worksheet(records):
    # Voltage stress must not be mistaken for dielectric spacing approval.
    voltages=[abs(r["values"]["vds"]) for r in records if r["kind"]=="output_open"]
    bypass=[max(0,r["values"]["v_sub"]) for r in records if r["kind"]=="substring_bypass"]
    blocking=[max(0,r["values"]["vrblock"]) for r in records if r["kind"]=="blocking_diode"]
    bounds=[
        ("MODULE_OUT_SWITCH_DIFF",max(voltages),"switch differential",
         "actual Vds magnitude and both polarity blocking","IEC 61730-1 and applicable switching standard"),
        ("BYPASS_DIODE_VRRM",max(bypass),"diode cathode to anode",
         "VRRM, leakage(T), surge, open/short failure","OEM bypass diode datasheet; IEC 61730-1"),
        ("SERIES_BLOCKING_DIODE_VRRM",max(blocking),"series blocking diode reverse bias",
         "VRRM, IF, I2t, reverse leakage(T), actual transient BV","OEM blocking diode datasheet; IEC 61730-1"),
        ("SUBSTRING_LOGIC_TO_FRAME",1500.0,"working common mode (assumed system class)",
         "material CTI, pollution degree, solid insulation, impulse","IEC 60664-1:2020+AMD1:2025; IEC 61730-1"),
        ("MODULE_CIRCUIT_TO_FRAME",1500.0,"system voltage (design input, NOT a simulated stress)",
         "frame potential, wet leakage, pollution, altitude","IEC 61730-1; IEC 60664-1"),
        ("SENSOR_COMM_TO_FRAME",1500.0,"design hypothesis for floating logic interface",
         "isolation barrier type and failure, transients","IEC 61730-1; IEC 60664-1")
    ]
    return [
       {"boundary_id":id,"screened_working_or_diff_v":round(v,5),
        "basis":basis,"required_evidence":req,"references":ref,
        "transient_peak_v":"UNKNOWN","required_impulse_withstand_v":"UNKNOWN",
        "clearance_mm":"TBD_LICENSED_STANDARD_AND_LAB",
        "creepage_mm":"TBD_LICENSED_STANDARD_AND_LAB",
        "solid_insulation_qualified":"NO",
        "material_group_CTI":"UNKNOWN","pollution_degree":"UNKNOWN",
        "altitude_m":"UNKNOWN","encapsulation_class":"UNKNOWN",
        "humidity_wet_leakage":"UNKNOWN",
        "voltage_rating_qualified":"NO",
        "product_design_state":"HOLD"}
       for id,v,basis,req,ref in bounds
    ]

def write_results(records,out_dir):
    worksheet=insulation_worksheet(records)
    (out_dir/"electrical-stress-results.json").write_text(json.dumps({
       "study":STUDY_ID,"label":"SPICE_OP_DC_BOUNDED_ONLY","cases":records,
       "no_claims":["no dielectric withstand test","no qualified component",
          "no real arc suppression","no insulation compliance","no risk reduction probability"]
    },indent=2)+"\n",encoding="utf8")
    with (out_dir/"insulation-boundary-worksheet.csv").open("w",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=list(worksheet[0]))
        w.writeheader(); w.writerows(worksheet)
    return worksheet

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--run",action="store_true",help="actually run ngspice for all generated decks")
    parser.add_argument("--out",default="results")
    args=parser.parse_args()
    out=Path(args.out)
    descriptions=generate(out)
    print(f"Generated {len(descriptions)} simulation decks in {out}.")
    if not args.run:
        print("No simulations executed (use --run and ensure ngspice installed).")
        return
    results=run_ngspice(descriptions,out)
    boundaries=write_results(results,out)
    print(f"Executed {len(results)} .op decks; produced {len(boundaries)} HOLD insulation worksheets.")
    for case in results:
        print(case["case_id"], json.dumps(case["values"],sort_keys=True))
if __name__=="__main__":
    main()
