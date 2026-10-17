"""Kuiper-keyed Vogel PV protection SCREENING, not a PV arc/EMT model.
No device Vds, fault clearing, probabilities, real thermal design or safety claimed.
"""
import json
import math

GOLDEN_ANGLE = math.pi * (3 - math.sqrt(5))
LEVELS = (1, 2, 4, 30)
SAMPLES_PER_PAIR = 64
MODULES_PER_STRING, STRINGS, WATTS_PER_MODULE = 30, 24, 660.0
IMP, VOC_STC, VOC_TEMP_COEFF, COLD_CELL_C = 17.31, 45.75, -0.0024, -10.0
FAULTS = (
    "internal_series_arc", "external_connector_series_arc", "parallel_arc",
    "insulation_or_earth_fault", "high_resistance_hot_connector", "reverse_feed",
    "switch_failed_short", "switch_failed_open", "control_supply_lost",
    "benign_inverter_or_mppt_noise",
)

def kuiper_xy(key):
    """Preserves the source Line Wafer law: r=sqrt(key), angle=key*GOLDEN."""
    if type(key) is not int or key < 1:
        raise ValueError("Kuiper key must be a positive integer")
    r, theta = math.sqrt(key), key * GOLDEN_ANGLE
    return r * math.cos(theta), r * math.sin(theta)

def vogel_disk(sample, total=SAMPLES_PER_PAIR):
    """Bounded experiment with two parameters; NOT a sampled probability law."""
    if not 1 <= sample <= total:
        raise ValueError("sample out of range")
    r, theta = math.sqrt((sample - .5) / total), sample * GOLDEN_ANGLE
    return .5 + .5 * r * math.cos(theta), .5 + .5 * r * math.sin(theta)

def cold_voc_per_module(cell_c=COLD_CELL_C):
    return VOC_STC * (1 + VOC_TEMP_COEFF * (cell_c - 25.0))

def devices_per_plant(max_modules):
    if max_modules not in LEVELS:
        raise ValueError("unsupported grouping")
    # Count partial groups: 30 modules / 4 -> 8 switches per string.
    return STRINGS * math.ceil(MODULES_PER_STRING / max_modules)

def propagation_delay_us(length_m, relative_permittivity=2.0):
    if length_m < 0 or relative_permittivity < 1:
        raise ValueError("invalid line parameters")
    return 1e6 * length_m * math.sqrt(relative_permittivity) / 299792458

def one_case(fault, level, sample):
    if fault not in FAULTS or level not in LEVELS:
        raise ValueError("unknown fault or protection level")
    if not 1 <= sample <= SAMPLES_PER_PAIR:
        raise ValueError("invalid sample")
    # Versioned key ledger: append new families, never silently reorder this tuple.
    key = (FAULTS.index(fault) * len(LEVELS) + LEVELS.index(level)) * SAMPLES_PER_PAIR + sample
    u, v = vogel_disk(sample)
    current_a = 8.0 + 16.0 * u
    series_r_ohm = .001 + .049 * v
    unit_w = current_a**2 * series_r_ohm
    count = devices_per_plant(level)
    plant_w = count * unit_w
    x, y = kuiper_xy(key)
    return {
        "key": key, "kuiper_xy": [round(x, 8), round(y, 8)],
        "fault": fault, "max_modules_per_unit": level, "sample": sample,
        "current_a_assumed": round(current_a, 5),
        "series_r_ohm_assumed": round(series_r_ohm, 7),
        "dissipation_w_per_unit": round(unit_w, 5),
        "plant_loss_kw_if_all_operating_at_assumed_current": round(plant_w / 1000, 6),
        "percent_of_stc_nameplate_NOT_energy_yield": round(100 * plant_w / (STRINGS * MODULES_PER_STRING * WATTS_PER_MODULE), 6),
        "max_group_source_voc_cold_v_NOT_switch_vds": round(level * cold_voc_per_module(), 4),
        "units_per_plant": count,
        "passes_0_5pct_stc_conduction_screen_only": plant_w <= .005 * STRINGS * MODULES_PER_STRING * WATTS_PER_MODULE,
        "physical_protection_status": "NOT_EVALUATED",
    }

def calculate():
    summaries = {}
    for level in LEVELS:
        rows = [one_case(f, level, s) for f in FAULTS for s in range(1, SAMPLES_PER_PAIR + 1)]
        rows.sort(key=lambda r: r["plant_loss_kw_if_all_operating_at_assumed_current"])
        summaries[str(level)] = {
            "unit_count": devices_per_plant(level),
            "maximum_group_cold_voc_v_NOT_semiconductor_vds": round(level * cold_voc_per_module(), 3),
            "r_budget_for_0_5pct_stc_loss_at_imp_ohm": round((.005 * STRINGS * MODULES_PER_STRING * WATTS_PER_MODULE) / (devices_per_plant(level) * IMP**2), 6),
            "sample_cases": len(rows),
            "passed_nominal_loss_screen_count": sum(row["passes_0_5pct_stc_conduction_screen_only"] for row in rows),
            "min_screened_loss_kw": rows[0]["plant_loss_kw_if_all_operating_at_assumed_current"],
            "max_screened_loss_kw": rows[-1]["plant_loss_kw_if_all_operating_at_assumed_current"],
            "illustrative_max_loss_case_key": rows[-1]["key"],
        }
    return {
        "status": "ILLUSTRATIVE_SCREENING_ONLY_NOT_A_PROTECTION_VALIDATION",
        "method": "Kuiper sqrt(key)/golden angle for keyed addresses; bounded Vogel disk for two assumed screening axes; no probabilistic inference",
        "reference_fixture": "Ventusltd/v11 PR3 provisional fixture through draft PR5 v11-reference-facts.json",
        "reference_kuiper": "Ventusltd/globalgrid2050/testcode/202609151339/lib.mjs",
        "fault_classes": list(FAULTS),
        "total_cases": len(FAULTS)*len(LEVELS)*SAMPLES_PER_PAIR,
        "architectures": summaries,
        "route_example_max_936m_one_way_us_epsr2": round(propagation_delay_us(936), 3),
        "whole_plant_dc_wp": int(STRINGS*MODULES_PER_STRING*WATTS_PER_MODULE),
        "explicit_exclusions": [
            "actual switch Vds/SOA/body diode", "validated PV IV/EMT/arc plasma", "fault clearing effectiveness",
            "hot spots and long-term heat transfer", "independent insulation sensing",
            "inverter/DC link/parallel feeder energy", "protection coordination",
            "nuisance trip statistics", "lifetime probabilities", "certification"],
        "unsampled_mandatory_extremes": [
            "0A/night backfeed", "max cold Voc", "brownout/faulted gate supply",
            "both blocking directions", "two earth faults", "parallel backfeed",
            "far-end arc and propagation delay", "hot connector without arc noise"],
    }

if __name__ == "__main__":
    print(json.dumps(calculate(), indent=2, sort_keys=True))
