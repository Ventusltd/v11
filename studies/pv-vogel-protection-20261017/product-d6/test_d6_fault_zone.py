"""D6 structural checks plus explicit negative result acceptance tests."""
import unittest
import tempfile
from pathlib import Path
from d6_fault_zone_spice import (Case,I_STC,R_FAULT,T_END_US,T_START_US,
  experiment_cases,circuit,parse_output,prepare,verify_physics,MEAS_NAMES)

class D6Tests(unittest.TestCase):
 def test_twelve_distinct_reproducible_cases(self):
  a=experiment_cases()
  self.assertEqual(len(a),12)
  self.assertEqual(len({x.name for x in a}),12)
 def test_named_terminals_and_diode_polarity(self):
  s=circuit(experiment_cases()[0])
  self.assertIn("DBY1 0 n1 DBY",s)
  self.assertIn("DBY3 n2 n3 DBY",s)
  self.assertIn("DBY2 dbtap2 n2 DBY",s)
  self.assertIn("VEXT n3 conntap DC 0",s)
  self.assertIn("M1 d1 gate mid mid NTOY",s)
  self.assertIn("M2 d2 gate mid mid NTOY",s)
 def test_inside_and_outside_defects_are_distinct_branches(self):
  a=circuit(Case("a","inside_substring",1000,True))
  b=circuit(Case("b","outside_module",1000,True))
  self.assertIn("RHOT2 sense2 n2 0.2",a)
  self.assertIn("REXT conntap out 0.2",b)
  self.assertIn("RHOT2 sense2 n2 0.00035",b)
  self.assertIn("REXT conntap out 0.00035",a)
 def test_on_off_gate_command(self):
  a=circuit(Case("a","inside_substring",100,False))
  b=circuit(Case("b","inside_substring",100,True))
  self.assertIn("VDRIVE drv mid DC 0",a)
  self.assertIn("PULSE(0 12 40u",b)
 def test_energy_uses_fault_branch_current(self):
  x=circuit(Case("a","inside_substring",100,True))
  self.assertIn("let rhot_power = ihot*ihot*0.2",x)
  self.assertIn("let rext_power = iext*iext*0.00035",x)
  self.assertIn("meas tran e_inside_j INTEG rhot_power",x)
 def test_no_real_arc_claim(self):
  self.assertIn("NOT A CALIBRATED PV ARC MODEL",circuit(experiment_cases()[0]))
 def test_parser_complete_metrics(self):
  l="\n".join(f"{x} = 1.234e-04" for x in MEAS_NAMES)
  self.assertEqual(len(parse_output(l)),len(MEAS_NAMES))
  with self.assertRaises(ValueError):parse_output("e_inside_j = 1e-5")
 def test_manifest_reproduces_all_12(self):
  with tempfile.TemporaryDirectory() as d:
   a=prepare(d);b=prepare(d)
   self.assertEqual(a,b)
   self.assertEqual(len(list(Path(d).glob("*.cir"))),12)
   self.assertEqual(a["status"],"GENERATED_NOT_EXECUTED")
   self.assertTrue(a["no_IEC_copyright_content"])
 def test_external_connector_arithmetic(self):
  joules=I_STC**2*R_FAULT*(T_END_US-T_START_US)*1e-6
  self.assertAlmostEqual(joules,0.0083881628,delta=.00001)
 def test_verifier_rejects_fake_protection(self):
  base={v:1e-6 for v in MEAS_NAMES}
  base["i_external_a"]=I_STC
  cases=[]
  for c in experiment_cases():
   q=base.copy()
   if c.fault_zone=="outside_module":
    q["e_external_j"]=.00001 if c.shunt_on else .008388
   cases.append({"name":c.name,"measurements":q})
  with self.assertRaises(AssertionError):verify_physics(cases)
 def test_illegal_zone_rejected(self):
  with self.assertRaises(ValueError):Case("bad","parallel_arc",100,True)
if __name__=="__main__":
 unittest.main(verbosity=2)
