"""D10 hypothesis/negative-control tests. Not certification or arc tests."""
import unittest
import numpy as np
from module_shunt_power_loss import (
    VOC,VMPP,IMPP,ISC,MODULES,ipv,steady_v,close_smooth,
    available_pulse_j,power_failure,isolated_string_oc_v,report,
    sunlight_powered_bootstrap)

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


    def test_2025_sun_gate_does_not_see_over_15v_while_module_hard_shorted(self):
        x=sunlight_powered_bootstrap(illumination=1.,mode="terminal_15v_gate",elapsed_s=10.)
        self.assertLess(x["terminal_voltage_while_shunted_v"],.10)
        self.assertFalse(x["original_sun_gate_above_15v"])
        self.assertEqual(x["hypothetical_harvest_net_w"],0.)
        self.assertFalse(x["conditional_reset_possible"])

    def test_independent_sun_power_could_recharge_reserve_in_daylight(self):
        x=sunlight_powered_bootstrap(
            illumination=1.,mode="independent_solar_harvester",elapsed_s=1.)
        self.assertAlmostEqual(x["hypothetical_harvest_net_w"],.145)
        self.assertGreater(x["usable_12_to_6v_j"],.05)
        self.assertLess(x["time_to_full_reserve_s"],1.)
        self.assertTrue(x["conditional_reset_possible"])
        self.assertFalse(x["real_harvester_or_fault_clearance_circuit_verified"])

    def test_sun_not_sufficient_for_safe_restart_while_fault_active(self):
        x=sunlight_powered_bootstrap(
            illumination=1.,mode="independent_solar_harvester",
            elapsed_s=10.,fault_clear=False)
        self.assertTrue(x["reservoir_full"])
        self.assertFalse(x["conditional_reset_possible"])

    def test_no_sun_or_too_little_charge_prevents_reset(self):
        for irr,secs in ((0.,1000.),(1.,0.),(.1,.01)):
            with self.subTest(irr=irr,sec=secs):
                x=sunlight_powered_bootstrap(
                    illumination=irr,mode="independent_solar_harvester",
                    elapsed_s=secs)
                self.assertFalse(x["conditional_reset_possible"])

    def test_ultra_low_input_boost_is_explicit_unverified_counterfactual(self):
        x=sunlight_powered_bootstrap(
            illumination=1.,mode="hypothetical_ultra_low_v_shunt_boost",
            elapsed_s=2.)
        self.assertTrue(x["conditional_reset_possible"])
        self.assertFalse(x["real_harvester_or_fault_clearance_circuit_verified"])
        shaded=sunlight_powered_bootstrap(
            illumination=.2,mode="hypothetical_ultra_low_v_shunt_boost",
            elapsed_s=100.)
        self.assertFalse(shaded["conditional_reset_possible"])

    def test_sun_logic_provenance_and_full_recovery_study_in_receipt(self):
        r=report()
        self.assertIn(">15V",r["original_sun_logic_source"])
        self.assertEqual(len(r["solar_bootstrap_counterexamples"]),3)
        self.assertTrue(any(x["conditional_reset_possible"] for x in r["solar_bootstrap_counterexamples"]))
        self.assertTrue(any(not x["conditional_reset_possible"] for x in r["solar_bootstrap_counterexamples"]))

if __name__=="__main__": unittest.main(verbosity=2)
