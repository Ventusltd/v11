#!/usr/bin/env python3
"""D11 real ngspice circuits around actual manufacturer part numbers.

Electrical macromodels are EXPLICIT DATASHEET-FITTED SURROGATES, not
manufacturer PSpice models. Physical parts are named and sourced; gate
drive and two-string switches intentionally contain idealised stimuli.
This distinction must never be removed from the result receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
from pathlib import Path

BASE=Path(__file__).resolve().parent
CASES={
 "single":"01_single_150v_shunt.cir",
 "bidirectional":"02_back_to_back_150v.cir",
 "power_loss":"03_driver_uvlo_negative_control.cir",
 "paired_strings":"04_two_strings_peer_backfeed.cir",
}
EXPECTED={
 "single":("v_normal","v_closed","i_closed","gate_closed"),
 "bidirectional":("v_normal","v_closed","i_closed","gate_to_mid"),
 "power_loss":("v_normal","v_closed","v_reenergized","gate_lost"),
 "paired_strings":("bus_peer_live","bus_both_shunted",
                   "shunt_a_peer","shunt_a_both","v_a_late","v_b_late")
}
PAT=re.compile(r"(?mi)^\s*([a-z][a-z0-9_]*)\s*=\s*"
               r"([+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?)\b")


def check_measurements(name, measurements, reference=None):
    def require(ok, reason):
        if not ok:
            raise AssertionError(f"{name}: {reason}; readings={measurements}")
    m=measurements
    require(all(math.isfinite(v) for v in m.values()),"non-finite SPICE readings")
    if name in ("single","bidirectional"):
        require(35.0<m["v_normal"]<41.0,"PV MPP anchor must be present")
        require(0<m["v_closed"]<.5,"shunt must collapse terminal voltage")
        require(14<abs(m["i_closed"])<24,"module short current boundary")
        require(8<m["gate_closed" if name=="single" else "gate_to_mid"]<11,
                "gate drive must reach nominal 10V")
        if name=="bidirectional" and reference:
            require(m["v_closed"]>reference["v_closed"]*1.25,
                    "two power MOSFETs must dissipate more R_on than one")
    elif name=="power_loss":
        require(35<m["v_normal"]<41,"MPP before short")
        require(0<m["v_closed"]<.5,"commanded shunt closes")
        require(35<m["v_reenergized"]<41,
                "ordinary MOSFET FAILS TO STAY SHORT when driver loses power")
        require(abs(m["gate_lost"])<.05,"gate must lose charge in stimulus")
    elif name=="paired_strings":
        require(abs(m["shunt_a_peer"])>28,
                "single shunted string must expose peer current above own Isc")
        require(10<abs(m["shunt_a_both"])<26,
                "both strings shunted: A current should approach own Isc")
        require(abs(m["shunt_a_peer"])>abs(m["shunt_a_both"])*1.45,
                "coordinated bypass reduces peer contribution")
        require(m["bus_peer_live"]>m["bus_both_shunted"]+1,
                "common-bus voltage reduces after paired shutdown")
    else:
        raise ValueError(name)


def run(ngspice="ngspice",output_dir="results"):
    if not shutil.which(ngspice):
        raise FileNotFoundError(f"ngspice executable missing: {ngspice}")
    out=Path(output_dir)
    if not out.is_absolute():out=BASE/out
    out.mkdir(parents=True,exist_ok=True)
    results={}
    for name, filename in CASES.items():
        proc=subprocess.run(
            [ngspice,"-b",filename],cwd=BASE,stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,text=True,timeout=120,check=False)
        (out/(name+".ngspice.log")).write_text(proc.stdout,encoding="utf8")
        if proc.returncode!=0:
            raise RuntimeError(f"ngspice {filename} rc={proc.returncode}; "+
                               proc.stdout[-2000:])
        values={k:float(v) for k,v in PAT.findall(proc.stdout)}
        missing=set(EXPECTED[name])-values.keys()
        if missing:
            raise AssertionError(f"{name} measurements missing: {sorted(missing)}; "+
                                 proc.stdout[-1800:])
        values={k:values[k] for k in EXPECTED[name]}
        check_measurements(name,values,results.get("single"))
        results[name]=values
    report={
      "schema":"v11.d11.actual-ngspice-with-real-part-number-surrogates.v1",
      "simulator":"ngspice executed in batch mode; measurements parsed from real .tran results",
      "circuits_executed":list(CASES.values()),
      "actual_part_numbers":[
        {"part":"Infineon IPT034N15NM6",
         "datasheet_url":"https://www.infineon.com/part/IPT034N15NM6",
         "role":"150V power MOSFET; 3.4mOhm max at specified 10V/25C test",
         "model_status":"STUDY-OWNED LEVEL1 datasheet fitted approximation ONLY"},
        {"part":"TI UCC27511A",
         "datasheet_url":"https://www.ti.com/product/UCC27511A",
         "role":"potential 4A/8A gate driver; output-low during UVLO",
         "model_status":"PWL gate source TEST STIMULUS; vendor macro NOT RUN"},
        {"part":"TI TLV7032",
         "datasheet_url":"https://www.ti.com/product/TLV7032",
         "role":"proposed sunlight/analogue fault comparator; 1.6-6.5V rail",
         "model_status":"NOT wired or run in this D11 suite"},
        {"part":"ADI LTC3108",
         "datasheet_url":"https://www.analog.com/en/products/LTC3108.html",
         "role":"20mV energy-harvest startup candidate, transformer mandatory",
         "model_status":"NOT wired or run; self-power while shorted remains unverified"},
        {"part":"Littelfuse SMBJ58CA",
         "datasheet_url":"https://www.littelfuse.com/",
         "role":"58V VRWM, 93.6V specified clamp under rated surge fixture",
         "model_status":"NOT in live deck; transient overshoot NOT validated"},
      ],
      "test_results":results,
      "passed_circuits":len(results),
      "electrical_assumptions":{
        "pv_single_diode_fit":"Isc 18.4A; Voc 45.75V; Vmpp 38.13V; Impp 17.31A at assumed STC",
        "device":"Infineon 150V/3.4mOhm maximum-Rds-on at 25C datasheet-anchored surrogate",
        "gate":"ideal 0->10V pulse, not modelled TI driver/power/UVLO",
        "module_cap_f":"10nF INVENTED test fixture, NOT measured",
        "two_string_short":"30 x 3.4mOhm = 0.102Ohm series proxy per 30-module string",
        "cable":"2*16m*3.08mOhm/m 6mm2 Cu at assumed 20C, one home-run per string",
        "inverter":"absent, no capacitor or active backfeed",
        "ground":"frame/PE excluded from all operating DC current paths",
        "rating":"150V is a MOSFET Vds rating, not array 1500V withstand or a safety approval",
      },
      "critical_negative_controls":[
        "UCC27511A-style UVLO output low makes enhancement MOSFET shunt reopen",
        "one healthy string can reverse-feed current through same-MPPT shunted peer",
        "simple two-string proxy is NOT a single 150V MOSFET placed across the entire 1500V string",
      ],
      "not_proven":[
        "manufacturer MOSFET macro or actual gate driver/vendor PSpice",
        "LTC3108 sunrise startup from low-voltage shunted PV terminals",
        "sunrise/sunset fail-safe and fault-clear autonomous restart",
        "nonlinear transient switching SOA, body diode reverse recovery, avalanche",
        "cell hotspots and reverse cell breakdown",
        "thermal conduction through a real junction box for 30 years",
        "parallel/series arc energy or actual fault extinction",
        "real 1500V inverter input, same-MPPT DC converter or capacitor energy",
        "any IEC/UL conformity or human-safe isolation",
      ],
      "source_and_confidentiality":"Only independent public vendor product pages and public V11 provisional PV fixture. NO confidential inverter files or uploaded IEC material.",
      "hardware_validation":False,
    }
    raw=json.dumps(report,sort_keys=True,separators=(",",":"),allow_nan=False)
    report["receipt_sha256"]=hashlib.sha256(raw.encode()).hexdigest()
    (out/"receipt.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "actual_ngspice_transient_circuits":len(results),
        "measurements":results,
        "vendor_device_macromodels_executed":False,
        "hardware_validated":False,
        "sha256":report["receipt_sha256"]},indent=2))
    return report


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ngspice",default="ngspice")
    ap.add_argument("--output-dir",default="results")
    a=ap.parse_args()
    run(a.ngspice,a.output_dir)


if __name__=="__main__":
    main()
