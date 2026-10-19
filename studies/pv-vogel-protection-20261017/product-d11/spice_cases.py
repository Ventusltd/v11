#!/usr/bin/env python3
"""D11 ngspice runnable circuits using IDENTIFIED REAL PARTS as design targets.

IMPORTANT: Until manufacturer model files are separately obtained with
licence clearance, MOSFETs in these simulations are DOCUMENTED GENERIC
LEVEL-1 proxies, not Infineon semiconductor models. The ideal Vgs waveform
is NOT TI's UCC27511A macro-model and comparator is NOT TLV7032 macro-model.
Do not call these 'real component SPICE validation'.
"""
from __future__ import annotations
import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

PARAMETERS = {
    "pv_module": "provisional 660Wp 38.13Vmpp 17.31A Impp 45.75Voc 18.4Isc",
    "mosfet_target": "Infineon IPT015N10N5, TWO back-to-back, 100V, Rds_on_max=1.5mohm at stated conditions",
    "gate_driver_target": "TI UCC27511A, requires verified vendor PSpice macro-model for device timing",
    "comparator_target": "TI TLV7032, requires verified separate macromodel before comparator claims",
    "prototype_mosfet_model": "GENERIC MOS1 with 1.5mohm path resistor per switch, not manufacturer-provided",
    "powering": "In first three circuits, gate drive supplied by ideal fixture; independent sunlight circuit only demonstrates a hypothetical auxiliary photovoltaic harvester",
    "voltage": "One module only, PV+ to PV- shunt; all terminals local. No PE current sink.",
}

def netlist(mode: str) -> str:
    if mode not in ("closed","power_loss","no_command","sun_aux"):
        raise ValueError("unsupported physical-control fixture")
    if mode=="sun_aux":
        return """D11 a separate sunlight-powered auxiliary reserve, NOT a verified solar harvester
* 16V Thevenin PV-equivalent source with R=256ohm gives <=0.25W maximum
* Main module stays shunted in other deck; this auxiliary cell is DISTINCT.
Vsun sun 0 16
Rsun sun pre 256
Dharv pre reserve SCHOTTKY
Cstore reserve 0 1000u ic=0
Rctl reserve 0 100k
.model SCHOTTKY D(Is=1n N=1.1 Rs=0.05)
.tran 0.5m 1s uic
.meas tran v_boot0 FIND v(reserve) AT=0.01
.meas tran v_boot1 FIND v(reserve) AT=0.9
.end
"""
    # Gate command is referenced to floating back-to-back MOSFET common source.
    # No user-shared OEM model or copyrighted documentation is embedded.
    gate = {
        "closed": "PULSE(0 10 1m 1u 1u 5m 10m)",
        "power_loss": "PULSE(0 10 1m 1u 1u 1m 10m)",
        "no_command": "DC 0",
    }[mode]
    return f"""D11 one 660Wp module, Infineon IPT015N10N5 TOPOLOGY but GENERIC parameter proxy ({mode})
* PV module current from 0 into pv. 3-anchor current-voltage surrogate only.
* Max 100V per target FET; no surge rating or thermal/avalanche validated.
.options reltol=0.0003 abstol=1n method=gear
Bpv 0 pv I = 18.4*(1-exp((v(pv)-45.75)/2.69622628029477))/(1-exp(-45.75/2.69622628029477))
Rload pv 0 2.202772963604853
Cpv pv 0 10u
* Back-to-back MOSFETs. Both drains face opposite module terminals.
* TWO 1.5mohm series R represent upper-limit @10V quoted on manufacturer's
* product page only; generic nmos intrinsic channel adds further R.
Rds1 pv d1 1.5m
M1 d1 gate src src PROXY W=1 L=1
M2 d2 gate src src PROXY W=1 L=1
Rds2 d2 0 1.5m
Rfloat src 0 1G
* Ciss 12nF and Coss ~1.8nF are approximate published anchors; simplified.
Cgs1 gate src 12n
Cgs2 gate src 12n
Coss1 d1 src 1.8n
Coss2 d2 src 1.8n
.model PROXY NMOS (LEVEL=1 KP=200 VTO=2.7 LAMBDA=0.0001)
* Gate drive is an IDEAL voltage fixture, not a UCC27511A model.
Vgate gate src {gate}
.tran 1u 4m
.meas tran v_before FIND v(pv) AT=0.5m
.meas tran v_during FIND v(pv) AT=1.7m
.meas tran v_after FIND v(pv) AT=3.5m
.meas tran v_gate_on FIND v(gate,src) AT=1.7m
.meas tran v_gate_after FIND v(gate,src) AT=3.5m
.end
"""


def parse_measurements(output):
    results={}
    for name,value in re.findall(
        r"(?im)^\s*([a-z][a-z0-9_]*)\s*=\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?)",
        output):
        results[name]=float(value)
    return results

def execute(output_dir: Path, real_runs=True):
    output_dir.mkdir(parents=True,exist_ok=True)
    result={"parameters":PARAMETERS, "cases":{}, "real_ngspice_executed":False,
            "vendor_mosfet_macro_model_executed":False,
            "vendor_gate_driver_macro_model_executed":False,
            "vendor_comparator_macro_model_executed":False,
            "actual_arc_extinction_tested":False}
    for mode in ("closed","power_loss","no_command","sun_aux"):
        deck=output_dir/f"d11-{mode}.cir"
        deck.write_text(netlist(mode),encoding="utf8")
        if real_runs:
            if not shutil.which("ngspice"):
                raise RuntimeError("ngspice must be installed, no silent Python fallback")
            p=subprocess.run(["ngspice","-b",str(deck.resolve())],text=True,
                stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                timeout=90,check=False)
            (output_dir/f"d11-{mode}.log").write_text(p.stdout,encoding="utf8")
            if p.returncode:
                raise RuntimeError(f"ngspice {mode} returncode {p.returncode}: {p.stdout[-1800:]}")
            values=parse_measurements(p.stdout)
            expected=("v_boot0","v_boot1") if mode=="sun_aux" else (
                "v_before","v_during","v_after","v_gate_on","v_gate_after")
            missing=set(expected)-values.keys()
            if missing:
                raise RuntimeError(f"SPICE measurements missing {missing}: {p.stdout[-1800:]}")
            result["cases"][mode]=values
        else:
            result["cases"][mode]={"status":"netlist_generated_not_executed"}
    if real_runs:
        v=result["cases"]
        assert 34 < v["closed"]["v_before"] < 42, v["closed"]
        assert 0 < v["closed"]["v_during"] < 1, v["closed"]
        assert 0 < v["power_loss"]["v_during"] < 1, v["power_loss"]
        assert 34 < v["power_loss"]["v_after"] < 42, v["power_loss"]
        assert 34 < v["no_command"]["v_during"] < 42, v["no_command"]
        assert v["sun_aux"]["v_boot1"] > 12, v["sun_aux"]
        assert v["sun_aux"]["v_boot0"] < 2, v["sun_aux"]
        # Key falsification: ordinary electrically gated shunt does NOT
        # stay shorted after its 10V gate drive disappears.
        result["real_ngspice_executed"]=True
        result["validated_observations"]=[
            "Generic MOSFET model drives module voltage below 1V while gate held ON",
            "Gate voltage removal RE-ENERGISES module output in the proxy",
            "Separate hypothetical sunlight PV source can recharge reserve while main module shunted",
        ]
    (output_dir/"receipt.json").write_text(
        json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf8")
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",default="results")
    p.add_argument("--generate-only",action="store_true")
    x=p.parse_args()
    r=execute(Path(x.output_dir),real_runs=not x.generate_only)
    print(json.dumps({"real_ngspice_executed":r["real_ngspice_executed"],
        "test_cases":list(r["cases"]),
        "closed_v_at_1p7ms":r["cases"]["closed"].get("v_during"),
        "power_loss_v_at_3p5ms":r["cases"]["power_loss"].get("v_after"),
        "sun_aux_boot_v_at_0p9s":r["cases"]["sun_aux"].get("v_boot1"),
        "real_vendor_macros_verified":False,
        "hardware_safe":False},indent=2))
