from __future__ import annotations

import json
import math
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v11_simulation.model import (
    SimulationInputError,
    canonical_json,
    electrical_module_order,
    load_reference_block,
    simulate_block,
    simulate_comparison,
)


class SimulationEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference_path = ROOT / "reference" / "lab_inverter_block_24_strings.json"
        cls.reference = load_reference_block(cls.reference_path)

    def test_reference_inverter_block_is_24_by_30(self):
        result = simulate_block(self.reference, strategy="leapfrog")
        boundary = result["reference_boundary"]
        self.assertEqual(boundary["string_count"], 24)
        self.assertEqual(boundary["modules_per_string"], 30)
        self.assertEqual(boundary["module_count"], 720)
        self.assertAlmostEqual(boundary["dc_nameplate_power_kwp"], 475.2)
        self.assertAlmostEqual(boundary["inverter_apparent_power_kva"], 352.0)

    def test_laboratory_electrical_order_is_retained(self):
        ids = tuple(f"M{i:02d}" for i in range(1, 7))
        self.assertEqual(electrical_module_order(ids, "sequential"), ids)
        self.assertEqual(electrical_module_order(ids, "leapfrog"), ("M01", "M03", "M05", "M06", "M04", "M02"))

    def test_all_24_strings_are_allocated_to_12_mppts(self):
        result = simulate_block(self.reference, strategy="leapfrog")
        self.assertEqual(len(result["strings"]), 24)
        self.assertEqual({item["mppt_id"] for item in result["strings"]}, {f"MPPT-{i:02d}" for i in range(1, 13)})
        self.assertTrue(all(sum(item["mppt_id"] == mppt for item in result["strings"]) == 2 for mppt in {item["mppt_id"] for item in result["strings"]}))

    def test_leapfrog_removes_field_row_return_but_retains_factory_penalty(self):
        result = simulate_comparison(self.reference)
        delta = result["delta_leapfrog_minus_sequential"]
        expected_saved = -24 * 29 * self.reference["array"]["module_pitch_m"]
        self.assertAlmostEqual(delta["field_cable_length_m"], expected_saved)
        self.assertAlmostEqual(delta["factory_lead_length_m"], 24 * self.reference["array"]["leapfrog_factory_extra_m_per_string"])
        self.assertLess(delta["circuit_loss_kw"], 0.0)
        self.assertLess(delta["approximate_loop_area_m2"], 0.0)

    def test_cold_voc_and_transmission_line_are_physical(self):
        result = simulate_block(self.reference, strategy="leapfrog", overrides={"minimum_cell_temperature_c": -25.0})
        self.assertGreater(result["totals"]["cold_string_voc_v"], 30 * self.reference["module"]["voc_v"])
        line = result["transmission_line"]
        product = line["external_inductance_h_per_m"] * line["differential_capacitance_f_per_m"]
        expected = 4e-7 * math.pi * 8.8541878128e-12 * result["inputs"]["effective_relative_permittivity"]
        self.assertTrue(math.isclose(product, expected, rel_tol=1e-12))
        self.assertGreater(line["characteristic_impedance_ohm"], 0.0)

    def test_simulation_is_byte_stable_for_identical_inputs(self):
        left = simulate_comparison(self.reference, {"route_multiplier": 1.125, "operating_current_a": 13.7})
        right = simulate_comparison(self.reference, {"route_multiplier": 1.125, "operating_current_a": 13.7})
        self.assertEqual(canonical_json(left), canonical_json(right))
        self.assertEqual(left["comparison_hash"], right["comparison_hash"])

    def test_invalid_pair_geometry_is_rejected(self):
        with self.assertRaisesRegex(SimulationInputError, "spacing"):
            simulate_block(self.reference, strategy="leapfrog", overrides={"home_pair_separation_m": 0.001})

    def test_python_and_browser_javascript_agree(self):
        completed = subprocess.run(
            [sys.executable, "scripts/compare_python_js.py", "--overrides", json.dumps({"operating_current_a": 15.2, "route_multiplier": 0.91}), "--timeout-seconds", "20"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["pass"], payload)
        self.assertEqual(payload["checked_metrics"], 8)


if __name__ == "__main__":
    unittest.main()
