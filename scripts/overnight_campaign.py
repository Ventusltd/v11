#!/usr/bin/env python3
"""Long-running deterministic/property campaign for the V11 inverter block."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import platform
import random
import subprocess
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v11_simulation.model import canonical_json, load_reference_block, simulate_comparison

REFERENCE = ROOT / "reference" / "lab_inverter_block_24_strings.json"


def random_overrides(rng: random.Random) -> dict[str, float]:
    return {
        "operating_current_a": rng.uniform(0.0, 22.0),
        "conductor_temperature_c": rng.uniform(-20.0, 95.0),
        "minimum_cell_temperature_c": rng.uniform(-35.0, 15.0),
        "home_pair_separation_m": rng.uniform(0.0060, 0.5),
        "effective_relative_permittivity": rng.uniform(1.05, 3.5),
        "sequential_row_return_separation_m": rng.uniform(0.1, 3.0),
        "route_multiplier": rng.uniform(0.35, 1.75),
        "module_pitch_m": rng.uniform(1.0, 2.5),
        "connector_resistance_ohm_each": rng.uniform(0.0, 0.0015),
    }


def assert_invariants(result: dict[str, Any]) -> None:
    seq = result["sequential"]
    leap = result["leapfrog"]
    boundary = seq["reference_boundary"]
    if boundary["string_count"] != 24 or boundary["modules_per_string"] != 30 or boundary["module_count"] != 720:
        raise AssertionError("reference inverter-block cardinality changed")
    if not math.isclose(boundary["dc_nameplate_power_kwp"], 475.2, abs_tol=1e-9):
        raise AssertionError("reference DC nameplate changed")
    if leap["totals"]["field_cable_length_m"] > seq["totals"]["field_cable_length_m"] + 1e-9:
        raise AssertionError("leapfrog field cable exceeded sequential")
    if leap["totals"]["approximate_loop_area_m2"] > seq["totals"]["approximate_loop_area_m2"] + 1e-9:
        raise AssertionError("leapfrog loop area exceeded sequential")
    for strategy in (seq, leap):
        if len(strategy["strings"]) != 24:
            raise AssertionError("string result count changed")
        if not strategy["simulation_hash"].startswith("sha256:"):
            raise AssertionError("simulation hash missing")
        for item in strategy["strings"]:
            for key in ("circuit_resistance_ohm", "voltage_drop_v", "loss_w", "round_trip_delay_us", "interruption_envelope_v"):
                value = float(item[key])
                if not math.isfinite(value) or value < 0:
                    raise AssertionError(f"invalid {key}: {value}")
            operating = item["delivered_power_w"] + item["loss_w"]
            if operating < -1e-9:
                raise AssertionError("negative operating power")


def run_javascript_parity(overrides: dict[str, float], timeout_seconds: float = 25.0) -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/compare_python_js.py", "--overrides", json.dumps(overrides, sort_keys=True), "--timeout-seconds", str(timeout_seconds)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout_seconds + 5.0,
    )
    payload = json.loads(completed.stdout)
    if not payload.get("pass"):
        raise AssertionError(f"Python/JavaScript parity failed: {payload}")


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration-seconds", type=float, default=0.0)
    parser.add_argument("--iterations", type=int, default=0)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--checkpoint-seconds", type=float, default=60.0)
    parser.add_argument("--parity-seconds", type=float, default=300.0)
    args = parser.parse_args()
    if args.duration_seconds <= 0 and args.iterations <= 0:
        parser.error("set --duration-seconds or --iterations")

    reference = load_reference_block(REFERENCE)
    rng = random.Random(args.seed)
    started = time.monotonic()
    last_checkpoint = started
    last_parity = started - args.parity_seconds
    iterations = 0
    parity_checks = 0
    failures: list[dict[str, Any]] = []
    digest = sha256()
    extrema = {
        "maximum_sequential_loss_kw": 0.0,
        "maximum_leapfrog_loss_kw": 0.0,
        "minimum_characteristic_impedance_ohm": float("inf"),
        "maximum_characteristic_impedance_ohm": 0.0,
        "maximum_round_trip_delay_us": 0.0,
    }

    while True:
        elapsed = time.monotonic() - started
        if args.duration_seconds > 0 and elapsed >= args.duration_seconds:
            break
        if args.iterations > 0 and iterations >= args.iterations:
            break
        overrides = random_overrides(rng)
        try:
            result = simulate_comparison(reference, overrides)
            assert_invariants(result)
            if iterations % 1000 == 0:
                repeated = simulate_comparison(reference, overrides)
                if canonical_json(result) != canonical_json(repeated):
                    raise AssertionError("same-process repeated simulation was not byte-stable")
            if time.monotonic() - last_parity >= args.parity_seconds:
                run_javascript_parity(overrides)
                parity_checks += 1
                last_parity = time.monotonic()
            digest.update(canonical_json(result).encode("utf-8"))
            seq, leap = result["sequential"], result["leapfrog"]
            extrema["maximum_sequential_loss_kw"] = max(extrema["maximum_sequential_loss_kw"], seq["totals"]["circuit_loss_kw"])
            extrema["maximum_leapfrog_loss_kw"] = max(extrema["maximum_leapfrog_loss_kw"], leap["totals"]["circuit_loss_kw"])
            z0 = leap["transmission_line"]["characteristic_impedance_ohm"]
            extrema["minimum_characteristic_impedance_ohm"] = min(extrema["minimum_characteristic_impedance_ohm"], z0)
            extrema["maximum_characteristic_impedance_ohm"] = max(extrema["maximum_characteristic_impedance_ohm"], z0)
            extrema["maximum_round_trip_delay_us"] = max(extrema["maximum_round_trip_delay_us"], max(item["round_trip_delay_us"] for item in leap["strings"]))
        except Exception as exc:
            failures.append({"iteration": iterations, "overrides": overrides, "error": f"{type(exc).__name__}: {exc}"})
            break
        iterations += 1
        now = time.monotonic()
        if now - last_checkpoint >= args.checkpoint_seconds:
            atomic_write(args.output, {
                "schema_version": "globalgrid2050.v11.overnight-campaign.v1",
                "phase": args.phase,
                "status": "running",
                "seed": args.seed,
                "iterations": iterations,
                "parity_checks": parity_checks,
                "elapsed_seconds": now - started,
                "digest_so_far": "sha256:" + digest.hexdigest(),
                "extrema": extrema,
                "failures": failures,
            })
            last_checkpoint = now

    elapsed = time.monotonic() - started
    payload = {
        "schema_version": "globalgrid2050.v11.overnight-campaign.v1",
        "phase": args.phase,
        "status": "passed" if not failures else "failed",
        "pass": not failures,
        "seed": args.seed,
        "iterations": iterations,
        "parity_checks": parity_checks,
        "elapsed_seconds": elapsed,
        "result_chain_digest": "sha256:" + digest.hexdigest(),
        "extrema": extrema,
        "failures": failures,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "github_sha": os.environ.get("GITHUB_SHA"),
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        },
        "reference": {
            "repository": reference["provenance"]["source_repository"],
            "commit": reference["provenance"]["source_commit"],
            "block_id": reference["block_id"],
            "string_count": reference["array"]["string_count"],
            "modules_per_string": reference["array"]["modules_per_string"],
        },
    }
    atomic_write(args.output, payload)
    print(json.dumps({"pass": payload["pass"], "iterations": iterations, "parity_checks": parity_checks, "elapsed_seconds": elapsed, "output": str(args.output)}, sort_keys=True))
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
