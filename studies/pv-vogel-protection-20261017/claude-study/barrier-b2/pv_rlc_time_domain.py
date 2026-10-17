"""B2 provisional time-domain PV fault network: nonlinear PV + RL cables + C_in.

RESEARCH MODEL; NOT a calibrated arc, IEC test, device-stress rating or safety proof.
Input fixture: ../fixture/system-fixture.json from V11 PR7, unchanged.

Network for a two-pole short across faulted S20 home-run:
  PV S20 - its RL two-wire cable -> F+  / F- -> R_fault
  PV S19 - its 600m cable, shared MPPT, S20 home-run RL -> F
  MPPT C_in - its S20 home-run RL -> F
The physical MPPT topology is assumed. Each source's plus/minus return forms
a complete loop. This is a lumped network: NO line wave travel/reflections.
P2: remove S19 and C_in path; P2b: remove S20; P3: remove both.
P1: remove S20 only (cut-set equivalent to P2b, NOT device equivalent).
P1b: no cut of complete string due to bypass (approximation).

Circuit dynamical identities while a path is connected:
  L_j di_j/dt = Vsource_j(i_j) - R_j i_j - Vf
  Vf = Rf * sum(i_j)
  C_in dVc/dt = -i_cap
Input source: nonlinear STC I(V) current-source fitted to four fixture
points, plus assumed PV-side output capacitance. NOT a calibrated single diode.
Input cap starts at Vmppt=1143.9V; PV current paths start at 0A,
PV terminal voltage at open-circuit Voc (precharged capacitive state,
NOT a loaded inverter at MPP). R_fault is a RESISTOR, NOT plasma.

When a control trip occurs, ideal isolation **redirects** the existing
inductor current into an imagined non-inductive R_dump (sources cease feeding
fault immediately); it accounts for inductive energy, but NOT Vds/driver,
semiconductor SOA, achievable commutation time or clamp qualification.
The capacitor retains energy after its input side is disconnected.

Energy balance E_PV + E_MPPT_Cinitial + E_PV_Cinitial = E_fault +
E_copper + E_dump + E_MPPT_Cfinal + E_PV_Cfinal + E_Lfinal within
numeric tolerance. Everything in SI units.
"""
import json
import math
from pathlib import Path
from dataclasses import dataclass
from typing import NamedTuple

FIXTURE = Path(__file__).resolve().parents[1] / "fixture/system-fixture.json"
BRANCHES = ("S20", "S19", "CAP")
STATES = ("i20","i19","icap","vcap","e_pv","e_wire","e_fault","e_dump","vpv20","vpv19")
CUT_SETS = {
    "P0": (), "P1": ("S20",), "P1b": (),
    "P2": ("S19","CAP"), "P2b": ("S20",),
    "P3": ("S20","S19","CAP"),
}
class Result(NamedTuple):
    outcome: dict
    samples: list

@dataclass(frozen=True)
class Config:
    location: str = "C2-far"
    action: str = "P0"
    horizon_s: float = 0.010
    trip_at_s: float = 0.003
    step_s: float = .0000005
    fault_resistance_ohm: float = 0.8
    dump_resistance_ohm: float = 1.0
    keep_samples: bool = False
    pv_output_capacitance_f: float | None = None
    mppt_input_capacitance_f: float | None = None

def fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))

def parameters(f, location):
    if location not in ("C2-far","C2-near"):
        raise ValueError("unsupported fault")
    lengths = (
        {"S20": 5.0, "S19": 600.0 + 931.0, "CAP": 931.0}
        if location == "C2-far" else
        {"S20": 931.0,"S19": 600.0 + 5.0,"CAP": 5.0}
    )
    # Generic per-metre *loop* inductance is assumed, NOT extracted
    # from a field-measured multi-conductor cable configuration.
    per_m_r_loop = 2 * f["conductors"]["field_cable"]["resistance_ohm_per_km_20c"] / 1000
    per_m_l_loop = (
       f["conductors"]["two_wire_line_defaults"]["loop_external_inductance_uh_per_m_approx"]
       + f["conductors"]["two_wire_line_defaults"]["loop_internal_inductance_dc_uh_per_m_approx"]
    ) * 1e-6
    r = [per_m_r_loop*lengths[b] for b in BRANCHES]
    l = [per_m_l_loop*lengths[b] for b in BRANCHES]
    # finite inductance for all three branches; parasitics of breaker UNKNOWN
    cap_f = f["inverter_dc_side"]["mppt_input_capacitance_f"]["value"]
    return {"length_m":lengths,"r_ohm":r,"l_h":l,"c_f":cap_f,
            "pv_output_c_f":0.000020, # EXPLICIT ASSUMPTION, NOT OEM PV capacitance
            "v_pv_open_circuit":f["module"]["voc_stc_v"]*f["plant"]["modules_per_string"],
            "v_cap_initial":f["plant"]["string_derived"]["vmpp_string_v"]}

def string_v_from_i(current, f):
    """Invert I=Isc(1-(V/Voc)^n) for STC string; NOT the PV diode equation."""
    i = max(0.0, current)
    m = f["module"]
    voc = m["voc_stc_v"]*f["plant"]["modules_per_string"]
    vmpp = m["vmpp_v"]*f["plant"]["modules_per_string"]
    isc, imp = m["isc_a"],m["impp_a"]
    n=math.log(1-imp/isc)/math.log(vmpp/voc)
    if i <= isc:
        return voc*max(0.0,1-i/isc)**(1/n)
    return -2.0*(i-isc) # extrapolation; physically unverified


def string_i_from_v(voltage, f):
    """Stable photovoltaic current-source fit through STC Isc/Voc/Impp/Vmpp.
    Illustrative, NOT an actual calibrated single-diode physical model.
    """
    m=f["module"]
    voc=m["voc_stc_v"]*f["plant"]["modules_per_string"]
    vmpp=m["vmpp_v"]*f["plant"]["modules_per_string"]
    isc,imp=m["isc_a"],m["impp_a"]
    n=math.log(1-imp/isc)/math.log(vmpp/voc)
    return isc*max(0.0,1-(max(0.0,voltage)/voc)**n)

def _trip_active(time, config):
    return time >= config.trip_at_s-1e-13

def _derivative(time, state, cfg, f, p):
    active = set(CUT_SETS[cfg.action]) if _trip_active(time,cfg) else set()
    currents=[max(0.0,x) for x in state[:3]]
    contributing=[0.0 if BRANCHES[j] in active else currents[j] for j in range(3)]
    vf=cfg.fault_resistance_ohm*sum(contributing)
    d=[0.0]*10
    for j in range(2):
        terminal_v=state[8+j]
        produced_i=string_i_from_v(terminal_v,f)
        # Each PV source has an explicit, hypothesised terminal capacitance.
        # The photogenerated current charges it; active branch discharge
        # follows Kirchoff exactly. This avoids the unbounded derivative of
        # the inverse I(V) fit near Isc and accounts for stored PV-side energy.
        d[8+j]=(produced_i-contributing[j])/p["pv_output_c_f"]
        d[4]+=terminal_v*produced_i
    for j in range(3):
        i=currents[j]
        if BRANCHES[j] in active:
            # Current redirected to a hypothetical passive dump outside the fault.
            # This is NOT proof of real switch/clamp commutation feasibility.
            d[j]=-cfg.dump_resistance_ohm*i/p["l_h"][j]
            d[7]+=cfg.dump_resistance_ohm*i*i
        else:
            source=(state[8+j] if j<2 else state[3])
            d[j]=(source-vf-p["r_ohm"][j]*i)/p["l_h"][j]
            d[5]+=p["r_ohm"][j]*i*i
            if j==2:
                d[3]=-i/p["c_f"]
        if state[j]<=0.0 and d[j]<0:
            d[j]=0.0 # positive-current-only model; reverse feeding excluded
    d[6]=vf*sum(contributing)
    return d

def _rk4(t,y,dt,cfg,f,p):
    def plus(z,k,q):
        return [a+q*b for a,b in zip(z,k)]
    k1=_derivative(t,y,cfg,f,p)
    k2=_derivative(t+dt/2,plus(y,k1,dt/2),cfg,f,p)
    k3=_derivative(t+dt/2,plus(y,k2,dt/2),cfg,f,p)
    k4=_derivative(t+dt,plus(y,k3,dt),cfg,f,p)
    res=[a+dt*(b+2*c+2*d+e)/6
         for a,b,c,d,e in zip(y,k1,k2,k3,k4)]
    # Solvers must never claim perfect conservation from a clamped derivative.
    # Numerical convergence and energy residual are reported for every run.
    return [max(0.0,z) if j<3 else z for j,z in enumerate(res)]

def run(cfg=Config()):
    if cfg.location not in ("C2-far","C2-near") or cfg.action not in CUT_SETS:
        raise ValueError("unknown location or action")
    if cfg.fault_resistance_ohm <= 0 or cfg.dump_resistance_ohm <= 0:
        raise ValueError("resistances must be positive")
    if cfg.step_s <= 0 or cfg.horizon_s <= 0 or not 0 <= cfg.trip_at_s <= cfg.horizon_s:
        raise ValueError("invalid time")
    count=round(cfg.horizon_s/cfg.step_s)
    if abs(count*cfg.step_s-cfg.horizon_s)>1e-11:
        raise ValueError("horizon must be divisible by step")
    trip_index=round(cfg.trip_at_s/cfg.step_s)
    if abs(trip_index*cfg.step_s-cfg.trip_at_s)>1e-11:
        raise ValueError("trip must be divisible by step")
    f=fixture()
    p=parameters(f,cfg.location)
    if cfg.pv_output_capacitance_f is not None:
        p["pv_output_c_f"]=cfg.pv_output_capacitance_f
    if cfg.mppt_input_capacitance_f is not None:
        p["c_f"]=cfg.mppt_input_capacitance_f
    if p["pv_output_c_f"] <= 0 or p["c_f"] <= 0:
        raise ValueError("energy storage capacitances must be positive")
    y=[0.0,0.0,0.0,p["v_cap_initial"],0.0,0.0,0.0,0.0,
       p["v_pv_open_circuit"],p["v_pv_open_circuit"]]
    ec0=.5*p["c_f"]*y[3]*y[3]
    epv0=.5*p["pv_output_c_f"]*(y[8]**2+y[9]**2)
    peak_fault_a=0.0;peak_vf=0.0; peak_cap_a=0.0
    samples=[]
    checkpoint=max(1,count//100)
    for k in range(count):
        t=k*cfg.step_s
        # Do not allow time-stepping over discontinuous switch state.
        is_off = k >= trip_index
        contributing=[0.0 if (is_off and b in CUT_SETS[cfg.action]) else max(y[j],0.0)
                      for j,b in enumerate(BRANCHES)]
        fault_i=sum(contributing);fault_v=cfg.fault_resistance_ohm*fault_i
        peak_fault_a=max(peak_fault_a,fault_i)
        peak_vf=max(peak_vf,fault_v)
        peak_cap_a=max(peak_cap_a,abs(y[2]))
        if cfg.keep_samples and (k%checkpoint==0 or k==count-1):
            samples.append({"t_s":round(t,9),"fault_a":round(fault_i,5),
                            "fault_v":round(fault_v,5),"cap_v":round(y[3],5)})
        # nudge the RK4 midpoint to preserve switch status *during* a step.
        # k stage at trip boundary belongs to post-trip segment.
        y=_rk4(t+(1e-11 if is_off else -1e-11),y,cfg.step_s,cfg,f,p)
    il=.5*sum(p["l_h"][j]*y[j]**2 for j in range(3))
    ec=.5*p["c_f"]*y[3]**2
    epv=.5*p["pv_output_c_f"]*(y[8]**2+y[9]**2)
    ein=ec0+epv0+y[4]
    eout=y[5]+y[6]+y[7]+ec+epv+il
    residual=ein-eout
    out={
        "status":"B2_LUMPED_RLC_NUMERICAL_ONLY_NOT_ARC_OR_PROTECTION_VALIDATION",
        "case":cfg.location,"action":cfg.action,
        "horizon_s":cfg.horizon_s,"trip_at_s":cfg.trip_at_s,
        "dt_s":cfg.step_s,"r_fault_assumed_ohm":cfg.fault_resistance_ohm,
        "pv_start":"OPEN_CIRCUIT_ZERO_FAULT_CURRENT_NOT_LOADED_MPPT",
        "capacitor_start_v":round(p["v_cap_initial"],5),
        "source_lengths_m":p["length_m"],"source_resistances_ohm":dict(zip(BRANCHES,p["r_ohm"])),
        "source_inductances_h":dict(zip(BRANCHES,p["l_h"])),
        "mppt_input_capacitance_f":p["c_f"],
        "assumed_pv_output_capacitance_f_per_string":p["pv_output_c_f"],
        "energy_pv_output_caps_start_j":round(epv0,5),
        "energy_pv_output_caps_end_j":round(epv,5),
        "energy_pv_source_j":round(y[4],5),
        "energy_cap_start_j":round(ec0,5),
        "energy_fault_resistor_j":round(y[6],5),
        "energy_wire_j":round(y[5],5),
        "energy_dump_j":round(y[7],5),
        "energy_cap_end_j":round(ec,5),
        "energy_inductors_end_j":round(il,5),
        "energy_residual_j":round(residual,6),
        "energy_residual_relative":round(abs(residual)/max(1.0,ein),9),
        "peak_fault_current_a":round(peak_fault_a,4),
        "peak_fault_voltage_v":round(peak_vf,4),
        "peak_capacitor_branch_current_a":round(peak_cap_a,4),
        "cap_final_v":round(y[3],4),
        "switch_stress_vds":"UNKNOWN",
        "residual_live_string_voltages":"UNKNOWN",
        "transient_wave_propagation":"NOT_MODELLED_LUMPED_RL",
        "arc_extinction":"NOT_MODELLED_FIXED_SHUNT_RESISTOR",
        "false_alarm_protection":"NOT_MODELLED",
        "source_blocking":"NO_REVERSE_CURRENT_SIMULATED",
        "experimental_validation":"NONE"
    }
    return Result(out,samples)

def suite(dt=5e-7):
    return {loc:{act:run(Config(location=loc,action=act,step_s=dt)).outcome
           for act in ("P0","P2","P2b","P3")}
            for loc in ("C2-far","C2-near")}

if __name__=="__main__":
    print(json.dumps(suite(),indent=2,sort_keys=True))
