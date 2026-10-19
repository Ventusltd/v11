"""D11: parasitic-capacitance assertions and genuine ngspice deck guards."""
import math
import tempfile
import unittest
from pathlib import Path
from d11_parasitic_spice import (
    CISS_F,COSS_F,CRSS_F,CGS_F,CDS_F,VMPP,
    Case,cases,netlist,parse,run,declared_capacitance_energy_j)

class ParasiticCapacitanceTest(unittest.TestCase):
    def test_real_device_capacitance_arithmetic(self):
        self.assertAlmostEqual(CGS_F+CRSS_F,CISS_F)
        self.assertAlmostEqual(CDS_F+CRSS_F,COSS_F)
        self.assertAlmostEqual(COSS_F,1800e-12)
        self.assertAlmostEqual(CRSS_F,80e-12)

    def test_small_fet_coss_is_not_large_unknown_module_junction_cap(self):
        small=declared_capacitance_energy_j(COSS_F)
        large=declared_capacitance_energy_j(100e-6)
        self.assertAlmostEqual(small,.5*COSS_F*VMPP**2)
        self.assertGreater(large,10000*small)

    def test_ten_cases_include_control_and_gate_power_loss(self):
        x=cases()
        self.assertEqual(len(x),10)
        self.assertEqual(len(set(c.name for c in x)),10)
        self.assertEqual({c.drive_mode for c in x},{"off","close","power_loss"})

    def test_frame_only_is_capacitively_coupled_and_not_shunt_return(self):
        s=netlist(cases()[2])
        self.assertIn("CFRAMEPLUS p 0",s)
        self.assertIn("CFRAMEMINUS n 0",s)
        self.assertIn("RFRAME_REF n 0 1000Meg",s)
        self.assertNotIn("RSHUNT p 0",s)
        self.assertIn("RLOAD p n",s)
        self.assertIn("RLEAD p lead",s)

    def test_active_shunt_intrinsic_coss_crss_and_gate_are_explicit(self):
        s=netlist(cases()[3])
        self.assertIn("CBULKDS fet_d n",s)
        self.assertIn("CMILLER fet_d gate",s)
        self.assertIn("CGATESRC gate n",s)
        self.assertIn("RGATE drive gate",s)
        self.assertIn("SFET fet_d fet_r gate n",s)

    def test_no_unsupported_negatives(self):
        with self.assertRaises(ValueError):
            Case("bad",-1,0,0,0,5)
        with self.assertRaises(ValueError):
            Case("bad",0,0,0,0,0)
        with self.assertRaises(ValueError):
            Case("bad",0,0,0,0,5,"earth_return")

    def test_parse_fails_closed_on_missing_real_spice_measurements(self):
        with self.assertRaises(ValueError):
            parse("ngspice maybe finished no measurements")

    def test_spice_preparation_is_deterministic_and_not_an_execution_claim(self):
        with tempfile.TemporaryDirectory() as d:
            x=run(d,execute=False)
            self.assertEqual(x["case_count"],10)
            self.assertEqual(x["status"],"DECKS_PREPARED_NOT_EXECUTED")
            self.assertFalse(x["actual_arc_simulated"])
            self.assertFalse(x["sunrise_bootstrap_demonstrated"])
            self.assertEqual(len(list(Path(d).glob("*.cir"))),10)
            self.assertIn("not manufacturer macro",str(x["real_candidate_parts"]).lower())

    def test_energy_no_hidden_source(self):
        self.assertAlmostEqual(declared_capacitance_energy_j(100e-6,38.13),.072694845)
        self.assertAlmostEqual(declared_capacitance_energy_j(0),0.)
        with self.assertRaises(ValueError):
            declared_capacitance_energy_j(-1)

if __name__=="__main__":
    unittest.main(verbosity=2)
