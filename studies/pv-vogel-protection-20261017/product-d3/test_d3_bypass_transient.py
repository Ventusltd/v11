"""Deterministic D3 netlist and evidence sanity tests, NOT component qualification."""
import json
import tempfile
import unittest
from pathlib import Path
from d3_bypass_transient import (IDS, netlist, manifest, parse,
                                 MEASURE_KEYS, evaluate)

class D3Tests(unittest.TestCase):
    def test_nine_distinct_cases(self):
        self.assertEqual(len(IDS),9)
        self.assertEqual(len({row[0] for row in IDS}),9)
    def test_pair_has_two_fets_shared_source_and_floating_drive(self):
        n=netlist(IDS[0])
        self.assertIn("M1 d1 gate mid mid NTOY",n)
        self.assertIn("M2 d2 gate mid mid NTOY",n)
        self.assertIn("VDRIVE drv mid PULSE",n)
    def test_single_contains_body_diode_prone_mosfet(self):
        n=next(netlist(c) for c in IDS if c[0]=="single_fullsun_off_body_diode")
        self.assertIn("M1 d1 gate plus plus NTOY",n)
        self.assertNotIn("M2 d2 gate",n)
    def test_illuminated_off_should_be_represented(self):
        n=next(netlist(c) for c in IDS if c[0]=="pair_full_sun")
        self.assertIn("IPH 0 cell DC 18.402067",n)
        self.assertIn("PULSE(0 12 40u",n)
    def test_bypass_diode_faults(self):
        q={c[0]:netlist(c) for c in IDS}
        self.assertIn("ROPEN b_anode plus 1e12",q["pair_shaded_bypass_open"])
        self.assertIn("RSHORT b_anode plus .001",q["pair_shaded_bypass_short"])
    def test_disabled_gate_is_not_triggered(self):
        q=next(netlist(c) for c in IDS if c[0]=="pair_shaded_gate_lost")
        self.assertIn("VDRIVE drv mid DC 0",q)
    def test_failed_short_is_modelled_separately(self):
        q=next(netlist(c) for c in IDS if c[0]=="pair_fullsun_stuck_short")
        self.assertIn("RFAILED plus 0 .005",q)
    def test_no_iec_text_or_vendor_approval(self):
        for c in IDS:
            s=netlist(c)
            self.assertIn("MOSFET generic L1 surrogate",s)
            self.assertIn("DO NOT USE FOR ELECTRICAL HARDWARE",s)
    def test_generation(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)
            items=manifest(f)
            self.assertEqual(len(list(f.glob("*.cir"))),9)
            self.assertEqual(len(items),9)
            metadata=json.loads((f/"cases.json").read_text())
            self.assertFalse(metadata["licensed_iec_content_in_repo"])
    def test_measure_parser(self):
        l="\n".join(f"{key} = {i+1}.0000e+00" for i,key in enumerate(MEASURE_KEYS))
        out=parse(l)
        self.assertEqual(len(out),len(MEASURE_KEYS))
        self.assertEqual(out["vsub_on"],2.0)
    def test_parser_rejects_incomplete(self):
        with self.assertRaises(ValueError):parse("vsub_on = .5\n")
    def test_regression_for_body_diode_risk_gate(self):
        stub=lambda **kw:{k:0.0 for k in MEASURE_KEYS} | kw
        fake=[
            {"id":"pair_full_sun","measurements":stub(vsub_off=12.8)},
            {"id":"single_fullsun_off_body_diode","measurements":stub(vsub_off=0.6)},
            {"id":"pair_shaded","measurements":stub(isw_on=15.5,vgs_on=12,
                       diode_power_on=.01,sw_power_on=1.5)}
        ]
        q=evaluate(fake)
        self.assertEqual(q["pair_fets_off_full_sun_v"],12.8)
        fake[1]["measurements"]["vsub_off"]=12.8
        with self.assertRaises(AssertionError):evaluate(fake)

if __name__=="__main__":unittest.main(verbosity=2)
