"""D10 hypothesis/negative-control tests. Not certification or arc tests."""
import unittest
import numpy as np
from module_shunt_power_loss import (
    VOC,VMPP,IMPP,ISC,MODULES,ipv,steady_v,close_smooth,
    available_pulse_j,power_failure,isolated_string_oc_v,report)

class TestPowerLossShunt(unittest.TestCase):
    def test_pv_iv_three_public_reference_anchors(self):
        np.testing.assert_allclose(ipv([0,VMPP,VOC]),[ISC,IMPP,0],atol=1e-10)

    def test_enhancement_mode_fet_not_held_on_without_gate_power(self):
        q=power_failure("volatile_enhancement_fet",reserve_cap_f=.002)
        self.assertFalse(q["remains_shorted_when_unpowered"])

    def test_latched_actuation_needs_some_stored_energy(self):
        q=power_failure("pulse_latched_contact",reserve_cap_f=0.)
        self.assertFalse(q["remains_shorted_when_unpowered"])

    def test_470uf_below_assumed_pulse_and_1000uf_above(self):
        self.assertLess(available_pulse_j(.00047),.05)
        self.assertGreater(available_pulse_j(.001),.05)
        self.assertFalse(power_failure("pulse_latched_contact",reserve_cap_f=.00047)["remains_shorted_when_unpowered"])
        self.assertTrue(power_failure("pulse_latched_contact",reserve_cap_f=.001)["remains_shorted_when_unpowered"])

    def test_mechanical_latch_remains_shorted_but_cannot_self_reset(self):
        a=power_failure("pulse_latched_contact",reserve_cap_f=.001)
        self.assertTrue(a["remains_shorted_when_unpowered"])
        self.assertFalse(a["reset_to_generation_power_available"])
        b=power_failure("pulse_latched_contact",reserve_cap_f=.001,auxiliary_reset_power=True)
        self.assertTrue(b["reset_to_generation_power_available"])

    def test_normal_closed_closes_without_electrical_reserve_but_needs_start_supply(self):
        q=power_failure("spring_normally_closed")
        self.assertTrue(q["remains_shorted_when_unpowered"])
        self.assertFalse(q["reset_to_generation_power_available"])
        self.assertTrue(q["needs_nonterminal_bootstrap_after_dark"])

    def test_nominal_active_shunt_reduces_module_to_0p1v_not_0v(self):
        q=close_smooth(.005,10e-6,.0002)
        self.assertEqual(q["initial_module_v"],VMPP)
        self.assertGreater(q["final_module_v"],.09)
        self.assertLess(q["final_module_v"],.1)
        self.assertLess(q["steady_shunt_heat_w"],2)
        self.assertAlmostEqual(q["final_module_v"]/.005,q["final_shunt_current_a"],places=7)

    def test_controlled_voltage_ramp_still_requires_pulsed_mosfet_soa(self):
        q=close_smooth(.005,10e-6,.0002)
        self.assertGreater(q["peak_shunt_current_a"],ISC)
        self.assertLess(q["peak_shunt_current_a"],40)
        self.assertGreater(q["peak_switch_instantaneous_w"],100)

    def test_energy_conservation_across_36_hypothetical_cap_slew_resistance_cases(self):
        for cap in (1e-9,1e-7,1e-5,1e-4):
            for dt in (.00005,.0002,.001):
                for r in (.001,.005,.012):
                    with self.subTest(C=cap,slew=dt,R=r):
                        q=close_smooth(r,cap,dt)
                        self.assertLess(abs(q["energy_ledger_error_j"]),2e-5)
                        self.assertGreaterEqual(q["peak_shunt_current_a"],q["final_shunt_current_a"])

    def test_large_cap_fast_ramp_current_exceeds_own_photocurrent(self):
        self.assertGreater(close_smooth(.005,1e-4,.00005)["peak_shunt_current_a"],50)

    def test_30_strings_zero_one_five_failed_short_bounds(self):
        self.assertAlmostEqual(isolated_string_oc_v(0),2.76)
        self.assertAlmostEqual(isolated_string_oc_v(1),48.418)
        self.assertGreater(isolated_string_oc_v(5),200)
        self.assertAlmostEqual(isolated_string_oc_v(30),MODULES*VOC)

    def test_no_silent_qualification_and_deterministic_receipt(self):
        a=report();b=report()
        self.assertEqual(len(a["36_control_ramp_stress_cases"]),36)
        self.assertTrue(a["NOT_QUALIFICATION"])
        self.assertIn("30-year life",str(a["unverified"]))
        self.assertIn("backfeed",str(a["unverified"]))
        self.assertIn("no private IEC",a["confidentiality"])
        self.assertEqual(a["sha256"],b["sha256"])

if __name__=="__main__": unittest.main(verbosity=2)
