"""Cross-check energy conservation and topology truth table, conditional only."""
import unittest
from b1_network import fixture,parallel_fault_paths,c2_illustration
from energy_ledger import energy_ledger

TRUTH = {
 "P0":(True,True),  # both PV sources can feed C2
 "P1":(False,True), # P1 module-output source cut; NOT rated in this study
 "P1b":(True,True), # bypassed substring switch
 "P2":(True,False),# inverter-end cutoff: own PV source remains
 "P2b":(False,True),# array-end cutoff: paired PV source remains
 "P3":(False,False)# both ends cut, but capacitance unknown
}
class SourceCutsetTests(unittest.TestCase):
 def test_explicit_manual_cutsets_both_fault_ends(self):
  f=fixture()
  for loc in ("C2-far","C2-near"):
   for act,expected in TRUTH.items():
    p=parallel_fault_paths(loc,act,f)
    got=tuple(p["pv_sources"][s]["sustained_path"] for s in ("S20","S19"))
    self.assertEqual(expected,got,(loc,act))
 def test_energy_conservation_at_all_actions_both_sites(self):
  for loc in ("C2-far","C2-near"):
   for act in TRUTH:
    d=energy_ledger(loc,act)
    self.assertAlmostEqual(d["pv_source_energy_j"],
       d["fault_energy_j"]+d["copper_heat_j"],delta=.0003)
 def test_energy_only_from_sources_still_connected(self):
  for loc in ("C2-far","C2-near"):
   p=energy_ledger(loc,"P2")
   self.assertEqual(p["sources"]["S19"]["pv_j"],0.0)
   self.assertGreater(p["sources"]["S20"]["fault_j"],0.0)
   q=energy_ledger(loc,"P3")
   self.assertEqual(q["pv_source_energy_j"],0.0)
   self.assertIn("input and line capacitors",q["not_accounted_for"])
 def test_copper_heating_is_not_fault_energy(self):
  p=energy_ledger("C2-far","P0")
  self.assertGreater(p["copper_heat_j"],0)
  self.assertGreater(p["pv_source_energy_j"],p["fault_energy_j"])
 def test_negative_horizon(self):
  with self.assertRaises(ValueError):energy_ledger("C2-far","P0",horizon_s=-1)

if __name__=="__main__": unittest.main(verbosity=2)
