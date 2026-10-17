"""Track C (SUP-C) initial-attack calculations. Deterministic; reads ONLY the shared fixture.
Grade: algebra (single-diode fit is illustrative, pending models/pv_module.py).
Run: python3 -I track_c_calcs.py
"""
import json, math, hashlib, sys
import numpy as np
from scipy.optimize import fsolve

from pathlib import Path
FX = str(Path(__file__).resolve().parents[2] / "fixture" / "system-fixture.json")
fx = json.load(open(FX))
m = fx["module"]; c = fx["conductors"]; inv = fx["inverter_dc_side"]; arc = fx["arc_model"]
Voc, Isc, Vmp, Imp = m["voc_stc_v"], m["isc_a"], m["vmpp_v"], m["impp_a"]
Ns = m["single_diode_fit"]["cells_in_series_total"]
k, q, T = 1.380649e-23, 1.602176634e-19, 298.15
Vt = k * T / q
print("# fixture", fx["fixture_id"])

# ---- illustrative 5-parameter single-diode fit (Iph, I0, n, Rs, Rsh) at STC ----
def I_of(V, I, p):
    Iph, I0, n, Rs, Rsh = p
    return Iph - I0 * (math.exp((V + I * Rs) / (n * Ns * Vt)) - 1) - (V + I * Rs) / Rsh - I

def eqs(p):
    Iph, I0, n, Rs, Rsh = p
    # dI/dV at MPP from implicit differentiation
    a = (Vmp + Imp * Rs) / (n * Ns * Vt)
    dIdV = -(I0 / (n * Ns * Vt) * math.exp(a) + 1 / Rsh) / (1 + Rs * (I0 / (n * Ns * Vt) * math.exp(a) + 1 / Rsh))
    return [I_of(0, Isc, p), I_of(Voc, 0, p), I_of(Vmp, Imp, p), Imp + Vmp * dIdV, Rsh - 2000.0]
# Rsh fixed at 2000 ohm (ASSUMED) to keep the fit well posed; 4 free params + fixed Rsh
p0 = [Isc, 1e-10, 1.1, 0.1, 2000.0]
p = fsolve(eqs, p0, xtol=1e-12)
Iph, I0, n, Rs, Rsh = p
print(f"fit Iph={Iph:.4f} A I0={I0:.3e} A n={n:.4f} Rs={Rs:.4f} ohm Rsh={Rsh:.0f} ohm; residuals={[round(x,6) for x in eqs(p)]}")

from scipy.optimize import brentq
def I_at(V, p=p):
    return brentq(lambda I: I_of(float(V), float(I), p), -5.0, Isc + 1.0)

def g_mod(V, p=p, dV=1e-3):
    return -(I_at(V + dV, p) - I_at(V - dV, p)) / (2 * dV)  # module incremental conductance A/V (positive)

g = g_mod(Vmp)
print(f"module incremental conductance at MPP g = {g:.4f} A/V  (r_mpp = {1/g:.3f} ohm); string r = {30/g:.1f} ohm")

# ---- cable ----
R_km = c["field_cable"]["resistance_ohm_per_km_20c"]; alpha = c["field_cable"]["temp_coeff_per_c"]
R936 = 2 * 936 * R_km / 1000; R931 = 2 * 931 * R_km / 1000; R600 = 2 * 600 * R_km / 1000; R5 = 2 * 5 * R_km / 1000
print(f"R_loop 936 m = {R936:.3f} ohm; 931 m = {R931:.3f}; 600 m = {R600:.3f}; 5 m = {R5:.4f} ohm; dR/dT(936) = {R936*alpha*1000:.1f} mohm/K")
Lpm = c["two_wire_line_defaults"]["loop_external_inductance_uh_per_m_approx"] + c["two_wire_line_defaults"]["loop_internal_inductance_dc_uh_per_m_approx"]
L936 = Lpm * 936e-6; L5 = Lpm * 5e-6
Cpm = c["two_wire_line_defaults"]["line_capacitance_pf_per_m_approx"]
print(f"L_loop 936 m = {L936*1e6:.0f} uH; 5 m = {L5*1e6:.2f} uH; C_line 936 m = {Cpm*936/1e6:.3f} uF; Z0 = {math.sqrt(Lpm*1e-6/(Cpm*1e-12)):.0f} ohm")
v = c["two_wire_line_defaults"]["propagation_velocity_m_per_s"]
print(f"one-way delay: 936 m {936/v*1e6:.3f} us; 931 m {931/v*1e6:.3f} us; 5 m {5/v*1e9:.1f} ns; 72 m array run {72/v*1e6:.3f} us (ASSUMED 30 x 2.4 m)")
Vdrop936 = Imp * R936
print(f"IR drop S20 at Impp: {Vdrop936:.1f} V; cable loss {Imp**2*R936:.0f} W = {100*Imp**2*R936/19800.9:.1f} % of string Pmpp")

# ---- C1 (a): series V_arc inserted OUTSIDE any bypass loop, inverter holds node voltage ----
print("# C1(a) series arc in string loop (outside bypass loop), node held, R_loop 936 m")
for Varc in (20, 40, 60):
    dVm = Varc / (30 + g * R936)
    dI = -g * dVm
    print(f"  V_arc={Varc} V: dV_module=+{dVm:.3f} V, dI={dI:.3f} A ({100*dI/Imp:.2f} %), P_arc={Varc*(Imp+dI):.0f} W")
# exact check with the IV curve for 20 V
def solve_series(Varc, Vnode, Rl):
    f = lambda I: 30 * (0) + 0  # placeholder
    from scipy.optimize import brentq
    # find I with 30*V_mod(I) = Vnode + Varc + I*Rl, where V_mod(I) via inverse of I_at
    def Vmod_of_I(I):
        from scipy.optimize import brentq as bq
        return bq(lambda V: I_at(V) - I, 0.0, Voc)
    return brentq(lambda I: 30 * Vmod_of_I(I) - (Vnode + Varc + I * Rl), 0.1, Isc - 1e-3)
Vnode0 = 30 * Vmp - Imp * R936
I20 = solve_series(20, Vnode0, R936); I60 = solve_series(60, Vnode0, R936)
print(f"  exact IV: V_node={Vnode0:.1f} V; I(20 V)={I20:.3f} A ({100*(I20-Imp)/Imp:.2f} %); I(60 V)={I60:.3f} A ({100*(I60-Imp)/Imp:.2f} %)")
# Stokes-Oppenlander arc voltages for reference
for gap in arc["gap_mm_variants"]:
    print(f"  S-O V_arc(gap {gap} mm) at 17.31 A = {(20+0.534*gap)*Imp**0.12:.1f} V; at 0.5 A = {(20+0.534*gap)*0.5**0.12:.1f} V (ILLUSTRATIVE, uncalibrated)")

# ---- C1 (b): arc INSIDE SS2 bypass loop ----
print("# C1(b) arc inside bypass loop of SS2 (fixture location)")
Voc_ss = Voc / 3; Voc_ss_cold = fx["plant"]["string_derived"]["voc_module_cold_minus10c_v"] / 3; Vf = 0.45
print(f"  substring Voc STC {Voc_ss:.2f} V, cold {Voc_ss_cold:.2f} V; max gap voltage with diode conducting = Voc_ss+Vf = {Voc_ss+Vf:.2f} V (STC) / {Voc_ss_cold+Vf:.2f} V (-10 C)")
print(f"  string-level DC signature = -(V_ss2(Impp)+Vf) = -({Vmp/3:.2f}+{Vf}) = {-(Vmp/3+Vf):.2f} V  (same as one shaded substring)")
print(f"  arc power upper bound inside loop ~ (Voc_ss+Vf)*I_b, I_b<=Isc: {(Voc_ss+Vf)*Isc:.0f} W; substring Pmpp = {660/3:.0f} W")
X_loop_100k = 2 * math.pi * 1e5 * L936
print(f"  string loop |Z| at 100 kHz (936 m route only) = {X_loop_100k:.0f} ohm vs diode r_d ~ {0.026/Imp*1000:.1f} mohm -> HF current division ratio ~ {0.026/Imp/X_loop_100k:.1e}")

# ---- C2-far parallel arc ----
print("# C2-far: arc 5 m from array end of S20 (931 m from inverter)")
for Varc in (20, 40, 60):
    Vnode = Varc + Isc * R931
    Vmod_S19 = Vnode / 30
    I_S19 = I_at(Vmod_S19 + 0)  # S19 modules at node/30 (ignores S19 cable drop; cable drop raises S19 module V slightly)
    print(f"  V_arc={Varc} V: V_node(steady, S19 at ~Isc)={Vnode:.0f} V, S19 module V={Vmod_S19:.1f} V -> I_S19={I_S19:.2f} A; S20 array-end V={Varc+Isc*R5:.1f} V; S20 modules at {(Varc+Isc*R5)/30:.2f} V each -> I={I_at((Varc+Isc*R5)/30):.2f} A")
Cin = inv["mppt_input_capacitance_f"]["value"]; Cdc = inv["dc_link_capacitance_f"]["value"]
Vn0 = 30 * Vmp - Imp * R600  # node voltage pre-fault set by S19 (600 m) and S20 (936 m) both at MPP ... use S19 estimate
print(f"  pre-fault node V (S19 estimate) = {Vn0:.0f} V; C_in energy 1/2CV^2 = {0.5*Cin*Vn0**2:.0f} J (150 uF), {0.5*500e-6*Vn0**2:.0f} J (500 uF); DC link 2 mF at node V = {0.5*Cdc*Vn0**2:.0f} J, at 1500 V = {0.5*Cdc*1500**2:.0f} J")
Ipk_far = (Vn0 - 40) / R931
print(f"  cap-discharge current into far fault, resistive limit = {Ipk_far:.0f} A; tau R*C_in = {R931*Cin*1e3:.2f} ms; tau R*C_dc = {R931*Cdc*1e3:.1f} ms")
print(f"  first wave step at inverter end: (V_node - V_arc)/Z0 = {(Vn0-40)/130:.1f} A per round trip ({2*931/v*1e6:.2f} us)")
print(f"  inverter-end S20 current swing: +{Imp:.2f} A -> about -{Isc:.2f} A steady (sign change, {Imp+Isc:.1f} A swing), transient -{Ipk_far:.0f} A")
# C2-near
Z5 = math.sqrt(L5 / Cin); f5 = 1 / (2 * math.pi * math.sqrt(L5 * Cin))
print(f"  C2-near (5 m from inverter): L_loop {L5*1e6:.2f} uH, C_in 150 uF -> Z={Z5:.3f} ohm, I_pk ~ V/Z = {Vn0/Z5:.0f} A (ESR/arc ignored), f_ring = {f5/1e3:.1f} kHz; R_5m = {R5*1e3:.1f} mohm")

# ---- C3 hot connector ----
print("# C3 hot connector detectability")
dRdT = R936 * alpha
for Rh in fx["priority_cases"]["C3"]["resistance_variants_ohm"]:
    dV = Imp * Rh; P = Imp**2 * Rh
    dT_ss = P / fx["priority_cases"]["C3"]["thermal"]["connector_to_ambient_w_per_k"]["value"]
    tau_th = fx["priority_cases"]["C3"]["thermal"]["connector_thermal_mass_j_per_k"]["value"] / fx["priority_cases"]["C3"]["thermal"]["connector_to_ambient_w_per_k"]["value"]
    # electrical: current reduction of S20 vs paired S19 at common node (node held)
    dVm = dV / (30 + g * R936); dI = -g * dVm
    print(f"  R={Rh} ohm: dV={dV:.2f} V, P={P:.1f} W, dT_ss={dT_ss:.0f} K (tau {tau_th:.0f} s), equiv cable dT={Rh/dRdT:.1f} K, ratio vs 40 K drift={Rh/(dRdT*40):.3f}, ramp rate {Rh/600*1e3:.3f} mohm/s vs drift 40K/4h={dRdT*40/14400*1e3:.3f} mohm/s -> rate ratio {Rh/600/(dRdT*40/14400):.1f}; paired-string dI={dI:.3f} A ({100*dI/Imp:.2f} %)")
# cell-temperature voltage sensitivity at string level
print(f"  string Voc temp sensitivity = {fx['plant']['string_derived']['vmpp_string_v']*abs(m['voc_temp_coeff_per_c']):.2f} V/K (at Vmpp scale) vs 0.87 V signal")
print(f"  module mismatch: 3 % of Impp = {0.03*Imp:.2f} A vs paired-string dI above (ASSUMED 3 % current mismatch)")

# ---- commutation / clamp ----
print("# commutation into clamp")
for dVc in (100, 200, 500):
    print(f"  L=667 uH, I=17.31 A, (V_clamp-V_src)={dVc} V: t_comm = {L936*Imp/dVc*1e6:.1f} us; E_L = {0.5*L936*Imp**2*1e3:.0f} mJ")
print("# energy to arc during latency budgets (W x s)")
for P in (300, 1100):
    print("  P=%d W: " % P + ", ".join(f"{t:g}s->{P*t:.4g} J" for t in (1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 0.1, 0.5, 2.0)))

h = hashlib.sha256(open(sys.argv[0], "rb").read()).hexdigest()
print("# script sha256", h)

# ---- additional checks: HF attenuation, line resonance, C_in charge to arc, first-opener voltage, dark-string conduction ----
print("# HF propagation along the home-run")
rho = 1.72e-8; mu0 = 4e-7 * math.pi; r_c = c["two_wire_line_defaults"]["conductor_radius_6mm2_m"]
Z0f = math.sqrt(Lpm * 1e-6 / (Cpm * 1e-12))
for f in (1e4, 1e5, 1e6):
    delta = math.sqrt(rho / (math.pi * f * mu0))
    ratio = max(1.0, r_c / (2 * delta))
    Rac = R936 * ratio
    alpha = (Rac / (2 * 936)) / (2 * Z0f)  # Np/m, loop R per m of route /(2 Z0)
    print(f"  f={f:.0e} Hz: skin depth {delta*1e3:.3f} mm, Rac/Rdc={ratio:.1f}, loop Rac={Rac:.0f} ohm, line attenuation over 936 m = {alpha*936*8.686:.2f} dB; |2 pi f L_loop| = {2*math.pi*f*L936:.0f} ohm -> i_n per 1 V rms arc noise = {1e3/(2*math.pi*f*L936):.2f} mA rms")
print("# quarter-wave line resonance f = v/(4*route) for inverter-end steps (C_in ~ short, array ~ high Z)")
for Lr in sorted(set(c["route_lengths_m"])):
    print(f"  route {Lr} m: f1 = {v/(4*Lr)/1e3:.1f} kHz, one-way delay {Lr/v*1e6:.3f} us")
print("# C2 energy split of the C_in discharge (far fault, V_arc = 40 V)")
V0 = Vn0; Vf_node = 40 + 18.4 * R931
Q = Cin * (V0 - Vf_node)
print(f"  Q = C_in*(V0-Vf) = {Q:.3f} C; E_arc from C_in = V_arc*Q = {40*Q:.1f} J; E_total released = {0.5*Cin*(V0**2-Vf_node**2):.0f} J; rest in cable R (DERIVED)")
print(f"  DC link 2 mF (V_DIRECTBUS): Q = {Cdc*(V0-Vf_node):.2f} C -> E_arc = {40*Cdc*(V0-Vf_node):.0f} J; tau = {R931*Cdc*1e3:.1f} ms")
print(f"  L/R of home-run = {L936/R931*1e6:.0f} us; loop energy at 164 A = {0.5*L936*164**2:.1f} J, at 18.4 A = {0.5*L936*18.4**2*1e3:.0f} mJ")
print("# steady arc power (S-O 1 mm, ILLUSTRATIVE): both strings 36.8 A, one string 18.4 A")
for I in (36.8, 18.4):
    Va = (20 + 0.534 * 1.0) * I ** 0.12
    print(f"  I={I} A: V_arc={Va:.1f} V, P={Va*I:.0f} W, E over 5 s = {Va*I*5/1e3:.2f} kJ")
print("# first-opened module switch under C2 (fault bridges S20+ to S20- via arc)")
for T, Vocm in ((25, Voc), (-10, fx["plant"]["string_derived"]["voc_module_cold_minus10c_v"])):
    print(f"  T={T} C: V_switch = 30*Voc_mod - V_arc = {30*Vocm:.0f} - 40 = {30*Vocm-40:.0f} V (all other 29 modules at Voc, no current)")
print(f"  healthy string, single open switch: V = V_string_oc - V_node: STC node 1073 V -> {30*Voc-1073:.0f} V; cold, node 500 V -> {30*49.593-500:.0f} V; node 0 V -> {30*49.593:.0f} V")
print("# dark string forward conduction with node energised (ADV night backfeed, V_DIRECTBUS)")
for Vn in (1073, 1500):
    Vcell = Vn / (30 * Ns)
    Idark = I0 * (math.exp(Vn / 30 / (n * Ns * Vt)) - 1)  # per module exp law, Iph = 0, Rs neglected
    print(f"  V_node={Vn} V -> {Vcell:.3f} V/cell -> I_reverse ~ {Idark:.2f} A (illustrative single-diode fit, Rs neglected, Iph=0)")
print("# partial shade DC equivalence: one substring bypassed -> string loses", round(Vmp/3+Vf,2), "V; dI with node held =", round(-(Vmp/3+Vf)/(30/g+R936),3), "A")
print("# cloud enhancement: 1200 W/m2 -> I ~", round(Imp*1.2,2), "A (", round(100*(1.2*Imp/Isc-1),1), "% above Isc_STC ) ASSUMED linear with G")
h = hashlib.sha256(open(sys.argv[0], "rb").read()).hexdigest()
print("# script sha256 (final)", h)
