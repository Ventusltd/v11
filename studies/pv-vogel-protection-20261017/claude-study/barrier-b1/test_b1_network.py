"""Arithmetic and circuit-topology regression tests only; NOT protection certification."""
import math
import unittest
from b1_network import (fixture, _edges, _reachable, parallel_fault_paths,
                        pv_current_for_terminal_voltage, illustrative_parallel_current,
                        c2_illustration, c1_loop_illustration, c3_hot_connector, report)

class B1CircuitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = fixture()
    def test_fixture_not_oem_verified(self):
        self.assertIn("PROVISIONAL", self.f["status"])
        self.assertEqual(self.f["plant"]["strings_per_mppt"], 2)
    def test_two_poles_each_have_a_path(self):
        edges=_edges("P0",self.f)
        for pole in ("p","n"):
            yes,length=_reachable(edges,"S20"+pole,"F20"+pole)
            self.assertTrue(yes); self.assertAlmostEqual(length,5)
    def test_baseline_both_illuminated_sources_can_feed_far_fault(self):
        p=parallel_fault_paths("C2-far","P0",self.f)
        self.assertTrue(p["pv_sources"]["S20"]["sustained_path"])
        self.assertTrue(p["pv_sources"]["S19"]["sustained_path"])
        self.assertTrue(p["mppt_input_capacitor_has_path"])
    def test_inverter_end_only_does_not_remove_S20(self):
        p=parallel_fault_paths("C2-far","P2",self.f)
        self.assertTrue(p["pv_sources"]["S20"]["sustained_path"])
        self.assertFalse(p["pv_sources"]["S19"]["sustained_path"])
        self.assertFalse(p["mppt_input_capacitor_has_path"])
    def test_array_end_only_does_not_remove_S19(self):
        p=parallel_fault_paths("C2-far","P2b",self.f)
        self.assertFalse(p["pv_sources"]["S20"]["sustained_path"])
        self.assertTrue(p["pv_sources"]["S19"]["sustained_path"])
        self.assertTrue(p["mppt_input_capacitor_has_path"])
    def test_double_end_isolation_cuts_sustained_sources(self):
        for loc in ("C2-far","C2-near"):
            p=parallel_fault_paths(loc,"P3",self.f)
            self.assertFalse(p["pv_sources"]["S20"]["sustained_path"])
            self.assertFalse(p["pv_sources"]["S19"]["sustained_path"])
            self.assertFalse(p["mppt_input_capacitor_has_path"])
            self.assertEqual(p["line_capacitive_energy"],"UNKNOWN_NOT_MODELLED")
            self.assertFalse(p["fault_interruption_proved"])
    def test_one_module_output_switch_is_array_source_cut_only(self):
        p=parallel_fault_paths("C2-far","P1",self.f)
        self.assertFalse(p["pv_sources"]["S20"]["sustained_path"])
        self.assertTrue(p["pv_sources"]["S19"]["sustained_path"])
    def test_substring_bypass_switch_does_not_cut_string_supply(self):
        p=parallel_fault_paths("C2-far","P1b",self.f)
        self.assertTrue(p["pv_sources"]["S20"]["sustained_path"])
        self.assertTrue(p["pv_sources"]["S19"]["sustained_path"])
    def test_resistance_far_s20(self):
        p=parallel_fault_paths("C2-far","P0",self.f)
        self.assertAlmostEqual(p["pv_sources"]["S20"]["loop_resistance_ohm_20c"],
                               2*5*.00339,places=6)
    def test_resistance_far_s19(self):
        p=parallel_fault_paths("C2-far","P0",self.f)
        self.assertAlmostEqual(p["pv_sources"]["S19"]["loop_resistance_ohm_20c"],
                               (2*600+2*(936-5))*.00339,places=6)
    def test_near_has_inverse_path_lengths(self):
        p=parallel_fault_paths("C2-near","P0",self.f)
        self.assertAlmostEqual(p["pv_sources"]["S20"]["plus_length_m"],931)
        self.assertAlmostEqual(p["pv_sources"]["S19"]["plus_length_m"],605)
    def test_illustrative_IV_fits_impp(self):
        m=self.f["module"]; self.assertAlmostEqual(
           pv_current_for_terminal_voltage(m["vmpp_v"]*30,self.f),m["impp_a"],places=6)
        self.assertAlmostEqual(pv_current_for_terminal_voltage(m["voc_stc_v"]*30,self.f),0)
        self.assertAlmostEqual(pv_current_for_terminal_voltage(0,self.f),m["isc_a"])
    def test_iv_current_monotonic(self):
        samples=[pv_current_for_terminal_voltage(v,self.f) for v in range(0,1373,10)]
        self.assertTrue(all(a>=b for a,b in zip(samples,samples[1:])))
    def test_bisection_consistency(self):
        r=10.0; vf=30.0
        i=illustrative_parallel_current(r,vf,self.f)
        self.assertAlmostEqual(i,pv_current_for_terminal_voltage(vf+i*r,self.f),places=6)
    def test_fault_energy_is_only_sustained_source_screen(self):
        p=c2_illustration("C2-far","P2",self.f)
        self.assertGreater(p["source_feed_current_a"],0)
        self.assertGreater(p["source_feed_energy_j_if_constant_for_horizon"],0)
        self.assertEqual(p["source_currents_a"]["S19"],0)
        q=c2_illustration("C2-far","P3",self.f)
        self.assertEqual(q["source_feed_energy_j_if_constant_for_horizon"],0)
        self.assertIn("line capacitance",q["energy_exclusions"])
    def test_c1_series_loop_cutset_not_arc_ignition(self):
        self.assertTrue(c1_loop_illustration("P0",self.f)["S20_series_source_load_loop_continuous"])
        self.assertFalse(c1_loop_illustration("P2",self.f)["S20_series_source_load_loop_continuous"])
        self.assertEqual(c1_loop_illustration("P0",self.f)["C1in_bypass_loop"],"UNASSESSED_ALTERNATE_PATH")
    def test_resistive_heating_and_unphysical_steady_state(self):
        c=c3_hot_connector(self.f,0.2)
        self.assertAlmostEqual(c["local_contact_heating_w_initial"],17.31**2*.2,places=3)
        self.assertEqual(c["detection"],"NOT_MODELLED")
        self.assertGreater(c["illustrative_linear_T_steady_c"],200)
        self.assertEqual(c["material_survival"],"UNKNOWN")
    def test_all_four_actions_reported(self):
        a=report()
        self.assertEqual(set(a["cases"]),{"C2-far","C2-near"})
        self.assertEqual(len(a["cases"]["C2-far"]),4)
        self.assertIn("NOT_PROTECTION_VALIDATION",a["status"])
    def test_bad_inputs(self):
        with self.assertRaises(ValueError): _edges("BAD",self.f)
        with self.assertRaises(ValueError): parallel_fault_paths("unrecognised","P0",self.f)
        with self.assertRaises(ValueError): illustrative_parallel_current(-1,30,self.f)

if __name__ == "__main__":
    unittest.main(verbosity=2)
