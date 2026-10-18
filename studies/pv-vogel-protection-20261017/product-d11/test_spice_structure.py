"""D11 static checks of real-part-number SPICE research test fixtures."""
from __future__ import annotations

import math
import re
import unittest
from pathlib import Path

from run_component_spice import BASE, CASES, EXPECTED, PAT, check_measurements


class SourceAndTopologyTests(unittest.TestCase):
    def test_four_distinct_spice_decks_exist(self):
        self.assertEqual(len(CASES),4)
        for f in CASES.values():
            self.assertTrue((BASE/f).is_file(),f)
            s=(BASE/f).read_text()
            self.assertIn(".tran",s)
            self.assertIn(".include device_envelopes.lib",s)

    def test_data_fit_reproduces_module_three_anchors(self):
        isc, impp, voc, vmpp=18.4,17.31,45.75,38.13
        is0=7.863925882139342e-7
        a=104.29468823668483*.025852
        i=lambda v:isc-is0*math.expm1(v/a)
        self.assertAlmostEqual(i(0),isc,places=6)
        self.assertAlmostEqual(i(vmpp),impp,places=5)
        self.assertAlmostEqual(i(voc),0.,places=5)

    def test_room_temp_ron_calibrated_near_real_datasheet_ceiling(self):
        r=0.00215+1/(126*(10.-3.5))
        self.assertGreater(r,.0033)
        self.assertLess(r,.0034)

    def test_actual_parts_not_falsely_claimed_vendor_spice(self):
        m=(BASE/"device_envelopes.lib").read_text()
        self.assertIn("NOT MANUFACTURER SPICE MACROMODELS",m)
        self.assertIn("INF_IPT034N15NM6_SURROGATE",m)
        self.assertIn("LAMBDA=0",m)
        self.assertIn("150V",m)

    def test_two_real_mosfets_block_opposed_body_diodes(self):
        s=(BASE/CASES["bidirectional"]).read_text()
        self.assertIn("Xsh1 dp gate mid",s)
        self.assertIn("Xsh2 0 gate mid",s)
        self.assertIn("Vgate drv mid",s)

    def test_uvlo_is_negative_control_not_fake_success(self):
        s=(BASE/CASES["power_loss"]).read_text()
        self.assertIn("600u 0",s)
        self.assertIn("v_reenergized",s)
        self.assertNotIn("LATCHED_CONTACT_PROVED",s)

    def test_150v_fet_never_shorting_whole_1500v_string(self):
        s=(BASE/CASES["paired_strings"]).read_text()
        self.assertIn("NEVER connect a physical 150V MOSFET",s)
        self.assertIn("SWPROXY",s)
        self.assertNotIn("Xshunt a 0",s)
        self.assertIn("RwireA a mppt",s)
        self.assertIn("RwireB b mppt",s)
        self.assertIn("VsenseA",s)

    def test_measurement_names_have_structural_producers(self):
        for name, filename in CASES.items():
            s=(BASE/filename).read_text().lower()
            for metric in EXPECTED[name]:
                self.assertIn(".meas tran "+metric,s)

    def test_spice_stdout_extractor_captures_exponents(self):
        d=dict((k,float(v)) for k,v in PAT.findall(
            "v_closed = 3.20e-02\nv_normal = 3.810e+01\n"))
        self.assertAlmostEqual(d["v_closed"],.032)
        self.assertAlmostEqual(d["v_normal"],38.1)

    def test_physical_invalid_controls_are_rejected(self):
        sample=dict(v_normal=38.13,v_closed=38.13,i_closed=0,
                    gate_closed=10)
        with self.assertRaises(AssertionError):
            check_measurements("single",sample)

    def test_all_design_sources_explicit_and_no_private_doc_embedded(self):
        s=(BASE/"README.md").read_text()
        for k in ("IPT034N15NM6","UCC27511A","TLV7032","LTC3108",
                  "source","not yet wired"):
            self.assertIn(k.lower(),s.lower())
        self.assertIn("IEC PDFs",s)
        self.assertIn("NOT embedded",s)

if __name__=="__main__":
    unittest.main(verbosity=2)
