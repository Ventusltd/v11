"""B2 deterministic numerical checks. Passing does NOT validate PV arc hardware."""
import math
import unittest
from dataclasses import replace
from pv_rlc_time_domain import (Config, CUT_SETS, fixture, parameters,
                                 string_v_from_i, run)

class B2NumericalTests(unittest.TestCase):
 def test_shared_fixture_and_parameters(self):
  f=fixture()
  self.assertIn("PROVISIONAL",f["status"])
  far=parameters(f,"C2-far")
  self.assertAlmostEqual(far["r_ohm"][0],.0339,places=6)
  self.assertAlmostEqual(far["r_ohm"][1],10.38018,places=5)
  self.assertAlmostEqual(far["c_f"],.00015)
 def test_phenomenological_IV_two_fixture_points(self):
  f=fixture();m=f["module"]
  self.assertAlmostEqual(string_v_from_i(0,f),45.75*30)
  self.assertAlmostEqual(string_v_from_i(m["impp_a"],f),m["vmpp_v"]*30,places=5)
  self.assertAlmostEqual(string_v_from_i(m["isc_a"],f),0)
 def test_source_switch_map_complete(self):
  self.assertEqual(set(CUT_SETS),{"P0","P1","P1b","P2","P2b","P3"})
  self.assertEqual(CUT_SETS["P3"],("S20","S19","CAP"))
 def test_all_off_at_initial_has_no_fault_feed(self):
  x=run(Config(action="P3",trip_at_s=0,horizon_s=.002)).outcome
  self.assertEqual(x["energy_fault_resistor_j"],0.0)
  self.assertEqual(x["energy_pv_source_j"],0.0)
  self.assertAlmostEqual(x["energy_cap_start_j"],x["energy_cap_end_j"],places=4)
  self.assertAlmostEqual(x["energy_residual_j"],0,delta=.0001)
 def test_equal_actions_no_trip_until_end(self):
  a=run(Config(action="P0",horizon_s=.003,trip_at_s=.003)).outcome
  b=run(Config(action="P3",horizon_s=.003,trip_at_s=.003)).outcome
  self.assertAlmostEqual(a["energy_fault_resistor_j"],b["energy_fault_resistor_j"],delta=.005)
 def test_model_energy_residual_far(self):
  for a in ("P0","P2","P2b","P3"):
   result=run(Config(location="C2-far",action=a,horizon_s=.006,trip_at_s=.002)).outcome
   self.assertLess(result["energy_residual_relative"],0.001,(a,result))
   self.assertEqual(result["arc_extinction"],"NOT_MODELLED_FIXED_SHUNT_RESISTOR")
 def test_model_energy_residual_near(self):
  for a in ("P0","P2","P2b","P3"):
   result=run(Config(location="C2-near",action=a,horizon_s=.004,trip_at_s=.001)).outcome
   self.assertLess(result["energy_residual_relative"],0.002,(a,result))
   self.assertEqual(result["switch_stress_vds"],"UNKNOWN")
 def test_some_capacitor_discharge_under_baseline(self):
  for loc in ("C2-far","C2-near"):
   r=run(Config(location=loc,action="P0",horizon_s=.005)).outcome
   self.assertLess(r["energy_cap_end_j"],r["energy_cap_start_j"])
   self.assertGreater(r["energy_fault_resistor_j"],0)
 def test_dump_captures_stored_current(self):
  r=run(Config(location="C2-far",action="P3",horizon_s=.006,trip_at_s=.002)).outcome
  self.assertGreater(r["energy_dump_j"],0)
  self.assertLess(r["energy_fault_resistor_j"],run(Config(location="C2-far",action="P0",horizon_s=.006)).outcome["energy_fault_resistor_j"])
 def test_near_far_not_identical(self):
  x=run(Config(location="C2-far",action="P0",horizon_s=.003)).outcome
  y=run(Config(location="C2-near",action="P0",horizon_s=.003)).outcome
  self.assertNotEqual(x["energy_fault_resistor_j"],y["energy_fault_resistor_j"])
 def test_timestep_convergence_at_millisecond_scale(self):
  base=Config(location="C2-far",action="P2",horizon_s=.003,trip_at_s=.001)
  a=run(replace(base,step_s=1e-6)).outcome
  b=run(replace(base,step_s=5e-7)).outcome
  self.assertLess(abs(a["energy_fault_resistor_j"]-b["energy_fault_resistor_j"]),
                  .015*max(1,b["energy_fault_resistor_j"]))
 def test_traced_samples_bounded_and_sorted(self):
  r=run(Config(action="P2",horizon_s=.001,trip_at_s=.0005,keep_samples=True))
  self.assertGreater(len(r.samples),5)
  self.assertEqual(r.samples[0]["t_s"],0)
  self.assertTrue(all(s["fault_a"]>=0 for s in r.samples))
  self.assertTrue(all(a["t_s"]<b["t_s"] for a,b in zip(r.samples,r.samples[1:])))
 def test_reject_bad_domains(self):
  with self.assertRaises(ValueError):run(Config(location="bad"))
  with self.assertRaises(ValueError):run(Config(fault_resistance_ohm=0))
  with self.assertRaises(ValueError):run(Config(trip_at_s=-1))
  with self.assertRaises(ValueError):run(Config(horizon_s=.00400001))

if __name__=="__main__":
 unittest.main(verbosity=2)
