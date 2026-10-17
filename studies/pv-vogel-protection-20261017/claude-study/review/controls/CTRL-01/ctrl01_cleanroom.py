#!/usr/bin/env python3
"""CTRL-01 Phase-1 clean-room recomputation of the Track E (SUP-E) screen quantities.

Grade: algebra.  Inputs: fixture/system-fixture.json ONLY, plus the ASSUMED constants in ASSUMED
below (each one is named in the CTRL-01 task text or in assumptions.json A-0xx and is labelled).
This file does not import, open or read review/track_e_screen.py or any other track's script or
result file (clean-room rule, controller preamble).

Run from claude-study/:   python3 -I review/controls/CTRL-01/ctrl01_cleanroom.py
Writes:                   review/controls/CTRL-01/cleanroom-results.json  (deterministic, no clock)
NOT modelled: single-diode IV (strings are ideal current sources where stated), irradiance
dependence of Voc, cable temperature in C2, arc dynamics, any probability or lifetime.
"""
import json
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parents[2]                      # claude-study/
F = json.loads((STUDY / "fixture" / "system-fixture.json").read_text())

MOD, PLANT, COND, ARC = F["module"], F["plant"], F["conductors"], F["arc_model"]
VOC_STC_V = MOD["voc_stc_v"]
VMPP_V = MOD["vmpp_v"]
IMPP_A = MOD["impp_a"]
ISC_A = MOD["isc_a"]
BETA_VOC = MOD["voc_temp_coeff_per_c"]
ALPHA_ISC = MOD["isc_temp_coeff_per_c"]["value"]
GAMMA_PMPP = MOD["pmpp_temp_coeff_per_c"]["value"]
N_SS = MOD["internal_structure"]["substrings_per_module"]
_vf = re.search(r"Vf_(\d+)p(\d+)_V", MOD["internal_structure"]["bypass_diode_type"])
VF_V = float(f"{_vf.group(1)}.{_vf.group(2)}")
LEAD_POS_M = MOD["internal_structure"]["positive_lead_m"]
LEAD_NEG_M = MOD["internal_structure"]["negative_lead_m"]
N_MOD = PLANT["modules_per_string"]
N_STR = PLANT["strings"]
N_TOTAL = PLANT["modules_total"]
P_NAMEPLATE_W = PLANT["dc_nameplate_wp"]
VMPP_STRING_V = PLANT["string_derived"]["vmpp_string_v"]
R_LEAD_OHM_PER_M = COND["factory_lead"]["resistance_ohm_per_km_20c"] / 1000.0
R_FIELD_OHM_PER_M = COND["field_cable"]["resistance_ohm_per_km_20c"] / 1000.0
ALPHA_CU = COND["field_cable"]["temp_coeff_per_c"]
R_CONN_OHM = COND["connector_resistance_ohm_each"]
N_MATED = COND["mated_interfaces_per_string"]["total"]
TWL = COND["two_wire_line_defaults"]
L_LOOP_H_PER_M = (TWL["loop_external_inductance_uh_per_m_approx"] + TWL["loop_internal_inductance_dc_uh_per_m_approx"]) * 1e-6
C_LINE_F_PER_M = TWL["line_capacitance_pf_per_m_approx"] * 1e-12
C_IN_F = F["inverter_dc_side"]["mppt_input_capacitance_f"]["value"]
C_DCLINK_F = F["inverter_dc_side"]["dc_link_capacitance_f"]["value"]
_law = re.search(r"V_arc = \(([\d.]+) \+ ([\d.]+) \* gap_mm\) \* I\^([\d.]+)", ARC["static_vi_law"])
ARC_A0_V, ARC_A1_V_PER_MM, ARC_EXP = (float(_law.group(i)) for i in (1, 2, 3))
I_MIN_A = ARC["minimum_sustaining_current_a"]["value"]
V_IGNITE_V = ARC["ignition_voltage_v"]["value"]
GAPS_MM = ARC["gap_mm_variants"]
C2 = F["priority_cases"]["C2"]
ROUTE_S20_M = C2["string_route_m"]["S20"]
ROUTE_S19_M = C2["string_route_m"]["S19"]
FAR_FROM_ARRAY_M = float(re.search(r"(\d+) m from the array end", C2["fault_location_variants"]["C2-far"]).group(1))
HORIZON_C2_S = F["figures_of_merit"]["horizon_s"]["C2"]
HORIZON_C3_S = F["figures_of_merit"]["horizon_s"]["C3"]
C3 = F["priority_cases"]["C3"]
R_VARIANTS_OHM = C3["resistance_variants_ohm"]
_ramp = re.search(r"from ([\d.]+) ohm to the variant value over ([\d.]+) s", C3["fault_phase"])
R0_OHM, T_RAMP_S = float(_ramp.group(1)), float(_ramp.group(2))
C_TH_J_PER_K = C3["thermal"]["connector_thermal_mass_j_per_k"]["value"]
H_W_PER_K = C3["thermal"]["connector_to_ambient_w_per_k"]["value"]
T_AMB_C3_C = C3["thermal"]["ambient_c"]

ASSUMED = {  # every constant not in the fixture; label ASSUMED; origin given
    "hours_per_year_h": {"value": 8760.0, "origin": "calendar convention (8766 h shown as sensitivity)"},
    "added_outages_target_per_year": {"value": 1.0, "origin": "CTRL-01 task / A-038 (proposed target, owner approval required)"},
    "p_die_task_w": {"value": 1.65, "origin": "CTRL-01 task"},
    "r_th_ja_k_per_w": {"value": 62.0, "origin": "CTRL-01 task / A-036"},
    "t_box_c": {"value": 85.0, "origin": "CTRL-01 task / A-037"},
    "cable_drift_k": {"value": 20.0, "origin": "CTRL-01 task / A-033 (Track C used 40 K, A-024)"},
    "v_node_collapsed_task_v": {"value": 40.0, "origin": "CTRL-01 task"},
    "vmpp_temp_coeff_alternatives_per_c": {"value": [-0.0024, -0.0034, -0.0039],
        "origin": "fixture gives NO Vmpp coefficient: -0.0024 = fixture Voc coeff; -0.0034 = fixture Pmpp coeff used as proxy; -0.0039 = Pmpp coeff minus Isc coeff (gamma_P = gamma_Vmpp + gamma_Impp, Impp coeff ~ Isc coeff)"},
    "loss_screen_fraction": {"value": 0.005, "origin": "brief section 8 screen (not an acceptance rule)"},
    "t_damage_c": {"value": 200.0, "origin": "A-034 (illustration)"},
    "e_as_j": {"value": 0.3, "origin": "A-035 (illustrative 100 V-class part)"},
    "v_br_v": {"value": 120.0, "origin": "SUP-E charter section 8 (illustrative 100 V-class part)"},
    "i2_duty_factor_annual": {"value": 0.12, "origin": "SUP-E charter section 8 (bonus check only)"},
    "trip_time_s_bonus": {"value": 0.010, "origin": "SUP-E charter section 8 (bonus check only)"},
    "c1_low_intercept_hypothesis_v": {"value": 13.0, "origin": "hypothesis only, NOT VERIFIED (A-025); bonus check only"},
}
A = {k: v["value"] for k, v in ASSUMED.items()}
TEMPS_C = (-10.0, 25.0, 70.0)


def voc_module(tc):
    """Fixture convention (Phase 0 cold_voc_per_module): linear relative coefficient about STC."""
    return VOC_STC_V * (1.0 + BETA_VOC * (tc - 25.0))


def v_arc(i_a, gap_mm):
    return (ARC_A0_V + ARC_A1_V_PER_MM * gap_mm) * i_a ** ARC_EXP


def theta_ramp(t, i_a, r0, rf, t_ramp, c_th, h):
    """Exact solution of C dtheta/dt = I^2 R(t) - h theta, theta(0)=0, R linear r0->rf over t_ramp, then rf."""
    tau, g, k = c_th / h, i_a * i_a / h, (rf - r0) / t_ramp
    if t <= t_ramp:
        e = 1.0 - math.exp(-t / tau)
        return g * (r0 * e + k * (t - tau * e))
    th_r = theta_ramp(t_ramp, i_a, r0, rf, t_ramp, c_th, h)
    th_ss = g * rf
    return th_ss + (th_r - th_ss) * math.exp(-(t - t_ramp) / tau)


def first_crossing(fun, target, t_hi):
    """Bisection on a monotone non-decreasing fun(t); None if fun(t_hi) < target."""
    if fun(t_hi) < target:
        return None
    lo, hi = 0.0, t_hi
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if fun(mid) >= target:
            hi = mid
        else:
            lo = mid
    return hi


R = {"_inputs": {"fixture_id": F["fixture_id"], "voc_stc_v": VOC_STC_V, "vmpp_v": VMPP_V, "impp_a": IMPP_A,
                 "isc_a": ISC_A, "beta_voc_per_c": BETA_VOC, "vf_v": VF_V, "arc_law": [ARC_A0_V, ARC_A1_V_PER_MM, ARC_EXP],
                 "i_min_a": I_MIN_A, "v_ignite_v": V_IGNITE_V},
     "_assumed": ASSUMED}

# ---- 1. in-loop available voltage (C1, arc inside SS2 bypass loop) ----------------------------
q1 = {}
for tc in TEMPS_C:
    voc_ss = voc_module(tc) / N_SS
    q1[f"T{tc:+.0f}C"] = {"voc_module_v": voc_module(tc), "voc_ss_v": voc_ss, "voc_ss_plus_vf_v": voc_ss + VF_V}
R["q1_in_loop_cap"] = q1

# ---- 2. fixture arc-law requirement at I_min -----------------------------------------------------
cap_cold = q1["T-10C"]["voc_ss_plus_vf_v"]
q2 = {"i_min_pow": I_MIN_A ** ARC_EXP}
for gap in GAPS_MM:
    vr = v_arc(I_MIN_A, gap)
    q2[f"gap{gap:g}mm"] = {"v_required_at_i_min_v": vr, "deficit_vs_cold_cap_v": vr - cap_cold,
                           "deficit_vs_stc_cap_v": vr - q1["T+25C"]["voc_ss_plus_vf_v"]}
q2["fixture_ignition_v_minus_cold_cap_v"] = V_IGNITE_V - cap_cold
R["q2_arc_law_at_i_min"] = q2

# ---- 3. single SW-M-OUT open, I = 0, KVL: V_sw = 30*Voc(T) - V_node --------------------------------
node_conv = {"node_held_1143p9V": lambda tc: VMPP_STRING_V}
for g in A["vmpp_temp_coeff_alternatives_per_c"]:
    node_conv[f"node_tracks_vmpp_coeff_{g:+.4f}"] = (lambda gg: (lambda tc: VMPP_STRING_V * (1.0 + gg * (tc - 25.0))))(g)
q3 = {}
for name, fnode in node_conv.items():
    q3[name] = {f"T{tc:+.0f}C": {"string_voc_v": N_MOD * voc_module(tc), "v_node_v": fnode(tc),
                                 "v_sw_v": N_MOD * voc_module(tc) - fnode(tc)} for tc in TEMPS_C}
q3["node_collapsed_40V"] = {f"T{tc:+.0f}C": {"v_sw_v": N_MOD * voc_module(tc) - A["v_node_collapsed_task_v"]} for tc in TEMPS_C}
# sensitivity: after S20 opens, the MPPT re-tracks S19 alone; node = S19 array-end Vmpp(T) minus S19 series-path IR drop
_r_s19_series = 2.0 * ROUTE_S19_M * R_FIELD_OHM_PER_M + N_MOD * (LEAD_POS_M + LEAD_NEG_M) * R_LEAD_OHM_PER_M + N_MATED * R_CONN_OHM
q3["node_s19_mpp_minus_cable_drop(coeff_-0.0034)"] = {"r_s19_series_ohm": _r_s19_series, **{
    f"T{tc:+.0f}C": {"v_node_v": VMPP_STRING_V * (1.0 + GAMMA_PMPP * (tc - 25.0)) - IMPP_A * (1.0 + ALPHA_ISC * (tc - 25.0)) * _r_s19_series,
                     "v_sw_v": N_MOD * voc_module(tc) - (VMPP_STRING_V * (1.0 + GAMMA_PMPP * (tc - 25.0)) - IMPP_A * (1.0 + ALPHA_ISC * (tc - 25.0)) * _r_s19_series)}
    for tc in TEMPS_C}}
q3["node_zero_V(bolted_near_fault)"] = {f"T{tc:+.0f}C": {"v_sw_v": N_MOD * voc_module(tc)} for tc in TEMPS_C}
v_arc_s19_only = v_arc(ISC_A, 1.0)
q3["node_collapsed_to_SO_arc_at_18p4A_1mm(diagnostic)"] = {
    "v_arc_v": v_arc_s19_only,
    **{f"T{tc:+.0f}C": {"v_sw_v": N_MOD * voc_module(tc) - v_arc_s19_only} for tc in TEMPS_C}}
R["q3_single_sw_m_out_open"] = q3

# ---- 4. all 30 SW-M-OUT open simultaneously (equal-sharing idealisation) -------------------------
q4 = {}
for name in list(node_conv) + ["node_collapsed_40V"]:
    q4[name] = {k: {"v_each_equal_share_v": v["v_sw_v"] / N_MOD, "v_total_v": v["v_sw_v"]}
                for k, v in q3[name].items()}
q4["skew_window_s"] = A["e_as_j"] / (A["v_br_v"] * IMPP_A)
q4["avalanche_power_w"] = A["v_br_v"] * IMPP_A
R["q4_all_30_open"] = q4

# ---- 5/6. C2-far steady powers and 5 s energies (strings = ideal current sources at Isc) ----------
i_both = 2.0 * ISC_A
v_both = v_arc(i_both, 1.0)
p_both = v_both * i_both
v_s20 = v_arc(ISC_A, 1.0)
p_s20 = v_s20 * ISC_A
p_superpos = 2.0 * p_s20      # diagnostic: each string evaluated at V_arc(18.4 A) and summed
r_s20_stub = 2.0 * FAR_FROM_ARRAY_M * R_FIELD_OHM_PER_M
r_s20_home_inv_side = 2.0 * (ROUTE_S20_M - FAR_FROM_ARRAY_M) * R_FIELD_OHM_PER_M
r_s19_loop = 2.0 * ROUTE_S19_M * R_FIELD_OHM_PER_M + r_s20_home_inv_side
R["q5_c2_far"] = {
    "i_arc_both_a": i_both, "v_arc_both_v": v_both, "p_arc_both_w": p_both,
    "i_arc_s20_alone_a": ISC_A, "v_arc_s20_alone_v": v_s20, "p_arc_s20_alone_w": p_s20,
    "p_both_if_superposed_w(diagnostic)": p_superpos,
    "ratio_s20_alone_to_both": p_s20 / p_both, "reduction_fraction": 1.0 - p_s20 / p_both,
    "e5_both_j": p_both * HORIZON_C2_S, "e5_s20_alone_j": p_s20 * HORIZON_C2_S,
    "e5_both_if_superposed_j(diagnostic)": p_superpos * HORIZON_C2_S,
    "r_s20_stub_loop_ohm": r_s20_stub, "r_s20_home_inverter_side_loop_ohm": r_s20_home_inv_side,
    "r_s19_loop_ohm": r_s19_loop,
    "v_terminal_s20_both_v": v_both + ISC_A * r_s20_stub, "v_terminal_s19_both_v": v_both + ISC_A * r_s19_loop,
    "p_cable_s19_loop_w": ISC_A ** 2 * r_s19_loop,
    "v_node_steady_both_v": v_both + ISC_A * r_s20_home_inv_side,
    "e_pretrip_10ms_both_j(bonus)": p_both * A["trip_time_s_bonus"],
}

# ---- 7. C3 detectability ratio vs cable drift ------------------------------------------------------
r_home_loop = 2.0 * ROUTE_S20_M * R_FIELD_OHM_PER_M
r_leads_string = N_MOD * (LEAD_POS_M + LEAD_NEG_M) * R_LEAD_OHM_PER_M
r_conns_string = N_MATED * R_CONN_OHM
spans = {
    "string_full(home+leads+33conn)": (r_home_loop + r_leads_string + r_conns_string, "all series elements, tempco applied to all"),
    "string_home+33conn(no module leads)": (r_home_loop + r_conns_string, "omits 30 x 0.63 m module leads"),
    "string_copper_only(home+leads)": (r_home_loop + r_leads_string, "contact resistance given no copper tempco"),
    "module_lead_span(0.63m leads+1conn)": ((LEAD_POS_M + LEAD_NEG_M) * R_LEAD_OHM_PER_M + R_CONN_OHM, "sense points across the mated pair"),
}
q7 = {}
for name, (rspan, note) in spans.items():
    entry = {"r_span_ohm": rspan, "note": note}
    for dk in (A["cable_drift_k"], 40.0):
        drift = rspan * ALPHA_CU * dk
        entry[f"drift_{dk:g}K_ohm"] = drift
        entry[f"ratio_{dk:g}K"] = {f"R{r:g}": r / drift for r in R_VARIANTS_OHM}
        entry[f"ratio_increment_{dk:g}K"] = {f"R{r:g}": (r - R0_OHM) / drift for r in R_VARIANTS_OHM}
    q7[name] = entry
R["q7_c3_detectability"] = q7

# ---- 8. unit and die counts -------------------------------------------------------------------------
q8 = {}
for g in (1, 2, 4, 30):
    units = N_STR * math.ceil(N_MOD / g)
    q8[f"group{g}"] = {"units": units, "dies_antiseries_pair": 2 * units, "dies_redundant_two_stage": 4 * units,
                       "partial_group_modules": N_MOD % g}
q8["per_substring_P1b"] = {"units": N_TOTAL * N_SS, "dies_unidirectional": N_TOTAL * N_SS, "dies_antiseries": 2 * N_TOTAL * N_SS}
R["q8_counts"] = q8

# ---- 9. required unit failure rate for <= 1 added outage per year (plant-wide), FIT -----------------
q9 = {}
for key, n in [(k, v["units"]) for k, v in q8.items()]:
    q9[key] = {"units": n,
               "fit_plantwide_8760h": 1e9 * A["added_outages_target_per_year"] / (n * A["hours_per_year_h"]),
               "fit_plantwide_8766h": 1e9 * A["added_outages_target_per_year"] / (n * 8766.0),
               "fit_if_target_per_string_8760h": 1e9 * A["added_outages_target_per_year"] / (n / N_STR * A["hours_per_year_h"])}
R["q9_required_fit"] = q9

# ---- 10. junction temperature screen -----------------------------------------------------------------
p_budget_plant_w = A["loss_screen_fraction"] * P_NAMEPLATE_W
p_die_derived = p_budget_plant_w / N_TOTAL / 2.0
R["q10_tj"] = {"p_die_task_w": A["p_die_task_w"], "p_die_derived_from_0p5pct_budget_w": p_die_derived,
               "delta_t_k": A["p_die_task_w"] * A["r_th_ja_k_per_w"],
               "tj_c": A["t_box_c"] + A["p_die_task_w"] * A["r_th_ja_k_per_w"]}

# ---- B. bonus: other charter quantities, recomputed independently ------------------------------------
bonus = {}
bonus["r_budget_ohm"] = {k: p_budget_plant_w / (v["units"] * IMPP_A ** 2) for k, v in
                         [(k, q8[k]) for k in ("group1", "group2", "group4", "group30")] + [("per_substring_P1b", q8["per_substring_P1b"])]}
bonus["w_per_unit_at_budget"] = {k: p_budget_plant_w / q8[k]["units"] for k in ("group1", "group2", "group4", "group30", "per_substring_P1b")}
bonus["plant_loss_at_screen_w"] = p_budget_plant_w
bonus["annual_loss_wh_duty0p12"] = p_budget_plant_w * A["hours_per_year_h"] * A["i2_duty_factor_annual"]
bonus["mated_interfaces_plant"] = N_MATED * N_STR
bonus["connector_ends_existing"] = 2 * N_MATED * N_STR
bonus["connector_ends_added_P1_inline"] = 2 * N_TOTAL
c3rows = {}
for rf in R_VARIANTS_OHM:
    k = (rf - R0_OHM) / T_RAMP_S
    g = IMPP_A ** 2 / H_W_PER_K
    need = A["t_damage_c"] - T_AMB_C3_C
    t_exact = first_crossing(lambda t: theta_ramp(t, IMPP_A, R0_OHM, rf, T_RAMP_S, C_TH_J_PER_K, H_W_PER_K), need, HORIZON_C3_S)
    r_need = need / g
    t_qs = (r_need - R0_OHM) / k if r_need <= rf else None
    r_15 = 15.0 / IMPP_A
    t_15 = (r_15 - R0_OHM) / k if r_15 <= rf else None
    c3rows[f"R{rf:g}"] = {
        "dv_at_impp_v": rf * IMPP_A, "p_w": IMPP_A ** 2 * rf, "dtheta_ss_k": IMPP_A ** 2 * rf / H_W_PER_K,
        "t_ss_c": T_AMB_C3_C + IMPP_A ** 2 * rf / H_W_PER_K,
        "e_3600s_j": IMPP_A ** 2 * (T_RAMP_S * (R0_OHM + rf) / 2.0 + rf * (HORIZON_C3_S - T_RAMP_S)),
        "t_to_200c_exact_ode_s": t_exact, "t_to_200c_quasi_static_no_thermal_mass_s": t_qs,
        "t_until_dv_15v_s": t_15}
bonus["c3_table"] = c3rows
bonus["c3_tau_s"] = C_TH_J_PER_K / H_W_PER_K
l_s20_inv_side = (ROUTE_S20_M - FAR_FROM_ARRAY_M) * L_LOOP_H_PER_M
bonus["c2_cin"] = {
    "e_stored_j": 0.5 * C_IN_F * VMPP_STRING_V ** 2,
    "share_to_arc_q_times_varc18p4_end_at_varc_j": C_IN_F * (VMPP_STRING_V - v_s20) * v_s20,
    "share_to_arc_q_times_varc36p8_end_at_node_steady_j": C_IN_F * (VMPP_STRING_V - (v_both + ISC_A * r_s20_home_inv_side)) * v_both,
    "i_peak_r_limited_a": (VMPP_STRING_V - v_s20) / r_s20_home_inv_side,
    "l_loop_inv_side_h": l_s20_inv_side, "l_over_r_s": l_s20_inv_side / r_s20_home_inv_side}
bonus["c2_dclink_directbus"] = {
    "e_stored_j": 0.5 * C_DCLINK_F * VMPP_STRING_V ** 2,
    "share_to_arc_j": C_DCLINK_F * (VMPP_STRING_V - v_s20) * v_s20,
    "tau_rc_s": r_s20_home_inv_side * C_DCLINK_F}
l936 = ROUTE_S20_M * L_LOOP_H_PER_M
bonus["line_936m"] = {"l_loop_h": l936, "e_l_at_isc_j": 0.5 * l936 * ISC_A ** 2,
                      "c_line_f": ROUTE_S20_M * C_LINE_F_PER_M, "e_c_at_vmpp_j": 0.5 * ROUTE_S20_M * C_LINE_F_PER_M * VMPP_STRING_V ** 2}
l5 = FAR_FROM_ARRAY_M * L_LOOP_H_PER_M
r5 = 2.0 * FAR_FROM_ARRAY_M * R_FIELD_OHM_PER_M
z0 = math.sqrt(l5 / C_IN_F)
alpha = r5 / (2 * l5)
w0 = 1 / math.sqrt(l5 * C_IN_F)
wd = math.sqrt(w0 ** 2 - alpha ** 2)
tp = math.atan(wd / alpha) / wd
v0n = VMPP_STRING_V - v_s20
bonus["c2_near_cin_pulse"] = {"l_loop_h": l5, "r_loop_ohm": r5, "i_peak_undamped_minus_varc_a": v0n / z0,
                              "i_peak_undamped_full_v_a": VMPP_STRING_V / z0,
                              "i_peak_damped_cable_r_a": v0n / (wd * l5) * math.exp(-alpha * tp) * math.sin(wd * tp),
                              "quarter_period_s": (math.pi / 2) / w0}
bonus["c2_current_step_array_end_fraction"] = ISC_A / IMPP_A - 1.0
bonus["c2_current_reversal_magnitude_a"] = IMPP_A + ISC_A
bonus["c1loop_current_dip_first_order"] = {  # arc in series string path, node held, R_dyn at MPP = Vmpp/Impp (proxy)
    "v_arc_at_impp_1mm_v": v_arc(IMPP_A, 1.0), "di_over_i_at_impp": v_arc(IMPP_A, 1.0) / VMPP_STRING_V,
    "di_over_i_at_isc_varc": v_arc(ISC_A, 1.0) / VMPP_STRING_V}
bonus["c1_low_intercept_hypothesis"] = {"p_w": A["c1_low_intercept_hypothesis_v"] * IMPP_A,
                                        "e5_j": A["c1_low_intercept_hypothesis_v"] * IMPP_A * 5.0,
                                        "fraction_of_vmpp_string": A["c1_low_intercept_hypothesis_v"] / VMPP_STRING_V,
                                        "substring_stc_w": MOD["rated_wp"] / N_SS}


def c2_far_transient(c_f, i_inv_after_a=0.0, t_end_s=0.05, gap_mm=1.0, max_step_s=2e-6):
    """Lumped C2-far transient (bonus bracket, illustrative): node capacitor c_f, S19 = 18.4 A source into the
    node, inverter draw i_inv_after_a for t>0, S20 home-run inverter side R,L to the far arc, S20 array = 18.4 A
    source into the arc.  States v_c, i_h (node -> arc).  i_h(0) = -Impp (S20 pre-fault current to inverter).
    Returns arc energy over t_end and the excess over steady-state power x t_end.  Line wave effects ignored."""
    from scipy.integrate import solve_ivp
    r_h, l_h = r_s20_home_inv_side, l_s20_inv_side

    def rhs(t, y):
        v_c, i_h = y
        i_arc = max(ISC_A + i_h, I_MIN_A)
        return [(ISC_A - i_inv_after_a - i_h) / c_f, (v_c - r_h * i_h - v_arc(i_arc, gap_mm)) / l_h]

    def p_arc(y):
        i_arc = ISC_A + y[1]
        return v_arc(i_arc, gap_mm) * i_arc if i_arc >= I_MIN_A else 0.0

    sol = solve_ivp(rhs, (0.0, t_end_s), [VMPP_STRING_V, -IMPP_A], method="LSODA", rtol=1e-9, atol=1e-9,
                    max_step=max_step_s, dense_output=False, t_eval=None)
    t, Y = sol.t, sol.y
    p = [p_arc(Y[:, k]) for k in range(len(t))]
    e = sum(0.5 * (p[k] + p[k + 1]) * (t[k + 1] - t[k]) for k in range(len(t) - 1))
    i_ss = 2 * ISC_A - i_inv_after_a
    p_ss = v_arc(i_ss, gap_mm) * i_ss
    i_arc_min = min(ISC_A + Y[1, k] for k in range(len(t)))
    i_arc_max = max(ISC_A + Y[1, k] for k in range(len(t)))
    return {"e_arc_0_to_tend_j": e, "p_steady_w": p_ss, "excess_over_steady_j": e - p_ss * t_end_s,
            "i_arc_min_a": i_arc_min, "i_arc_max_a": i_arc_max, "v_c_end_v": float(Y[0, -1]), "n_steps": len(t),
            "t_end_s": t_end_s}


bonus["c2_far_transient_ode_cin_150uF"] = c2_far_transient(C_IN_F)
_half = c2_far_transient(C_IN_F, max_step_s=1e-6)
bonus["c2_far_transient_ode_cin_150uF_halfstep_check"] = {
    "excess_over_steady_j_halfstep": _half["excess_over_steady_j"],
    "rel_change": _half["excess_over_steady_j"] / bonus["c2_far_transient_ode_cin_150uF"]["excess_over_steady_j"] - 1.0}
bonus["c2_far_transient_ode_cin_150uF_first_10ms"] = c2_far_transient(C_IN_F, t_end_s=A["trip_time_s_bonus"])
bonus["c2_far_transient_ode_directbus_2p15mF"] = c2_far_transient(C_IN_F + C_DCLINK_F, t_end_s=0.2)
R["B_bonus"] = bonus

# ---- self-checks (fail loudly) ---------------------------------------------------------------------
assert abs(voc_module(-10.0) - PLANT["string_derived"]["voc_module_cold_minus10c_v"]) < 5e-4
assert abs(N_MOD * voc_module(-10.0) - PLANT["string_derived"]["voc_string_cold_minus10c_v"]) < 5e-3
assert abs(N_MOD * VMPP_V - VMPP_STRING_V) < 1e-9 and abs(N_MOD * VOC_STC_V - PLANT["string_derived"]["voc_string_stc_v"]) < 1e-9
assert [q8[f"group{g}"]["units"] for g in (1, 2, 4, 30)] == [720, 360, 192, 24]
assert abs(p_die_derived - A["p_die_task_w"]) < 1e-9
for gap in GAPS_MM:  # law minimum over I >= I_min is at I_min because the exponent is positive
    assert ARC_EXP > 0 and v_arc(I_MIN_A, gap) > cap_cold
assert abs(p_both - v_both * i_both) < 1e-12 and p_both > p_superpos  # V_arc increasing in I => P(2I) > 2 P(I)
R["_self_checks"] = "PASS"

out = HERE / "cleanroom-results.json"
out.write_text(json.dumps(R, indent=1, sort_keys=True) + "\n")
print(json.dumps({"wrote": str(out.relative_to(STUDY)), "self_checks": R["_self_checks"]}))
