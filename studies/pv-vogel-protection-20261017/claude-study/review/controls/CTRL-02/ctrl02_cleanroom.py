"""CTRL-02 clean-room recomputation (Phase 1) of the quantities claimed by the Track C (SUP-C) charter.

Written WITHOUT opening review/supc-calcs/track_c_calcs.py or any SUP-C result file.
Inputs: ONLY claude-study/fixture/system-fixture.json plus the control assumptions listed in ASSUMED below.
Run from claude-study/:   python3 -I review/controls/CTRL-02/ctrl02_cleanroom.py
Deterministic (no random numbers, no wall-clock values in the results). SI units throughout.
Evidence grade of every number: algebra (the C2 ODE cross-check is illustrative_simulation of a lumped model).
Not modelled: arc physics beyond the uncalibrated fixture law, HF impedance of the string, skin/proximity effect
(except the optional estimate flagged as such), inverter control during the fault, cable temperature profile.
"""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.integrate import quad, solve_ivp
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
STUDY = HERE.parents[2]  # claude-study/
FIXTURE = STUDY / "fixture" / "system-fixture.json"
OUT = HERE / "clean-room-results.json"

FX = json.loads(FIXTURE.read_text())
MOD = FX["module"]
PLANT = FX["plant"]
COND = FX["conductors"]
LINE = COND["two_wire_line_defaults"]
INV = FX["inverter_dc_side"]
ARC = FX["arc_model"]
C3 = FX["priority_cases"]["C3"]

K_B = 1.380649e-23   # J/K (SI exact)
Q_E = 1.602176634e-19  # C (SI exact)
C0 = 299792458.0     # m/s (SI exact)

N_MOD = PLANT["modules_per_string"]                 # 30
VMPP_MOD, IMPP = MOD["vmpp_v"], MOD["impp_a"]        # 38.13 V, 17.31 A
VOC_MOD, ISC = MOD["voc_stc_v"], MOD["isc_a"]        # 45.75 V, 18.4 A
BETA_VOC = MOD["voc_temp_coeff_per_c"]               # -0.0024 /K
NS_CELLS = MOD["single_diode_fit"]["cells_in_series_total"]  # 66
N_SUB = MOD["internal_structure"]["substrings_per_module"]   # 3
VF_BYP = 0.45  # V, fixture text "Schottky_assumed_Vf_0p45_V_at_17A" (A-032)
VMPP_STR = PLANT["string_derived"]["vmpp_string_v"]  # 1143.9 V
VOC_STR = PLANT["string_derived"]["voc_string_stc_v"]  # 1372.5 V
R_FIELD_PER_M = COND["field_cable"]["resistance_ohm_per_km_20c"] / 1000.0  # ohm/m per conductor
ALPHA_CU = COND["field_cable"]["temp_coeff_per_c"]   # 0.00393 /K
R_LEAD_PER_M = COND["factory_lead"]["resistance_ohm_per_km_20c"] / 1000.0
R_CONN = COND["connector_resistance_ohm_each"]
N_MATES = COND["mated_interfaces_per_string"]["total"]
ROUTES = sorted(set(COND["route_lengths_m"]))         # [78, 200, 300, 600, 936]
EPSR = COND["effective_relative_permittivity"]       # 2.0
L_EXT_PER_M = LINE["loop_external_inductance_uh_per_m_approx"] * 1e-6
L_INT_PER_M = LINE["loop_internal_inductance_dc_uh_per_m_approx"] * 1e-6
C_PER_M = LINE["line_capacitance_pf_per_m_approx"] * 1e-12
C_IN = INV["mppt_input_capacitance_f"]["value"]      # 150 uF
S_O_A, S_O_B, S_O_EXP = 20.0, 0.534, 0.12            # fixture static_vi_law constants
I_MIN_ARC = ARC["minimum_sustaining_current_a"]["value"]
ROUTE_S20 = FX["priority_cases"]["C2"]["string_route_m"]["S20"]  # 936
ROUTE_S19 = FX["priority_cases"]["C2"]["string_route_m"]["S19"]  # 600
C2_FAR_DIST = 931.0  # m from inverter, fixture C2-far text "931 m from inverter"
TH = C3["thermal"]
C_TH = TH["connector_thermal_mass_j_per_k"]["value"]  # 8 J/K
H_TH = TH["connector_to_ambient_w_per_k"]["value"]    # 0.25 W/K
T_AMB = TH["ambient_c"]                               # 35 C
R_C3 = C3["resistance_variants_ohm"]                  # [0.05, 0.2, 1.0]

ASSUMED = {
    "cell_temperature_for_fit_k": {"value": 298.15, "label": "ASSUMED (STC)"},
    "ideality_factor_band": {"value": [1.0, 1.1, 1.2, 1.3], "label": "ASSUMED control band; no datasheet IV curve"},
    "drift_k": {"value": [40.0, 20.0], "label": "ASSUMED (A-024 40 K SUP-C; A-033 20 K SUP-E)"},
    "c2_inverter_draw_after_fault_a": {"value": 0.0, "label": "ASSUMED (node collapses below 500 V window)"},
    "c2_string_sources": {"value": "ideal 18.4 A current sources (both strings at Isc)", "label": "ASSUMED per task"},
    "connector_limit_c": {"value": [150, 200], "label": "ASSUMED (A-043 / A-034)"},
    "v_clamp_v": {"value": [400, 600, 800, 1000, 1200, 1400, 1600], "label": "ASSUMED sweep per task"},
}


def r3(x, n=6):
    return float(f"{x:.{n}g}")


# ---------------------------------------------------------------- single-diode fit (control-only, not pv_module.py)
def sd_fit(n_ideal, t_k=298.15):
    a = n_ideal * NS_CELLS * K_B * t_k / Q_E

    def iph_i0(rs, rsh):
        i0 = (ISC - (VOC_MOD - ISC * rs) / rsh) / (math.exp(VOC_MOD / a) - math.exp(ISC * rs / a))
        iph = i0 * (math.exp(VOC_MOD / a) - 1.0) + VOC_MOD / rsh
        return iph, i0

    def f_mpp(rs, rsh):
        iph, i0 = iph_i0(rs, rsh)
        vd = VMPP_MOD + IMPP * rs
        return iph - i0 * (math.exp(vd / a) - 1.0) - vd / rsh - IMPP

    def rsh_of(rs):
        g = lambda lr: f_mpp(rs, math.exp(lr))
        lo, hi = 0.0, math.log(1e9)
        if g(lo) * g(hi) > 0:
            return None
        return math.exp(brentq(g, lo, hi, xtol=1e-14, rtol=1e-14))

    def mpp_slope_resid(rs):
        rsh = rsh_of(rs)
        iph, i0 = iph_i0(rs, rsh)
        vd = VMPP_MOD + IMPP * rs
        g = i0 / a * math.exp(vd / a) + 1.0 / rsh
        return IMPP - VMPP_MOD * g / (1.0 + rs * g)

    prev = None
    root = None
    for k in range(1, 600):
        rs = k * 1e-3
        if rsh_of(rs) is None:
            continue
        d = mpp_slope_resid(rs)
        if prev is not None and prev[1] * d < 0:
            root = brentq(mpp_slope_resid, prev[0], rs, xtol=1e-15, rtol=1e-15)
            break
        prev = (rs, d)
    if root is None:
        return None
    rs = root
    rsh = rsh_of(rs)
    iph, i0 = iph_i0(rs, rsh)
    return {"n": n_ideal, "a_v": a, "iph_a": iph, "i0_a": i0, "rs_ohm": rs, "rsh_ohm": rsh}


def mod_i(v, p):
    f = lambda i: p["iph_a"] - p["i0_a"] * (math.exp((v + i * p["rs_ohm"]) / p["a_v"]) - 1.0) - (v + i * p["rs_ohm"]) / p["rsh_ohm"] - i
    return brentq(f, -100.0, p["iph_a"] + 5.0, xtol=1e-14, rtol=1e-14)


def mod_v(i, p):
    f = lambda v: p["iph_a"] - p["i0_a"] * (math.exp((v + i * p["rs_ohm"]) / p["a_v"]) - 1.0) - (v + i * p["rs_ohm"]) / p["rsh_ohm"] - i
    return brentq(f, -50.0, VOC_MOD + 10.0, xtol=1e-14, rtol=1e-14)


def fit_residuals(p):
    i_sc = mod_i(0.0, p)
    v_oc = mod_v(0.0, p)
    i_mp = mod_i(VMPP_MOD, p)
    dv = 1e-4
    dp = ((VMPP_MOD + dv) * mod_i(VMPP_MOD + dv, p) - (VMPP_MOD - dv) * mod_i(VMPP_MOD - dv, p)) / (2 * dv)
    return {"isc_rel": (i_sc - ISC) / ISC, "voc_rel": (v_oc - VOC_MOD) / VOC_MOD,
            "impp_rel": (i_mp - IMPP) / IMPP, "dpdv_at_vmpp_a": dp}


# ---------------------------------------------------------------- derived line/loop constants
def loop_r(route_m, length_override=None):
    l = route_m if length_override is None else length_override
    return 2.0 * l * R_FIELD_PER_M


R_LOOP_S20 = loop_r(ROUTE_S20)                       # 6.3461 ohm
R_LOOP_S19 = loop_r(ROUTE_S19)
R_LOOP_S20_931 = loop_r(ROUTE_S20, C2_FAR_DIST)
L_LOOP_S20 = (L_EXT_PER_M + L_INT_PER_M) * ROUTE_S20  # 0.66737 mH
L_LOOP_S20_HF = L_EXT_PER_M * ROUTE_S20               # internal inductance removed (HF)
V_PHASE = C0 / math.sqrt(EPSR)
Z0 = math.sqrt(L_EXT_PER_M / C_PER_M)
R_LEADS = N_MOD * (MOD["internal_structure"]["positive_lead_m"] + MOD["internal_structure"]["negative_lead_m"]) * R_LEAD_PER_M
R_MATES = N_MATES * R_CONN

res = {"control_id": "CTRL-02", "phase": 1, "fixture_sha256": hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
       "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "assumed": ASSUMED,
       "grade": "algebra unless stated", "derived_constants": {
           "r_loop_s20_936m_ohm": R_LOOP_S20, "r_loop_s20_931m_ohm": R_LOOP_S20_931, "r_loop_s19_600m_ohm": R_LOOP_S19,
           "l_loop_s20_dc_h": L_LOOP_S20, "l_loop_s20_hf_ext_only_h": L_LOOP_S20_HF,
           "v_phase_m_per_s": V_PHASE, "z0_lossless_ohm": Z0, "r_module_leads_string_ohm": R_LEADS,
           "r_33_mates_ohm": R_MATES}}

# ---------------------------------------------------------------- C1 series-arc current dip
r_dyn_mod_exact = VMPP_MOD / IMPP          # |dV/dI| at MPP from dP/dV = 0 (model independent)
r_dyn_str_exact = N_MOD * r_dyn_mod_exact  # = VMPP_STR / IMPP
v_arcs = [20.0, 40.0, 60.0]
c1 = {"method_note": "node (MPPT input, held by C_in) fixed at its pre-fault value during the dip; string modules identical and uniformly lit; "
                     "arc OUTSIDE any bypass loop so all cells keep the string current (see in-loop cap: an in-SS2 arc cannot exceed Voc_ss+Vf)",
      "r_dyn_module_exact_ohm": r_dyn_mod_exact, "r_dyn_string_exact_ohm": r_dyn_str_exact,
      "r_dyn_label": "DERIVED exact small-signal value at MPP (dP/dV=0 gives dV/dI=-V/I); valid for any smooth IV curve",
      "linear_no_cable": {}, "linear_with_s20_loop": {}, "sdm_large_signal": {}}
r_series_extra = R_LOOP_S20 + R_LEADS + R_MATES
for va in v_arcs:
    di0 = va / r_dyn_str_exact
    di1 = va / (r_dyn_str_exact + r_series_extra)
    c1["linear_no_cable"][f"{va:g}"] = {"di_a": di0, "di_frac_of_impp": di0 / IMPP}
    c1["linear_with_s20_loop"][f"{va:g}"] = {"di_a": di1, "di_frac_of_impp": di1 / IMPP, "r_total_ohm": r_dyn_str_exact + r_series_extra}

fits = {}
for n in ASSUMED["ideality_factor_band"]["value"]:
    p = sd_fit(n)
    if p is None:
        continue
    fr = fit_residuals(p)
    entry = {"params": p, "residuals": fr, "dip": {}}
    for va in v_arcs:
        # (i) string terminal voltage forced to Vmpp_string + V_arc (no cable)
        i_new = mod_i(VMPP_MOD + va / N_MOD, p)
        # (ii) node fixed at Vmpp_string - Impp*R_series (pre-fault), cable/leads/mates in the loop
        v_node = VMPP_STR - IMPP * r_series_extra
        g = lambda i: N_MOD * mod_v(i, p) - (v_node + i * r_series_extra + va)
        i_new2 = brentq(g, IMPP - 6.0, IMPP + 0.5, xtol=1e-13)  # bracket kept below Iph so mod_v stays valid
        entry["dip"][f"{va:g}"] = {"no_cable_di_a": IMPP - i_new, "with_loop_di_a": IMPP - i_new2}
    fits[f"{n:g}"] = entry
c1["sdm_large_signal"] = fits
# Maximum DC dip an IN-LOOP (SS2) arc can cause: once V_arc > V_ss(I)+Vf the bypass diode D2 conducts and the
# string loses at most one substring (Vss -> -Vf). Node held at Vmpp_string, no cable (SDM n=1.1) and linear.
p11 = fits["1.1"]["params"]
g_byp = lambda i: (N_MOD - 1) * mod_v(i, p11) + (N_SUB - 1) / N_SUB * mod_v(i, p11) - VF_BYP - VMPP_STR
i_byp = brentq(g_byp, IMPP - 6.0, IMPP + 0.5, xtol=1e-13)
c1["inloop_max_dip_bypassed_substring"] = {"sdm_n1p1_di_a": IMPP - i_byp,
                                           "linear_di_a": (VMPP_MOD / N_SUB + VF_BYP) / r_dyn_str_exact,
                                           "equivalent_v_step_v": VMPP_MOD / N_SUB + VF_BYP}
# MPPT/mismatch context (A-022, A-023): small-signal current change for a 1-2 % Vmpp step and 3 % mismatch
c1["context_mppt_step_di_a"] = {f"{s:g}": s * VMPP_STR / r_dyn_str_exact for s in (0.01, 0.02)}
c1["context_mismatch_3pct_a"] = 0.03 * IMPP
res["C1_dip"] = c1

# ---------------------------------------------------------------- C1 in-loop voltage cap
def voc_mod_at(tc):
    return VOC_MOD * (1.0 + BETA_VOC * (tc - 25.0))


cap = {}
for tc in (25.0, -10.0, 70.0):
    voc_ss = voc_mod_at(tc) / N_SUB
    cap[f"{tc:g}"] = {"voc_module_v": voc_mod_at(tc), "voc_ss_v": voc_ss, "cap_v": voc_ss + VF_BYP}
so_min = {f"{g:g}": (S_O_A + S_O_B * g) * I_MIN_ARC ** S_O_EXP for g in ARC["gap_mm_variants"]}
res["C1_inloop_cap"] = {"cap_by_temp_c": cap, "vmpp_ss_v": VMPP_MOD / N_SUB, "bypass_onset_at_impp_v": VMPP_MOD / N_SUB + VF_BYP,
                        "s_o_voltage_at_i_min_v": so_min,
                        "note": "fixture S-O law needs >= 18.9 V at I_min 0.5 A (1 mm); cap <= 16.98 V at -10 C -> no steady in-loop solution under the fixture law (illustrative, uncalibrated)"}

# ---------------------------------------------------------------- HF current per volt, 936 m loop (lumped, as specified)
hf = {"inputs": {"L_h": 0.667e-3, "R_ohm": 6.35, "L_exact_h": L_LOOP_S20, "R_exact_ohm": R_LOOP_S20}, "lumped": {}, "lumped_hf_L_ext_only": {}, "distributed_lossless": {}}
for f in (1e4, 1e5, 1e6):
    w = 2 * math.pi * f
    z = math.hypot(6.35, w * 0.667e-3)
    hf["lumped"][f"{f:g}"] = {"absZ_ohm": z, "a_per_v": 1.0 / z}
    z2 = math.hypot(R_LOOP_S20, w * L_LOOP_S20_HF)
    hf["lumped_hf_L_ext_only"][f"{f:g}"] = {"absZ_ohm": z2, "a_per_v": 1.0 / z2}
    bl = w * ROUTE_S20 / V_PHASE
    # lossless line, inverter end shorted by C_in at HF, arc-noise source at array end with zero source impedance
    zin = abs(Z0 * math.tan(bl))
    i_inv = 1.0 / abs(Z0 * math.sin(bl))
    hf["distributed_lossless"][f"{f:g}"] = {"beta_l_rad": bl, "length_over_lambda": ROUTE_S20 * f / V_PHASE,
                                            "array_end_a_per_v": 1.0 / zin, "inverter_end_a_per_v": i_inv}
# lossy line with an ASSUMED round-wire skin-effect factor R_ac/R_dc = max(1, r/(2 delta) + 1/4), proximity ignored,
# inverter end shorted (C_in), zero source impedance. Control extension, not a fixture value.
RHO_EFF = COND["field_cable"]["resistance_ohm_per_km_20c"] / 1000.0 * COND["field_cable"]["area_mm2"] * 1e-6
MU0 = 4e-7 * math.pi
r_wire = LINE["conductor_radius_6mm2_m"]
for f in (1e4, 1e5, 1e6):
    w = 2 * math.pi * f
    delta = math.sqrt(RHO_EFF / (math.pi * f * MU0))
    k_skin = max(1.0, r_wire / (2 * delta) + 0.25)
    zser = 2 * R_FIELD_PER_M * k_skin + 1j * w * L_EXT_PER_M
    yshu = 1j * w * C_PER_M
    gam = complex(np.sqrt(zser * yshu))
    z0c = complex(np.sqrt(zser / yshu))
    zin = z0c * complex(np.tanh(gam * ROUTE_S20))
    i_far = abs(1.0 / (z0c * complex(np.sinh(gam * ROUTE_S20))))
    hf.setdefault("lossy_skin_assumed", {})[f"{f:g}"] = {"skin_depth_m": delta, "rac_over_rdc": k_skin,
                                                          "absZin_ohm": abs(zin), "array_end_a_per_v": 1.0 / abs(zin),
                                                          "inverter_end_a_per_v": i_far}
res["HF_per_volt_936m"] = hf

# ---------------------------------------------------------------- quarter-wave frequencies
res["quarter_wave_hz"] = {str(l): {"f_qw_hz": V_PHASE / (4.0 * l), "f_3qw_hz": 3 * V_PHASE / (4.0 * l), "f_halfwave_hz": V_PHASE / (2.0 * l)} for l in ROUTES}

# ---------------------------------------------------------------- C2-far steady state (both strings at Isc, 40 V arc)
V_ARC_C2 = 40.0
c2 = {}
for tag, r in (("936m", R_LOOP_S20), ("931m", R_LOOP_S20_931)):
    v_node = V_ARC_C2 + ISC * r
    c2[tag] = {"r_home_ohm": r, "v_node_v": v_node, "i_arc_a": 2 * ISC, "i_s20_homerun_a_toward_arc": ISC,
               "i_s20_modules_a": ISC, "i_s19_a": ISC, "v_s19_terminal_v": v_node + ISC * R_LOOP_S19,
               "inverter_end_swing_from_impp_a": IMPP + ISC, "inverter_end_swing_from_isc_a": 2 * ISC}
res["C2_far_steady"] = c2

# ---------------------------------------------------------------- C_in energy fraction to a 40 V arc
e_cin = 0.5 * C_IN * VMPP_STR ** 2
frac = {"e_cin_j": e_cin,
        "full_discharge_Q_CV0": {"q_c": C_IN * VMPP_STR, "e_arc_j": V_ARC_C2 * C_IN * VMPP_STR, "fraction": V_ARC_C2 * C_IN * VMPP_STR / e_cin},
        "to_v_arc_Q_C(V0-Varc)": {"q_c": C_IN * (VMPP_STR - V_ARC_C2), "e_arc_j": V_ARC_C2 * C_IN * (VMPP_STR - V_ARC_C2),
                                  "fraction": V_ARC_C2 * C_IN * (VMPP_STR - V_ARC_C2) / e_cin}}
for tag in ("936m", "931m"):
    vf = c2[tag]["v_node_v"]
    q = C_IN * (VMPP_STR - vf)
    frac[f"to_steady_node_{tag}"] = {"v_final_v": vf, "q_c": q, "e_arc_j": V_ARC_C2 * q, "fraction": V_ARC_C2 * q / e_cin,
                                     "e_cin_released_j": 0.5 * C_IN * (VMPP_STR ** 2 - vf ** 2)}
res["Cin_fraction_40V"] = frac


# ---------------------------------------------------------------- C2-far 5 s energies (S-O law 1 mm)
def v_so(i, gap=1.0):
    return (S_O_A + S_O_B * gap) * i ** S_O_EXP


e5 = {"both_steady_j": 5.0 * v_so(2 * ISC) * 2 * ISC, "v_arc_both_v": v_so(2 * ISC),
      "s20_alone_j": 5.0 * v_so(ISC) * ISC, "v_arc_s20_v": v_so(ISC)}
e5["ratio_s20_over_both"] = e5["s20_alone_j"] / e5["both_steady_j"]
e5["ratio_closed_form_0p5_pow_1p12"] = 0.5 ** (1 + S_O_EXP)


# lumped ODE cross-check incl. C_in discharge and S20 home-run L/R (illustrative_simulation)
def c2_ode(r_home, l_home, arc_fn, t_end=5.0):
    i_s19, i_s20 = ISC, ISC

    def rhs_e(t, y):
        vc, il, e_arc, q_arc, e_r = y
        ia = il + i_s20
        va = arc_fn(max(ia, 1e-9))
        return [(i_s19 - il) / C_IN, (vc - r_home * il - va) / l_home, va * ia, ia, r_home * il * il]

    y0 = [VMPP_STR, -IMPP, 0.0, 0.0, 0.0]  # pre-fault: S20 home-run carries Impp toward the inverter
    sol = solve_ivp(rhs_e, (0.0, t_end), y0, method="Radau", rtol=1e-10, atol=[1e-6, 1e-9, 1e-6, 1e-9, 1e-6],
                    dense_output=True, first_step=1e-9, max_step=0.05)
    vc, il, e_arc, q_arc, e_r = sol.y[:, -1]
    # minimum arc current and peak current over the transient
    tt = np.concatenate([np.linspace(0, 0.02, 20001), np.linspace(0.02, t_end, 2001)])
    yy = sol.sol(tt)
    ia = yy[1] + i_s20
    return {"e_arc_j": e_arc, "q_arc_c": q_arc, "v_node_end_v": vc, "i_home_end_a": il, "e_r_home_j": e_r,
            "i_arc_min_a": float(ia.min()), "i_arc_peak_a": float(ia.max()), "t_peak_s": float(tt[int(ia.argmax())]),
            "nfev": int(sol.nfev), "status": int(sol.status)}


ode40 = c2_ode(R_LOOP_S20_931, (L_EXT_PER_M + L_INT_PER_M) * C2_FAR_DIST, lambda i: V_ARC_C2)
odeSO = c2_ode(R_LOOP_S20_931, (L_EXT_PER_M + L_INT_PER_M) * C2_FAR_DIST, lambda i: v_so(i))
e5["ode_const40V_931m"] = ode40
e5["ode_const40V_cin_part_j"] = ode40["e_arc_j"] - V_ARC_C2 * 2 * ISC * 5.0
e5["ode_SO1mm_931m"] = odeSO
e5["ode_SO1mm_minus_steady_j"] = odeSO["e_arc_j"] - e5["both_steady_j"]
res["C2_far_5s_energy"] = e5

# ---------------------------------------------------------------- C3 hot connector
c3 = {"i_a": IMPP, "variants": {}}
drdt_936 = R_LOOP_S20 * ALPHA_CU
c3["cable_drdt_936m_ohm_per_k"] = drdt_936
c3["cable_drdt_by_route_ohm_per_k"] = {str(l): loop_r(l) * ALPHA_CU for l in ROUTES}
for r in R_C3:
    dv = IMPP * r
    p_w = IMPP ** 2 * r
    v = {"dv_v": dv, "p_w": p_w, "dT_steady_k": p_w / H_TH, "T_steady_c": T_AMB + p_w / H_TH}
    for dk in ASSUMED["drift_k"]["value"]:
        v[f"ratio_vs_{dk:g}K_drift_936m"] = r / (drdt_936 * dk)
        v[f"ratio_vs_{dk:g}K_drift_by_route"] = {str(l): r / (loop_r(l) * ALPHA_CU * dk) for l in ROUTES}
    # first-order string current reduction if MPPT holds the node (linear, exact R_dyn)
    v["di_if_node_held_a"] = dv / (r_dyn_str_exact + r_series_extra + r)
    c3["variants"][f"{r:g}"] = v
c3["drift_40K_dv_at_impp_936m_v"] = IMPP * drdt_936 * 40.0
c3["tau_s"] = C_TH / H_TH


# time to limit under the fixture ramp (R from 0.35 mOhm to R_f over 600 s, then constant), lumped C_th/h
def theta_ramp(t, r_f, i=IMPP, r0=R_CONN, t_r=600.0):
    tau = C_TH / H_TH
    k = (r_f - r0) / t_r
    g = i * i / H_TH
    if t <= t_r:
        return g * (r0 + k * (t - tau + tau * math.exp(-t / tau)))
    th_r = g * (r0 + k * (t_r - tau + tau * math.exp(-t_r / tau)))
    th_ss = g * r_f
    return th_ss + (th_r - th_ss) * math.exp(-(t - t_r) / tau)


ttl = {}
for r in R_C3:
    row = {}
    for lim in ASSUMED["connector_limit_c"]["value"]:
        dth = lim - T_AMB
        if theta_ramp(1e5, r) < dth:
            row[f"{lim}"] = None
        else:
            row[f"{lim}"] = brentq(lambda t: theta_ramp(t, r) - dth, 0.0, 1e5, xtol=1e-9)
    ttl[f"{r:g}"] = row
c3["time_to_limit_s_under_600s_ramp"] = ttl
res["C3"] = c3

# ---------------------------------------------------------------- commutation time L*I/V_clamp
com = {"L_h_task": 0.667e-3, "L_h_exact": L_LOOP_S20, "rows": {}}
for vcl in ASSUMED["v_clamp_v"]["value"]:
    com["rows"][str(vcl)] = {
        "t_s_impp_L0p667mH": 0.667e-3 * IMPP / vcl,
        "t_s_isc_L0p667mH": 0.667e-3 * ISC / vcl,
        "t_s_impp_Lexact": L_LOOP_S20 * IMPP / vcl,
    }
# IV-aware first-order check (SW-STR-INV opening, node held by C_in at its pre-fault value, quasi-static string IV,
# string capacitance ignored): L dI/dt = -(V_clamp - (V_str(I) - R I - V_node)); the clamp interval ends only if
# V_clamp exceeds the open-circuit excess V_str(0) - V_node.
p_ref = fits["1.1"]["params"]
v_node_pre = VMPP_STR - IMPP * R_LOOP_S20
excess_oc = N_MOD * mod_v(0.0, p_ref) - v_node_pre
com["iv_aware"] = {"ideality_n": 1.1, "v_node_pre_v": v_node_pre, "open_circuit_excess_v": excess_oc, "rows": {}}
for vcl in ASSUMED["v_clamp_v"]["value"]:
    drive = lambda i: vcl - (N_MOD * mod_v(i, p_ref) - R_LOOP_S20 * i - v_node_pre)
    if drive(0.0) <= 0:
        i_hold = brentq(drive, 0.0, IMPP)
        com["iv_aware"]["rows"][str(vcl)] = {"t_s": None, "clamp_holds_current_a": i_hold,
                                             "clamp_power_w": vcl * i_hold}
        continue
    t_iv = quad(lambda i: L_LOOP_S20 / drive(i), 0.0, IMPP, limit=200, epsabs=1e-13, epsrel=1e-10)[0]
    e_cl = quad(lambda i: L_LOOP_S20 * vcl * i / drive(i), 0.0, IMPP, limit=200, epsabs=1e-12, epsrel=1e-10)[0]
    com["iv_aware"]["rows"][str(vcl)] = {"t_s": t_iv, "e_clamp_j": e_cl}
com["half_LI2_impp_j"] = 0.5 * L_LOOP_S20 * IMPP ** 2
com["half_LI2_isc_j"] = 0.5 * L_LOOP_S20 * ISC ** 2
com["round_trip_936m_s"] = 2 * ROUTE_S20 / V_PHASE
com["z0_step_v_at_impp"] = Z0 * IMPP
com["offstate_v_sw_str_inv"] = {"node_at_vmpp_stc_v": VOC_STR - VMPP_STR,
                                "node_at_0_stc_v": VOC_STR,
                                "node_at_0_cold_v": PLANT["string_derived"]["voc_string_cold_minus10c_v"]}
res["commutation"] = com

OUT.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")


def p(*a):
    print(*a)


p("fixture sha256", res["fixture_sha256"])
p("script sha256", res["script_sha256"])
p("R_loop S20 936 m %.5f ohm; 931 m %.5f; S19 600 m %.5f; L_loop S20 %.6e H (HF ext-only %.6e); Z0 %.3f; v %.1f" %
  (R_LOOP_S20, R_LOOP_S20_931, R_LOOP_S19, L_LOOP_S20, L_LOOP_S20_HF, Z0, V_PHASE))
p("R leads %.5f ohm, R 33 mates %.5f ohm" % (R_LEADS, R_MATES))
p("C1 R_dyn string exact %.4f ohm" % r_dyn_str_exact)
for va in v_arcs:
    k = f"{va:g}"
    s = "  V_arc %g: lin %.4f A (%.3f %%), lin+loop %.4f A" % (va, c1["linear_no_cable"][k]["di_a"], 100 * c1["linear_no_cable"][k]["di_frac_of_impp"], c1["linear_with_s20_loop"][k]["di_a"])
    for n, e in fits.items():
        s += " | SDM n=%s: %.4f / %.4f" % (n, e["dip"][k]["no_cable_di_a"], e["dip"][k]["with_loop_di_a"])
    p(s)
for n, e in fits.items():
    pr = e["params"]
    p("  fit n=%s Rs %.5f Rsh %.2f I0 %.3e Iph %.5f resid %s" % (n, pr["rs_ohm"], pr["rsh_ohm"], pr["i0_a"], pr["iph_a"],
      {k: float(f"{v:.2e}") for k, v in e["residuals"].items()}))
p("C1 cap", {k: round(v["cap_v"], 4) for k, v in cap.items()}, "S-O at I_min", {k: round(v, 3) for k, v in so_min.items()})
p("HF lumped", {k: round(v["a_per_v"] * 1e3, 4) for k, v in hf["lumped"].items()}, "mA/V")
p("HF lumped ext-L", {k: round(v["a_per_v"] * 1e3, 4) for k, v in hf["lumped_hf_L_ext_only"].items()}, "mA/V")
p("HF distributed", {k: (round(v["array_end_a_per_v"] * 1e3, 3), round(v["inverter_end_a_per_v"] * 1e3, 3), round(v["length_over_lambda"], 3)) for k, v in hf["distributed_lossless"].items()})
p("HF lossy+skin (ASSUMED)", {k: (round(v["rac_over_rdc"], 2), round(v["array_end_a_per_v"] * 1e3, 3), round(v["inverter_end_a_per_v"] * 1e3, 3)) for k, v in hf["lossy_skin_assumed"].items()})
p("C1 in-loop max dip", {k: round(v, 4) for k, v in c1["inloop_max_dip_bypassed_substring"].items()})
p("quarter-wave",{k: round(v["f_qw_hz"], 1) for k, v in res["quarter_wave_hz"].items()})
p("C2 steady", {k: (round(v["v_node_v"], 3), round(v["v_s19_terminal_v"], 2)) for k, v in c2.items()}, "swing", IMPP + ISC)
p("Cin fraction", {k: (round(v["e_arc_j"], 4), round(v["fraction"], 5)) for k, v in frac.items() if isinstance(v, dict)}, "E_Cin %.4f" % e_cin)
p("5 s: both %.2f J (V %.4f), S20 %.2f J (V %.4f), ratio %.5f" % (e5["both_steady_j"], e5["v_arc_both_v"], e5["s20_alone_j"], e5["v_arc_s20_v"], e5["ratio_s20_over_both"]))
p("ODE 40V", {k: (round(v, 5) if isinstance(v, float) else v) for k, v in ode40.items()}, "Cin part %.4f" % e5["ode_const40V_cin_part_j"])
p("ODE S-O", {k: (round(v, 5) if isinstance(v, float) else v) for k, v in odeSO.items()}, "minus steady %.4f" % e5["ode_SO1mm_minus_steady_j"])
p("C3", {k: (round(v["dv_v"], 4), round(v["p_w"], 3), round(v["dT_steady_k"], 2), round(v["ratio_vs_40K_drift_936m"], 4), round(v["ratio_vs_20K_drift_936m"], 4)) for k, v in c3["variants"].items()},
  "dR/dT %.6f" % drdt_936, "tau", c3["tau_s"])
p("C3 time-to-limit", ttl)
p("commutation", {k: (round(v["t_s_impp_L0p667mH"] * 1e6, 3), round(v["t_s_isc_L0p667mH"] * 1e6, 3)) for k, v in com["rows"].items()}, "us")
p("commutation IV-aware", "excess_oc %.2f V node %.2f V" % (com["iv_aware"]["open_circuit_excess_v"], v_node_pre),
  {k: (round(v["t_s"] * 1e6, 3) if v.get("t_s") else ("hold %.3f A" % v["clamp_holds_current_a"]), round(v.get("e_clamp_j", float("nan")), 4)) for k, v in com["iv_aware"]["rows"].items()},
  "1/2 L I^2 %.5f J" % com["half_LI2_impp_j"])
p("wrote", OUT)
