import json
import unittest
from pathlib import Path
from latest_iteration_sensitivity import calculate, INPUT

class PVLatestIterationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.o=calculate(json.loads(INPUT.read_text()))
    def test_nameplate(self):
        self.assertEqual(self.o["plant"]["dc_nameplate_kw"],475.2)
    def test_cold_voltage(self):
        self.assertAlmostEqual(self.o["plant"]["string_voc_cold_v"],1487.79)
    def test_module_voltage_separate_from_string(self):
        self.assertAlmostEqual(self.o["plant"]["module_voc_cold_v"],49.593)
    def test_shunt(self):
        self.assertAlmostEqual(self.o["dissipation_scenarios"]["published_100milliohm"]["shunt_w_per_module"],17.31**2*0.1,places=3)
    def test_fets(self):
        self.assertAlmostEqual(self.o["dissipation_scenarios"]["published_typ_25C"]["fets_w_per_module"],2*17.31**2*.027,places=3)
    def test_total(self):
        self.assertAlmostEqual(self.o["published_fets_and_shunt_loss_kw_at_impp"],33.224,places=2)
    def test_legacy_lowpass(self):
        self.assertLess(self.o["RC_1k_100nF"]["amplitude_30kHz"],0.06)
    def test_capacitor(self):
        self.assertAlmostEqual(self.o["snubber_energy_j"]["2.2uF_at_1500V_joule"],2.475,places=3)
    def test_backfeed_groups(self):
        self.assertAlmostEqual(self.o["plant"]["backfeed_assuming_only_two_strings_parallel_a"],18.4)
    def test_module_count(self):
        self.assertEqual(self.o["plant"]["module_total"],720)

if __name__=="__main__":unittest.main()
