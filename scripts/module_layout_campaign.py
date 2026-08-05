#!/usr/bin/env python3
"""Deterministic module-placement campaign for the V11 24-string inverter block."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
import math
from pathlib import Path
import random
import time
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference" / "lab_inverter_block_24_strings.json"


@dataclass(frozen=True)
class Module:
    module_id: str
    string_id: str
    row: int
    column: int
    x_m: float
    y_m: float


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def canonical_hash(value: object) -> str:
    return "sha256:" + sha256(canonical_json(value).encode("utf-8")).hexdigest()


def load_reference(path: Path = REFERENCE) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    array = data["array"]
    if array["string_count"] != 24 or array["modules_per_string"] != 30:
        raise ValueError("module-placement study requires the canonical 24 x 30 block")
    return data


def baseline_layout(reference: dict) -> list[Module]:
    array = reference["array"]
    pitch = float(array["module_pitch_m"])
    row_spacing = float(array["row_spacing_m"])
    modules: list[Module] = []
    for row in range(int(array["string_count"])):
        string_id = f"STR-{row + 1:02d}"
        for col in range(int(array["modules_per_string"])):
            modules.append(Module(f"{string_id}-M{col + 1:02d}", string_id, row, col, round(col * pitch, 9), round(row * row_spacing, 9)))
    return modules


def grouped(layout: Iterable[Module]) -> dict[str, list[Module]]:
    result: dict[str, list[Module]] = {}
    for module in layout:
        result.setdefault(module.string_id, []).append(module)
    for items in result.values():
        items.sort(key=lambda item: item.column)
    return result


def electrical_order(items: list[Module], strategy: str) -> list[Module]:
    if strategy == "sequential":
        return items
    if strategy == "leapfrog":
        return items[0::2] + list(reversed(items[1::2]))
    raise ValueError(f"unknown strategy {strategy}")


def distance(a: Module, b: Module) -> float:
    return math.hypot(a.x_m - b.x_m, a.y_m - b.y_m)


def collision_count(layout: list[Module], minimum_separation_m: float = 0.25) -> int:
    count = 0
    for i, left in enumerate(layout):
        for right in layout[i + 1:]:
            if abs(left.x_m - right.x_m) <= minimum_separation_m and abs(left.y_m - right.y_m) <= minimum_separation_m and distance(left, right) < minimum_separation_m:
                count += 1
    return count


def evaluate(layout: list[Module], reference: dict) -> dict:
    by_string = grouped(layout)
    if len(layout) != 720 or len(by_string) != 24 or any(len(v) != 30 for v in by_string.values()):
        raise ValueError("layout cardinality changed")
    inverter_x = -10.0
    inverter_y = sum(module.y_m for module in layout) / len(layout)
    results = {}
    for strategy in ("sequential", "leapfrog"):
        total_path = total_home = total_loop_proxy = 0.0
        worst_string = ("", -1.0)
        per_string = []
        for string_id, items in sorted(by_string.items()):
            order = electrical_order(items, strategy)
            internal = sum(distance(a, b) for a, b in zip(order, order[1:]))
            home = math.hypot(order[0].x_m - inverter_x, order[0].y_m - inverter_y) + math.hypot(order[-1].x_m - inverter_x, order[-1].y_m - inverter_y)
            xs, ys = [m.x_m for m in items], [m.y_m for m in items]
            loop_proxy = (max(xs) - min(xs)) * (max(ys) - min(ys) + 0.0064)
            total = internal + home
            total_path += total
            total_home += home
            total_loop_proxy += loop_proxy
            if total > worst_string[1]:
                worst_string = (string_id, total)
            per_string.append({"string_id": string_id, "internal_path_m": internal, "home_path_m": home, "total_path_m": total, "loop_area_proxy_m2": loop_proxy})
        results[strategy] = {"total_path_m": total_path, "total_home_path_m": total_home, "loop_area_proxy_m2": total_loop_proxy, "worst_string_id": worst_string[0], "worst_string_path_m": worst_string[1], "strings": per_string}
    collisions = collision_count(layout)
    payload = {
        "module_count": len(layout),
        "string_count": len(by_string),
        "collision_count": collisions,
        "sequential": results["sequential"],
        "leapfrog": results["leapfrog"],
        "objective": results["leapfrog"]["total_path_m"] + 0.25 * results["leapfrog"]["loop_area_proxy_m2"] + collisions * 1_000_000.0,
        "layout_hash": canonical_hash([asdict(m) for m in layout]),
    }
    payload["evaluation_hash"] = canonical_hash(payload)
    return payload


def mutate(layout: list[Module], rng: random.Random, mode: str, pitch: float, row_spacing: float) -> list[Module]:
    result = list(layout)
    if mode == "row-shift":
        row, dx = rng.randrange(24), rng.uniform(-0.35 * pitch, 0.35 * pitch)
        return [Module(**{**asdict(m), "x_m": m.x_m + dx}) if m.row == row else m for m in result]
    if mode == "module-move":
        idx = rng.randrange(len(result)); m = result[idx]
        result[idx] = Module(**{**asdict(m), "x_m": m.x_m + rng.uniform(-0.2 * pitch, 0.2 * pitch), "y_m": m.y_m + rng.uniform(-0.08 * row_spacing, 0.08 * row_spacing)})
        return result
    if mode == "swap":
        a, b = rng.sample(range(len(result)), 2); ma, mb = result[a], result[b]
        result[a] = Module(**{**asdict(ma), "x_m": mb.x_m, "y_m": mb.y_m}); result[b] = Module(**{**asdict(mb), "x_m": ma.x_m, "y_m": ma.y_m})
        return result
    if mode == "stagger":
        row = rng.randrange(24); offset = 0.5 * pitch if row % 2 else -0.5 * pitch
        return [Module(**{**asdict(m), "x_m": m.x_m + offset}) if m.row == row else m for m in result]
    if mode == "compact":
        sx, sy = rng.uniform(0.97, 1.0), rng.uniform(0.97, 1.0)
        return [Module(**{**asdict(m), "x_m": m.x_m * sx, "y_m": m.y_m * sy}) for m in result]
    if mode == "mixed":
        return mutate(mutate(result, rng, rng.choice(["row-shift", "module-move", "stagger"]), pitch, row_spacing), rng, rng.choice(["row-shift", "module-move", "compact"]), pitch, row_spacing)
    raise ValueError(f"unsupported mode {mode}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["row-shift", "module-move", "swap", "stagger", "compact", "mixed"], required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--duration-seconds", type=float, default=0)
    parser.add_argument("--iterations", type=int, default=0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.duration_seconds <= 0 and args.iterations <= 0:
        parser.error("set --duration-seconds or --iterations")
    reference = load_reference(); baseline = baseline_layout(reference); baseline_eval = evaluate(baseline, reference)
    best_layout, best_eval = baseline, baseline_eval
    rng = random.Random(args.seed); started = time.monotonic(); iterations = accepted = 0
    while not ((args.iterations and iterations >= args.iterations) or (args.duration_seconds and time.monotonic() - started >= args.duration_seconds)):
        candidate = mutate(best_layout, rng, args.mode, float(reference["array"]["module_pitch_m"]), float(reference["array"]["row_spacing_m"]))
        candidate_eval = evaluate(candidate, reference)
        if candidate_eval["objective"] < best_eval["objective"]:
            best_layout, best_eval, accepted = candidate, candidate_eval, accepted + 1
        iterations += 1
    if canonical_json(best_eval) != canonical_json(evaluate(best_layout, reference)):
        raise AssertionError("layout evaluation is not deterministic")
    output = {"schema_version": "globalgrid2050.v11.module-layout-study.v1", "mode": args.mode, "seed": args.seed, "iterations": iterations, "accepted_moves": accepted, "elapsed_seconds": time.monotonic() - started, "baseline": baseline_eval, "best": best_eval, "improvement": {"objective": baseline_eval["objective"] - best_eval["objective"], "leapfrog_path_m": baseline_eval["leapfrog"]["total_path_m"] - best_eval["leapfrog"]["total_path_m"], "loop_area_proxy_m2": baseline_eval["leapfrog"]["loop_area_proxy_m2"] - best_eval["leapfrog"]["loop_area_proxy_m2"]}, "best_layout": [asdict(m) for m in best_layout]}
    output["study_hash"] = canonical_hash(output)
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": True, "mode": args.mode, "iterations": iterations, "accepted_moves": accepted, "output": str(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
