"""Track E (SUP-E) algebra-grade screening numbers quoted in track-E-charter-and-initial-attack.md.

Grade: algebra. Every input comes from fixture/system-fixture.json; the few extra constants are
labelled ASSUMED in the dict `ASSUMED` below and are listed in the charter's ASSUMPTIONS ADDED.
Deterministic, no randomness, no wall clock, no network.
Run from claude-study/:  python3 -I review/track_e_screen.py   (optional arg: path to fixture)
Self-checks: KVL identity, energy formula and I^2R budget identity are asserted at the end.
"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / "fixture" / "system-fixture.json"
fx = json.loads(FIXTURE.read_text())
m, p, c, inv, arc, cases = (fx["module"], fx["plant"], fx["conductors"], fx["inverter_dc_side"],
                             fx["arc_model"], fx["priority_cases"])
sd = p["string_derived"]

ASSUMED = {
    "vmpp_temp_coeff_per_c": m["pmpp_temp_coeff_per_c"]["value"],  # Pmpp coefficient used as Vmpp proxy
    "bypass_diode_vf_v": 0.45,                 # fixture text: Schottky_assumed_Vf_0p45_V_at_17A
    "conductor_temp_swing_k": 20.0,            # drift band for the C3 detectability ratio
    "connector_damage_temp_c": 200.0,          # polymer housing damage threshold (illustration only)
    "mosfet_avalanche_energy_j": 0.3,          # E_AS of a large TO-247 class part, illustration only
    "mosfet_breakdown_v": 120.0,               # 100 V-class part avalanche voltage, illustration only
    "r_th_ja_unheatsunk_k_per_w": 62.0,        # TO-247 free-air figure quoted in the PR5 review
    "junction_box_ambient_c": 85.0,
    "i2_duty_factor_annual": 0.12,             # annual mean of (I/Impp)^2, illustration only
    "service_target_added_outages_per_year": 1.0,
    "assumed_trip_time_s_for_prediction": 0.010,
}
A = ASSUMED
out = {}

def v_arc(i_a, gap_mm):            # uncalibrated Stokes-Oppenlander form from the fixture (ILLUSTRATIVE)
    return (20.0 + 0.534 * gap_mm) * i_a ** 0.12

i_min = arc["minimum_sustaining_current_a"]["value"]
impp, isc, vmpp_m = m["impp_a"], m["isc_a"], m["vmpp_v"]
i2 = impp ** 2
voc_str_stc, voc_str_cold = sd["voc_string_stc_v"], sd["voc_string_cold_minus10c_v"]
vmpp_str = sd["vmpp_string_v"]

# ---------------- arc law values ----------------
for gap in arc["gap_mm_variants"]:
    out[f"v_arc_gap{gap:g}mm_at_impp_v"] = round(v_arc(impp, gap), 2)
    out[f"v_arc_gap{gap:g}mm_at_imin_v"] = round(v_arc(i_min, gap), 2)
voc_ss_stc = voc_str_stc / p["modules_per_string"] / m["internal_structure"]["substrings_per_module"]
voc_ss_cold = sd["voc_module_cold_minus10c_v"] / m["internal_structure"]["substrings_per_module"]
out["substring_voc_stc_v"] = round(voc_ss_stc, 2)
out["substring_voc_cold_v"] = round(voc_ss_cold, 2)
out["substring_gap_voltage_cold_with_bypass_conducting_v"] = round(voc_ss_cold + A["bypass_diode_vf_v"], 2)
out["C1_fixture_law_arc_sustainable_by_substring"] = bool(v_arc(i_min, 1.0) < voc_ss_cold + A["bypass_diode_vf_v"])
out["C1_substring_max_power_stc_w"] = round(m["rated_wp"] / 3, 1)
out["C1_substring_bound_energy_5s_j"] = round(m["rated_wp"] / 3 * fx["figures_of_merit"]["horizon_s"]["C1"], 0)

# ---------------- P1 SW-M-OUT post-trip switch voltage (KVL, I = 0, single switch open) ----------------
def vmpp_str_at(tc):
    return vmpp_str * (1 + A["vmpp_temp_coeff_per_c"] * (tc - 25))
def voc_str_at(tc):
    return voc_str_stc * (1 + m["voc_temp_coeff_per_c"] * (tc - 25))
for tc in cases["C1"]["cell_temperature_variants_c"]:
    out[f"P1_vsw_single_open_node_at_vmpp_T{tc:+d}_v"] = round(voc_str_at(tc) - vmpp_str_at(tc), 1)
    out[f"P1_vsw_single_open_node_collapsed_T{tc:+d}_v"] = round(voc_str_at(tc) - v_arc(isc, 1.0), 1)
out["P1_vsw_all30_open_equal_share_node_at_vmpp_stc_v"] = round((voc_str_stc - vmpp_str) / 30, 1)
out["P1_skew_bound_us_for_first_opened_device"] = round(1e6 * A["mosfet_avalanche_energy_j"] / (A["mosfet_breakdown_v"] * impp), 0)
out["P1b_vsw_cold_bypass_intact_v"] = round(voc_ss_cold + A["bypass_diode_vf_v"], 2)
out["P1b_vsw_bypass_open_cold_v"] = voc_str_cold

# ---------------- C2 parallel arc on the S20 home run ----------------
r_km = c["field_cable"]["resistance_ohm_per_km_20c"]
route = cases["C2"]["string_route_m"]
r_loop = lambda length_m: 2 * length_m * r_km / 1000.0
out["C2far_loop_r_inverter_side_931m_ohm"] = round(r_loop(route["S20"] - 5), 2)
out["C2far_loop_r_S19_total_path_ohm"] = round(r_loop(route["S19"]) + r_loop(route["S20"] - 5), 2)
v_s19 = v_arc(isc, 1.0) + isc * (r_loop(route["S19"]) + r_loop(route["S20"] - 5))
out["C2far_S19_terminal_v_feeding_arc_at_isc_v"] = round(v_s19, 0)
out["C2_each_string_stays_current_source"] = bool(v_s19 < 0.5 * vmpp_str)
p_one = v_arc(isc, 1.0) * isc
out["C2_arc_power_per_illuminated_string_at_isc_w"] = round(p_one, 0)
out["C2_P0_two_strings_5s_horizon_kj"] = round(2 * p_one * 5 / 1000, 2)
out["C2_P2_or_P2b_remaining_one_string_5s_kj"] = round(p_one * 5 / 1000, 2)
out["C2_P3_pretrip_energy_at_assumed_trip_j"] = round(2 * p_one * A["assumed_trip_time_s_for_prediction"], 1)
out["C2_array_end_current_step_percent"] = round(100 * (isc - impp) / impp, 1)
for name, cap in (("C_in", inv["mppt_input_capacitance_f"]["value"]), ("C_dclink_DIRECTBUS", inv["dc_link_capacitance_f"]["value"])):
    out[f"{name}_stored_at_vmpp_j"] = round(0.5 * cap * vmpp_str ** 2, 0)
    out[f"{name}_charge_limited_share_to_arc_j"] = round(cap * (vmpp_str - v_arc(isc, 1.0)) * v_arc(isc, 1.0), 1)
    out[f"{name}_discharge_tau_far_ms"] = round(1e3 * r_loop(route["S20"] - 5) * cap, 2)
    out[f"{name}_discharge_tau_near_us"] = round(1e6 * r_loop(5) * cap, 1)
l_m = (c["two_wire_line_defaults"]["loop_external_inductance_uh_per_m_approx"]
       + c["two_wire_line_defaults"]["loop_internal_inductance_dc_uh_per_m_approx"]) * 1e-6
cl = c["two_wire_line_defaults"]["line_capacitance_pf_per_m_approx"] * 1e-12
out["line936_L_uh"] = round(l_m * 936 * 1e6, 0)
out["line936_E_L_at_isc_j"] = round(0.5 * l_m * 936 * isc ** 2, 2)
out["line936_E_C_at_vmpp_j"] = round(0.5 * cl * 936 * vmpp_str ** 2, 3)
# C_in discharge pulse through SW-STR-INV (lumped, cap ESR/ESL UNKNOWN and set to zero: upper bound)
c_in = inv["mppt_input_capacitance_f"]["value"]
out["C2far_Cin_pulse_peak_R_limited_a"] = round((vmpp_str - v_arc(isc, 1.0)) / r_loop(route["S20"] - 5), 0)
out["C2far_Cin_pulse_L_over_R_rise_us"] = round(1e6 * l_m * (route["S20"] - 5) / r_loop(route["S20"] - 5), 0)
z0_near = math.sqrt(l_m * 5 / c_in)
out["C2near_5m_loop_L_uh"] = round(l_m * 5 * 1e6, 1)
out["C2near_Cin_pulse_peak_surge_impedance_bound_ka"] = round((vmpp_str - v_arc(isc, 1.0)) / z0_near / 1e3, 1)
out["C2near_Cin_pulse_quarter_period_us"] = round(1e6 * 0.5 * math.pi * math.sqrt(l_m * 5 * c_in), 0)
out["C2_inverter_end_steady_current_reversal_a"] = round(-isc - impp, 2)
out["C2_G500_arc_power_per_string_w"] = round(v_arc(isc * 0.5, 1.0) * isc * 0.5, 0)

# ---------------- C1 detection scale ----------------
r_dyn_str = (vmpp_m / impp) * p["modules_per_string"]      # crude dV/dI at MPP proxy (ASSUMED)
out["C1_dc_current_dip_percent_if_arc_in_string_path"] = round(100 * v_arc(impp, 1.0) / r_dyn_str / impp, 1)
out["C1_P0_energy_if_afci_trips_at_2s_and_bypass_absent_j"] = round(v_arc(impp, 1.0) * impp * 2.0, 0)

# ---------------- C3 hot connector ----------------
r_loop_str = r_loop(route["S20"]) + c["connector_resistance_ohm_each"] * c["mated_interfaces_per_string"]["total"]
drift = r_loop_str * c["field_cable"]["temp_coeff_per_c"] * A["conductor_temp_swing_k"]
lead_r = (m["internal_structure"]["positive_lead_m"] + m["internal_structure"]["negative_lead_m"]) * c["factory_lead"]["resistance_ohm_per_km_20c"] / 1000 + c["connector_resistance_ohm_each"]
drift_lead = lead_r * c["factory_lead"]["temp_coeff_per_c"] * A["conductor_temp_swing_k"]
out["C3_string_loop_r_ohm"] = round(r_loop_str, 3)
out["C3_string_loop_drift_20K_ohm"] = round(drift, 3)
out["C3_module_lead_plus_one_connector_r_mohm"] = round(lead_r * 1e3, 2)
out["C3_module_lead_drift_20K_mohm"] = round(drift_lead * 1e3, 3)
th = cases["C3"]["thermal"]
h, cth = th["connector_to_ambient_w_per_k"]["value"], th["connector_thermal_mass_j_per_k"]["value"]
out["C3_thermal_tau_s"] = round(cth / h, 0)
d_dmg = A["connector_damage_temp_c"] - th["ambient_c"]
r_ign = arc["ignition_voltage_v"]["value"] / impp
out["C3_r_at_which_drop_equals_ignition_voltage_ohm"] = round(r_ign, 3)
for r in cases["C3"]["resistance_variants_ohm"]:
    tag = f"C3_R{r:g}"
    out[f"{tag}_dV_v"] = round(impp * r, 3)
    out[f"{tag}_ratio_string_span"] = round(r / drift, 2)
    out[f"{tag}_ratio_module_lead_span"] = round(r / drift_lead, 0)
    out[f"{tag}_equiv_string_temp_change_k"] = round(impp * r / (vmpp_str * abs(A["vmpp_temp_coeff_per_c"])), 2)
    out[f"{tag}_power_w"] = round(i2 * r, 1)
    out[f"{tag}_quasi_steady_dT_k"] = round(i2 * r / h, 0)
    out[f"{tag}_E_3600s_kj"] = round(i2 * (600 * (0.00035 + r) / 2 + 3000 * r) / 1000, 1)
    slope = i2 * (r - 0.00035) / 600                         # W/s during the ramp
    t_dmg = d_dmg * h / slope
    out[f"{tag}_t_to_damage_temp_s"] = round(t_dmg, 0) if t_dmg < 600 else "beyond ramp"
    t_ign = 600 * (r_ign - 0.00035) / (r - 0.00035)
    out[f"{tag}_t_drop_reaches_ignition_v_s"] = round(t_ign, 0) if t_ign < 600 else "never"

# ---------------- lifecycle screen ----------------
units = {1: 720, 2: 360, 4: 192, 30: 24}
for n, u in units.items():
    rb = 0.005 * p["dc_nameplate_wp"] / (u * i2)
    out[f"g{n}_units"] = u
    out[f"g{n}_dies_antiseries"] = 2 * u
    out[f"g{n}_dies_redundant_two_stage"] = 4 * u
    out[f"g{n}_r_budget_0p5pct_mohm"] = round(rb * 1e3, 2)
    out[f"g{n}_w_per_unit_at_budget_w"] = round(i2 * rb, 2)
    out[f"g{n}_required_lambda_fit_for_service_target"] = round(1e9 * A["service_target_added_outages_per_year"] / (u * 8760), 0)
out["P1b_units"] = 3 * 720
out["P1b_r_budget_0p5pct_mohm"] = round(1e3 * 0.005 * p["dc_nameplate_wp"] / (out["P1b_units"] * i2), 2)
out["P1b_w_per_unit_at_budget_w"] = round(0.005 * p["dc_nameplate_wp"] / out["P1b_units"], 2)
out["P1b_required_lambda_fit_for_service_target"] = round(1e9 * A["service_target_added_outages_per_year"] / (out["P1b_units"] * 8760), 0)
out["C1_hypothesis_13V_arc_power_at_impp_w"] = round(13.0 * impp, 0)       # hypothesis arithmetic only
out["C1_string_voltage_drop_percent_13V_to_18p9V"] = (round(100 * 13.0 / vmpp_str, 2), round(100 * v_arc(i_min, 1.0) / vmpp_str, 2))
out["P1_avalanche_power_at_impp_w"] = round(A["mosfet_breakdown_v"] * impp, 0)
out["C2far_S19_cable_dissipation_w"] = round(isc ** 2 * (r_loop(route["S19"]) + r_loop(route["S20"] - 5)), 0)
out["plant_loss_at_0p5pct_w"] = 0.005 * p["dc_nameplate_wp"]
out["annual_loss_at_0p5pct_duty_mwh"] = round(0.005 * p["dc_nameplate_wp"] * 8760 * A["i2_duty_factor_annual"] / 1e6, 2)
out["string_power_lost_per_fail_open_w"] = sd["pmpp_string_w"]
out["existing_mated_interfaces_plant"] = c["mated_interfaces_per_string"]["total"] * p["strings"]
out["new_mated_interfaces_inline_P1"] = 2 * 720
out["g1_tj_rise_per_die_half_budget_unheatsunk_k"] = round(A["r_th_ja_unheatsunk_k_per_w"] * i2 * (0.005 * p["dc_nameplate_wp"] / (720 * i2)) / 2, 0)
out["g1_tj_estimate_in_hot_junction_box_c"] = round(A["junction_box_ambient_c"] + out["g1_tj_rise_per_die_half_budget_unheatsunk_k"], 0)

# ---------------- self-checks ----------------
assert abs((voc_str_stc - vmpp_str) - out["P1_vsw_single_open_node_at_vmpp_T+25_v"]) < 0.1
assert abs(sum(i2 * out[f"g{n}_r_budget_0p5pct_mohm"] / 1e3 * units[n] for n in units) / 4 - 0.005 * p["dc_nameplate_wp"]) < 1.0
assert abs(out["C3_R0.05_E_3600s_kj"] - i2 * (600 * 0.025175 + 150) / 1000) < 0.1
assert math.isclose(out["g4_units"], 24 * math.ceil(30 / 4))

if __name__ == "__main__":
    print("fixture", fx["fixture_id"])
    for k, v in ASSUMED.items():
        print(f"ASSUMED {k} = {v}")
    for k, v in out.items():
        print(f"{k} = {v}")
    print("self-checks OK")
