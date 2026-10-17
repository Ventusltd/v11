"""Arithmetic/indexing tests only: do not treat as protection validation."""
import math
import unittest
from vogel_study import (
    GOLDEN_ANGLE, FAULTS, LEVELS, SAMPLES_PER_PAIR, kuiper_xy, vogel_disk,
    cold_voc_per_module, devices_per_plant, propagation_delay_us,
    one_case, calculate,
)

class VogelScreenTests(unittest.TestCase):
    def test_source_law(self):
        self.assertAlmostEqual(GOLDEN_ANGLE,math.pi*(3-math.sqrt(5)))
        self.assertAlmostEqual(math.hypot(*kuiper_xy(97)),math.sqrt(97))
    def test_key_strict(self):
        for x in [0,-1,1.3,True]:
            with self.assertRaises(ValueError): kuiper_xy(x)
    def test_stability(self):
        self.assertEqual(kuiper_xy(100),kuiper_xy(100))
        self.assertNotEqual(kuiper_xy(100),kuiper_xy(101))
    def test_disk(self):
        for k in range(1,SAMPLES_PER_PAIR+1):
            u,v=vogel_disk(k)
            self.assertLessEqual((2*u-1)**2+(2*v-1)**2,1.0000000001)
    def test_cold_voc(self):
        self.assertAlmostEqual(cold_voc_per_module(-10),49.593,places=3)
    def test_partial_four_module_groups(self):
        self.assertEqual([devices_per_plant(x) for x in LEVELS],[720,360,192,24])
    def test_cable_delay(self):
        self.assertAlmostEqual(propagation_delay_us(936),4.415,places=2)
    def test_loss_formula(self):
        p=one_case("parallel_arc",1,15)
        self.assertAlmostEqual(p["dissipation_w_per_unit"],
            p["current_a_assumed"]**2*p["series_r_ohm_assumed"],delta=.0001)
        self.assertEqual(p["physical_protection_status"],"NOT_EVALUATED")
    def test_all_2560_keys(self):
        keys=[one_case(f,l,s)["key"] for f in FAULTS for l in LEVELS
              for s in range(1,SAMPLES_PER_PAIR+1)]
        self.assertEqual(keys,list(range(1,2561)))
        self.assertEqual(len(set(keys)),2560)
    def test_summary(self):
        a=calculate()
        self.assertEqual(a["total_cases"],2560)
        self.assertIn("no probabilistic inference",a["method"])
    def test_inputs(self):
        with self.assertRaises(ValueError): one_case("invalid",1,1)
        with self.assertRaises(ValueError): one_case(FAULTS[0],5,1)
        with self.assertRaises(ValueError): vogel_disk(0)

if __name__ == "__main__":
    unittest.main(verbosity=2)
