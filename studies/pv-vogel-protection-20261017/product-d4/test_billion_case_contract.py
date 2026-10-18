"""Verify virtual billion-case cardinality and actual live Kuiper geometry exactly.

CPU only: proves index/geometry contract and bounded pilots, not 1bn solves.
"""
import json
import math
import unittest
from pathlib import Path
from billion_case_contract import (
    AXES, NAMES, RADICES, SIZE, TWO32, G32, KUIPER_BLOB, MODEL_STATUS,
    scheme, scheme_sha256, encode_indices, decode_indices, decode_case,
    kuiper_position, virtual_key, pilot_keys, pilot_receipt,
    simple_arithmetic_screen, IRRADIANCE, coprime_stride,
)

class BillionContractTests(unittest.TestCase):
    def test_real_billion_cartesian_not_billion_circuit_solutions(self):
        self.assertEqual(len(AXES),12)
        self.assertEqual(math.prod(RADICES),1_000_000_000)
        self.assertEqual(SIZE,1_000_000_000)
        self.assertEqual(len(KUIPER_BLOB),40)
    def test_axis_roundtrip_corners(self):
        all0=tuple(0 for _ in RADICES)
        allmax=tuple(r-1 for r in RADICES)
        self.assertEqual(encode_indices(all0),0)
        self.assertEqual(encode_indices(allmax),SIZE-1)
        for k in (0,1,2,256,SIZE//2,SIZE-2,SIZE-1):
            self.assertEqual(encode_indices(decode_indices(k)),k)
        with self.assertRaises(ValueError): decode_indices(SIZE)
        with self.assertRaises(ValueError): decode_indices(-1)
        with self.assertRaises(ValueError): encode_indices([0]*11)
    def test_every_axis_changes_key_and_is_unambiguous(self):
        for i,(name,values) in enumerate(AXES):
            probes=[0]*len(RADICES)
            probes[i]=len(values)-1
            idx=encode_indices(probes)
            self.assertEqual(decode_case(idx)[name],values[-1])
            self.assertNotEqual(idx,0)
    def test_law_is_hash_golden_angle_and_half_index_radial(self):
        first=kuiper_position(0)
        self.assertEqual(first["angle_word_u32"],0)
        self.assertAlmostEqual(first["radius"],math.sqrt(.5))
        self.assertAlmostEqual(first["x"],math.sqrt(.5))
        second=kuiper_position(1)
        self.assertEqual(second["angle_word_u32"],2654435769)
        self.assertAlmostEqual(second["radius"],math.sqrt(1.5))
        self.assertAlmostEqual(math.hypot(second["x"],second["y"]),second["radius"])
    def test_live_law_32bit_angle_wrap_not_radial_wrap(self):
        a=kuiper_position(0);b=kuiper_position(TWO32)
        self.assertEqual(a["angle_word_u32"],b["angle_word_u32"])
        self.assertAlmostEqual(a["turns"],b["turns"])
        self.assertGreater(b["radius"],a["radius"])
        with self.assertRaises(ValueError):kuiper_position(-1)
    def test_distinct_sensible_case_placement(self):
        sample=[kuiper_position(k) for k in (0,1,2,1000,999_999_999)]
        for p in sample:
            self.assertTrue(-1e-15<=p["turns"]<1)
            self.assertAlmostEqual(math.hypot(p["x"],p["y"]),p["radius"],delta=1e-8)
        self.assertEqual(len({p["angle_word_u32"] for p in sample}),len(sample))
    def test_scheme_is_content_addressed(self):
        self.assertEqual(scheme()["size"],SIZE)
        self.assertEqual(len(scheme_sha256()),64)
        self.assertEqual(scheme_sha256(),scheme_sha256())
        self.assertEqual(virtual_key(5),"v11.pv.d4-billion/v1/5")
        self.assertIn("NOT_A_VALIDATED",MODEL_STATUS)
    def test_pilot_is_bounded_coprime_and_deterministic(self):
        a=pilot_keys(128)
        self.assertEqual(a,pilot_keys(128))
        self.assertEqual(len(a),len(set(a)))
        self.assertEqual(a[0],0)
        self.assertEqual(a[-1],SIZE-1)
        self.assertEqual(math.gcd(coprime_stride(),SIZE),1)
        with self.assertRaises(ValueError):pilot_keys(SIZE+1)
    def test_bounded_pilot_never_claims_all_cases_done(self):
        r=pilot_receipt(128)
        self.assertEqual(r["declared_unique_cases"],SIZE)
        self.assertEqual(r["actually_examined_distinct_cases"],128)
        self.assertEqual(r["cuda_cases_executed"],0)
        self.assertEqual(r["ngspice_cases_executed_in_this_pilot"],0)
        self.assertTrue(r["cpu_pilot_only"])
    def test_cold_30_module_source_exceeds_1500_hypothetically(self):
        q=simple_arithmetic_screen(0)
        self.assertIn("ILLUSTRATIVE_COLD_STRING_ABOVE_1500",q["model_rejection_flags"])
        self.assertEqual(q["scenario"]["cell_temperature_c"],-30)
        self.assertEqual(q["electrical_screen"]["shunt_on_resistive_loss_w"],None)
    def test_control_failure_and_static_only_evidence(self):
        digits=[0]*len(RADICES)
        digits[NAMES.index("architecture")]=1
        digits[NAMES.index("externally_forced_current_a")]=3
        digits[NAMES.index("assumed_hot_pair_r_ohm")]=1
        digits[NAMES.index("controller_state")]=1
        q=simple_arithmetic_screen(encode_indices(digits))
        self.assertAlmostEqual(q["electrical_screen"]["shunt_on_resistive_loss_w"],
                               17.31**2*.005,delta=1e-7)
        self.assertIn("CONTROL_FAULT_NEEDS_FULL_NETLIST",q["model_rejection_flags"])
        self.assertIn("ARC_PLASMA_AND_REAL_SOURCE_TO_FAULT_UNMODELLED",q["model_rejection_flags"])
        self.assertNotIn("SAFE",q["evidence_grade"])
    def test_dark_module_current_without_backfeed_is_contradiction(self):
        d=[0]*len(RADICES)
        d[NAMES.index("irradiance_profile")]=4
        d[NAMES.index("externally_forced_current_a")]=3
        q=simple_arithmetic_screen(encode_indices(d))
        self.assertIn("PHYSICALLY_INCONSISTENT_CURRENT_WITHOUT_DECLARED_SOURCE",
                      q["model_rejection_flags"])
    def test_energy_is_cap_inventory_not_fault_energy(self):
        d=[0]*len(RADICES)
        d[NAMES.index("assumed_mppt_input_c_f")]=3
        d[NAMES.index("assumed_bus_state")]=3
        q=simple_arithmetic_screen(encode_indices(d))
        self.assertAlmostEqual(q["electrical_screen"]["input_cap_stored_energy_j_not_fault_energy"],
                               .5*.0005*1500**2)
        self.assertIn("HYPOTHETICAL_MPPT_CAP_STORED_ENERGY_GT_100J",
                      q["model_rejection_flags"])
        self.assertIn("fault-site energy",q["unproven"])
    def test_no_unlicensed_iec_normative_content(self):
        body=json.dumps(scheme())
        self.assertNotIn("creepage_mm",body)
        self.assertNotIn("clearance_mm",body)
        self.assertEqual(tuple(NAMES),tuple(k for k,_ in AXES))
    def test_static_viewer_contract(self):
        p=Path(__file__).parent/"wafer"/"case-schema.json"
        if not p.exists():self.skipTest("viewer schema not authored yet")
        self.assertEqual(json.loads(p.read_text(encoding="utf8")),scheme())
if __name__=="__main__":
    unittest.main(verbosity=2)
