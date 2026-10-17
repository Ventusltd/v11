"""SUP-A (review track A, power systems) independent cross-check for the charter
`track-A-charter-and-initial-attack.md`.  Deterministic; reads ONLY the shared fixture.

This is a reviewer's sanity calculation (grade: algebra), NOT the study model.  The single-diode
fit here uses a FIXED ideality factor n in {1.0, 1.2, 1.4}; the study fit must come from
claude-study/models/pv_module.py (W02) with reported residuals.

Run from claude-study/:   python3 review/track-A-check.py
"""
import hashlib
import json
import math
from pathlib import Path

from scipy.optimize import brentq, fsolve

HERE = Path(__file__).resolve().parent
FX = json.loads((HERE.parent / "fixture" / "system-fixture.json").read_text())
m, p, c, inv = FX["module"], FX["plant"], FX["conductors"], FX["inverter_dc_side"]
Voc, Isc, Vmp, Imp = m["voc_stc_v"], m["isc_a"], m["vmpp_v"], m["impp_a"]
Ns = m["single_diode_fit"]["cells_in_series_total"]
NSS = m["internal_structure"]["substrings_per_module"]
VF = 0.45  # fixture: bypass_diode_type Schottky_assumed_Vf_0p45_V_at_17A
kVoc, kIsc = m["voc_temp_coeff_per_c"], m["isc_temp_coeff_per_c"]["value"]
N = p["modules_per_string"]
Vmp_s, Voc_s, Voc_s_cold = (p["string_derived"][k] for k in ("vmpp_string_v", "voc_string_stc_v", "voc_string_cold_minus10c_v"))
VT = 1.380649e-23 * 298.15 / 1.602176634e-19  # thermal voltage at 25 C, V
ROW_RETURN_LENGTH_M = 40.0  # ASSUMED: 30 modules x ~1.3 m pitch; NOT in fixture


def fit(n):
    """Fixed-n 5-parameter single-diode fit to (Voc, Isc, Vmp, Imp). Iph, I0 eliminated analytically."""
    a = n * Ns * VT

    def elim(Rs, Rsh):
        I0 = (Isc + Isc * Rs / Rsh - Voc / Rsh) / (math.exp(Voc / a) - math.exp(Isc * Rs / a))
        return I0 * (math.exp(Voc / a) - 1) + Voc / Rsh, I0

    def F(x):
        Rs, Rsh = x
        Iph, I0 = elim(Rs, Rsh)
        e = math.exp((Vmp + Imp * Rs) / a)
        g = I0 * e / a + 1 / Rsh
        return [Iph - I0 * (e - 1) - (Vmp + Imp * Rs) / Rsh - Imp, -g / (1 + Rs * g) + Imp / Vmp]

    best = None
    for Rs0 in (0.05, 0.1, 0.2, 0.3):
        for Rsh0 in (100.0, 300.0, 1000.0):
            x = fsolve(F, [Rs0, Rsh0], xtol=1e-13)
            res = max(abs(v) for v in F(x))
            if x[0] > 0 and x[1] > 0 and (best is None or res < best["residual"]):
                Iph, I0 = elim(*x)
                best = dict(n=n, Iph=Iph, I0=I0, Rs=x[0], Rsh=x[1], residual=res)
    return best


def I_of_V(V, q, G=1.0):
    a = q["n"] * Ns * VT
    f = lambda I: q["Iph"] * G - q["I0"] * (math.exp((V + I * q["Rs"]) / a) - 1) - (V + I * q["Rs"]) / q["Rsh"] - I
    return brentq(f, -200, 200)


def V_of_I(I, q, G=1.0):
    a = q["n"] * Ns * VT
    f = lambda V: q["Iph"] * G - q["I0"] * (math.exp((V + I * q["Rs"]) / a) - 1) - (V + I * q["Rs"]) / q["Rsh"] - I
    return brentq(f, -60.0, Voc + 5)


def V_mod_bypassed(I, q, G=1.0):
    """Illuminated module with ideal per-substring bypass: terminal V >= -3*VF."""
    return -NSS * VF if I >= I_of_V(-NSS * VF, q, G) else V_of_I(I, q, G)


def V_dark(I, q):
    """Dark module carrying I in the forward-diode (backfeed) direction."""
    a = q["n"] * Ns * VT
    return brentq(lambda V: q["I0"] * (math.exp((V - I * q["Rs"]) / a) - 1) + (V - I * q["Rs"]) / q["Rsh"] - I, 0, 80)


def Varc(I, gap_mm):
    return (20 + 0.534 * gap_mm) * I ** 0.12  # fixture Stokes-Oppenlander form, UNCALIBRATED


# ---------------- cable / loop (fixture geometry) ----------------
r = c["two_wire_line_defaults"]["conductor_radius_6mm2_m"]
D = c["home_pair_separation_m"]
mu0, eps0 = 4e-7 * math.pi, 8.8541878128e-12
L_ext = mu0 / math.pi * math.log(D / r)                       # H/m, thin-wire form
L_ext_acosh = mu0 / math.pi * math.acosh(D / (2 * r))         # H/m, exact two-wire
L_int = 0.1e-6                                                # H/m, fixture dc internal
C_line = math.pi * eps0 * c["effective_relative_permittivity"] / math.log(D / r)
Z0, v = math.sqrt(L_ext / C_line), 1 / math.sqrt(L_ext * C_line)
L_hr = (L_ext + L_int) * 936
L_row = (mu0 / math.pi * math.log(c["sequential_row_return_separation_m"] / r) + L_int) * ROW_RETURN_LENGTH_M
L_loop = L_hr + L_row
Rkm = c["field_cable"]["resistance_ohm_per_km_20c"]
R_loop = lambda one_way_m: 2 * one_way_m * Rkm / 1000
R_str = (N * (m["internal_structure"]["positive_lead_m"] + m["internal_structure"]["negative_lead_m"])
         * c["factory_lead"]["resistance_ohm_per_km_20c"] / 1000
         + c["mated_interfaces_per_string"]["total"] * c["connector_resistance_ohm_each"])
Cin, Cdc = inv["mppt_input_capacitance_f"]["value"], inv["dc_link_capacitance_f"]["value"]


def c2_two_strings(R20, R19, gap, q):
    """Two illuminated strings on one node feeding one parallel arc; node voltage is the scalar unknown."""
    def I_str(Vn, R):
        return brentq(lambda I: N * V_mod_bypassed(I, q) - R * I - Vn, 0.0, q["Iph"] * 1.5)
    Vn = brentq(lambda Vn: Varc(max(I_str(Vn, R20) + I_str(Vn, R19), 0.5), gap) - Vn, 1.0, Voc_s - 0.01)
    I20, I19 = I_str(Vn, R20), I_str(Vn, R19)
    return I20, I19, Varc(I20 + I19, gap)


def c2_one_string(R, gap, q, G=1.0):
    I = brentq(lambda I: N * V_mod_bypassed(I, q, G) - Varc(I, gap) - R * I, 0.6, q["Iph"] * G * 1.5 + 1)
    return I, Varc(I, gap)


def clamp(Vc, Vsrc, I, L):
    if Vc <= Vsrc:
        return f"Vc={Vc:.0f} V <= Vsrc={Vsrc:.1f} V: clamp conducts indefinitely, P={Vc*Isc:.0f} W"
    return f"Vc={Vc:.0f} V, Vsrc={Vsrc:.1f} V: t_off={L*I/(Vc-Vsrc)*1e6:.1f} us, E_clamp={0.5*L*I*I*Vc/(Vc-Vsrc):.3f} J"


def main():
    fits = {n: fit(n) for n in (1.0, 1.2, 1.4)}
    q = fits[1.2]
    print("== single-diode fits (fixed n; supervisor cross-check only) ==")
    for n, f in fits.items():
        print(f"n={n}: Iph={f['Iph']:.4f} A I0={f['I0']:.3e} A Rs={f['Rs']:.4f} ohm Rsh={f['Rsh']:.1f} ohm residual={f['residual']:.1e}")
    print("\n== arc law (fixture, uncalibrated) ==")
    for I in (0.5, 3.68, 9.2, Imp, Isc, 36.77):
        print(f"I={I:6.2f} A: Varc gap1/3/5 mm = {Varc(I,1):.2f}/{Varc(I,3):.2f}/{Varc(I,5):.2f} V, P(gap1)={Varc(I,1)*I:.0f} W")
    print("\n== C1 substring loop (SS2 of M15) ==")
    Voc_ss = Voc / NSS
    for T in (-10, 25, 70):
        vs = Voc_ss * (1 + kVoc * (T - 25))
        print(f"T={T:+d} C: Voc_ss={vs:.2f} V, loop max Voc_ss+Vf={vs+VF:.2f} V, Varc(Imin=0.5 A,gap1)={Varc(0.5,1):.2f} V -> sustain? {vs+VF>=Varc(0.5,1)}")
    print(f"P_arc bound (D2 off, V_arc<=Voc_ss+Vf) = (Voc_ss+Vf)*Isc = {(Voc_ss+VF)*Isc:.0f} W STC; "
          f"{(Voc_ss*(1+kVoc*-35)+VF)*Isc*(1+kIsc*-35):.0f} W at -10 C")
    print("\n== X-001: steady voltage across an opened SW-M-OUT (M15, S20) = |30*Voc(T) - V_node| ==")
    for lab, vnode in (("(a) node at Vmpp STC", Vmp_s), ("(a) node at MPPT window min 500 V", 500.0), ("(b) node 0 V", 0.0),
                       ("(c) parallel arc, node=30 V", 30.0), ("(c) bolted, node=0 V", 0.0)):
        print(f"{lab:36s}: STC {Voc_s - vnode:7.1f} V | S20 at -10 C {Voc_s_cold - vnode:7.1f} V")
    print(f"(a) both strings at -10 C, node at cold Vmpp {Vmp_s*(1+kVoc*-35):.1f} V: {Voc_s_cold - Vmp_s*(1+kVoc*-35):.1f} V  (Vmpp scaled by Voc coeff: ASSUMED)")
    print(f"inverter relay open, S19 lit at Voc: |Voc_20-Voc_19| = 0 V same conditions; S19 at 200 W/m2: {N*q['n']*Ns*VT*math.log(5):.0f} V; S20 -10 C vs S19 25 C: {Voc_s_cold-Voc_s:.1f} V")
    print(f"SW-SS (inside bypass loop, forward current, D2 healthy): Voc_ss+Vf = {Voc_ss+VF:.2f} V STC, {Voc_ss*(1+kVoc*-35)+VF:.2f} V at -10 C")
    print(f"SW-SS under reverse feed or D2 open: reverts to SW-M-OUT class (up to {Voc_s_cold:.1f} V)")
    print("\n== cable / loop ==")
    print(f"L_ext ln-form {L_ext*1e6:.3f} uH/m (acosh-form {L_ext_acosh*1e6:.3f}, diff {100*(L_ext-L_ext_acosh)/L_ext_acosh:.1f} %), C {C_line*1e12:.1f} pF/m, Z0 {Z0:.0f} ohm, v {v:.4g} m/s, delay 936 m {936/v*1e6:.3f} us")
    print(f"L_hr(936 m) {L_hr*1e3:.3f} mH; L_row({ROW_RETURN_LENGTH_M:.0f} m at 1 m sep, ASSUMED) {L_row*1e3:.3f} mH; L_loop {L_loop*1e3:.3f} mH")
    print(f"R loop 936/931/600/5 m: {R_loop(936):.3f}/{R_loop(931):.3f}/{R_loop(600):.3f}/{R_loop(5):.4f} ohm; string internal {R_str:.3f} ohm; 936 m drift per 30 K {R_loop(936)*c['field_cable']['temp_coeff_per_c']*30:.3f} ohm")
    print(f"lumped-model validity (lambda/10 on loop 2x936 m): f < {v/(10*2*936):.0f} Hz; one-way lambda/10: {v/(10*936):.0f} Hz")
    print("\n== stored energies ==")
    print(f"0.5*L*I^2: home-run 936 m at 18.4 A = {0.5*L_hr*Isc**2:.4f} J (external only {0.5*L_ext*936*Isc**2:.4f} J); full loop at 17.31 A = {0.5*L_loop*Imp**2:.4f} J, at 18.4 A = {0.5*L_loop*Isc**2:.4f} J")
    print(f"0.5*C*V^2: C_in {Cin*1e6:.0f} uF at Vmpp {0.5*Cin*Vmp_s**2:.1f} J (range {0.5*5e-5*Vmp_s**2:.1f}-{0.5*5e-4*Vmp_s**2:.1f} J), at Voc STC {0.5*Cin*Voc_s**2:.1f} J, at Voc cold {0.5*Cin*Voc_s_cold**2:.1f} J")
    print(f"           DC link {Cdc*1e3:.0f} mF at Vmpp {0.5*Cdc*Vmp_s**2:.0f} J (range {0.5*1e-3*Vmp_s**2:.0f}-{0.5*4e-3*Vmp_s**2:.0f} J); line C 936 m {0.5*C_line*936*Vmp_s**2:.4f} J")
    print(f"unclamped L*dI/dt for 1 us turn-off of 17.31 A in L_loop: {L_loop*Imp/1e-6/1e3:.1f} kV")
    print("\n== X-002: C2 parallel arc operating points (STC, gap 1 mm, n=1.2 fit) ==")
    I20, I19, Va = c2_two_strings(R_loop(5) + R_str, R_loop(931) + R_loop(600) + R_str, 1.0, q)
    print(f"C2-far P0 pre-trip: I20={I20:.2f} A, I19={I19:.2f} A, Iarc={I20+I19:.2f} A, Varc={Va:.1f} V, Parc={Va*(I20+I19):.0f} W, node at inverter ~{Va+R_loop(931)*I19:.0f} V")
    I, Va = c2_one_string(R_loop(5) + R_str, 1.0, q)
    print(f"C2-far after SW-STR-INV opens (S20 modules only): I={I:.2f} A ({100*I/Isc:.2f} % of Isc), Varc={Va:.1f} V, Parc={Va*I:.0f} W")
    I, Va = c2_one_string(R_loop(931) + R_loop(600) + R_str, 1.0, q)
    print(f"C2-far after SW-STR-ARR opens (S19 via node + 931 m): I={I:.2f} A, Varc={Va:.1f} V, Parc={Va*I:.0f} W, cable loss {I*I*(R_loop(931)+R_loop(600)):.0f} W")
    I20, I19, Va = c2_two_strings(R_loop(931) + R_str, R_loop(5) + R_loop(600) + R_str, 1.0, q)
    print(f"C2-near P0 pre-trip: Iarc={I20+I19:.2f} A, Varc={Va:.1f} V, Parc={Va*(I20+I19):.0f} W")
    I, Va = c2_one_string(R_loop(931) + R_str, 1.0, q)
    print(f"C2-near after SW-STR-INV opens (S20 modules via 931 m): I={I:.2f} A, Varc={Va:.1f} V, Parc={Va*I:.0f} W, cable loss {I*I*R_loop(931):.0f} W")
    for G in (0.5, 0.2):
        I, Va = c2_one_string(R_loop(5) + R_str, 1.0, q, G)
        print(f"single-string residual at G={G*1000:.0f} W/m2: I={I:.2f} A, Varc={Va:.1f} V, Parc={Va*I:.0f} W")
    print(f"module V at 1.1 V gives I/Isc = {I_of_V(1.1,q)/Isc:.5f} (current-source approximation error {100*(1-I_of_V(1.1,q)/Isc):.3f} %)")
    print(f"extinction by law needs I<0.5 A: G < {0.5/Isc*1000:.0f} W/m2 (ILLUSTRATIVE)")
    L931, L5 = (L_ext + L_int) * 931, (L_ext + L_int) * 5
    dQ = Cin * (Vmp_s - 147.6)
    print(f"C_in into far arc: released {0.5*Cin*(Vmp_s**2-147.6**2):.1f} J, charge {dQ:.3f} C, at 30 V arc -> {30*dQ:.1f} J to arc, rest in 931 m R; zeta={(R_loop(931)/2)*math.sqrt(Cin/L931):.2f}, RC={R_loop(931)*Cin*1e3:.2f} ms, Ipk~{(Vmp_s-147.6)/R_loop(931):.0f} A")
    print(f"C_in into near arc: {0.5*Cin*Vmp_s**2:.0f} J, Z_surge={math.sqrt(L5/Cin):.3f} ohm, Ipk bound {(Vmp_s-30)/math.sqrt(L5/Cin):.0f} A, zeta(cable only)={(R_loop(5)/2)*math.sqrt(Cin/L5):.2f}, LC period {2*math.pi*math.sqrt(L5*Cin)*1e6:.0f} us, arc floor at 30 V {30*Cin*(Vmp_s-31):.1f} J")
    print(f"DC link (V_DIRECTBUS) into near arc: {0.5*Cdc*Vmp_s**2:.0f} J, Z_surge={math.sqrt(L5/Cdc):.3f} ohm, Ipk bound {(Vmp_s-30)/math.sqrt(L5/Cdc):.0f} A, floor {30*Cdc*(Vmp_s-31):.0f} J")
    print(f"travelling-wave current step at inverter end, far arc: (Vmpp-Varc)/Z0 = {(Vmp_s-31.6)/Z0:.1f} A per transit, arrives {931/v*1e6:.2f} us after inception")
    print("\n== backfeed through a series arc in a DARK S20 (gap 1 mm) ==")
    for n, f in fits.items():
        I_night = brentq(lambda I: N * V_dark(I, f) - Vmp_s, 1e-7, 60)
        I_voc = brentq(lambda I: N * V_dark(I, f) - Voc_s, 1e-7, 60)
        try:
            I_bf = brentq(lambda I: N * V_of_I(I, f) - Varc(I, 1.0) - N * V_dark(I, f), 0.5, 18.0)
        except ValueError:
            I_bf = 0.0
        print(f"n={n}: node held at Vmpp -> {I_night:.2f} A; node at Voc_STC (stiff) -> {I_voc:.1f} A; S19 lit (STC) into dark S20 + arc, inverter off -> {I_bf:.2f} A at Varc {Varc(max(I_bf,0.5),1):.1f} V = {I_bf*Varc(max(I_bf,0.5),1):.0f} W")
    print("\n== SW-M-OUT clamp energy / turn-off time (I=17.31 A, L_loop) ==")
    for Vc, Vsrc in ((600, Voc_s - Vmp_s), (1200, Voc_s - Vmp_s), (1200, Voc_s - 30), (1500, Voc_s - 30), (1500, Voc_s_cold - 30)):
        print(clamp(Vc, Vsrc, Imp, L_loop))
    print("\n== SW-STR-INV clamp (931 m loop of S20, 18.4 A) ==")
    for lab, Vsrc in (("node at Vmpp", Vmp_s - 30), ("node at Voc STC", Voc_s - 30), ("node at Voc cold", Voc_s_cold - 30)):
        print(lab + ": " + clamp(1500, Vsrc, Isc, L931))
    print("\n== C3 hot connector (I=17.31 A, lumped thermal: C=8 J/K, G=0.25 W/K, ambient 35 C; ASSUMED) ==")
    th = FX["priority_cases"]["C3"]["thermal"]
    Gth, Cth, Ta = th["connector_to_ambient_w_per_k"]["value"], th["connector_thermal_mass_j_per_k"]["value"], th["ambient_c"]
    for R in FX["priority_cases"]["C3"]["resistance_variants_ohm"]:
        P = Imp ** 2 * R
        print(f"R={R:.2f} ohm: P={P:.1f} W, dV={Imp*R:.2f} V ({100*Imp*R/Vmp_s:.2f} % of Vmpp_string), dT_ss={P/Gth:.0f} K -> {Ta+P/Gth:.0f} C, E(3600 s)={P*3.6:.0f} kJ; tau={Cth/Gth:.0f} s")
    print(f"cable thermal drift signature for comparison: {R_loop(936)*c['field_cable']['temp_coeff_per_c']*30*Imp:.1f} V per 30 K on the 936 m route")
    sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    print(f"\nSCRIPT_SHA256 {sha}")


if __name__ == "__main__":
    main()
