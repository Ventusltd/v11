"""Deterministic 2D solar-module placement and movement engine."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json, math
from typing import Any, Mapping

class LayoutError(ValueError):
    pass

def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

def layout_hash(value: object) -> str:
    return "sha256:" + sha256(canonical_json(value).encode()).hexdigest()

def _num(name: str, value: Any, minimum: float | None = None) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise LayoutError(f"{name} must be numeric") from exc
    if not math.isfinite(result):
        raise LayoutError(f"{name} must be finite")
    if minimum is not None and result < minimum:
        raise LayoutError(f"{name} must be >= {minimum}")
    return result

def footprint(module: Mapping[str, Any]) -> dict[str, float]:
    rotation = int(module.get("rotation_deg", 0)) % 180
    if rotation not in (0, 90):
        raise LayoutError("rotation must be 0 or 90 degrees")
    width = _num("width_m", module["width_m"], 0.001)
    height = _num("height_m", module["height_m"], 0.001)
    if rotation == 90:
        width, height = height, width
    x = _num("x_m", module["x_m"])
    y = _num("y_m", module["y_m"])
    return {"left": x-width/2, "right": x+width/2, "bottom": y-height/2, "top": y+height/2, "width": width, "height": height}

def intersects(a: Mapping[str, float], b: Mapping[str, float]) -> bool:
    return min(a["right"], b["right"]) > max(a["left"], b["left"]) and min(a["top"], b["top"]) > max(a["bottom"], b["bottom"])

def _boundary(layout: Mapping[str, Any]) -> dict[str, float]:
    boundary = {key: _num(key, layout["boundary"][key]) for key in ("x_min", "x_max", "y_min", "y_max")}
    if boundary["x_max"] <= boundary["x_min"] or boundary["y_max"] <= boundary["y_min"]:
        raise LayoutError("boundary must have positive width and height")
    return boundary

def _candidate_errors(module: Mapping[str, Any], boundary: Mapping[str, float], obstacles: list[Mapping[str, Any]], existing: list[tuple[str, Mapping[str, float]]]) -> list[str]:
    errors: list[str] = []
    fp = footprint(module)
    if fp["left"] < boundary["x_min"]-1e-12 or fp["right"] > boundary["x_max"]+1e-12 or fp["bottom"] < boundary["y_min"]-1e-12 or fp["top"] > boundary["y_max"]+1e-12:
        errors.append(f"{module['id']}: outside boundary")
    for obstacle in obstacles:
        obstacle_fp = {"left": _num("x_min", obstacle["x_min"]), "right": _num("x_max", obstacle["x_max"]), "bottom": _num("y_min", obstacle["y_min"]), "top": _num("y_max", obstacle["y_max"])}
        if intersects(fp, obstacle_fp):
            errors.append(f"{module['id']}: intersects obstacle {obstacle.get('id', '?')}")
    for other_id, other_fp in existing:
        if intersects(fp, other_fp):
            errors.append(f"{module['id']}: overlaps {other_id}")
    return errors

def validate_layout(layout: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        boundary = _boundary(layout)
    except Exception as exc:
        return [str(exc)]
    modules = layout.get("modules", [])
    obstacles = layout.get("obstacles", [])
    ids = [module.get("id") for module in modules]
    if len(ids) != len(set(ids)):
        errors.append("module ids must be unique")
    existing: list[tuple[str, Mapping[str, float]]] = []
    for module in modules:
        try:
            candidate_errors = _candidate_errors(module, boundary, obstacles, existing)
            errors.extend(candidate_errors)
            existing.append((module["id"], footprint(module)))
        except Exception as exc:
            errors.append(f"{module.get('id', '?')}: {exc}")
    return errors

def _rehash(layout: dict[str, Any]) -> dict[str, Any]:
    layout["layout_hash"] = layout_hash({key: value for key, value in layout.items() if key != "layout_hash"})
    return layout

def fill_rectangle(*, boundary: Mapping[str, float], module_width_m: float, module_height_m: float, gap_x_m: float = 0.02, gap_y_m: float = 0.02, orientation: str = "portrait", stagger_m: float = 0.0, obstacles: list[dict[str, Any]] | None = None, limit: int | None = None) -> dict[str, Any]:
    if orientation not in {"portrait", "landscape"}:
        raise LayoutError("orientation must be portrait or landscape")
    width = _num("module_width_m", module_width_m, 0.001)
    height = _num("module_height_m", module_height_m, 0.001)
    gap_x = _num("gap_x_m", gap_x_m, 0)
    gap_y = _num("gap_y_m", gap_y_m, 0)
    stagger = _num("stagger_m", stagger_m, 0)
    if limit is not None and int(limit) < 0:
        raise LayoutError("limit must be non-negative")
    rotation = 90 if orientation == "landscape" else 0
    footprint_width, footprint_height = (height, width) if rotation == 90 else (width, height)
    layout: dict[str, Any] = {"schema_version": "globalgrid2050.v11.module-layout.v1", "boundary": dict(boundary), "obstacles": deepcopy(obstacles or []), "modules": []}
    valid_boundary = _boundary(layout)
    accepted: list[tuple[str, Mapping[str, float]]] = []
    row = 0
    y = valid_boundary["y_min"] + footprint_height/2
    while y + footprint_height/2 <= valid_boundary["y_max"] + 1e-12:
        x = valid_boundary["x_min"] + footprint_width/2 + (stagger if row % 2 else 0)
        column = 0
        while x + footprint_width/2 <= valid_boundary["x_max"] + 1e-12:
            module = {"id": f"MOD-{len(layout['modules'])+1:04d}", "x_m": round(x, 9), "y_m": round(y, 9), "width_m": width, "height_m": height, "rotation_deg": rotation, "row": row, "column": column, "string_id": None}
            if not _candidate_errors(module, valid_boundary, layout["obstacles"], accepted):
                layout["modules"].append(module)
                accepted.append((module["id"], footprint(module)))
                if limit is not None and len(layout["modules"]) >= int(limit):
                    return _rehash(layout)
            x += footprint_width + gap_x
            column += 1
        y += footprint_height + gap_y
        row += 1
    return _rehash(layout)

def move_module(layout: Mapping[str, Any], module_id: str, x_m: float, y_m: float, *, snap_m: float = 0.01) -> dict[str, Any]:
    result = deepcopy(layout)
    snap = _num("snap_m", snap_m, 0.000001)
    target = next((module for module in result["modules"] if module["id"] == module_id), None)
    if target is None:
        raise LayoutError(f"unknown module {module_id}")
    target["x_m"] = round(round(_num("x_m", x_m)/snap)*snap, 9)
    target["y_m"] = round(round(_num("y_m", y_m)/snap)*snap, 9)
    errors = validate_layout(result)
    if errors:
        raise LayoutError("; ".join(errors))
    return _rehash(result)

def rotate_module(layout: Mapping[str, Any], module_id: str) -> dict[str, Any]:
    result = deepcopy(layout)
    target = next((module for module in result["modules"] if module["id"] == module_id), None)
    if target is None:
        raise LayoutError(f"unknown module {module_id}")
    target["rotation_deg"] = 90 if int(target.get("rotation_deg", 0)) % 180 == 0 else 0
    errors = validate_layout(result)
    if errors:
        raise LayoutError("; ".join(errors))
    return _rehash(result)

def assign_strings(layout: Mapping[str, Any], modules_per_string: int = 30, *, snake: bool = True) -> dict[str, Any]:
    if modules_per_string <= 0:
        raise LayoutError("modules_per_string must be positive")
    result = deepcopy(layout)
    rows: dict[float, list[dict[str, Any]]] = {}
    for module in result["modules"]:
        rows.setdefault(round(module["y_m"], 9), []).append(module)
    ordered: list[dict[str, Any]] = []
    for row_index, y in enumerate(sorted(rows)):
        row = sorted(rows[y], key=lambda module: module["x_m"], reverse=snake and row_index % 2 == 1)
        ordered.extend(row)
    for index, module in enumerate(ordered):
        module["string_id"] = f"STR-{index//modules_per_string+1:02d}"
        module["electrical_index"] = index % modules_per_string + 1
    return _rehash(result)
