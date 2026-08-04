"""Authoritative connector-end and mating-interface accounting for one PV string."""

from __future__ import annotations

from typing import Any

SCHEMA_VERSION = "globalgrid2050.v11.connector-accounting.v1"


class ConnectorAccountingError(ValueError):
    """Raised when connector accounting inputs or invariants are invalid."""


def _module_count(value: Any) -> int:
    if isinstance(value, bool):
        raise ConnectorAccountingError("modules_per_string must be an integer >= 2")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ConnectorAccountingError("modules_per_string must be an integer >= 2") from exc
    if number != value or number < 2:
        raise ConnectorAccountingError("modules_per_string must be an integer >= 2")
    return number


def connector_accounting(modules_per_string: int) -> dict[str, int | str]:
    """Return complete-system counts, including the two inverter connector ends."""

    modules = _module_count(modules_per_string)
    module_to_module = modules - 1
    module_to_string_cable = 2
    string_cable_to_inverter = 2
    total_interfaces = module_to_module + module_to_string_cable + string_cable_to_inverter

    module_ends = 2 * modules
    string_cable_ends = 4
    inverter_ends = 2
    total_ends = module_ends + string_cable_ends + inverter_ends
    positive_ends = modules + 3
    negative_ends = modules + 3

    result: dict[str, int | str] = {
        "schema_version": SCHEMA_VERSION,
        "modules_per_string": modules,
        "module_connector_end_count": module_ends,
        "string_cable_connector_end_count": string_cable_ends,
        "inverter_connector_end_count": inverter_ends,
        "complete_system_connector_end_count": total_ends,
        "module_to_module_mate_count": module_to_module,
        "module_to_string_cable_mate_count": module_to_string_cable,
        "string_cable_to_inverter_mate_count": string_cable_to_inverter,
        "total_mated_interface_count": total_interfaces,
        "loose_module_connector_end_count_before_home_runs": 2,
        "positive_connector_end_count": positive_ends,
        "negative_connector_end_count": negative_ends,
    }
    validate_accounting(result)
    return result


def validate_accounting(accounting: dict[str, int | str]) -> None:
    modules = _module_count(accounting["modules_per_string"])
    total_ends = int(accounting["complete_system_connector_end_count"])
    total_interfaces = int(accounting["total_mated_interface_count"])
    positive = int(accounting["positive_connector_end_count"])
    negative = int(accounting["negative_connector_end_count"])

    if total_ends != 2 * modules + 6:
        raise ConnectorAccountingError("complete-system connector ends must equal 2N + 6")
    if total_interfaces != modules + 3:
        raise ConnectorAccountingError("mated interfaces must equal N + 3")
    if total_ends != 2 * total_interfaces:
        raise ConnectorAccountingError("every completed interface must consume exactly two connector ends")
    if positive != negative or positive + negative != total_ends:
        raise ConnectorAccountingError("positive and negative connector-end counts must be equal and exhaustive")


def resistance_accounting(
    modules_per_string: int,
    contact_resistance_ohm_per_mated_interface: float,
) -> dict[str, float | int | str]:
    """Apply the provisional resistance uniformly to all completed mated interfaces."""

    accounting = connector_accounting(modules_per_string)
    resistance = float(contact_resistance_ohm_per_mated_interface)
    if resistance < 0:
        raise ConnectorAccountingError("contact resistance must be non-negative")
    count = int(accounting["total_mated_interface_count"])
    return {
        "schema_version": "globalgrid2050.v11.connector-resistance-policy.v1",
        "evidence_state": "provisional_fixture",
        "applies_to": "all_completed_mated_interfaces",
        "mated_interface_count": count,
        "contact_resistance_ohm_per_mated_interface": resistance,
        "total_connector_contact_resistance_ohm": count * resistance,
    }
