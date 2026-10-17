"""Unit tests for experiments/sampling_benchmark.py (Track D, W06).

Geometry/reproducibility tests only: nothing here validates any PV, arc or protection physics, and no test result is a
probability of anything physical.

Run from claude-study/:  python3 -B -m unittest -v experiments/test_sampling_benchmark.py
"""
import hashlib
import importlib.util
import itertools
import math
import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True        # keep __pycache__ out of the study tree even without `python3 -B`
sys.path.insert(0, str(HERE))
import sampling_benchmark as sb  # noqa: E402

PHASE0_SCRIPT = HERE.parent.parent / "vogel_study.py"   # studies/pv-vogel-protection-20261017/vogel_study.py


def _load_phase0():
    """Import the frozen Phase 0 module read-only, without writing bytecode next to it."""
    spec = importlib.util.spec_from_file_location("vogel_study_phase0_readonly", PHASE0_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


class VogelGeometry(unittest.TestCase):
    def test_golden_angle_matches_source_law(self):
        self.assertEqual(sb.GOLDEN, math.pi * (3 - math.sqrt(5)))

    def test_vogel_points_lie_in_disk(self):
        for n in sb.BUDGETS:
            p = sb.vogel_disk(n)
            r2 = (2 * p[:, 0] - 1) ** 2 + (2 * p[:, 1] - 1) ** 2
            self.assertTrue(np.all(r2 <= 1.0 + 1e-12), f"N={n}")
            self.assertTrue(np.all((p >= 0.0) & (p <= 1.0)))
            for d in sb.DIMS:
                for seed in sb.SEEDS:
                    x = sb.vogel_paired(n, d, seed)
                    self.assertTrue(np.all(sb.inside_pair_disks(x)), f"N={n} d={d} seed={seed}")

    def test_vogel2d_is_exactly_phase0(self):
        if not PHASE0_SCRIPT.exists():
            self.skipTest("Phase 0 vogel_study.py not present")
        phase0 = _load_phase0()
        ours = sb.vogel_disk(64)
        for s in range(1, 65):
            self.assertEqual(tuple(ours[s - 1]), phase0.vogel_disk(s, 64))   # bit-identical arithmetic

    def test_golden_lattice_is_preimage_of_phase0_disk(self):
        for n in sb.BUDGETS:
            np.testing.assert_allclose(sb.polar_equal_area_map(sb.golden_lattice(n)), sb.vogel_disk(n),
                                       rtol=0, atol=1e-12)

    def test_vogel_paired_pairs_are_permutations_of_the_disk(self):
        n, d, seed = 256, 6, 3
        x = sb.vogel_paired(n, d, seed)
        disk = sb.vogel_disk(n)
        np.testing.assert_array_equal(x[:, 0:2], disk)            # pair 1 keeps Phase 0 order
        key = np.lexsort(disk.T[::-1])
        for p in (1, 2):
            block = x[:, 2 * p:2 * p + 2]
            np.testing.assert_array_equal(block[np.lexsort(block.T[::-1])], disk[key])
            self.assertFalse(np.array_equal(block, disk))          # but in a different order
        np.testing.assert_array_equal(sb.vogel_paired(n, d, seed), x)
        self.assertFalse(np.array_equal(sb.vogel_paired(n, d, seed + 1), x))
        self.assertTrue(np.array_equal(sb.vogel_paired(n, 2, 0), sb.vogel2d(n, 2)))

    def test_identity_tiling_duplicates_axes(self):
        x = sb.vogel2d(64, 4)
        np.testing.assert_array_equal(x[:, 0:2], x[:, 2:4])
        self.assertAlmostEqual(sb.max_abs_axis_correlation(x), 1.0, places=12)

    def test_vertex_boxes_unreachable_by_disk(self):
        s_star = 0.5 - 0.5 / math.sqrt(2)                          # nearest disk point to a vertex box
        self.assertLess(sb.CORNER_BOX_SIDE, s_star)
        self.assertLess(sb.CORNER_METRIC_SIDE, s_star)
        self.assertLess(1 - sb.CORNER6D_LO, s_star)
        self.assertGreater(math.sqrt(2) * (sb.HOLDOUT_LO - 0.5), 0.5)   # holdout box outside the pair disk


class CornerDetection(unittest.TestCase):
    def test_pure_vogel2d_misses_all_four_corners_at_n64(self):
        x = sb.vogel2d(64, 2)
        masks = sb.region_masks(x)
        for j in range(1, 5):
            self.assertFalse(masks[f"corner_box_{j}"].any(), f"corner_box_{j}")
        self.assertEqual(sb.corner_fraction_hit(x), 0.0)
        self.assertEqual(sb.pair_corner_hits(x, 0, 1), [False, False, False, False])

    def test_corner_test_flags_hits_correctly(self):
        verts = sb.all_vertices(2)
        masks = sb.region_masks(verts)
        for j in range(1, 5):
            self.assertTrue(masks[f"corner_box_{j}"].any())
        self.assertEqual(sb.corner_fraction_hit(verts), 1.0)
        # a point just inside / just outside the 0.08 box at the origin
        inside = sb.region_masks(np.array([[0.079, 0.079]]))["corner_box_1"]
        outside = sb.region_masks(np.array([[0.081, 0.079]]))["corner_box_1"]
        self.assertTrue(inside[0])
        self.assertFalse(outside[0])
        self.assertEqual(sb.corner_fraction_hit(np.array([[0.01, 0.99], [0.5, 0.5]])), 0.25)

    def test_region_definitions(self):
        self.assertEqual(len(sb.region_masks(np.full((1, 2), 0.5))), 7)
        self.assertEqual(len(sb.region_masks(np.full((1, 4), 0.5))), 9)
        self.assertEqual(len(sb.region_masks(np.full((1, 6), 0.5))), 10)
        for d in sb.DIMS:
            self.assertEqual(len(sb.CORNER_BOX_VERTICES[d]), len(set(sb.CORNER_BOX_VERTICES[d])))
            centre = np.array([sb.BALL_CENTRE[:d]])
            self.assertTrue(sb.region_masks(centre)["ball_interior"][0])
            self.assertTrue(sb.inside_pair_disks(centre)[0])        # ball reachable by the Vogel disk
        x = np.array([[0.5, 0.51, 0.95, 0.95, 0.93, 0.93]])
        m = sb.region_masks(x)
        self.assertTrue(m["ridge_x1x2"][0])
        self.assertTrue(m["holdout_x3x4"][0])
        self.assertFalse(m["slab_x1"][0])
        self.assertFalse(m["corner6d"][0])
        self.assertTrue(sb.region_masks(np.full((1, 6), 0.95))["corner6d"][0])


class Reproducibility(unittest.TestCase):
    def test_sobol_lhs_random_reproducible_with_seed(self):
        for name in ("sobol", "lhs", "random"):
            for d in sb.DIMS:
                a = sb.generate(name, 64, d, 2)
                b = sb.generate(name, 64, d, 2)
                c = sb.generate(name, 64, d, 3)
                np.testing.assert_array_equal(a, b, err_msg=name)
                self.assertFalse(np.array_equal(a, c), name)

    def test_lhs_is_latin(self):
        x = sb.lhs(256, 4, 1)
        for i in range(4):
            np.testing.assert_array_equal(np.sort(np.floor(x[:, i] * 256).astype(int)), np.arange(256))

    def test_sobol_balance_and_power_of_two(self):
        x = sb.sobol(256, 2, 0)
        counts = np.histogram2d(x[:, 0], x[:, 1], bins=16, range=[[0, 1], [0, 1]])[0]
        self.assertTrue(np.all(counts == 1))                      # (0, 8, 2)-net: one point per 1/16 x 1/16 cell
        with self.assertRaises(ValueError):
            sb.sobol(100, 2, 0)

    def test_equal_budget_and_validity_every_method(self):
        for d in sb.DIMS:
            for n in sb.BUDGETS:
                for m in sb.ALL_METHODS:
                    x = sb.generate(m, n, d, 0)
                    sb.validate_design(x, n, d)                    # shape (n, d), in cube, no duplicates

    def test_grid_corners_deterministic_and_contains_vertices(self):
        for d in sb.DIMS:
            for n in sb.BUDGETS:
                x = sb.grid_corners(n, d)
                np.testing.assert_array_equal(x, sb.grid_corners(n, d))
                k = min(n, 2 ** d)
                np.testing.assert_array_equal(x[:k], sb.all_vertices(d)[:k])
        self.assertEqual(sb.grid_corners_plan(64, 2), (7, 11))
        self.assertEqual(sb.grid_corners_plan(1024, 6), (3, 231))

    def test_fractional_factorial_resolution_iv(self):
        ff = sb.fractional_factorial_6_2() * 2 - 1
        self.assertEqual(ff.shape, (16, 6))
        self.assertEqual(len({tuple(r) for r in ff}), 16)
        for cols in itertools.combinations(range(6), 3):          # every 3-D projection is a full 2^3 factorial
            self.assertEqual(len({tuple(r) for r in ff[:, cols]}), 8)

    def test_bad_inputs(self):
        with self.assertRaises(ValueError):
            sb.vogel_disk(0)
        with self.assertRaises(ValueError):
            sb.vogel_paired(64, 3, 0)
        with self.assertRaises(ValueError):
            sb.lhs(True, 2, 0)


class Metrics(unittest.TestCase):
    def test_metrics_deterministic(self):
        for d in sb.DIMS:
            ref = sb.Reference(d)
            np.testing.assert_array_equal(ref.points, sb.Reference(d).points)
            for m in sb.ALL_METHODS:
                x = sb.generate(m, 256, d, 1)
                self.assertEqual(sb.evaluate(x, ref), sb.evaluate(x.copy(), sb.Reference(d)), m)

    def test_metrics_invariant_to_row_order(self):
        ref = sb.Reference(4)
        x = sb.sobol(256, 4, 0)
        perm = np.random.default_rng(99).permutation(256)
        a, b = sb.evaluate(x, ref), sb.evaluate(x[perm], ref)
        for key, val in a.items():
            if isinstance(val, float):
                # mathematically invariant; scipy's pairwise CD sum is floating-point order dependent (~1e-11 rel)
                self.assertTrue(math.isclose(val, b[key], rel_tol=1e-9, abs_tol=1e-15), f"{key}: {val} vs {b[key]}")
            else:
                self.assertEqual(val, b[key], key)

    def test_metric_definitions_on_known_designs(self):
        ref = sb.Reference(2)
        r = sb.evaluate(sb.all_vertices(2), ref)
        self.assertAlmostEqual(r["min_pairwise_distance"], 1.0)
        self.assertEqual(r["corner_fraction_hit_side0p05"], 1.0)
        self.assertAlmostEqual(r["covering_radius_ref_plus_lattice3"], math.sqrt(0.5), places=12)   # cube centre
        self.assertLessEqual(r["covering_radius_ref"], math.sqrt(0.5))
        self.assertAlmostEqual(r["cd_centred_l2"] ** 2, r["cd_squared_scipy"], places=15)
        self.assertEqual(r["max_1d_projection_gap"], 1.0)
        # covering radius of the Vogel disk is bounded below by the vertex-to-disk distance (analytic floor)
        floor = (math.sqrt(2) - 1) / 2
        r_v = sb.evaluate(sb.vogel2d(1024, 2), ref)
        self.assertGreaterEqual(r_v["covering_radius_ref_plus_lattice3"], floor)

    def test_lowdim_families(self):
        x = np.array([[0.505, 0.505]])                                         # off every placement boundary
        f = sb.lowdim_missed_fractions(x)
        self.assertAlmostEqual(f["lowdim_corner2d_missed_frac"], 1.0)
        self.assertAlmostEqual(f["lowdim_slab_missed_frac"], (198 - 4) / 198)  # per axis k=49,50 contain 0.505
        self.assertAlmostEqual(f["lowdim_box2d_missed_frac"], 1 - 4 / 361)     # a, b in {0.45, 0.50}
        self.assertEqual(sb.lowdim_missed_fractions(sb.all_vertices(2))["lowdim_corner2d_missed_frac"], 0.0)

    def test_phase0_screen_corner_gap(self):
        g = sb.phase0_screen_corner_gap()
        self.assertAlmostEqual(g["max_unit_w_at_rectangle_corner_24a_0p05ohm"], 24.0 ** 2 * 0.05)
        self.assertLess(g["max_unit_w_over_64_phase0_samples"], g["max_unit_w_over_continuous_disk"])
        self.assertLess(g["max_unit_w_over_continuous_disk"], g["max_unit_w_at_rectangle_corner_24a_0p05ohm"])
        self.assertEqual([v["units"] for v in g["screen_pass_counts_depend_on_layout"].values()], [720, 360, 192, 24])

    def test_phase0_screen_counts_match_frozen_phase0(self):
        if not PHASE0_SCRIPT.exists():
            self.skipTest("Phase 0 vogel_study.py not present")
        phase0 = _load_phase0()
        table = sb.phase0_screen_corner_gap()["screen_pass_counts_depend_on_layout"]
        for level in phase0.LEVELS:
            rows = [phase0.one_case(phase0.FAULTS[0], level, s) for s in range(1, 65)]
            ours = table[f"level_{level}"]["phase0_disk_64_samples_pass"]
            self.assertEqual(ours, sum(r["passes_0_5pct_stc_conduction_screen_only"] for r in rows), level)
            self.assertEqual(table[f"level_{level}"]["units"], phase0.devices_per_plant(level))
        mx = max(phase0.one_case(phase0.FAULTS[0], 1, s)["dissipation_w_per_unit"] for s in range(1, 65))
        self.assertAlmostEqual(sb.phase0_screen_corner_gap()["max_unit_w_over_64_phase0_samples"], mx, places=4)


class Outputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.csv_text, cls.summary, cls.summary_text = sb.run_benchmark()

    def test_csv_regenerates_byte_identically(self):
        rows2, csv2, _summary2, summary_text2 = sb.run_benchmark()
        self.assertEqual(csv2.encode(), self.csv_text.encode())
        self.assertEqual(summary_text2, self.summary_text)
        if sb.CSV_PATH.exists():
            self.assertEqual(sb.CSV_PATH.read_bytes(), self.csv_text.encode(),
                             "committed CSV differs from regeneration: rerun sampling_benchmark.py")
        if sb.SUMMARY_PATH.exists():
            self.assertEqual(sb.SUMMARY_PATH.read_bytes(), self.summary_text.encode(),
                             "committed summary differs from regeneration: rerun sampling_benchmark.py")
        self.assertEqual(self.summary["outputs"]["csv_sha256"], hashlib.sha256(self.csv_text.encode()).hexdigest())

    def test_row_counts_and_budgets(self):
        expected = sum((len(sb.SEEDS) if sb.is_stochastic(m, d) else 1)
                       for d in sb.DIMS for _n in sb.BUDGETS for m in sb.ALL_METHODS)
        self.assertEqual(len(self.rows), expected)
        self.assertEqual(len(self.csv_text.strip().split("\n")), expected + 1)
        for row in self.rows:
            self.assertEqual(row["n_points"], row["budget_n"])

    def test_disclaimer_and_labels(self):
        self.assertIn("say NOTHING about physical fault probabilities", self.summary["disclaimer"])
        self.assertIn(sb.DISCLAIMER, self.summary["ranking_text"])
        self.assertEqual(self.summary["labels"]["probabilities"]["label"], "UNKNOWN")
        self.assertEqual(self.summary["config"]["reference_set"]["points"], 20000)
        self.assertFalse(self.summary["config"]["reference_set"]["reduced"])
        for line in self.csv_text.strip().split("\n")[1:]:
            self.assertTrue(line.endswith("DERIVED,illustrative_simulation,"
                                          "synthetic_unit_cube_geometry_only;no_physics;not_a_probability"))

    def test_vogel_misses_corners_and_holdout_in_every_design(self):
        for row in self.rows:
            if row["method"] in ("vogel2d", "vogel_paired"):
                for name, hit in row["hits"].items():
                    if name.startswith("corner_box_") or name in ("holdout_x3x4", "corner6d"):
                        self.assertFalse(hit, f"{row['method']} d={row['d']} N={row['budget_n']} {name}")
                self.assertEqual(row["corner_fraction_hit_side0p05"], 0.0)

    def test_results_report_both_wins_and_losses(self):
        conc = self.summary["conclusion"]
        self.assertTrue(conc["vogel_wins"])
        self.assertTrue(conc["vogel_losses"])
        self.assertIn("REJECTED as a general claim", conc["verdict_x006"])

    def test_readme_quotes_current_results(self):
        readme = HERE / "README-sampling.md"
        if not readme.exists():
            self.skipTest("README-sampling.md not present")
        text = readme.read_text()
        self.assertIn(self.summary["outputs"]["csv_sha256"], text,
                      "README-sampling.md quotes numbers from a different CSV: update it")
        self.assertIn(self.summary["producer"]["script_sha256"], text,
                      "README-sampling.md quotes a different script revision: update it")
        self.assertIn(sb.DISCLAIMER, text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
