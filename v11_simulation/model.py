"""V11-native 24-string solar DC inverter-block simulation core.

The reference boundary is adapted from the pinned laboratory inverter-block,
topology and routing modules. The implementation is independent V11 code and
keeps provisional equipment values visibly provisional.
"""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
import json
import math
from pathlib import Path
import re
from typing import Any, Iterable, Mapping

MU0 = 4.0e-7 * math.pi
EPS0 = 8.8541878128e-12
REFERENCE_PATH = Path(__file__).resolve().parents[1] / "reference" / "lab_inverter_block_24_strings.json"


class SimulationInputError(ValueError):
    """Raised when a simulation input is physically or structurally invalid."""


def _finite(name: str, value: Any, *, minimum: float | None = None) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise SimulationInputError(f"{name} must be numeric") from exc
    if not math.isfinite(result):
        raise SimulationInputError(f"{name} must be finite")
    if minimum is not None and result < minimum:
        raise SimulationInputError(f"{name} must be >= {minimum}")
    return result


def _positive_int(name: str, value: Any) -> int:
    if isinstance(value, bool):
        raise SimulationInputError(f"{name} must be an integer")
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise SimulationInputError(f"{name} must be an integer") from exc
    if result <= 0 or result != value:
        raise SimulationInputError(f"{name} must be a positive integer")
    return result


def _javascript_number(value: float) -> str:
    """Serialise one finite IEEE-754 number as JSON.stringify does.

    Python and JavaScript use the same binary64 arithmetic but historically
    emitted different shortest JSON spellings (for example 1.0 versus 1 and
    1e-07 versus 1e-7). Hash receipts must be byte-identical across engines.
    """

    if not math.isfinite(value):
        return "null"
    if value == 0.0:
        return "0"

    text = repr(float(value))
    magnitude = abs(value)
    if 1.0e-6 <= magnitude < 1.0e21:
        if "e" in text.lower():
            text = format(Decimal(text), "f")
        if "." in text:
            text = text.rstrip("0").rstrip(".")
        return text

    if "e" not in text.lower():
        text = format(Decimal(text), "e")
    mantissa, exponent = re.split("[eE]", text)
    if "." in mantissa:
        mantissa = mantissa.rstrip("0").rstrip(".")
    exponent_value = int(exponent)
    sign = "+" if exponent_value >= 0 else "-"
    return f"{mantissa}e{sign}{abs(exponent_value)}"


def canonical_json(payload: object) -> str:
    """Return recursively key-sorted JSON matching JavaScript canonicalJson."""

    if payload is None:
        return "null"
    if payload is True:
        return "true"
    if payload is False:
        return "false"
    if isinstance(payload, str):
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if isinstance(payload, int):
        return str(payload)
    if isinstance(payload, float):
        return _javascript_number(payload)
    if isinstance(payload, (list, tuple)):
        return "[" + ",".join(canonical_json(item) for item in payload) + "]"
    if isinstance(payload, Mapping):
        entries = (
            json.dumps(str(key), ensure_ascii=False, separators=(",", ":"))
            + ":"
            + canonical_json(payload[key])
            for key in sorted(payload)
        )
        return "{" + ",".join(entries) + "}"
    raise TypeError(f"unsupported canonical JSON type: {type(payload).__name__}")


def canonical_hash(payload: object) -> str:
    return "sha256:" + sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def load_reference_block(path: Path | str = REFERENCE_PATH) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_reference_block(payload)
    return payload


def validate_reference_block(payload: Mapping[str, Any]) -> None:
    if payload.get("schema_version") != "globalgrid2050.v11.inverter-block-input.v1":
        raise SimulationInputError("unsupported inverter-block schema")
    array = payload.get("array", {})
    inverter = payload.get("inverter", {})
    routing = payload.get("routing", {})
    strings = _positive_int("string_count", array.get("string_count"))
    modules = _positive_int("modules_per_string", array.get("modules_per_string"))
    inputs = _positive_int("physical_dc_input_count", inverter.get("physical_dc_input_count"))
    if strings > inputs:
        raise SimulationInputError("string count exceeds physical DC input count")
    routes = routing.get("route_lengths_m")
    if not isinstance(routes, list) or len(routes) != strings:
        raise SimulationInputError("one route length is required for every string")
    for index, value in enumerate(routes, start=1):
        _finite(f"route_lengths_m[{index}]", value, minimum=0.0)
    _finite("module_pitch_m", array.get("module_pitch_m"), minimum=0.001)
    _finite("junction_box_separation_m", array.get("junction_box_separation_m"), minimum=0.0)
    if modules < 2:
        raise SimulationInputError("at least two modules are required per string")


def electrical_module_order(module_ids: Iterable[str], strategy: str) -> tuple[str, ...]:
    """Return the laboratory-authorised traversal law.

    Sequential preserves physical order. Leapfrog uses alternate modules forward
    followed by the remaining modules in reverse order.
    """

    ids = tuple(module_ids)
    if not ids:
        raise SimulationInputError("at least one module is required")
    if len(ids) != len(set(ids)):
        raise SimulationInputError("module identifiers must be unique")
    if strategy == "sequential":
        return ids
    if strategy == "leapfrog":
        return ids[0::2] + tuple(reversed(ids[1::2]))
    raise SimulationInputError(f"unsupported wiring strategy: {strategy!r}")


def _temperature_resistance(r20_ohm_per_km: float, temperature_c: float, alpha: float) -> float:
    factor = 1.0 + alpha * (temperature_c - 20.0)
    if factor <= 0.0:
        raise SimulationInputError("conductor temperature correction is non-positive")
    return r20_ohm_per_km * factor


def _two_wire_parameters(area_mm2: float, centre_spacing_m: float, relative_permittivity: float) -> dict[str, float]:
    area_m2 = _finite("area_mm2", area_mm2, minimum=0.001) * 1.0e-6
    diameter_m = math.sqrt(4.0 * area_m2 / math.pi)
    spacing = _finite("centre_spacing_m", centre_spacing_m, minimum=0.000001)
    eps_r = _finite("relative_permittivity", relative_permittivity, minimum=1.0)
    if spacing <= diameter_m:
        raise SimulationInputError("pair centre spacing must exceed equivalent conductor diameter")
    geometry = math.acosh(spacing / diameter_m)
    inductance_h_per_m = MU0 / math.pi * geometry
    capacitance_f_per_m = math.pi * EPS0 * eps_r / geometry
    characteristic_impedance_ohm = math.sqrt(inductance_h_per_m / capacitance_f_per_m)
    propagation_velocity_m_per_s = 1.0 / math.sqrt(inductance_h_per_m * capacitance_f_per_m)
    return {
        "equivalent_conductor_diameter_m": diameter_m,
        "external_inductance_h_per_m": inductance_h_per_m,
        "differential_capacitance_f_per_m": capacitance_f_per_m,
        "characteristic_impedance_ohm": characteristic_impedance_ohm,
        "propagation_velocity_m_per_s": propagation_velocity_m_per_s,
    }


def _merged_config(reference: Mapping[str, Any], overrides: Mapping[str, Any] | None) -> dict[str, Any]:
    result = deepcopy(reference)
    if not overrides:
        return result
    allowed = {
        "operating_current_a",
        "conductor_temperature_c",
        "minimum_cell_temperature_c",
        "home_pair_separation_m",
        "effective_relative_permittivity",
        "sequential_row_return_separation_m",
        "route_multiplier",
        "module_pitch_m",
        "connector_resistance_ohm_each",
    }
    unknown = sorted(set(overrides) - allowed)
    if unknown:
        raise SimulationInputError(f"unknown simulation override(s): {unknown}")
    result["simulation_overrides"] = dict(overrides)
    return result


def simulate_block(
    reference: Mapping[str, Any],
    *,
    strategy: str,
    overrides: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    validate_reference_block(reference)
    cfg = _merged_config(reference, overrides)
    module = cfg["module"]
    array = cfg["array"]
    inverter = cfg["inverter"]
    conductors = cfg["conductors"]
    routing = cfg["routing"]
    override = cfg.get("simulation_overrides", {})

    strings = int(array["string_count"])
    modules_per_string = int(array["modules_per_string"])
    module_pitch_m = _finite("module_pitch_m", override.get("module_pitch_m", array["module_pitch_m"]), minimum=0.001)
    row_span_m = module_pitch_m * (modules_per_string - 1)
    route_multiplier = _finite("route_multiplier", override.get("route_multiplier", 1.0), minimum=0.001)
    operating_current_a = _finite("operating_current_a", override.get("operating_current_a", module["imp_a"]), minimum=0.0)
    conductor_temperature_c = _finite("conductor_temperature_c", override.get("conductor_temperature_c", 70.0))
    minimum_cell_temperature_c = _finite("minimum_cell_temperature_c", override.get("minimum_cell_temperature_c", -10.0))
    pair_spacing_m = _finite("home_pair_separation_m", override.get("home_pair_separation_m", routing["home_pair_separation_m"]), minimum=0.000001)
    eps_r = _finite("effective_relative_permittivity", override.get("effective_relative_permittivity", routing["effective_relative_permittivity"]), minimum=1.0)
    row_return_separation_m = _finite(
        "sequential_row_return_separation_m",
        override.get("sequential_row_return_separation_m", routing["sequential_row_return_separation_m"]),
        minimum=0.0,
    )
    connector_resistance = _finite(
        "connector_resistance_ohm_each",
        override.get("connector_resistance_ohm_each", conductors["connector_resistance_ohm_each"]),
        minimum=0.0,
    )

    field = conductors["field_cable"]
    factory = conductors["factory_lead"]
    field_r_ohm_per_km = _temperature_resistance(
        _finite("field resistance", field["resistance_ohm_per_km_20c"], minimum=0.0),
        conductor_temperature_c,
        _finite("field alpha", field["temperature_coefficient_per_c"], minimum=0.0),
    )
    factory_r_ohm_per_km = _temperature_resistance(
        _finite("factory resistance", factory["resistance_ohm_per_km_20c"], minimum=0.0),
        conductor_temperature_c,
        _finite("factory alpha", factory["temperature_coefficient_per_c"], minimum=0.0),
    )
    line = _two_wire_parameters(field["area_mm2"], pair_spacing_m, eps_r)

    module_ids = tuple(f"M{index:02d}" for index in range(1, modules_per_string + 1))
    order = electrical_module_order(module_ids, strategy)
    factory_base_m = modules_per_string * (
        _finite("positive_lead_m", module["positive_lead_m"], minimum=0.0)
        + _finite("negative_lead_m", module["negative_lead_m"], minimum=0.0)
    )
    if strategy == "leapfrog":
        factory_total_m = factory_base_m + _finite(
            "leapfrog_factory_extra_m_per_string",
            array["leapfrog_factory_extra_m_per_string"],
            minimum=0.0,
        )
        row_return_m = 0.0
    elif strategy == "sequential":
        factory_total_m = factory_base_m
        row_return_m = row_span_m
    else:
        raise SimulationInputError(f"unsupported wiring strategy: {strategy!r}")

    string_results: list[dict[str, Any]] = []
    total_loss_w = 0.0
    total_field_length_m = 0.0
    total_factory_length_m = 0.0
    total_loop_area_m2 = 0.0
    total_magnetic_energy_j = 0.0
    route_lengths = routing["route_lengths_m"]

    for index, raw_route in enumerate(route_lengths, start=1):
        one_way_route_m = _finite("route length", raw_route, minimum=0.0) * route_multiplier
        positive_field_m = one_way_route_m
        negative_field_m = one_way_route_m + row_return_m
        field_loop_m = positive_field_m + negative_field_m
        field_resistance_ohm = field_r_ohm_per_km * field_loop_m / 1000.0
        factory_resistance_ohm = factory_r_ohm_per_km * factory_total_m / 1000.0
        connector_count = int(conductors["connector_count_per_string"])
        connector_total_ohm = connector_count * connector_resistance
        circuit_resistance_ohm = field_resistance_ohm + factory_resistance_ohm + connector_total_ohm
        voltage_drop_v = operating_current_a * circuit_resistance_ohm
        loss_w = operating_current_a * voltage_drop_v
        string_vmp_v = modules_per_string * _finite("module vmp", module["vmp_v"], minimum=0.0)
        string_operating_power_w = string_vmp_v * operating_current_a
        delivered_power_w = max(0.0, string_operating_power_w - loss_w)
        loop_area_m2 = one_way_route_m * pair_spacing_m
        if strategy == "sequential":
            loop_area_m2 += row_span_m * row_return_separation_m
        one_way_delay_s = one_way_route_m / line["propagation_velocity_m_per_s"]
        round_trip_delay_s = 2.0 * one_way_delay_s
        interruption_envelope_v = operating_current_a * line["characteristic_impedance_ohm"]
        magnetic_energy_j = 0.5 * line["external_inductance_h_per_m"] * one_way_route_m * operating_current_a**2
        result = {
            "string_id": f"STR-{index:02d}",
            "input_id": f"IN-{index:02d}",
            "mppt_id": f"MPPT-{((index - 1) // int(inverter['strings_per_mppt'])) + 1:02d}",
            "one_way_route_m": one_way_route_m,
            "positive_field_length_m": positive_field_m,
            "negative_field_length_m": negative_field_m,
            "field_loop_length_m": field_loop_m,
            "factory_lead_length_m": factory_total_m,
            "circuit_resistance_ohm": circuit_resistance_ohm,
            "voltage_drop_v": voltage_drop_v,
            "loss_w": loss_w,
            "delivered_power_w": delivered_power_w,
            "voltage_drop_percent": (100.0 * voltage_drop_v / string_vmp_v) if string_vmp_v else 0.0,
            "approximate_loop_area_m2": loop_area_m2,
            "one_way_delay_us": one_way_delay_s * 1.0e6,
            "round_trip_delay_us": round_trip_delay_s * 1.0e6,
            "interruption_envelope_v": interruption_envelope_v,
            "external_magnetic_energy_j": magnetic_energy_j,
        }
        string_results.append(result)
        total_loss_w += loss_w
        total_field_length_m += field_loop_m
        total_factory_length_m += factory_total_m
        total_loop_area_m2 += loop_area_m2
        total_magnetic_energy_j += magnetic_energy_j

    rated_dc_kwp = strings * modules_per_string * _finite("rated_power_wp", module["rated_power_wp"], minimum=0.0) / 1000.0
    inverter_kva = _finite("apparent_power_kva", inverter["apparent_power_kva"], minimum=0.001)
    cold_voc_module_v = _finite("voc_v", module["voc_v"], minimum=0.0) * (
        1.0 + _finite("voc temperature coefficient", module["voc_temperature_coefficient_per_c"]) * (minimum_cell_temperature_c - 25.0)
    )
    cold_string_voc_v = cold_voc_module_v * modules_per_string
    block_operating_power_w = 0.0
    for item in string_results:
        block_operating_power_w += item["delivered_power_w"]
        block_operating_power_w += item["loss_w"]
    output = {
        "schema_version": "globalgrid2050.v11.inverter-block-simulation.v1",
        "block_id": cfg["block_id"],
        "strategy": strategy,
        "provenance": cfg["provenance"],
        "reference_boundary": {
            "string_count": strings,
            "modules_per_string": modules_per_string,
            "module_count": strings * modules_per_string,
            "module_rated_power_wp": module["rated_power_wp"],
            "dc_nameplate_power_kwp": rated_dc_kwp,
            "inverter_apparent_power_kva": inverter_kva,
            "dc_ac_nameplate_ratio": rated_dc_kwp / inverter_kva,
            "physical_dc_input_count": inverter["physical_dc_input_count"],
            "mppt_count": inverter["mppt_count"],
            "equipment_evidence_state": "incomplete_evidence",
        },
        "inputs": {
            "operating_current_a": operating_current_a,
            "conductor_temperature_c": conductor_temperature_c,
            "minimum_cell_temperature_c": minimum_cell_temperature_c,
            "module_pitch_m": module_pitch_m,
            "row_span_m": row_span_m,
            "home_pair_separation_m": pair_spacing_m,
            "effective_relative_permittivity": eps_r,
            "route_multiplier": route_multiplier,
        },
        "electrical_traversal": list(order),
        "transmission_line": line,
        "totals": {
            "field_cable_length_m": total_field_length_m,
            "factory_lead_length_m": total_factory_length_m,
            "circuit_loss_kw": total_loss_w / 1000.0,
            "block_operating_power_kw": block_operating_power_w / 1000.0,
            "delivered_power_kw": (block_operating_power_w - total_loss_w) / 1000.0,
            "loss_percent_of_operating_power": (100.0 * total_loss_w / block_operating_power_w) if block_operating_power_w else 0.0,
            "approximate_loop_area_m2": total_loop_area_m2,
            "external_magnetic_energy_j": total_magnetic_energy_j,
            "cold_string_voc_v": cold_string_voc_v,
        },
        "strings": string_results,
    }
    output["simulation_hash"] = canonical_hash(output)
    return output


def simulate_comparison(reference: Mapping[str, Any], overrides: Mapping[str, Any] | None = None) -> dict[str, Any]:
    sequential = simulate_block(reference, strategy="sequential", overrides=overrides)
    leapfrog = simulate_block(reference, strategy="leapfrog", overrides=overrides)
    result = {
        "schema_version": "globalgrid2050.v11.inverter-block-comparison.v1",
        "reference_block_id": reference["block_id"],
        "sequential": sequential,
        "leapfrog": leapfrog,
        "delta_leapfrog_minus_sequential": {
            "field_cable_length_m": leapfrog["totals"]["field_cable_length_m"] - sequential["totals"]["field_cable_length_m"],
            "factory_lead_length_m": leapfrog["totals"]["factory_lead_length_m"] - sequential["totals"]["factory_lead_length_m"],
            "circuit_loss_kw": leapfrog["totals"]["circuit_loss_kw"] - sequential["totals"]["circuit_loss_kw"],
            "approximate_loop_area_m2": leapfrog["totals"]["approximate_loop_area_m2"] - sequential["totals"]["approximate_loop_area_m2"],
        },
    }
    result["comparison_hash"] = canonical_hash(result)
    return result
