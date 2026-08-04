from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from v11_simulation.connectors import connector_accounting, resistance_accounting
from v11_simulation.model import canonical_json, load_reference_block, simulate_block

ROOT = Path(__file__).resolve().parents[1]


class ConnectorAccountingTests(unittest.TestCase):
    def test_owner_authority_examples(self):
        expected = {
            30: (66, 33, 33, 33),
            28: (62, 31, 31, 31),
            20: (46, 23, 23, 23),
        }
        for modules, values in expected.items():
            with self.subTest(modules=modules):
                accounting = connector_accounting(modules)
                self.assertEqual(
                    (
                        accounting["complete_system_connector_end_count"],
                        accounting["total_mated_interface_count"],
                        accounting["positive_connector_end_count"],
                        accounting["negative_connector_end_count"],
                    ),
                    values,
                )
                self.assertEqual(
                    accounting["complete_system_connector_end_count"],
                    2 * accounting["total_mated_interface_count"],
                )

    def test_default_subsystem_counts(self):
        accounting = connector_accounting(30)
        self.assertEqual(accounting["module_connector_end_count"], 60)
        self.assertEqual(accounting["string_cable_connector_end_count"], 4)
        self.assertEqual(accounting["inverter_connector_end_count"], 2)
        self.assertEqual(accounting["module_to_module_mate_count"], 29)
        self.assertEqual(accounting["module_to_string_cable_mate_count"], 2)
        self.assertEqual(accounting["string_cable_to_inverter_mate_count"], 2)
        self.assertEqual(accounting["loose_module_connector_end_count_before_home_runs"], 2)

    def test_reference_uses_completed_interface_count(self):
        reference = json.loads((ROOT / "reference/lab_inverter_block_24_strings.json").read_text())
        conductors = reference["conductors"]
        accounting = connector_accounting(reference["array"]["modules_per_string"])
        self.assertEqual(conductors["connector_count_per_string"], 33)
        self.assertEqual(
            conductors["connector_count_per_string"],
            accounting["total_mated_interface_count"],
        )
        self.assertNotEqual(conductors["connector_count_per_string"], 31)
        self.assertEqual(
            conductors["connector_count_per_string_status"],
            "deprecated_compatibility_projection",
        )

    def test_provisional_resistance_policy_is_explicit(self):
        policy = resistance_accounting(30, 0.00035)
        self.assertEqual(policy["mated_interface_count"], 33)
        self.assertEqual(policy["applies_to"], "all_completed_mated_interfaces")
        self.assertEqual(policy["evidence_state"], "provisional_fixture")
        self.assertAlmostEqual(policy["total_connector_contact_resistance_ohm"], 0.01155)

    def test_python_simulation_ignores_deprecated_compatibility_count(self):
        reference = load_reference_block(ROOT / "reference/lab_inverter_block_24_strings.json")
        expected = simulate_block(reference, strategy="leapfrog")

        stale = deepcopy(reference)
        stale["conductors"]["connector_count_per_string"] = 999
        stale_result = simulate_block(stale, strategy="leapfrog")

        absent = deepcopy(reference)
        absent["conductors"].pop("connector_count_per_string")
        absent_result = simulate_block(absent, strategy="leapfrog")

        self.assertEqual(canonical_json(stale_result), canonical_json(expected))
        self.assertEqual(canonical_json(absent_result), canonical_json(expected))


if __name__ == "__main__":
    unittest.main()
