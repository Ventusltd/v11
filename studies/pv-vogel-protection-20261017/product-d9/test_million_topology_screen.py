"""D9 controls: algebra, current-source limits, false-safety rejection, repeatability."""
import math
import unittest

import numpy as np

from million_topology_screen import (
    ISC, N, VOC, VMPP, IMPP, TOPOLOGIES,
    _base_physics, _pv_voltage, _samples, evaluate_candidate,
    normal_paper_loss_w, residual_shunted_string_v, run,
    unblocked_peer_backfeed,
)


class OneMillionStudyTests(unittest.TestCase):
    def test_original_disclosure_conditional_loss_is_not_a_new_design_spec(self):
        self.assertAlmostEqual(normal_paper_loss_w(), 46.1439594)
        self.assertAlmostEqual(normal_paper_loss_w(20), 61.6)

    def test_three_anchor_pv_surrogate_not_real_cell_arc(self):
        i=np.array([0.,IMPP,ISC])
        v=_pv_voltage(i,np.full(3,ISC),np.ones(3),np.full(3,VOC))
        np.testing.assert_allclose(v,[VOC,VMPP,0.],atol=1e-12)

    def test_opposing_peer_can_backfeed_a_complete_shunt_string(self):
        one=np.ones(1)
        peer=unblocked_peer_backfeed(
            18.4*one,18.4*one,0.005*one,16*one,20*one,one,VOC*one)
        self.assertGreater(float(peer[0]),18.0)
        self.assertLess(float(peer[0]),18.4)
        heat_hot=0.005*(18.4+float(peer[0]))**2
        self.assertGreater(heat_hot,6.)
        self.assertLess(heat_hot,7.)

    def test_fault_injection_residual_voltage_and_substring_hypothesis(self):
        x=np.array([0,1,2,3])
        a=residual_shunted_string_v(x,18.4,.005,VOC,substrings=1)
        b=residual_shunted_string_v(x,18.4,.005,VOC,substrings=3)
        self.assertAlmostEqual(float(a[0]),2.76)
        self.assertGreater(float(a[2]),90.)
        self.assertLess(float(b[3]),60.)
        self.assertGreater(float(a[1]),float(b[1]))

    def test_inputs_outside_declared_fault_units_are_rejected(self):
        with self.assertRaises(ValueError):
            residual_shunted_string_v(31,ISC,.005,VOC,substrings=1)
        with self.assertRaises(ValueError):
            residual_shunted_string_v(-1,ISC,.005,VOC,substrings=3)
        with self.assertRaises(ValueError):
            residual_shunted_string_v(0,ISC,.005,VOC,substrings=2)

    def test_individual_string_shunting_cannot_claim_common_bus_suppression(self):
        rng=np.random.default_rng(900)
        x=_samples(rng,250)
        phys=_base_physics(x)
        solo=next(t for t in TOPOLOGIES if t["key"]=="single_module_shunt_reverse_block")
        result=evaluate_candidate(x,phys,solo)
        self.assertFalse(result["external_zone_covered"])
        self.assertEqual(len(result["heat"]),250)
        self.assertGreater(float(np.min(phys["feed_a"])),0.)

    def test_reverse_blocking_assumption_removes_peak_peer_conduction_only(self):
        rng=np.random.default_rng(911)
        x=_samples(rng,1000)
        phys=_base_physics(x)
        unblocked=next(t for t in TOPOLOGIES if t["key"]=="paired_module_shunt")
        blocked=next(t for t in TOPOLOGIES if t["key"]=="paired_module_shunt_reverse_block")
        a=evaluate_candidate(x,phys,unblocked)
        b=evaluate_candidate(x,phys,blocked)
        self.assertTrue(np.all(a["heat"] >= b["heat"]-1e-12))
        self.assertTrue(np.any(a["heat"] > b["heat"]+1.))
        self.assertTrue(a["external_zone_covered"])
        self.assertTrue(b["external_zone_covered"])

    def test_stress_receipt_reproducible_for_fixed_seed_chunk_size(self):
        a=run(iterations=3000,seed=99,chunk_size=750)
        b=run(iterations=3000,seed=99,chunk_size=750)
        self.assertEqual(a["receipt_sha256"],b["receipt_sha256"])
        self.assertEqual(a["only_priority_topologies_for_followup"],
                         b["only_priority_topologies_for_followup"])

    def test_select_only_three_multi_string_proposals(self):
        record=run(iterations=7000,seed=20261018,chunk_size=1700)
        self.assertEqual(record["scenario_count"],7000)
        self.assertEqual(record["candidate_topologies_evaluated"],6)
        winners=record["only_priority_topologies_for_followup"]
        self.assertEqual(len(winners),3)
        self.assertEqual(len(set(w["topology"] for w in winners)),3)
        for w in winners:
            self.assertTrue(w["requires_both_strings_commanded"])
            self.assertEqual(w["statistics"]["scenarios"],7000)
            self.assertLessEqual(w["statistics"]["joint_screen_fraction"],1)
            self.assertIn("NOT_probability",next(iter(
                [k for k in w if "NOT_probability" in k])))
        self.assertIn("NOT field probability",str(record["screening_envelope"]))
        self.assertTrue(any("plasma" in x for x in record["must_falsify_next"]))

    def test_no_earth_as_operational_sink(self):
        record=run(iterations=100,seed=71,chunk_size=50)
        source=str(record)
        self.assertIn("do not use PE",source)
        self.assertNotIn("earth_as_shunt",source)


if __name__=="__main__":
    unittest.main(verbosity=2)
