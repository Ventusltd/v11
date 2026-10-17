"""SUP-B (power electronics) initial-attack arithmetic. Grade: algebra. Deterministic, no wall-clock.
Every value is DERIVED from claude-study/fixture/system-fixture.json unless printed with ASSUMED.
Run from claude-study/:  python3 -I review/track-B-initial-attack-calcs.py
Companion to review/track-B-charter-and-initial-attack.md (numbers quoted there come from this output).
"""
import json, math, sys
from pathlib import Path

FX = json.loads((Path(__file__).resolve().parents[1] / "fixture" / "system-fixture.json").read_text())
m, p, c, inv = FX["module"], FX["plant"], FX["conductors"], FX["inverter_dc_side"]
Impp, Isc = m["impp_a"], m["isc_a"]
aIsc = m["isc_temp_coeff_per_c"]["value"]            # ASSUMED in fixture
sd = p["string_derived"]
Voc_s, Voc_s_cold, Voc_m_cold, Vmpp_s, Pstr = sd["voc_string_stc_v"], sd["voc_string_cold_minus10c_v"], sd["voc_module_cold_minus10c_v"], sd["vmpp_string_v"], sd["pmpp_string_w"]
tw = c["two_wire_line_defaults"]
ROUTE = 936.0
L_per_m = (tw["loop_external_inductance_uh_per_m_approx"] + tw["loop_internal_inductance_dc_uh_per_m_approx"]) * 1e-6
L = L_per_m * ROUTE                                   # string home-run loop inductance, H
C_line = tw["line_capacitance_pf_per_m_approx"] * 1e-12 * ROUTE
Z0 = tw["characteristic_impedance_ohm_approx"]
R_loop = 2 * ROUTE * c["field_cable"]["resistance_ohm_per_km_20c"] / 1000
Vwin_min, Vwin_max = inv["input_voltage_window_v"]["min"], inv["input_voltage_window_v"]["max"]
C_in, C_dc = inv["mppt_input_capacitance_f"]["value"], inv["dc_link_capacitance_f"]["value"]
Vf = 0.45                                             # fixture bypass diode Vf at 17 A (ASSUMED in fixture)
V_ARC = 30.0                                          # ASSUMED collapsed-node arc voltage for bounding only

def hdr(t): print("\n== " + t)

hdr("A. fixture-derived loop constants (936 m home run)")
print(f"L_loop_h = {L:.4e} (0.713 uH/m x 936 m)   C_line_f = {C_line:.3e}   R_loop_ohm_20c = {R_loop:.3f}   Z0_ohm = {Z0}")
r_cond = tw["conductor_radius_6mm2_m"]; L_row_per_m = 4e-7 * math.log(c["sequential_row_return_separation_m"] / r_cond)
print(f"row-return loop (1.0 m separation) external L = {L_row_per_m*1e6:.2f} uH/m -> +{L_row_per_m*39*1e6:.0f}..{L_row_per_m*72*1e6:.0f} uH for 39..72 m row (ASSUMED row length; Track A to derive)")
for I, lab in ((Impp, "Impp"), (Isc, "Isc_stc"), (Isc * (1 + aIsc * 45), "Isc_70C")):
    print(f"half_L_I2_j at {lab} = {I:.2f} A: {0.5*L*I*I:.4f} J")
print(f"1 us unclamped ramp of Impp: L*dI/dt = {L*Impp/1e-6:.0f} V (fixture L); = {0.66e-3*Impp/1e-6:.0f} V at 0.66 mH")
print(f"distributed-line first step I*Z0 = {Impp*Z0:.0f} V for ~{2*tw['one_way_delay_936m_us']:.1f} us round trip; lumped LC ring f = {1/(2*math.pi*math.sqrt(L*C_line)):.0f} Hz")

hdr("B. post-trip DC standoff across an open series switch (forward = generation direction)")
cases = [("node held by paired string at Vmpp_s", Vmpp_s), ("node at MPPT window min", Vwin_min), ("node collapsed to arc (C2-near, V_ARC ASSUMED)", V_ARC), ("node at 0 V (inverter off, C_in discharged, paired string dark)", 0.0)]
for name, Vn in cases:
    print(f"  {name:62s}: STC {Voc_s - Vn:7.1f} V   cold -10C {Voc_s_cold - Vn:7.1f} V")
print(f"  reverse (string dark, node charged): V_BOOST {Vmpp_s:.1f} V (C_in at last MPP) .. V_DIRECTBUS {Vwin_max} V; both across an anti-series pair or a string switch")

hdr("C. clamp trade for the string loop: t_decay = L*I/(Vc-Vs); E_clamp = 0.5*L*I^2*Vc/(Vc-Vs); I = Impp")
E0 = 0.5 * L * Impp ** 2
for Vs in (Voc_s - Vmpp_s, Voc_s_cold - Vmpp_s, Voc_s_cold - Vwin_min, Voc_s_cold - V_ARC):
    for Vc in (400, 600, 1000, 1600, 1700, 2500):
        if Vc > Vs:
            t = L * Impp / (Vc - Vs); E = E0 * Vc / (Vc - Vs)
            print(f"  Vs={Vs:7.1f} V  Vc={Vc:5d} V : t_decay={t*1e6:7.1f} us  E_clamp={E:6.3f} J  P_avg={E/t/1e3:6.1f} kW")
print("  note: Vs follows the PV IV curve from ~0 V (at Impp) to Voc_s-V_node (at zero current); the table uses the end value -> conservative")

hdr("D. RCD snubber alternative (capacitor absorbs 0.5*L*I^2 with overshoot dV = I*sqrt(L/C))")
for Cs in (10e-6, 40e-6):
    print(f"  C_snub={Cs*1e6:.0f} uF: dV={Impp*math.sqrt(L/Cs):.0f} V at Impp; {Isc*math.sqrt(L/Cs):.0f} V at Isc; stored at 1458 V = {0.5*Cs*1458**2:.1f} J")

hdr("E. conduction-loss budgets (0.5 % and 1 % of STC nameplate at Impp)")
Pmod, Pplant = m["rated_wp"], p["dc_nameplate_wp"]
for frac in (0.005, 0.01):
    print(f"  {frac*100:.1f} %: module {frac*Pmod/Impp**2*1e3:.2f} mOhm | 2-module {frac*2*Pmod/Impp**2*1e3:.2f} | 4-module (plant/192) {frac*Pplant/192/Impp**2*1e3:.2f} | string {frac*Pstr/Impp**2*1e3:.1f} mOhm")
print("  illustrative hot anti-series pair resistances by voltage class (ASSUMED market ranges, W04 to verify):")
for cls, r in (("60-100 V Si, 1 die/direction", 5), ("150 V Si", 10), ("200 V Si", 20), ("600-650 V SJ Si", 60), ("650 V SiC (2x27 mOhm typ x1.4 hot)", 76), ("1200 V SiC", 40), ("1700 V SiC (2x45 mOhm x1.4)", 126)):
    P = Impp ** 2 * r * 1e-3
    print(f"    {cls:38s} {r:4d} mOhm -> {P:5.1f} W/unit = {P/Pmod*100:5.2f} % of module; x720 = {P*720/1e3:5.1f} kW; as string unit = {P/Pstr*100:5.2f} %")

hdr("F. thermal budget relation: R_pair_hot <= 2*(Tj_max_screen - Ta_box)/(Rth_single*I^2)  [each device own path]")
for Rth in (15, 30, 60):
    print(f"  Rth_ja={Rth:2d} K/W (ASSUMED), Ta_box=70 C (ASSUMED), Tj<=125 C: R_pair_hot <= {2*55/(Rth*Impp**2)*1e3:.1f} mOhm")
print("  fixed-point Tj = Ta + Rth*I^2*R25*(1+alpha*(Tj-25)); loop gain g = Rth*I^2*R25*alpha must be < 1")
def tj(Ta, Rth, R25, alpha):
    g = Rth * Impp ** 2 * R25 * alpha
    if g >= 1: return float("inf"), g
    return (Ta + Rth * Impp ** 2 * R25 * (1 - 25 * alpha)) / (1 - g), g
for R25, alpha, lab in ((2.5e-3, 0.006, "100 V Si 2.5 mOhm a=0.6%/K"), (5.0e-3, 0.008, "hypothetical 5 mOhm a=0.8%/K"), (22e-3, 0.0085, "650 V SJ 22 mOhm a=0.85%/K"), (27e-3, 0.004, "650 V SiC 27 mOhm a=0.4%/K"), (45e-3, 0.004, "1700 V SiC 45 mOhm a=0.4%/K")):
    for Rth in (2, 15, 30, 60):
        T, g = tj(70.0, Rth, R25, alpha)
        print(f"    {lab:32s} Rth={Rth:2d} K/W: Tj = {'RUNAWAY' if T==float('inf') else f'{T:6.1f} C'}  g={g:.2f}  {'FAIL' if T>125 else 'ok'}")

hdr("G. adiabatic / semi-infinite pulse bound dTj = 2E/(A*sqrt(pi*rho*cp*k*t))  (uniform current; x2 for crowding)")
for mat, rho, cp, k in (("Si", 2330, 700, 120), ("SiC", 3210, 690, 300)):
    for E, t in ((0.162, 31e-6), (0.234, 45e-6), (0.702, 48e-6), (1.125, 81e-6)):
        print(f"  {mat:3s} E={E:.3f} J t={t*1e6:4.0f} us: A=10 mm2 -> {2*E/(10e-6*math.sqrt(math.pi*rho*cp*k*t)):5.0f} K ; A=25 mm2 -> {2*E/(25e-6*math.sqrt(math.pi*rho*cp*k*t)):5.0f} K")

hdr("H. SW-SS (inside bypass loop)")
print(f"  Voc_substring cold = {Voc_m_cold/3:.2f} V; off-state = Voc_ss + Vf = {Voc_m_cold/3+Vf:.2f} V; diode P when bypassing = {Vf*Impp:.2f} W; 3 diodes = {3*Vf*Impp:.1f} W/module")
for Lss in (1e-6, 5e-6):
    print("  L_ss=%.0f uH (ASSUMED): L*dI/dt = " % (Lss*1e6) + ", ".join(f"{Lss*Impp/toff:.0f} V @ {toff*1e6:.1f} us" for toff in (0.2e-6, 1e-6, 5e-6)) + f"; 0.5*L*I^2 = {0.5*Lss*Impp**2*1e3:.2f} mJ")

hdr("I. body diode as heater when one device of a pair is OFF or one has failed short")
for lab, vsd in (("Si body diode Vsd~1.0 V (ASSUMED)", 1.0), ("SiC body diode Vsd~3.5..5 V (ASSUMED)", 3.5), ("SiC upper", 5.0)):
    print(f"  {lab:38s}: {vsd*Impp:5.1f} W at Impp, {vsd*Isc:5.1f} W at Isc, continuous, not interruptible by the other device")

hdr("J. DC shunt (X-005)")
for R in (0.1, 2e-3, 1e-3, 0.5e-3):
    print(f"  R={R*1e3:5.1f} mOhm: P={R*Impp**2:6.3f} W at Impp ({R*Isc**2:6.3f} W at Isc); signal {R*Impp*1e3:7.2f} mV; x720 = {R*Impp**2*720/1e3:5.2f} kW; share of 11.01 mOhm budget {R/11.01e-3*100:5.1f} %; 2 nH parasitic corner {R/(2*math.pi*2e-9)/1e3:6.0f} kHz")

hdr("K. SW-STR-INV capacitor-discharge duty, C2-near (arc 5 m from inverter end)")
L_stub = L_per_m * 5 + 0.1e-6; R_stub = 2 * 5 * c["field_cable"]["resistance_ohm_per_km_20c"] / 1000
for Cx, lab in ((C_in, "C_in V_BOOST"), (C_dc, "C_dc V_DIRECTBUS")):
    Ipk = Vmpp_s * math.sqrt(Cx / L_stub); zeta = R_stub / 2 * math.sqrt(Cx / L_stub)
    print(f"  {lab:16s}: stored {0.5*Cx*Vmpp_s**2:6.0f} J at Vmpp_s; undamped peak {Ipk/1e3:5.1f} kA at t={math.pi/2*math.sqrt(L_stub*Cx)*1e6:5.1f} us; zeta={zeta:.2f}; initial dI/dt={Vmpp_s/L_stub/1e6:.0f} A/us")
for Lr in (20e-6, 100e-6):
    didt = Vmpp_s / (Lr + L_stub)
    for td in (1e-6, 5e-6, 10e-6):
        I = Impp + didt * td; EL = 0.5 * (Lr + L_stub) * I ** 2
        print(f"  reactor {Lr*1e6:3.0f} uH (ASSUMED), trip delay {td*1e6:4.1f} us: I_let_through={I:5.0f} A  E_L={EL:6.3f} J  E_clamp(Vc=1600 V, Vs=Vmpp_s)={EL*1600/(1600-Vmpp_s):6.2f} J")

hdr("L. X-003 energy scale")
print(f"  arc at 30 V x Impp = {30*Impp:.0f} W; 1 us vs 10 us switch = {30*Impp*9e-6*1e3:.1f} mJ; 1 ms detection = {30*Impp*1e-3:.2f} J; one home-run interruption clamp >= {E0:.3f} J")

hdr("M. responses to B0 objections from Tracks A/C/D")
# Track D OBJ-D3: 1.0 m pair separation over the whole route (fixture sequential_row_return_separation_m) as a loop variant
L2 = (4e-7 * math.log(1.0 / r_cond) + 0.1e-6) * ROUTE
print(f"  D3 variant L_loop at 1.0 m separation over 936 m = {L2*1e3:.3f} mH; 0.5*L*I^2 = {0.5*L2*Impp**2:.3f} J; 1 us unclamped = {L2*Impp/1e-6/1e3:.1f} kV")
for Vs, Vc in ((343.9, 1600), (1457.8, 1600), (1457.8, 1500)):
    print(f"     Vs={Vs:6.1f} V Vc={Vc} V: t_decay={L2*Impp/(Vc-Vs)*1e6:6.1f} us  E_clamp={0.5*L2*Impp**2*Vc/(Vc-Vs):6.3f} J   (fixture-L: {L*Impp/(Vc-Vs)*1e6:6.1f} us, {E0*Vc/(Vc-Vs):6.3f} J)")
# Track A B-3: dark-string reverse current at V_node, Track A cross-check fit n=1.2, I0=3.14e-9 A, Rs=0.0938 ohm, 25 C (ASSUMED night cell T = 25 C, pessimistic)
I0, n, Rs, Nc, Vt = 3.14e-9, 1.2, 0.0938, 66, 0.02569
def dark_I(Vmod):
    """Bisection on f(I) = I - I0*(exp((V - I*Rs)/(n*Nc*Vt)) - 1); f is monotonic increasing in I."""
    lo, hi = 0.0, 1000.0
    f = lambda I: I - I0 * (math.exp((Vmod - I * Rs) / (n * Nc * Vt)) - 1)
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if f(mid) > 0: hi = mid
        else: lo = mid
    return 0.5 * (lo + hi)
for Vn in (Vmpp_s, 1300.0, Vwin_max):
    Id = dark_I(Vn / 30)
    print(f"  B-3 dark S20 on node {Vn:6.1f} V: {Vn/30:5.2f} V/module -> reverse I = {Id:6.2f} A (25 C fit); string absorbs {Vn*Id/1e3:5.1f} kW; body-diode (Vsd 1 V) heater {Id:5.2f} W per unidirectional module switch")
# P1-shared (30 switches open on a string-wide signal): first device's clamp at Vc carries ~Isc for the skew time if Vc < standing voltage
for Vc in (200, 400):
    print(f"  P1-shared Vc={Vc} V: first clamp P = {Vc*Isc/1e3:.2f} kW; E per skew: " + ", ".join(f"{Vc*Isc*t:.2f} J @ {t*1e3:g} ms" for t in (0.1e-3, 1e-3, 10e-3, 100e-3)) + f"; after all 30 open each holds {Voc_s_cold/30:.1f} V (node 0) -> clamps off")
# Track A B-2: SPD coordination at SW-STR-INV
for Up in (2500, 4000):
    print(f"  B-2 SPD Up={Up} V (ASSUMED class): array-side line-to-line during clamp = V_node + Vc = {Vmpp_s:.0f} + 1600 = {Vmpp_s+1600:.0f} V -> SPD {'CONDUCTS' if Vmpp_s+1600 > Up else 'does not conduct'}; with node at 0: 1600 V -> {'CONDUCTS' if 1600 > Up else 'no'}")

# self-checks (algebra sanity, not protection validation)
assert abs(L * Impp / 1e-6 - 11552) < 5
assert abs(E0 - 0.1000) < 0.0005
assert abs(Voc_s_cold - V_ARC - 1457.79) < 0.01
print("\nself-checks OK")
