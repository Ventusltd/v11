"""D4 CPU oracle and optional pinned GPU engine integration tests."""
import json
import math
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from gpu_parameter_sweep import (
    SIZE, AXES, NAMES, RADICES, LOSS_BUDGET_W,
    D3_SHUNT_A, EXPECTED_D3_W, GPU_ENGINE_SHA,
    decode_scalar, independent_scalar, independent_counts, run, engine_import,
)

class V11D4Tests(unittest.TestCase):
    def test_complete_small_grid(self):
        self.assertEqual(SIZE,17640)
        self.assertEqual(math.prod(RADICES),SIZE)
        self.assertEqual(len(NAMES),6)
    def test_d3_shunt_loss(self):
        self.assertAlmostEqual(D3_SHUNT_A**2*.005,EXPECTED_D3_W,delta=.0001)
    def test_ordinary_17a_series_diode_loss(self):
        self.assertGreater(.8*17.31,LOSS_BUDGET_W)
        self.assertAlmostEqual(LOSS_BUDGET_W/17.31**2,.011013359204715321)
    def test_all_cases_decode(self):
        self.assertEqual(decode_scalar(0),tuple(a[0] for a in AXES.values()))
        self.assertEqual(decode_scalar(SIZE-1),tuple(a[-1] for a in AXES.values()))
        with self.assertRaises(ValueError): decode_scalar(SIZE)
        with self.assertRaises(ValueError): decode_scalar(-1)
    def test_hard_fail_if_imposed_v_stress_at_rating(self):
        self.assertGreaterEqual(independent_scalar(0),0)
        # Selected explicit synthetic electrical counterexample: V=1500 and rating=80
        from itertools import product
        hits=0
        for idx in range(SIZE):
            current,r,d,v,rated,vf=decode_scalar(idx)
            if v==1500 and rated==80:
                self.assertEqual(independent_scalar(idx),2)
                hits+=1
        self.assertGreater(hits,0)
    def test_no_voltage_margin_claim(self):
        for idx in range(SIZE):
            current,r,d,v,rated,vf=decode_scalar(idx)
            if v>=rated:
                self.assertEqual(independent_scalar(idx),2)
    def test_no_pass_label(self):
        from gpu_parameter_sweep import LABELS
        self.assertEqual(set(LABELS),{"0","1","2","3"})
        self.assertNotIn("CERTIFIED",str(LABELS).upper())
    def test_scalar_oracle_counts_are_complete(self):
        c=independent_counts()
        self.assertEqual(len(c),4)
        self.assertEqual(sum(c),SIZE)
        self.assertGreater(min(c),0)
    def test_required_reference_engine_pinned(self):
        self.assertEqual(len(GPU_ENGINE_SHA),40)
        self.assertEqual(GPU_ENGINE_SHA,"bfdc344289c0f03093e0c65979487e9916ea1ef4")
    def test_refuse_unavailable_engine_without_fake_fallback(self):
        with patch.dict(os.environ,{"V11_GPU_ENGINE_DIR":""}):
            with self.assertRaisesRegex(RuntimeError,"SET V11_GPU_ENGINE_DIR"):
                engine_import()
    def test_reject_non_cuda_claim_implicit(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                run("auto",Path(folder)/"fake.json")
    def test_cpu_end_to_end_pinned_source(self):
        if not os.environ.get("V11_GPU_ENGINE_DIR"):
            self.skipTest("requires pinned read-only reference checkout; CI supplies it")
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"receipts"/"cpu.json"
            out=run("cpu",p)
            self.assertTrue(p.is_file())
            self.assertEqual(out["backend_actually_executed"],"numpy")
            self.assertEqual(out["cpu_oracle_all_cases"],SIZE)
            self.assertEqual(out["backend_parity_cases"],SIZE)
            self.assertEqual(out["backend_parity_differences"],0)
            self.assertEqual(sum(out["verdict_counts"]),SIZE)
            self.assertEqual(len(out["input_and_verdict_digest_sha256"]),64)
            again=json.loads(p.read_text())
            self.assertEqual(again["verdict_counts"],out["verdict_counts"])
            self.assertEqual(out["evidence_grade"],"synthetic_electrical_screen_only")
            self.assertIn("PV arc extinction",out["not_proven"])
    def test_gpu_never_masquerades_as_numpy(self):
        if not os.environ.get("V11_GPU_ENGINE_DIR"):
            self.skipTest("reference engine unavailable")
        if os.environ.get("V11_D4_REQUIRE_GPU") != "1":
            self.skipTest("GPU explicit opt-in only, CPU CI doesn't require CUDA")
        with tempfile.TemporaryDirectory() as d:
            outcome=run("gpu",Path(d)/"gpu.json")
            self.assertEqual(outcome["backend_actually_executed"],"cupy")
            self.assertEqual(outcome["backend_parity_differences"],0)

if __name__=="__main__":
    unittest.main(verbosity=2)
