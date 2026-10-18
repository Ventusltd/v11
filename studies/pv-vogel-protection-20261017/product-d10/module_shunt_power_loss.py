#!/usr/bin/env python3
"""D10: 660Wp isolated module, commanded terminal shunt and unpowered hold.

Only source-limited hypothetical lumped single-diode PV, capacitance,
forced smooth voltage ramp, energy ledger and mechanism state logic.
A prescribed ramp is a TARGET, NOT a demonstrated gate-driver waveform.
No actual switch, reverse cell model, cable inductance, inverter, SPICE arc,
electrical safety validation, 30-year life or certified isolation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

STUDY = "v11.d10.single-module-shunt-and-power-loss.v1"
VOC, VMPP, IMPP, ISC = 45.75, 38.13, 17.31, 18.4
RLOAD = VMPP / IMPP
MODULES = 30

def _scale():
    lo, hi = .1, 30.
    for _ in range(100):
        a = (lo+hi)*.5
        frac = (1-np.exp((VMPP-VOC)/a))/(1-np.exp(-VOC/a))
        if frac>IMPP/ISC: lo=a
        else: hi=a
    return .5*(lo+hi)

A_DIODE = _scale()

def ipv(v):
    v=np.asarray(v,dtype=float)
    if np.any(v<0) or np.any(v>VOC*1.001):
        raise ValueError("No reverse-cell breakdown or above-Voc model")
    return ISC*(1-np.exp((v-VOC)/A_DIODE))/(1-np.exp(-VOC/A_DIODE))

def steady_v(r_hot):
    if r_hot<=0: raise ValueError("R_on must be positive")
    lo, hi=0.,VMPP
    for _ in range(90):
        v=.5*(lo+hi)
        if float(ipv(v))-v/RLOAD-v/r_hot > 0: lo=v
        else: hi=v
    return .5*(lo+hi)

def close_smooth(r_hot=.005, assumed_c_f=10e-6, slew_s=.0002):
    """Demand a smooth V(t) and calculate I_switch, P_switch and energy.

    A real semiconductor may FAIL to reproduce this demanded gate waveform,
    especially without an energy reserve or enough pulsed SOA. There is no
    claim the inferred resistance is an actual available device.
    """
    if assumed_c_f<0 or slew_s<=0: raise ValueError("invalid closure fixture")
    vf=steady_v(r_hot)
    t=np.linspace(0,slew_s,1201)
    u=t/slew_s
    dv=VMPP-vf
    v=vf+dv*(1-3*u*u+2*u*u*u)
    slope=dv*6*u*(u-1)/slew_s
    pv_i=ipv(v)
    load_i=v/RLOAD
    switch_i=pv_i-load_i-assumed_c_f*slope
    if float(np.min(switch_i)) < -1e-7:
        raise AssertionError("negative commanded shunt current")
    switch_i=np.maximum(switch_i,0)
    power=v*switch_i
    energy_pv=float(np.trapezoid(v*pv_i,t))
    energy_load=float(np.trapezoid(v*load_i,t))
    energy_switch=float(np.trapezoid(power,t))
    stored_start=.5*assumed_c_f*VMPP**2
    stored_finish=.5*assumed_c_f*vf**2
    residual=energy_pv-energy_load-energy_switch-(stored_finish-stored_start)
    return {
        "switch_r_hot_ohm":r_hot, "assumed_terminal_c_f":assumed_c_f,
        "command_slew_s":slew_s, "initial_module_v":VMPP,
        "final_module_v":float(vf),
        "final_pv_current_a":float(pv_i[-1]),
        "final_shunt_current_a":float(switch_i[-1]),
        "peak_shunt_current_a":float(np.max(switch_i)),
        "peak_switch_instantaneous_w":float(np.max(power)),
        "switch_energy_j":energy_switch,
        "source_energy_j":energy_pv,"load_energy_j":energy_load,
        "cap_initial_j":stored_start,"cap_final_j":stored_finish,
        "energy_ledger_error_j":float(residual),
        "steady_shunt_heat_w":float(power[-1]),
    }

def available_pulse_j(cap_f, full_v=12., minimum_v=6.):
    if cap_f<0 or full_v<minimum_v or minimum_v<0:
        raise ValueError("invalid actuation reserve")
    return .5*cap_f*(full_v**2-minimum_v**2)

def power_failure(mechanism, command_short=True, lost_power=True,
                  reserve_cap_f=0., assumed_pulse_j=.05,
                  auxiliary_reset_power=False):
    """Mechanism-level truth table ONLY; no certified device implied.

    Ordinary enhancement MOSFET: no off-power gate drive -> short opens.
    Latching mechanical: short holds with no power ONLY IF closing pulse
    was delivered with sufficient charged reserve before total blackout.
    Spring normally-closed: shorts with zero electrical holding energy,
    but requires powered means to OPEN for PV energy harvesting.
    Reset is impossible in this fixture absent a separately usable source.
    """
    if mechanism not in ("volatile_enhancement_fet",
                         "pulse_latched_contact","spring_normally_closed"):
        raise ValueError("unknown shunt mechanism")
    reserve=available_pulse_j(reserve_cap_f)
    if mechanism=="volatile_enhancement_fet":
        closed=bool(command_short and not lost_power)
    elif mechanism=="pulse_latched_contact":
        closed=bool(command_short and reserve>=assumed_pulse_j)
    else:
        closed=bool(command_short or lost_power)
    return {
        "mechanism":mechanism,"power_lost":lost_power,
        "remains_shorted_when_unpowered":closed,
        "reset_to_generation_power_available":bool(closed and auxiliary_reset_power),
        "reserve_energy_j":reserve,
        "required_actuation_energy_j_ASSUMED":
            assumed_pulse_j if mechanism=="pulse_latched_contact" else None,
        "needs_nonterminal_bootstrap_after_dark":
            mechanism=="spring_normally_closed",
    }

def isolated_string_oc_v(failed_open=0,r_hot=.005):
    if not 0<=failed_open<=MODULES: raise ValueError("invalid failures")
    return failed_open*VOC+(MODULES-failed_open)*ISC*r_hot


def sunlight_powered_bootstrap(illumination=1., mode="terminal_15v_gate",
                              elapsed_s=1., reserve_cap_f=.001,
                              fault_clear=True, full_sun_harvester_w=.25,
                              conversion_eff=.60, control_w=.005):
    """Counterfactual sunlight-powered reset of an unpowered *latched shunt*.

    Sun is present but terminal-voltage sunlight detection (>15V, 2025
    disclosure) is blind while terminal short is held (~0.092V). Additional
    hypothetical photovoltaic-side harvester OR a verified converter starting
    below ~100mV could solve energy, but neither exists in our tested circuit.
    Clearance indication is an EXTERNAL ASSUMPTION; do not restart on light alone.
    """
    if mode not in ("terminal_15v_gate","independent_solar_harvester",
                    "hypothetical_ultra_low_v_shunt_boost"):
        raise ValueError("unknown proposed supply path")
    if not 0<=illumination<=1 or elapsed_s<0 or reserve_cap_f<=0:
        raise ValueError("invalid illumination, duration or reserve")
    if not 0<=conversion_eff<=1 or full_sun_harvester_w<0 or control_w<0:
        raise ValueError("invalid hypothetical efficiency / loads")
    pv_terminal_v = steady_v(.005)*illumination
    if mode=="terminal_15v_gate":
        harvested_w = 0. if pv_terminal_v<15 else full_sun_harvester_w*illumination*conversion_eff
    elif mode=="independent_solar_harvester":
        harvested_w = full_sun_harvester_w*illumination*conversion_eff
    else:
        # Hypothetical ultra-low-input converter, not an identified device:
        # maximum tap fraction .12 of bypass I2R, 40% efficiency and startup
        # voltage >=50mV, while deliberately retaining shunt functionality.
        harvested_w = (.12*.40*(ISC*illumination*pv_terminal_v)
                       if pv_terminal_v>=.05 else 0.)
    net_w = max(0.,harvested_w-control_w) if harvested_w>0 else 0.
    cap_e_full_j = .5*reserve_cap_f*12.**2
    cap_e_usable_j = .5*reserve_cap_f*(12.**2-6.**2)
    available_j = min(cap_e_full_j,net_w*elapsed_s)
    time_to_full_s = cap_e_full_j/net_w if net_w>0 else None
    # A reset path is only conditionally possible if the sunlight-powered
    # reservoir has fully recharged AND an INDEPENDENT fault clear check exists.
    return {
        "mode":mode, "illumination_fraction":illumination,
        "terminal_voltage_while_shunted_v":float(pv_terminal_v),
        "original_sun_gate_above_15v":bool(pv_terminal_v>=15.),
        "hypothetical_harvest_net_w":float(net_w),
        "full_reserve_energy_j":cap_e_full_j,
        "usable_12_to_6v_j":cap_e_usable_j,
        "time_to_full_reserve_s":time_to_full_s,
        "elapsed_s":elapsed_s,
        "reservoir_full":bool(available_j>=cap_e_full_j),
        "fault_clear_assumed":bool(fault_clear),
        "conditional_reset_possible":bool(
            cap_e_usable_j>=.05 and available_j>=cap_e_full_j and fault_clear),
        "real_harvester_or_fault_clearance_circuit_verified":False,
    }

def report():
    base=close_smooth()
    mechanisms=[
        power_failure("volatile_enhancement_fet",reserve_cap_f=.002),
        power_failure("pulse_latched_contact",reserve_cap_f=.00047),
        power_failure("pulse_latched_contact",reserve_cap_f=.001),
        power_failure("spring_normally_closed"),
    ]
    sweep=[]
    for c in (1e-9,1e-7,1e-5,1e-4):
        for slew in (.00005,.0002,.001):
            for r in (.001,.005,.012):
                z=close_smooth(r,c,slew)
                sweep.append({
                    "C_f":c,"slew_s":slew,"R_hot_ohm":r,
                    "terminal_v":round(z["final_module_v"],7),
                    "peak_switch_i_a":round(z["peak_shunt_current_a"],5),
                    "peak_switch_power_w":round(z["peak_switch_instantaneous_w"],5),
                    "switch_linear_region_energy_j":round(z["switch_energy_j"],7),
                    "hold_short_heat_w":round(z["steady_shunt_heat_w"],6),
                    "ledger_error_j":abs(z["energy_ledger_error_j"]),
                })
    out={
        "schema":STUDY,
        "pv_fixture":{"rated_w":660.,"voc_v":VOC,"vmpp_v":VMPP,
                      "impp_a":IMPP,"isc_a":ISC,"module_count":MODULES,
                      "single_diode_scale_v":A_DIODE,
                      "curve":"calibrated at three STC anchors; no Rs/Rsh, thermal or reverse breakdown"},
        "single_module_5mohm_controlled_closure":base,
        "power_loss_logic":[*mechanisms],
        "latch_energy_hypotheses":{
            "voltage_start_v":12,"voltage_min_v":6,
            "required_pulse_j_ASSUMED":.05,
            "available_470uf_j":available_pulse_j(.00047),
            "available_1000uf_j":available_pulse_j(.001),
        },
        "all_shorts_or_failed_open_30_module_isolated_string_v":{
            str(f):isolated_string_oc_v(f) for f in (0,1,5,30)},
        "36_control_ramp_stress_cases":sweep,
        "solar_bootstrap_counterexamples": [
            sunlight_powered_bootstrap(mode=mode,elapsed_s=1.)
            for mode in ("terminal_15v_gate","independent_solar_harvester",
                         "hypothetical_ultra_low_v_shunt_boost")],
        "original_sun_logic_source": "https://github.com/Ventusltd/pv-arc-protection-circuit/blob/main/Open-Hardware-Disclosure.md; self-energised from >15V PV voltage, originally fail OPEN on loss of power",
        "abrupt_short_R_only_unphysical_initial_cap_current_a":VMPP/(.005+.001),
        "abrupt_model_warning":"R-only peak is NOT a prediction: module capacitance unknown and wiring L, ESR, SOA and gate speed missing",
        "conclusion":"Near-zero terminal voltage under assumed shunt is supported; sunlight is the primary energy source, but original PV-terminal >15V detector browns out during hard short. A separate solar harvester or verified ultra-low-voltage conversion could recharge an unpowered latch, conditional on fault-clear confirmation. Neither implementation nor autonomous reset is validated.",
        "unverified":[
            "gate/coil/latch actual SOA and 30-40A backfeed",
            "hot contact/wire thermal endurance and 30-year life",
            "sunlight-powered cold-start/reset circuit while module terminals are shunted",
            "independent analogue fault-clear evidence before controlled reopening",
            "real gate drive shaping, module capacitance and Ldi/dt",
            "inverter/cable energy, series/parallel arc plasma and safe isolation",
            "thermal hotspot, cell reverse breakdown and leakage to PE",
            "real paired-string and 30-module timing/fault location tests",
        ],
        "confidentiality":"Public V11 provisional module figures; no private IEC PDFs or user inverter manuals",
        "NOT_QUALIFICATION":True,
    }
    raw=json.dumps(out,sort_keys=True,separators=(",",":"),allow_nan=False)
    out["sha256"]=hashlib.sha256(raw.encode()).hexdigest()
    return out

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    q=report();target=Path(a.output)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(q,indent=2,sort_keys=True,allow_nan=False)+"\n")
    z=q["single_module_5mohm_controlled_closure"]
    print(json.dumps({
        "V_before":VMPP,"V_after":round(z["final_module_v"],5),
        "shunt_W_steady":round(z["steady_shunt_heat_w"],4),
        "controlled_ramp_peak_I_A":round(z["peak_shunt_current_a"],4),
        "controlled_ramp_peak_switch_P_W":round(z["peak_switch_instantaneous_w"],4),
        "mechanism_power_loss":[
            {"mechanism":x["mechanism"],
             "remain_short":x["remains_shorted_when_unpowered"]}
            for x in q["power_loss_logic"]],
        "sun_bootstrap_counterfactual_modelled":True,
        "autonomous_reset_verified_in_hardware":False,
        "actual_arc_or_device_validation":False,
        "receipt_sha256":q["sha256"],
    },indent=2))
