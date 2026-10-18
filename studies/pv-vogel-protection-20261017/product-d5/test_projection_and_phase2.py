"""D5 bounded projection and Phase II audit tests; no empirical fault claims."""
import json
import tempfile
import unittest
from pathlib import Path
from kuiper_projection import build_projection, generate, CHART_SCHEMA
from phase2_evidence import analysis,run

class D5ProjectionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.projection=build_projection(512)
 def test_exact_corner_projection(self):
  p=self.projection
  self.assertEqual(p["schema"],CHART_SCHEMA)
  self.assertEqual(p["projected"],512)
  self.assertEqual(p["distinct_projected"],512)
  self.assertEqual(p["declared_input_space"],1_073_741_824)
 def test_projection_has_no_global_key_claim(self):
  p=self.projection
  self.assertIn("LOCAL",p["identity"])
  self.assertTrue(p["input_space_not_physically_simulated"])
  self.assertFalse(p["GPU_execution_claimed"])
 def test_projected_points_are_unique(self):
  p=self.projection
  self.assertEqual(len({x["local_case_id"] for x in p["points"]}),512)
  self.assertEqual(len({x["local_index"] for x in p["points"]}),512)
 def test_versions_are_not_silently_combined(self):
  l=build_projection(512,"legacy-golden-angle")
  self.assertNotEqual(self.projection["coordinate_law"],l["coordinate_law"])
  self.assertNotAlmostEqual(self.projection["points"][1]["x"],l["points"][1]["x"])
 def test_bounded_more_than_50k_is_rejected(self):
  with self.assertRaises(ValueError):build_projection(50_001)
  with self.assertRaises(ValueError):build_projection(200)
 def test_generate_digest_reproducible(self):
  with tempfile.TemporaryDirectory() as d:
   one=generate(Path(d)/"one.json",512)
   two=generate(Path(d)/"two.json",512)
   self.assertEqual(one["sha256"],two["sha256"])
   self.assertEqual(json.loads((Path(d)/"one.json").read_text())["sha256"],one["sha256"])
 def test_phase2_refuses_unverified_physics_promotion(self):
  x=analysis(self.projection,24)
  self.assertFalse(x["graph"]["causal_edges_claimed"])
  self.assertFalse(x["global_faraday_numbers_assigned"])
  self.assertEqual(x["review_count"],24)
  self.assertFalse(any(z[2]=="proven" for z in x["graph"]["edges"]))
 def test_phase2_typed_graph_only(self):
  from phase2_evidence import VOCAB
  a=analysis(self.projection,24)
  self.assertTrue(all(e[2] in VOCAB for e in a["graph"]["edges"]))
  self.assertTrue(all(n["status"]=="NOT_PHYSICALLY_VALIDATED"
                 for n in a["graph"]["nodes"] if n["kind"]=="hypothesis_case"))
 def test_faraday_negative_cases_preserved(self):
  a=analysis(self.projection,24)
  self.assertTrue(all(x["refuted_if"] for x in a["faraday_style_proposals"]))
  self.assertTrue(any(x["result"]=="NOT_RUN" for x in a["faraday_style_proposals"]))
 def test_review_shortlist_cross_codes_when_possible(self):
  a=analysis(self.projection,48)
  possible=sum(n>0 for n in a["screen_counts_in_projection"].values())
  actual=len(set(q["screen_code"] for q in a["review_cases"]))
  self.assertGreaterEqual(actual,min(3,possible))
 def test_phase2_rejects_untraced_status(self):
  p=dict(self.projection);p["input_space_not_physically_simulated"]=False
  with self.assertRaises(ValueError):analysis(p)
 def test_production_artefacts_need_no_iec_text(self):
  p=analysis(self.projection)
  self.assertFalse(p["licensed_IEC_text_in_export"])
  self.assertEqual(p["evidence_grade"],"synthetic_triage_not_circuit_validation")
 def test_script_emits_graph(self):
  with tempfile.TemporaryDirectory() as d:
   source=Path(d)/"projection.json";out=Path(d)/"phase2.json"
   generate(source,512)
   result=run(source,out,shortlist=20)
   self.assertTrue(out.exists())
   self.assertEqual(len(result["review_cases"]),20)
if __name__=="__main__":unittest.main(verbosity=2)
