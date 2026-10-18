"""D6 adaptive loop tests: repeated rounds, lineage, negative paths, fake GPU refusal."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from adaptive_kuiper_loop import (
  anchors,append_log,canonical,digest,evaluate_ids,independent_code,
  loop,physical_receipt,select_next,variants,verify_log,VERSION)
from billion_case_space import (TOTAL,AXES,decode_offsets,encode_offsets,
  explicit_corner_ids,classify,case_tag)

class LoopTests(unittest.TestCase):
    def test_cpu_two_independent_expressions_agree_for_adversarial_corners(self):
        cases=explicit_corner_ids()
        self.assertEqual(len(cases),512)
        r=evaluate_ids(cases,"cpu")
        self.assertEqual(r,[independent_code(i) for i in cases])
    def test_real_d6_hot_connector_label_present_in_seed(self):
        seeds=anchors()
        self.assertEqual(len(seeds),len(set(seeds)))
        self.assertTrue(set(explicit_corner_ids()).issubset(set(seeds)))
        self.assertTrue(any(decode_offsets(i)[1]==6 for i in seeds))
    def test_next_selection_never_reuses_ids(self):
        ids,next_step=select_next(0,768,set(),[],0)
        self.assertEqual(len(ids),768)
        self.assertEqual(len(set(x[0] for x in ids)),768)
        mock=[{"index":i,"code":classify(i)} for i,why in ids]
        ids2,next_step=select_next(1,768,{i for i,why in ids},mock,next_step)
        self.assertEqual(len(ids2),768)
        self.assertFalse(set(i for i,why in ids).intersection(i for i,why in ids2))
        self.assertTrue(any(why.startswith("phase2") for i,why in ids2))
    def test_one_factor_neighbors_are_actual_distinct_cases(self):
        index=encode_offsets((3,6,0,13,7,6,8,5,0))
        for code in range(5):
            generated=variants(index,code)
            self.assertTrue(all(new_index!=index for new_index,reason in generated))
            for new_index,reason in generated:
                a=decode_offsets(index);b=decode_offsets(new_index)
                self.assertEqual(sum(x!=y for x,y in zip(a,b)),1)
    def test_run_three_cycles_appends_local_kuiper_history(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"loop"
            output=loop(p,iterations=3,batch=768)
            self.assertEqual(output["iterations"],3)
            self.assertEqual(output["actually_evaluated_distinct_synthetic_cases"],2304)
            self.assertFalse(output["CuPy_GPU_executed"])
            self.assertEqual(output["repeated_cases"],0)
            self.assertEqual(output["global_Kuiper_keys_allocated"],0)
            self.assertEqual(output["physical_netlists_run_by_this_loop"],0)
            log=verify_log(p/"kuiper-evidence.jsonl")
            self.assertEqual(log["unique_cases"],2304)
            self.assertEqual(log["iterations"],3)
            self.assertEqual(log["hash"],output["hashed_kuiper_ledger"]["hash"])
            self.assertEqual(len(list(p.glob("iteration-*.json"))),3)
    def test_existing_append_only_log_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"history"
            loop(p,iterations=1,batch=512)
            with self.assertRaises(FileExistsError):loop(p,iterations=1,batch=512)
    def test_log_digest_chain_detects_tampering(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"history"
            loop(p,iterations=1,batch=512)
            f=p/"kuiper-evidence.jsonl"
            rows=f.read_text().splitlines()
            first=json.loads(rows[0])
            first["screen_code"]=4
            first["code"]=4
            rows[0]=canonical(first)
            f.write_text("\n".join(rows)+"\n")
            with self.assertRaises(ValueError):verify_log(f)
    def test_gpu_refuses_missing_explicit_authorisation(self):
        with patch.dict(os.environ,{"V11_GPU_APPROVED":""}):
            with self.assertRaisesRegex(RuntimeError,"requires"):
                evaluate_ids([1,2],"gpu",approve_gpu=False)
    def test_bad_spice_receipt_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"bad.json"
            p.write_text(json.dumps({"status":"CERTIFIED","cases_executed":12}))
            with self.assertRaises(ValueError):physical_receipt(p)
    def test_fixed_current_d6_observation_is_not_lab_arc_result(self):
        e=physical_receipt(None)
        self.assertFalse(e["no_external_isolation_evidence"])
        self.assertFalse(e["fault_zones_validated"])
    def test_limits_enforced(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):loop(Path(d)/"t",iterations=0)
            with self.assertRaises(ValueError):select_next(0,2,set(),[],0)
    def test_iteration_algorithms_do_not_assign_safety_or_global_keys(self):
        with tempfile.TemporaryDirectory() as d:
            r=loop(Path(d)/"t",iterations=2,batch=512)
            self.assertIn("fault_class",r["inert_axes_in_screen"])
            self.assertFalse(r["CuPy_GPU_executed"])
            self.assertTrue(r["no_IEC_licensed_content"])
            self.assertEqual(r["physical_D6_spice"]["status"],"MISSING_REAL_SPICE_INPUT")

if __name__=="__main__":
    unittest.main(verbosity=2)
