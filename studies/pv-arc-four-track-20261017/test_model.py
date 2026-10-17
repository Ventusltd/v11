import json, unittest
from pathlib import Path
from model import analyse

class TestScreen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=json.loads(Path(__file__).with_name("illustrative-input.json").read_text())
        cls.a,cls.b=analyse(cls.c)["cases"]
    def test_count(self):
        self.assertEqual(self.a["topology"]["modules"],624)
        self.assertEqual(self.b["topology"]["mppt_groups"],20)
    def test_voltage(self):
        self.assertAlmostEqual(self.a["steady"]["cold_Voc_string_v"],1397.76)
    def test_switch_is_not_rated(self):
        self.assertFalse(self.a["switch_screen"]["ideal_rating_pass"])
        self.assertFalse(self.a["switch_screen"]["one_short_rating_pass"])
    def test_heat(self):
        self.assertAlmostEqual(self.a["switch_screen"]["pair_w_at_Impp"],17.496)
        self.assertAlmostEqual(self.a["switch_screen"]["shunt_w_at_Impp"],32.4)
    def test_group_backfeed(self):
        self.assertEqual(self.a["fault_envelopes"]["same_MPPT_group_other_strings_Isc_a"],39.0)
    def test_inverter_cap(self):
        self.assertEqual(self.a["steady"]["output_ac_kw"],350.0)
    def test_bad_topology(self):
        b=json.loads(json.dumps(self.c));b["cases"][0]["strings_per_mppt"]=5
        with self.assertRaises(ValueError):analyse(b)

if __name__=="__main__":unittest.main()
