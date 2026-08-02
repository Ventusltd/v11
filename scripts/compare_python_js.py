#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v11_simulation.model import load_reference_block, simulate_comparison

PATHS = (
    ("sequential", "totals", "field_cable_length_m"),
    ("sequential", "totals", "circuit_loss_kw"),
    ("sequential", "totals", "cold_string_voc_v"),
    ("sequential", "transmission_line", "characteristic_impedance_ohm"),
    ("leapfrog", "totals", "field_cable_length_m"),
    ("leapfrog", "totals", "circuit_loss_kw"),
    ("leapfrog", "totals", "approximate_loop_area_m2"),
    ("delta_leapfrog_minus_sequential", "circuit_loss_kw"),
)


def pick(payload: dict, path: tuple[str, ...]):
    value = payload
    for key in path:
        value = value[key]
    return value


def compare(overrides: dict, *, timeout_seconds: float) -> dict:
    reference_path = ROOT / "reference" / "lab_inverter_block_24_strings.json"
    python_result = simulate_comparison(load_reference_block(reference_path), overrides)
    completed = subprocess.run(
        ["node", "browser/simulate-cli.mjs", str(reference_path), json.dumps(overrides, sort_keys=True)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    javascript_result = json.loads(completed.stdout)
    mismatches = []
    for path in PATHS:
        left = float(pick(python_result, path))
        right = float(pick(javascript_result, path))
        if not math.isclose(left, right, rel_tol=1e-11, abs_tol=1e-10):
            mismatches.append({"path": ".".join(path), "python": left, "javascript": right})
    return {"pass": not mismatches, "checked_metrics": len(PATHS), "mismatches": mismatches}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overrides", default="{}")
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    args = parser.parse_args()
    result = compare(json.loads(args.overrides), timeout_seconds=args.timeout_seconds)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
