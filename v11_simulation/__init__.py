"""V11-native solar DC inverter-block simulation package."""

from .model import (
    load_reference_block,
    simulate_block,
    simulate_comparison,
    canonical_json,
    electrical_module_order,
)

__all__ = [
    "load_reference_block",
    "simulate_block",
    "simulate_comparison",
    "canonical_json",
    "electrical_module_order",
]
