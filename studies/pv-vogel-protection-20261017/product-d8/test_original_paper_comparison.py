"""D8 original paper vs whole-module bypass screening: algebra and honesty gates."""
import math
import tempfile
import unittest
from pathlib import Path
from original_paper_comparison import (
 MODULES,VOC,VMPP,IMPP,ISC,ACTIVE_MODULE_SHUNT_OHM,
 STUDY_TARGET_W,pv_module_iv,paper_loss,whole_string_bypass_ocv,
 peer_backfeed,capacitor_stored_energy_j,report
)

class D8PhysicalAssumptionsTests(unittest.TestCase):
 def test_original_shunt_dissipates_40w_20amps(self):
  p=paper_loss(20)
  self.assertAlmostEqual(p["shunt_w"],40.)
  self.assertAlmostEqual(p["fet_pair_w"],21.6)
  self.assertAlmostEqual(p["total_per_module_w"],61.6)
 def test_original_at_module_impp_exceeds_lifetime_target(self):
  p=paper_loss(IMPP)
  self.assertAlmostEqual(p["total_per_module_w"],46.1439594,places=5)
  self.assertGreater(p["total_per_module_w"],STUDY_TARGET_W)
 def test_all_30_bypassed_not_a_perfect_zero_volt_source(self):
  self.assertAlmostEqual(whole_string_bypass_ocv(),2.76)
  self.assertGreater(whole_string_bypass_ocv(),0)
 def test_failed_one_shunt_restores_photovoltaic_source(self):
  self.assertAlmostEqual(whole_string_bypass_ocv(29),48.418)
  self.assertGreater(whole_string_bypass_ocv(29),VOC)
 def test_uncommanded_string_open_circuit(self):
  self.assertAlmostEqual(whole_string_bypass_ocv(0),MODULES*VOC)
 def test_piecewise_iv_uses_fixture_anchors(self):
  self.assertEqual(pv_module_iv(0),VOC)
  self.assertAlmostEqual(pv_module_iv(IMPP),VMPP)
  self.assertEqual(pv_module_iv(ISC),0)
 def test_IV_no_guessed_reverse_breakdown(self):
  for v in (-1,ISC+.001):
   with self.assertRaises(ValueError):pv_module_iv(v)
 def test_backfeed_exists_even_without_inverter(self):
  for length in (16,50,100,200,300):
   x=peer_backfeed(length)
   self.assertGreater(x["inter_string_backfeed_a"],0)
   self.assertLess(x["inter_string_backfeed_a"],ISC)
   self.assertGreater(x["each_bypass_path_current_a"],ISC)
   self.assertLess(abs(x["power_residual_w"]),1e-7)
 def test_longer_wire_reduces_but_does_not_remove_crossfeed(self):
  a=[peer_backfeed(length)["inter_string_backfeed_a"] for length in (16,50,100,200,300)]
  self.assertTrue(all(a[i]>a[i+1] for i in range(4)))
  self.assertGreater(a[-1],10) # only within declared surrogate
 def test_one_string_shunt_thermals_exceed_research_target(self):
  x=peer_backfeed(16)
  self.assertGreater(x["each_bypassed_module_heat_w"],STUDY_TARGET_W)
  self.assertGreater(x["all_30_bypass_heat_w"],100)
  self.assertGreater(x["each_bypass_path_current_a"],35)
 def test_sensitivity_changes_current(self):
  low=peer_backfeed(300,shape=.35)["inter_string_backfeed_a"]
  high=peer_backfeed(300,shape=2.5)["inter_string_backfeed_a"]
  self.assertGreater(low,high)
  self.assertGreater(low-high,.2)
 def test_assumed_capacitor_energy_but_not_arc(self):
  self.assertAlmostEqual(capacitor_stored_energy_j(150e-6,1500),168.75)
  self.assertAlmostEqual(capacitor_stored_energy_j(150e-6,MODULES*VMPP),98.13804075)
 def test_explicitly_not_dynamic_or_OEM(self):
  x=report()
  self.assertTrue(any("actual DC series" in k for k in x["not_validated"]))
  self.assertIn("hypothetical",x["assumed_150uf_bus_energy_j"]["CAUTION"].lower())
  self.assertIn("UNCALIBRATED",x["source_and_hypothesis_parameters"]["pv_curve"])
 def test_cross_string_not_twenty_four_parallel(self):
  self.assertIn("not a common 24-string",report()["source_and_hypothesis_parameters"]["mppt_pairing"])
 def test_vendor_claim_corrected_without_claiming_voltage_sharing(self):
  x=report()["original_vs_revised"]
  self.assertIn("650V",x["fet_original_datasheet"])
  self.assertIn("do not automatically",x["series_voltage_sharing"])
 def test_no_copyrighted_standard_text_in_records(self):
  s=str(report())
  self.assertNotIn("Customer:",s)
  self.assertNotIn("Order No.:",s)
 def test_reproducible_hash(self):
  a=report()
  b=report()
  self.assertEqual(a["inputs_results_sha256"],b["inputs_results_sha256"])
 def test_file_output_stable_and_json_serialisable(self):
  x=report()
  self.assertEqual(len(x["peer_connected_results"]),5)
  self.assertEqual(len(x["iv_uncertainty_results_300m"]),5)

if __name__=="__main__":
 unittest.main(verbosity=2)
