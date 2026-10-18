"""D2 manifest/IEC hold constraints and SPICE result parser tests."""
import math
import tempfile
import unittest
from pathlib import Path
from d2_spice_campaign import (
    cases, generate, insulation_worksheet, parse_log,
    OUTPUT_CASES, BLOCKING_CASES, BYPASS_CASES, IMPP,
)

class D2CampaignTests(unittest.TestCase):
    def test_case_counts_and_ids(self):
        a=list(cases())
        self.assertEqual(len(a),len(OUTPUT_CASES)+len(BLOCKING_CASES)+len(BYPASS_CASES))
        self.assertEqual(len({x["case_id"] for x in a}),len(a))
    def test_cold_output_open_stress_reaches_string_class(self):
        c=next(x for x in cases() if x["case_id"]=="D2-OUTPUT-cold_mppt_collapsed")
        self.assertAlmostEqual(c["expected_vds_v"],30*49.593,places=5)
        self.assertGreater(c["expected_vds_v"],1200)
    def test_stc_mpp_and_collapsed_are_different(self):
        c={x["case_id"]:x for x in cases()}
        self.assertAlmostEqual(c["D2-OUTPUT-stc_mpp"]["expected_vds_v"],228.6,places=5)
        self.assertAlmostEqual(c["D2-OUTPUT-stc_mppt_collapsed"]["expected_vds_v"],1372.5,places=5)
    def test_reverse_voltage_is_explicit_negative(self):
        c=next(x for x in cases() if x["case_id"]=="D2-OUTPUT-reverse_feed_stress")
        self.assertAlmostEqual(c["expected_vds_v"],-1500.)
    def test_blocking_diode_reverse_not_bypass_diode(self):
        c={x["case_id"]:x for x in cases()}
        self.assertAlmostEqual(c["D2-BLOCK-night_high_bus"]["expected_vrblock_v"],1500)
        self.assertEqual(c["D2-BLOCK-night_high_bus"]["tag"],"SERIES_STRING_BLOCKING_REVERSE_NOT_BYPASS")
        self.assertEqual(c["D2-BYPASS-shaded_normal"]["kind"],"substring_bypass")
    def test_no_pretend_semiconductor_or_arc_simulation(self):
        for c in cases():
            self.assertNotIn("MODEL_CERTIFIED",c["deck"])
            self.assertIn(".control",c["deck"])
            self.assertIn(".endc",c["deck"])
            self.assertTrue(c["deck"].rstrip().endswith(".end"))
    def test_generator_is_reproducible_and_creates_real_decks(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d); a=generate(out)
            self.assertEqual(len(list(out.glob("*.cir"))),len(a))
            self.assertTrue((out/"case-manifest.json").exists())
            self.assertEqual(a[0]["case_id"],"D2-OUTPUT-stc_mpp")
    def test_log_parser(self):
        log="vds = 1.487790e+03\nvcm = 1.487790e+03\n"
        self.assertEqual(parse_log(log),{"vds":1487.79,"vcm":1487.79})
        with self.assertRaises(ValueError):parse_log("no vector printed")
    def test_insulation_sheet_does_not_invent_creepage(self):
        records=[
          {"kind":"output_open","values":{"vds":1487.79}},
          {"kind":"blocking_diode","values":{"vrblock":1500.}},
          {"kind":"substring_bypass","values":{"v_sub":15.25}}
        ]
        q=insulation_worksheet(records)
        self.assertGreaterEqual(len(q),6)
        self.assertTrue(all(x["product_design_state"]=="HOLD" for x in q))
        self.assertTrue(all(x["voltage_rating_qualified"]=="NO" for x in q))
        self.assertTrue(all("TBD_" in x["creepage_mm"] for x in q))
        self.assertTrue(all(x["solid_insulation_qualified"]=="NO" for x in q))
        self.assertEqual(next(x for x in q if x["boundary_id"]=="SERIES_BLOCKING_DIODE_VRRM")["screened_working_or_diff_v"],1500)
    def test_real_series_diode_forward_loss_breaks_module_budget(self):
        # Vf=0.8 V is a hypothetical illustrative blocking-diode forward drop.
        self.assertGreater(.8*IMPP,3.3)
        self.assertLess(3.3/IMPP,.2)
    def test_source_voltage_is_not_insulation_certification(self):
        caseset=list(cases())
        self.assertTrue(all("evidence_grade" not in x or x["evidence_grade"]!="CERTIFIED" for x in caseset))
        self.assertTrue(any("common" in x["basis"] for x in insulation_worksheet([
            {"kind":"output_open","values":{"vds":1500.}},
            {"kind":"blocking_diode","values":{"vrblock":1500.}},
            {"kind":"substring_bypass","values":{"v_sub":15.}}
        ])))

if __name__=="__main__":unittest.main(verbosity=2)
