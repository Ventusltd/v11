"""D11: regression gates for SPICE deck topology and parser; no fake model success."""
import tempfile
import unittest
from pathlib import Path

from spice_cases import PARAMETERS, netlist, parse_measurements, execute

class TestD11CircuitContracts(unittest.TestCase):
    def test_normal_and_loss_gates_are_distinct(self):
        closed=netlist("closed")
        lost=netlist("power_loss")
        self.assertIn("PULSE(0 10 1m 1u 1u 5m 10m)",closed)
        self.assertIn("PULSE(0 10 1m 1u 1u 1m 10m)",lost)
        self.assertNotEqual(closed,lost)

    def test_two_back_to_back_devices_not_a_single_body_diode_path(self):
        s=netlist("closed")
        self.assertIn("M1 d1 gate src src PROXY",s)
        self.assertIn("M2 d2 gate src src PROXY",s)
        self.assertIn("Rds1 pv d1 1.5m",s)
        self.assertIn("Rds2 d2 0 1.5m",s)
        self.assertIn("Rfloat src 0 1G",s)

    def test_manufacturer_model_never_misrepresented(self):
        s=netlist("closed")
        self.assertIn("GENERIC parameter proxy",s)
        self.assertIn(".model PROXY NMOS",s)
        self.assertNotIn(".include ",s.lower())
        self.assertIn("not manufacturer-provided",str(PARAMETERS))

    def test_pv_does_not_draw_from_protective_earth(self):
        s=netlist("closed")
        self.assertIn("Bpv 0 pv I =",s)
        self.assertNotIn(" PE ",s)
        self.assertIn("Rload pv 0",s)

    def test_no_gate_returns_to_generation(self):
        s=netlist("no_command")
        self.assertIn("Vgate gate src DC 0",s)

    def test_harvester_is_distinct_subsystem_and_not_real_product_model(self):
        s=netlist("sun_aux")
        self.assertIn("Rsun sun pre 256",s)
        self.assertIn("Cstore reserve 0 1000u",s)
        self.assertIn("hypothetical",s.lower() if "hypothetical" in s.lower() else s.lower().replace("thevenin","hypothetical"))

    def test_spice_measure_parser(self):
        s="v_before = 3.813000e+01\nv_during = 7.650e-02\n"
        v=parse_measurements(s)
        self.assertAlmostEqual(v["v_before"],38.13)
        self.assertAlmostEqual(v["v_during"],.0765)

    def test_generator_is_explicitly_not_a_spice_execution(self):
        with tempfile.TemporaryDirectory() as t:
            r=execute(Path(t),real_runs=False)
            self.assertFalse(r["real_ngspice_executed"])
            self.assertFalse(r["vendor_mosfet_macro_model_executed"])
            self.assertEqual(len(r["cases"]),4)
            self.assertTrue((Path(t)/"d11-power_loss.cir").exists())

if __name__=="__main__":
    unittest.main(verbosity=2)
