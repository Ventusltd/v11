#!/usr/bin/env python3
"""D9: reproducible ONE-MILLION-SCENARIO topology screening (not arc certification).

Compares hypothetical commanded module/substring PV shunts against the
provisional PUBLIC Ventus 2025 series-open disclosure as analysed in V11 D8.
Each sampled input is evaluated against all candidate topologies; scenario
frequency is intentionally a STRESS MIXTURE, never field-failure probability.

PHYSICAL SCOPE: steady I(V) surrogate and two-string same-MPPT Kirchhoff
cross-feed, with simplified sequential command stress. Excludes real arc
plasma, inverter internal bus topology/capacitor, Ldi/dt, semiconductor SOA,
cell hotspots, insulation/PE dynamics and gate-drive lifetime reliability.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

N = 30
VOC = 45.75
VMPP = 38.13
IMPP = 17.31
ISC = 18.4
R_COPPER_PER_M_CONDUCTOR_20C = 0.00308
R_COPPER_ALPHA = 0.00393
ORIGINAL_SENSE_R = 0.1
ORIGINAL_SERIES_FET_PAIR_R = 0.054  # conditional original D8 series-path calculation
PUBLIC_ORIGINAL_SHA = "a9649d2c7d8733ecf5803b94c384206d101460df"
SCHEMA = "v11.d9.million-scenarios.source-limited-topology-prioritisation.v1"

# These are research screening ceilings, NOT safety limits, IEC thresholds,
# arc-extinction criteria, device ratings, or empirical failure probabilities.
SCREEN_VOLTAGE_CEILING_V = 60.0
SCREEN_SHUNT_HEAT_CEILING_W = 10.0
LENGTHS = np.array([16., 50., 100., 200., 300.])

# Separate conceptual alternatives. A protective-earth shunt is NOT a candidate.
# 'reverse_block' is an IDEAL directional current gate in the fault calculation;
# its on-state normal loss below is a separate hypothetical resistance model.
TOPOLOGIES = (
    dict(key="paired_module_shunt_reverse_block",
         description="Command all 30 full-module shunts on BOTH strings of one MPPT; add string-level reverse-current blocking",
         paired=True, reverse_block=True, substrings=1, isolate_after=False),
    dict(key="paired_substring_shunt_reverse_block",
         description="Command all 90 independently switched substrings on BOTH strings; add string-level reverse-current blocking",
         paired=True, reverse_block=True, substrings=3, isolate_after=False),
    dict(key="paired_module_shunt",
         description="Command all 30 full-module shunts on BOTH strings with bounded activation skew; no reverse blocker",
         paired=True, reverse_block=False, substrings=1, isolate_after=False),
    dict(key="paired_module_shunt_then_isolate",
         description="Command both strings to full-module shunt, then open a downstream string isolator under controlled current",
         paired=True, reverse_block=False, substrings=1, isolate_after=True),
    dict(key="single_module_shunt_reverse_block",
         description="Command only faulted string, with directional blocker; peer can still feed a shared-bus fault",
         paired=False, reverse_block=True, substrings=1, isolate_after=False),
    dict(key="single_module_shunt",
         description="Command only faulted string; healthy same-MPPT string can feed bypasses continuously",
         paired=False, reverse_block=False, substrings=1, isolate_after=False),
)


def normal_paper_loss_w(i=IMPP):
    """Conditional: original 0.1-ohm sensor and both series FETs carry i."""
    return float(i*i*(ORIGINAL_SENSE_R+ORIGINAL_SERIES_FET_PAIR_R))


def residual_shunted_string_v(failed_shunt_units, isc, r_hot, voc, substrings=1):
    """Conservative source-side no-load voltage for FAILED-OPEN controlled paths.

    When substrings=3, each unit contributes 1/3 of module Voc, with
    effective R_hot/3 in each of 3 shunt segments. This is a hypothesis, not
    a validated substring/diode reverse-breakdown circuit.
    """
    if substrings not in (1, 3):
        raise ValueError("supported substring divisions are 1 and 3")
    f = np.asarray(failed_shunt_units)
    if np.any(f < 0) or np.any(f > N*substrings):
        raise ValueError("invalid failed-unit count")
    return ((N*substrings-f) * np.asarray(r_hot)/substrings
            * np.asarray(isc) + f*np.asarray(voc)/substrings)


def _pv_voltage(i, isc, exponent, voc):
    """Three-anchor uncalibrated interpolation; NEVER used for cell reverse bias."""
    impp = isc*(IMPP/ISC)
    vmpp = voc*(VMPP/VOC)
    low_branch = voc-(voc-vmpp)*i/impp
    high_branch = vmpp*np.power(
        np.clip((isc-i)/np.maximum(isc-impp, 1e-12), 0., 1.), exponent)
    return np.where(i <= impp, low_branch, high_branch)


def unblocked_peer_backfeed(isc_shunt, isc_peer, r_hot_shunt,
                            length_m, cable_temp_c, exponent, voc_peer):
    """Same-MPPT two-string steady crossover via 30-step vector bisection.

    Vpeer(I)-I*Rcable = N*Rshunt*(Isc_shunted+I)+I*Rcable.
    One (positive + negative) copper pair PER string, not 24 merged strings.
    """
    rc = 2*length_m*R_COPPER_PER_M_CONDUCTOR_20C * (
        1.+R_COPPER_ALPHA*(cable_temp_c-20.))
    lo = np.zeros_like(isc_shunt)
    hi = np.array(isc_peer, copy=True)
    for _ in range(31):
        i = .5*(lo+hi)
        healthy = N*_pv_voltage(i, isc_peer, exponent, voc_peer)-i*rc
        bypassed = N*r_hot_shunt*(isc_shunt+i)+i*rc
        still_rise = healthy > bypassed
        lo = np.where(still_rise, i, lo)
        hi = np.where(still_rise, hi, i)
    return .5*(lo+hi)


def _samples(rng, size):
    """Bounded deliberately synthetic stress envelope, NOT probabilistic evidence."""
    return {
        "length": LENGTHS[rng.integers(0, len(LENGTHS), size=size)],
        "isc_a": ISC*rng.uniform(.25, 1.2, size=size),
        "isc_b": ISC*rng.uniform(.25, 1.2, size=size),
        "r_a": np.exp(rng.uniform(np.log(.001), np.log(.012), size=size)),
        "r_b_multiplier": rng.uniform(.8, 1.2, size=size),
        "wire_temp": rng.uniform(20., 85., size=size),
        "iv_exponent": rng.uniform(.35, 2.5, size=size),
        "voc_factor": rng.uniform(.94, 1.10, size=size),
        "first_a": rng.integers(0, 2, size=size).astype(bool),
        "skew_s": rng.uniform(0., .020, size=size),
        # Equal-weight fault-injection categories, NOT real lifetime rates.
        "failed_units": rng.integers(0, 4, size=size),
        "r_block": rng.uniform(.005, .04, size=size),  # hypothesis, per STRING
    }


def _base_physics(x):
    r_a = x["r_a"]
    r_b = r_a*x["r_b_multiplier"]
    v_oc = VOC*x["voc_factor"]
    isc_a, isc_b = x["isc_a"], x["isc_b"]
    # Backfeed into A if A shunts before B; reverse direction if B first.
    feed_a = unblocked_peer_backfeed(
        isc_a, isc_b, r_a, x["length"], x["wire_temp"],
        x["iv_exponent"], v_oc)
    feed_b = unblocked_peer_backfeed(
        isc_b, isc_a, r_b, x["length"], x["wire_temp"],
        x["iv_exponent"], v_oc)
    r_cable = 2*x["length"]*R_COPPER_PER_M_CONDUCTOR_20C*(
        1.+R_COPPER_ALPHA*(x["wire_temp"]-20.))
    # Steady loop current if both strings shunt and inverter is absent.
    loop = N*(r_a*isc_a-r_b*isc_b)/(N*(r_a+r_b)+2*r_cable)
    return {
        "r_b": r_b,
        "voc": v_oc,
        "feed_a": feed_a,
        "feed_b": feed_b,
        "loop": loop,
        "unblocked_peak_heat": np.where(
            x["first_a"], r_a*(isc_a+feed_a)**2, r_b*(isc_b+feed_b)**2),
        "unblocked_peak_current": np.where(
            x["first_a"], isc_a+feed_a, isc_b+feed_b),
        "simultaneous_heat": np.maximum(
            r_a*(isc_a-loop)**2, r_b*(isc_b+loop)**2),
    }


def evaluate_candidate(x, phys, topology):
    """One scenario array against one topology; conservative/simplified gates."""
    r_a, r_b = x["r_a"], phys["r_b"]
    isc_a, isc_b = x["isc_a"], x["isc_b"]
    if topology["reverse_block"]:
        # Ideal directionality isolates the unshunted peer from reverse current
        # THROUGH a string-level blocker. It does NOT isolate a shared MPPT bus.
        heat = np.maximum(r_a*isc_a**2, r_b*isc_b**2)
        peak_i = np.maximum(isc_a, isc_b)
        skew_heat_j = heat*x["skew_s"]
    elif topology["paired"]:
        heat = np.maximum(phys["unblocked_peak_heat"], phys["simultaneous_heat"])
        peak_i = phys["unblocked_peak_current"]
        skew_heat_j = phys["unblocked_peak_heat"]*x["skew_s"]
    else:
        # Uncoordinated A string carries own short circuit and live peer
        # indefinitely: failed shared-bus zone-source gate regardless of heat.
        heat = r_a*(isc_a+phys["feed_a"])**2
        peak_i = isc_a+phys["feed_a"]
        skew_heat_j = np.full_like(heat, np.nan)  # no bounded peer-trip time

    # Inject 0..3 open switch paths into string A; string B is intact
    # and fully commanded only for paired topologies.
    voltage_a = residual_shunted_string_v(
        x["failed_units"], isc_a, r_a, phys["voc"],
        substrings=topology["substrings"])
    if topology["paired"]:
        voltage_b = residual_shunted_string_v(
            0, isc_b, r_b, phys["voc"], substrings=topology["substrings"])
        voltage = np.maximum(voltage_a, voltage_b)
    else:
        voltage = voltage_a  # upper bound on A; live B NOT collapsed

    # Normal series blocker/isolator conduction: HYPOTHETICAL current-path R.
    # OFF-state shunt gate leakage/control consumption is NOT modelled.
    extra_r_string = (
        x["r_block"]*int(topology["reverse_block"]) +
        .01*int(topology["isolate_after"]))
    normal_loss_per_module = (IMPP**2*extra_r_string)/N
    heat_ok = heat <= SCREEN_SHUNT_HEAT_CEILING_W
    voltage_ok = voltage <= SCREEN_VOLTAGE_CEILING_V

    # Essential source-zone gate: both PV strings must have a voltage-collapse
    # command to control a fault at the common MPPT bus. An ideal reverse
    # blocker alone cannot stop the live peer feeding a downstream bus fault.
    external_zone_covered = bool(topology["paired"])
    return {
        "heat": heat,
        "voltage": voltage,
        "peak_i": peak_i,
        "skew_heat_j": skew_heat_j,
        "normal_loss": normal_loss_per_module,
        "heat_pass": heat_ok,
        "voltage_pass": voltage_ok,
        "joint_pass": heat_ok & voltage_ok,
        "external_zone_covered": external_zone_covered,
    }


def _priority(stats, candidate):
    """Transparent engineering TRIAGE score, never a probability of success.

    Fault-source coverage is a mandatory selection gate. Relative 0..1
    weightings encode TEST PRIORITY only, not reliability or compliance.
    Penalise higher switch count and additional post-bypass HV isolation.
    """
    if not candidate["paired"]:
        return None
    return round(
        .40*stats["heat_pass_fraction"]
        +.30*stats["voltage_pass_fraction"]
        +.15*int(candidate["paired"])
        +.15*int(candidate["reverse_block"])
        -.10*(candidate["substrings"]-1)
        -.06*int(candidate["isolate_after"]), 6)


def run(iterations=1_000_000, seed=20261018, chunk_size=100_000, keep_top=3):
    if iterations < 1 or chunk_size < 1 or keep_top < 1:
        raise ValueError("iterations, chunk_size and keep_top must be positive")
    rng = np.random.default_rng(seed)
    acc = {t["key"]: dict(heats=[], voltages=[], currents=[], normal_losses=[],
                          skew_heat=[], hpass=0, vpass=0, joint=0, evaluated=0)
           for t in TOPOLOGIES}
    total = 0
    while total < iterations:
        n = min(chunk_size, iterations-total)
        x = _samples(rng, n)
        phys = _base_physics(x)
        for candidate in TOPOLOGIES:
            r = evaluate_candidate(x, phys, candidate)
            a = acc[candidate["key"]]
            for k, arr_name in (("heat","heats"),("voltage","voltages"),
                                ("peak_i","currents"),("normal_loss","normal_losses")):
                a[arr_name].append(np.asarray(r[k], dtype=float))
            if np.isfinite(r["skew_heat_j"]).any():
                a["skew_heat"].append(r["skew_heat_j"][np.isfinite(r["skew_heat_j"])])
            a["hpass"] += int(np.count_nonzero(r["heat_pass"]))
            a["vpass"] += int(np.count_nonzero(r["voltage_pass"]))
            a["joint"] += int(np.count_nonzero(r["joint_pass"]))
            a["evaluated"] += n
        total += n

    candidates = []
    for t in TOPOLOGIES:
        a = acc[t["key"]]
        heat = np.concatenate(a["heats"])
        voltage = np.concatenate(a["voltages"])
        peak_i = np.concatenate(a["currents"])
        losses = np.concatenate(a["normal_losses"])
        stress = np.concatenate(a["skew_heat"]) if a["skew_heat"] else None
        stats = {
            "scenarios": int(a["evaluated"]),
            "heat_pass_fraction": round(a["hpass"]/iterations, 6),
            "voltage_pass_fraction": round(a["vpass"]/iterations, 6),
            "joint_screen_fraction": round(a["joint"]/iterations, 6),
            "heat_peak_p99_w": round(float(np.percentile(heat,99)), 4),
            "heat_peak_max_w": round(float(np.max(heat)), 4),
            "shunt_current_p99_a": round(float(np.percentile(peak_i,99)), 4),
            "residual_upper_bound_p99_v": round(float(np.percentile(voltage,99)), 4),
            "normal_series_loss_mean_w_per_module":
                round(float(np.mean(losses)), 5),
            "skew_shunt_energy_p99_j_per_module":
                None if stress is None else round(float(np.percentile(stress,99)), 5),
        }
        score = _priority(stats,t)
        if score is not None:
            candidates.append({
                "topology":t["key"], "description":t["description"],
                "triage_priority_score_NOT_probability":score,
                "external_fault_zones_modelled":"string home run AND shared same-MPPT bus (PV contribution only)",
                "controlled_shunt_units_per_module":t["substrings"],
                "ideal_reverse_current_blocking_assumed":t["reverse_block"],
                "requires_both_strings_commanded":t["paired"],
                "statistics":stats,
            })
    selected = sorted(candidates, key=lambda a:(
        -a["triage_priority_score_NOT_probability"],a["topology"]))[:keep_top]

    output = {
        "schema":SCHEMA,
        "scenario_count":int(iterations),
        "same_scenarios_per_topology":True,
        "candidate_topologies_evaluated":len(TOPOLOGIES),
        "seed":int(seed),
        "source_original_public_sha":PUBLIC_ORIGINAL_SHA,
        "original_paper_baseline_conditional":{
            "topology":"June 2025 proposed two-series-FET opens + analogue current sense + passive substring bypass",
            "series_path_loss_at_impp_w_per_module":normal_paper_loss_w(),
            "series_path_loss_at_20a_w_per_module":normal_paper_loss_w(20.),
            "assumption":"Original 0.1-ohm sense resistor and 2x27-milliohm FETs ALL in series carrying full string current; not an as-built netlist",
            "arc_interrupt_success":"NOT MEASURED",
        },
        "only_priority_topologies_for_followup":selected,
        "screening_envelope":{
            "module_fixture":"30 x provisional STC 660Wp, Voc 45.75V, Vmpp 38.13V, Impp 17.31A, Isc 18.4A",
            "string_lengths_one_way_m":LENGTHS.tolist(),
            "source_current_isc_multiplier_range":[.25,1.2],
            "hot_bypass_r_per_full_module_ohms_log_uniform":[.001,.012],
            "second_string_r_multiplier_range":[.8,1.2],
            "copper_celsius_range":[20.,85.],
            "pv_iv_uncalibrated_exponent_range":[.35,2.5],
            "voc_scaled_range":[.94,1.10],
            "activation_skew_seconds":[0.,.02],
            "failed_switch_paths_uniform_injection":[0,1,2,3],
            "reverse_block_string_on_r_ohm_hypothesis":[.005,.04],
            "post_bypass_isolator_on_r_ohm_hypothesis":.01,
            "triage_voltage_ceiling_v_NOT_standard":SCREEN_VOLTAGE_CEILING_V,
            "triage_bypass_heat_ceiling_w_NOT_rating":SCREEN_SHUNT_HEAT_CEILING_W,
            "sample_distribution":"Synthetic bounded design stress; NOT field probability, lifetime FIT, failure prediction or evidence of real-world feasibility",
            "score":"Weighted triage heuristic .40 thermal-screen + .30 residual-voltage-screen + .15 both-string coverage + .15 ideal reverse block - .10 per extra switch per module - .06 optional isolator; not a success probability",
        },
        "must_falsify_next":[
            "actual arc energy at each fault electrode and true plasma extinction (NONE computed here)",
            "bus/input capacitor and converter/inverter backfeed including stored joules (UNKNOWN)",
            "hot device SOA, body diodes, reverse-block implementation, transients and Ldi/dt",
            "real module cell hotspots and short-circuit exposure duration",
            "independent autonomy under gate power loss, single switch failures and data latency",
            "module-internal fault and PV-to-PE insulation: do not use PE as an operating current sink",
            "reverse current from peer for a fault DOWNSTREAM of blocking element remains",
            "claimed reliability and population failure probabilities require field/component data",
        ],
        "interpretation":"ONE MILLION arithmetic screenings per topology, NOT one million SPICE/arc experiments. Only prioritized contenders emitted; controls were evaluated but withheld from output.",
        "confidentiality":"Public V11 source surrogate and original PUBLIC paper only; NO user-supplied IEC or inverter manuals or derivative private data.",
    }
    digest = hashlib.sha256(json.dumps(
        output,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
    output["receipt_sha256"] = digest
    return output


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--iterations",type=int,default=1_000_000)
    parser.add_argument("--seed",type=int,default=20261018)
    parser.add_argument("--chunk-size",type=int,default=100_000)
    parser.add_argument("--top",type=int,default=3)
    parser.add_argument("--output",required=True)
    opts=parser.parse_args()
    result=run(iterations=opts.iterations,seed=opts.seed,
               chunk_size=opts.chunk_size,keep_top=opts.top)
    target=Path(opts.output)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,sort_keys=True,indent=2,
                                 allow_nan=False)+"\n",encoding="utf8")
    print(json.dumps({
        "screened_scenarios":result["scenario_count"],
        "tested_topologies":result["candidate_topologies_evaluated"],
        "topologies_to_test":[x["topology"] for x in result["only_priority_topologies_for_followup"]],
        "original_paper_baseline_loss_w_module":
            result["original_paper_baseline_conditional"]["series_path_loss_at_impp_w_per_module"],
        "real_arc_validation":False,
        "receipt_sha256":result["receipt_sha256"],
    },indent=2))


if __name__=="__main__":
    main()
