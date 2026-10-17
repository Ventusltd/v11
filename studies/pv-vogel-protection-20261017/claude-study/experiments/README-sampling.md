# Sampling / search-strategy benchmark (Track D, W06, cycle 1, 2026-10-17)

**Status:** illustrative numerical experiment on synthetic geometry in the unit hypercube. No PV, arc, cable, EMT,
inverter or protection physics is modelled. Evidence grade of every benchmark number: `illustrative_simulation`
(label `DERIVED`); analytic disk-geometry numbers: `algebra` (`DERIVED`); planted regions and benchmark parameters:
`ASSUMED` (synthetic, fixed before any result was computed); physical probabilities: `UNKNOWN`.

> These metrics are properties of point layouts in a unit cube and say NOTHING about physical fault probabilities.

The planted "counterexample regions" are synthetic sets, not fault mechanisms. A fraction of seeds, points, placements
or volume is never the probability of anything physical.

Question (contradiction register **X-006**, "Vogel sampling is inherently superior"): at **equal evaluation budgets**,
how do point layouts compare on coverage metrics, and how many planted synthetic counterexample regions do they miss?
No method was assumed better.

## Reproduce

From `claude-study/`:

```
python3 -B experiments/sampling_benchmark.py            # writes the CSV and summary JSON, prints rankings + conclusion
python3 -B experiments/sampling_benchmark.py --check    # regenerates in memory; byte comparison with the files on disk
python3 -B -m unittest -v experiments/test_sampling_benchmark.py
```

| file | sha256 |
|---|---|
| `sampling_benchmark.py` (producer) | `f31bd61c066a7324d09411a4638fafe275e4cefbffead0ccca8c9a6674a6882b` |
| `sampling-benchmark-results.csv` (330 rows) | `73e122ece05f0cbf9cade8c8b14ab0f23134914cf8e8f724c768b58568e69c86` |
| `sampling-benchmark-summary.json` | `e2b701b2a577defd45fee16827188577656c4061a76af04cb7b85ade363d47a2` |

Environment: Python 3.13.16, numpy 2.5.3, scipy 1.18.1, 2 vCPU. Benchmark run: about 9 s wall-clock. Tests: about
22 s, because they regenerate the full benchmark twice. Both are far inside the ~3 min budget, so the covering-radius
reference set was **not reduced**: 20 000 points, `numpy.random.default_rng([20261017, d]).random((20000, d))`. If the
scipy QMC implementation or the numpy generator changes, the scrambled designs change and the CSV hash will change.
The byte-identity check and test will then fail visibly, which is the intent.

## Design of the benchmark

**Budgets and dimensions.** N in {64, 256, 1024}; d in {2, 4, 6}; seeds {0, 1, 2, 3, 4} for every stochastic method.
Every design has exactly N distinct points in [0,1]^d (asserted). A method that does not depend on a seed is evaluated once.

**Specified methods**

| method | construction |
|---|---|
| `vogel2d` | Phase 0 bounded disk, sample s = 1..N: r = sqrt((s - 0.5)/N), theta = s * GOLDEN, u = 0.5 + 0.5 r cos(theta), v = 0.5 + 0.5 r sin(theta). Bit-identical to `vogel_study.vogel_disk` (tested). At d > 2 the same disk with the same index is tiled onto every axis pair (x3 = x1, x4 = x2, ...). This is a deliberately degenerate control, marked `*` in the rankings. |
| `vogel_paired` | The N-point Phase 0 disk on each axis pair (x1,x2), (x3,x4), (x5,x6). Pair 1 keeps the Phase 0 order. Pair p >= 2 is reordered by the (p-1)-th draw of `numpy.random.default_rng(seed).permutation(N)`. At d = 2 it is the same point set as `vogel2d`. |
| `sobol` | `scipy.stats.qmc.Sobol(d, scramble=True, rng=seed).random_base2(log2 N)` |
| `lhs` | `scipy.stats.qmc.LatinHypercube(d, rng=seed).random(N)` (strength 1, no optimisation) |
| `random` | `numpy.random.default_rng(seed).random((N, d))` |
| `grid_corners` | All 2^d vertices, plus a full factorial with k cell-centred levels (i + 0.5)/k (largest k with 2^d + k^d <= N), plus greedy-maximin padding from the (k+1)-level factorial (ties go to the lowest lexicographic index). If 2^d >= N, the vertices alone are used, truncated lexicographically. At d = 6, N = 64 the design is exactly the 64 vertices. |

**Extra designs (not among the six specified; reported separately and marked in italics in the tables)**

- *`golden_lattice_paired`*: a diagnostic. It is the pre-image of the Phase 0 disk under the equal-area polar map,
  ((i - 0.5)/N, frac(i * GOLDEN / 2 pi)) on the full square (the identity is tested to 1e-12). Pairing and permutation
  follow the same rule as `vogel_paired`. It separates the effect of the golden-angle ordering from the effect of the
  disk.
- *`corners_plus_sobol`*, *`corners_plus_vogel_paired`*, *`corners_plus_golden_lattice`*: composite candidates. Each
  is an explicit vertex block E plus (N - |E|) points of the named bulk method, so the budget is still N. E is all 2^d
  vertices when 2^d <= N/4. Otherwise (only d = 6, N = 64) E is the textbook 16-run 2^(6-2) resolution-IV fraction
  (E = ABC, F = BCD). E was not chosen with knowledge of the planted regions.

**Metrics** (per method, d, N, seed; all dimensionless; CSV columns in brackets)

- *Planted regions missed* (key metric) `[planted_regions_missed]`: the number of planted regions that contain no
  design point. Per-region hits are in `hit_*` (`NA` = region not defined at that d).
- Centred L2 discrepancy `[cd_centred_l2]` = sqrt(`scipy.stats.qmc.discrepancy(x, method="CD")`). SciPy returns the
  squared quantity (its docstring says the square root is not taken); the raw value is kept in `[cd_squared_scipy]`.
- Minimum pairwise Euclidean distance `[min_pairwise_distance]`.
- Covering radius `[covering_radius_ref]`: the maximum over the 20 000 reference points of the distance to the nearest
  design point. It is a lower bound on the true covering radius and coarse in 6-D. Supplementary variants: the
  {0, 0.5, 1}^d lattice added `[covering_radius_ref_plus_lattice3]`, and reference points restricted to the inscribed
  pair disks, i.e. Vogel's own domain `[covering_radius_inside_pair_disks]`.
- Corner coverage `[corner_fraction_hit_side0p05]`: the fraction of the 2^d vertex boxes of side 0.05 that contain a point.
- Supplementary, exhaustive and RNG-free low-order families. These check robustness beyond the fixed placements:
  - 1-D slabs, 0.02 thick, on every axis (d x 99 placements) `[lowdim_slab_missed_frac]`;
  - 2-D boxes of side 0.1 on every axis pair (C(d,2) x 361 placements) `[lowdim_box2d_missed_frac]`;
  - 2-D pair-corner boxes of side 0.1 (C(d,2) x 4) `[lowdim_corner2d_missed_frac]`.
- Diagnostics:
  - `[max_1d_projection_gap]`;
  - `[frac_points_outside_pair_disks]`;
  - `[frac_coords_in_extreme_bands]` (coordinates within 0.05 of a face; a uniform layout gives 0.10);
  - `[uncovered_frac_r0p03]`;
  - `[max_abs_axis_correlation]` (1.0 flags duplicated axes).

**Planted synthetic counterexample regions.** These are fixed a priori, identical for every method and never tuned.
A region is hit if any design point lies inside it. Totals: 7 regions at d = 2 (a square has only four corners), 9 at
d = 4, 10 at d = 6.

| region | definition | volume share of cube, d = 2 / 4 / 6 | contains a cube vertex |
|---|---|---|---|
| corner_box_1 | axis-aligned box of side 0.08 at vertex (0,0) / (0,0,0,0) / (0,0,0,0,0,0) (d = 2 / 4 / 6) | 0.0064 / 4.1e-05 / 2.62e-07 | yes |
| corner_box_2 | axis-aligned box of side 0.08 at vertex (1,0) / (1,1,1,1) / (1,0,1,0,1,0) (d = 2 / 4 / 6) | 0.0064 / 4.1e-05 / 2.62e-07 | yes |
| corner_box_3 | axis-aligned box of side 0.08 at vertex (0,1) / (1,0,1,0) / (0,1,0,1,0,1) (d = 2 / 4 / 6) | 0.0064 / 4.1e-05 / 2.62e-07 | yes |
| corner_box_4 | axis-aligned box of side 0.08 at vertex (1,1) / (0,1,0,1) / (1,1,1,0,0,0) (d = 2 / 4 / 6) | 0.0064 / 4.1e-05 / 2.62e-07 | yes |
| corner_box_5 | axis-aligned box of side 0.08 at vertex - / (1,1,0,0) / (0,0,0,1,1,1) (d = 2 / 4 / 6) | - / 4.1e-05 / 2.62e-07 | yes |
| slab_x1 | x1 in [0.98, 1] (thin boundary slab, thickness 0.02) | 0.02 / 0.02 / 0.02 | yes |
| ball_interior | ball of radius 0.03 centred at the first d components of (0.71, 0.29, 0.37, 0.63, 0.58, 0.42) | 0.00283 / 4e-06 / 3.77e-09 | no |
| ridge_x1x2 | \|x1 - x2\| < 0.02 (diagonal ridge) | 0.0396 / 0.0396 / 0.0396 | yes |
| holdout_x3x4 | x3 in [0.9, 1] and x4 in [0.9, 1] (emulated categorical holdout); defined for d = 4, 6 | - / 0.01 / 0.01 | yes |
| corner6d | all six axes > 0.92 (6-D corner); defined for d = 6 | - / - / 2.62e-07 | yes |

Note that 6 of 7, 8 of 9 and 9 of 10 regions contain a cube vertex, which favours any design that includes vertices.
The low-order families above are reported for exactly this reason.

## Headline results

**Planted regions missed** (mean over seeds; (min-max) where seeds differ):

| method | d2 N64 | d2 N256 | d2 N1024 | d4 N64 | d4 N256 | d4 N1024 | d6 N64 | d6 N256 | d6 N1024 |
|---|---|---|---|---|---|---|---|---|---|
| vogel2d | 6 | 4 | 4 | 8 | 7 | 7 | 9 | 8 | 8 |
| vogel_paired | 6 | 4 | 4 | 8 | 7 | 7 | 9 | 8 | 8 |
| sobol | 4 (3-5) | 0.4 (0-1) | 0 | 6 (5-7) | 5.6 (5-6) | 5.6 (5-6) | 7.2 (7-8) | 7 | 7 |
| lhs | 2.4 (1-4) | 1.2 (0-2) | 0.2 (0-1) | 6.6 (6-7) | 6 (5-7) | 5.8 (5-6) | 7.4 (7-8) | 7 | 7 |
| random | 4 (2-5) | 1 (0-2) | 0 | 6.4 (6-7) | 6 | 5.6 (5-6) | 7.4 (7-8) | 7 | 7 |
| grid_corners | 1 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 1 |
| *golden_lattice_paired* | 4 | 0 | 0 | 6 | 5.6 (5-6) | 5.8 (5-6) | 7 | 7 | 7 |
| *corners_plus_sobol* | 0.8 (0-1) | 0.4 (0-1) | 0 | 1 | 1 | 1 | 5 | 1 | 1 |
| *corners_plus_vogel_paired* | 0 | 0 | 0 | 1 | 1 | 1 | 5 | 1 | 1 |
| *corners_plus_golden_lattice* | 1 | 0 | 0 | 1 | 1 | 1 | 5 | 1 | 1 |

**Mean rank over the nine (d, N) cells, six specified methods** (1 = best; competition ranking; means equal to
3 significant figures share a rank; **bold** = primary metric):

| metric (better) | vogel2d | vogel_paired | sobol | lhs | random | grid_corners |
|---|---|---|---|---|---|---|
| **planted_regions_missed** (lower) | 5.00 | 5.00 | 2.00 | 3.11 | 2.44 | 1.00 |
| **cd_centred_l2** (lower) | 5.22 | 4.00 | 1.00 | 2.00 | 3.67 | 4.78 |
| **min_pairwise_distance** (higher) | 3.67 | 2.78 | 2.67 | 4.44 | 5.44 | 1.67 |
| **covering_radius_ref** (lower) | 5.56 | 4.44 | 1.89 | 3.11 | 3.89 | 1.56 |
| **corner_fraction_hit_side0p05** (higher) | 3.22 | 3.22 | 2.00 | 2.33 | 2.56 | 1.00 |
| lowdim_slab_missed_frac (lower) | 2.67 | 2.67 | 1.22 | 1.11 | 3.00 | 6.00 |
| lowdim_box2d_missed_frac (lower) | 4.56 | 3.44 | 1.44 | 2.44 | 3.33 | 4.44 |
| lowdim_corner2d_missed_frac (lower) | 5.44 | 5.22 | 1.44 | 2.11 | 2.89 | 1.00 |
| covering_radius_ref_plus_lattice3 (lower) | 5.56 | 4.67 | 1.89 | 3.11 | 3.89 | 1.56 |
| covering_radius_inside_pair_disks (lower) | 4.56 | 2.67 | 2.56 | 4.22 | 5.11 | 1.56 |
| max_1d_projection_gap (lower) | 3.33 | 3.33 | 1.00 | 1.89 | 4.33 | 6.00 |
| uncovered_frac_r0p03 (lower) | 1.44 | 1.56 | 1.78 | 2.11 | 2.56 | 1.67 |

Analytic geometry of the bounded disk (`algebra`; it holds for every N, so no budget can fix it):

- The disk never samples 21.5 % of the 2-D square, 38.3 % of the 4-D cube or 51.6 % of the 6-D cube (product of pair
  disks). These are volume shares, not probabilities.
- Any vertex box of side < 0.146 lies wholly outside the inscribed disk. That covers the 0.05 corner-metric boxes, the
  0.08 planted corner boxes, the 0.08-wide 6-D corner, and the 0.1 pair-corner boxes.
- The holdout box x3, x4 >= 0.9 is 0.566 from the disk centre against a radius of 0.5. It is unreachable here because
  x3 and x4 form one Vogel pair. If they sat in different pairs, it would be reachable at only 0.27x the uniform density.
- The covering radius can never fall below the vertex-to-disk distance: 0.207 (d = 2), 0.293 (d = 4), 0.359 (d = 6).
  The centred discrepancy converges to a positive constant, not to zero, because the disk layout converges to the
  uniform law on the disk.
- A boundary slab x1 >= 0.98 receives 4.2x fewer disk points than a uniform layout: 0.31 / 1.22 / 4.89 expected points
  at N = 64 / 256 / 1024, against 1.28 / 5.12 / 20.5.

## Candid conclusion

**X-006 verdict: REJECTED as a general claim on this benchmark.** The bounded Vogel representative (`vogel2d` at d = 2,
`vogel_paired` at d > 2) ranks 5th of 5 against Sobol, LHS, random and grid+corners on planted regions missed in all
nine (d, N) cells.

**Where bounded Vogel wins (numbers from the run)**

- **2-D point separation.** `vogel2d` has the largest minimum pairwise distance of the six specified methods at every
  budget: 0.0966 / 0.0483 / 0.0242 against grid_corners 0.0768 / 0.0364 / 0.0192 and sobol 0.0399 / 0.0129 / 0.00473.
  No two runs sit close together.
- **Coverage of its own disk.** Inside the inscribed disk (d = 2), its covering radius 0.103 / 0.0559 / 0.0265 is
  second only to grid_corners (0.101 / 0.0468 / 0.0227) and better than sobol (0.124 / 0.0649 / 0.0319).
- **Smallest budget.** At d = 2, N = 64 it misses the fewest 0.1-sided 2-D boxes (0.335 against 0.338 for grid_corners
  and 0.437 for sobol). The margin is 0.8 %, and the advantage reverses from N = 256 onwards.
- **Mid-table at d > 2.** With seeded pair permutations, `vogel_paired` is mid-table (ranks 3 to 5 of 6) on centred
  discrepancy and minimum distance. It is not last.
- **With explicit vertices added (d = 2).** `corners_plus_vogel_paired` misses 0 / 0 / 0 planted regions, against
  0.8 / 0.4 / 0 for `corners_plus_sobol`. Its disk happens to hit the fixed interior ball at every N. This is one
  deterministic layout against one fixed ball, so read it as layout luck rather than a property: the pure 64-point
  disk misses the same ball, and the expected number of disk points inside it is only 0.23 at N = 64.

**Where it loses**

- **Corners (structural).** The Vogel representative hits no 0.05 vertex box in 9/9 cells and misses every planted
  0.08 corner box in every design. This is fixed by geometry, so no budget N can change it.
- **Categorical-holdout proxy (structural).** `vogel_paired` misses `holdout_x3x4` in 15/15 designs at d = 4 and 15/15
  at d = 6. For comparison, sobol misses it in 1/15 / 1/15, lhs in 4/15 / 1/15 and random in 2/15 / 1/15.
- **Pair corners.** At least 1/(d - 1) of all 2-D pair-corner boxes are unreachable for paired Vogel: its own pairs'
  corners. Observed misses at d = 4 are 0.875 / 0.667 / 0.375, against 0.325 / 0 / 0 for sobol.
- **No convergence.** At d = 2 the centred L2 discrepancy is 0.0673 / 0.0645 / 0.0641, against 0.0126 / 0.00331 /
  0.000876 for sobol (73x worse at N = 1024). The covering radius 0.254 / 0.224 / 0.208 tends to the 0.207 floor.
- **Boundary slabs.** At N = 64, `slab_x1` is missed by vogel2d (d = 2) and by vogel_paired in 5/5 designs at both
  d = 4 and d = 6. Sobol and LHS never miss it there. Of the enumerated 0.02-thick slabs at d = 2, N = 64, vogel2d
  misses 0.273, against 0.0525 for sobol and 0.0626 for lhs.
- **Identity tiling.** Reusing the Phase 0 2-D index on several axis pairs duplicates axes (|corr| = 1). It ranks
  last or second-last on covering radius in all six d > 2 cells.
- **Phase 0's own screen.** On the Phase 0 illustrative axes (I = 8-24 A, R = 1-50 mOhm, P = I^2 R per unit, `ASSUMED`
  in `vogel_study.py`), the worst of the 64 disk samples is 18.9 W and the continuous disk maximum is 20.2 W. The
  rectangle corner (24 A, 0.05 ohm) gives 28.8 W, so the screened worst case is understated 1.52x (`algebra`). The
  screen's pass count also depends on the layout: at the single-module level, 17 of 64 disk samples pass (the same
  count as Phase 0 `vogel_study.py`, cross-checked in a test), against 20-23 of 64 for Sobol seeds 0-4 on the full
  rectangle. A pass fraction is a property of the layout, never a
  probability.

**Attribution.** The losses come from the inscribed-disk map, not from the golden-angle sequence. The full-square
golden lattice (`golden_lattice_paired`) has centred L2 discrepancy 0.0151 / 0.00321 / 0.000871 at d = 2, comparable
to Sobol's 0.0126 / 0.00331 / 0.000876. It hits the holdout in every d = 4 design. It still misses the
full-dimensional corner boxes, like every space-filling design.

**Other methods, candidly**

- **grid_corners** wins the key metric: 1 miss in 7 of 9 cells and 0 in the other two (d = 2, N = 256 and 1024).
  The miss is always the interior ball. It wins mainly because it contains the vertices and 8 of 9 planted regions at
  d = 4 contain a vertex. Its 1-D projections collapse: the maximum 1-D gap is 0.25 / 0.208 / 0.15 at d = 4, against
  0.0297 / 0.00744 / 0.00191 for Sobol. It misses 0.848 / 0.828 / 0.707 of the enumerated 0.02-thick slabs at d = 4,
  against 0.0732 / 0 / 0 for Sobol. At d = 6, N = 64 it is nothing but the 64 vertices (centred discrepancy 1.17).
- **Sobol** is first on centred discrepancy in 9/9 cells and first on 1-D projection gap in 9/9 (sharing first place
  with LHS at d = 6, N = 64), and in the top two on covering radius in 9/9. It converges with N. Without explicit vertices it still misses full-dimensional corners: no planted
  corner box is hit in any d = 6 Sobol design.
- **No method** finds `ball_interior` at d = 4 or d = 6, at any budget or seed. An iid uniform design of N = 1024
  would hold 0.0041 (d = 4) or 0.0000039 (d = 6) points in it in expectation. Non-adaptive designs do not find small
  full-dimensional interior features at these budgets.

## Deterministic augmentation required if a Vogel construction is kept

1. Add all four vertices of every Vogel axis pair. For d > 2, add the full 2^d vertex block, or a resolution-IV
   fraction plus the physically named corners.
2. Add face points for one-at-a-time limits on every axis.
3. Enumerate categorical factors as separate levels. Never map them onto a continuous sub-box.
4. Permute the sample order independently per axis pair, with a documented seed. Never reuse one 2-D index on
   several pairs.
5. Kuiper keys remain addresses only. Vogel coverage statistics are not evidence of anything physical.

## Recommended composite design for wave 2 / Phase D

1. **Categorical factors are enumerated** as a full factorial over their levels: protection P0..P3, inverter
   V_BOOST / V_DIRECTBUS, fault location near / far, irradiance including night, and case family. This is what the
   cycle-1 scenario ledger already does. Use a strength-2 covering array if the product grows too large.
2. **Per categorical combination, an explicit deterministic extreme block** on the continuous axes: all 2^d vertices
   when 2^d <= N/4. Otherwise use a resolution-IV fraction plus the physically named corners supplied by the physics
   tracks (for example cold Voc x maximum irradiance, 0 A night, longest route, minimum sustaining current), plus face
   points.
3. **Remaining budget: scrambled Sobol.** Use a power-of-two N and record the seeds. Reuse the same Sobol block across
   protection candidates so that architecture comparisons are paired.
4. **Adversarial and adaptive cases** from brief §6, plus refinement around observed near-failures. No non-adaptive
   design finds small interior features.

**Why this design, from the numbers**

- *Explicit vertices do the corner work.* At d = 4, sobol's mean misses fall from 6 / 5.6 / 5.6 to 1 / 1 / 1 with the
  vertex block. Paired Vogel's fall from 8 / 7 / 7 to 1 / 1 / 1. The remaining miss is the interior ball. The cost is
  that centred discrepancy rises (d = 4 Sobol 0.0322 / 0.0106 / 0.00293 becomes 0.2 / 0.0504 / 0.0126), because 16 of
  N points sit on vertices.
- *A generic fraction is not enough at small N.* At d = 6, N = 64, the 16-run fraction still leaves 5 regions missed:
  4 corner boxes outside the fraction, plus the ball. The physically critical corners must be named explicitly, or N
  raised.
- *Sobol beats paired Vogel as the bulk.* Behind the same vertex block, the Sobol bulk has the better covering radius
  in 9/9 cells and the better centred discrepancy in 6/9. The paired-Vogel bulk wins discrepancy only at d4 N64,
  d6 N64 and d6 N256. That is plausibly corner over-weight from the vertex block being offset by the disk's corner
  under-weight (an interpretation, not measured). The disk bulk does not converge.
- *Possible alternative bulk.* The full-square golden lattice performs comparably to Sobol at d = 2 and LHS-like at
  d = 6. If a golden-angle construction is wanted for a 2-D screen, use that lattice plus the four vertices, never the
  bounded disk.

## Plain-text rankings (primary metrics, six specified methods; value = mean over seeds)

```
[planted_regions_missed] lower is better -- KEY METRIC: planted synthetic regions containing no design point (of 7 at d=2, 9 at d=4, 10 at d=6)
  d2_N64    1. grid_corners 1 | 2. lhs 2.4 | 3. random 4 | 3. sobol 4 | 5. vogel2d 6 | 5. vogel_paired 6
  d2_N256   1. grid_corners 0 | 2. sobol 0.4 | 3. random 1 | 4. lhs 1.2 | 5. vogel2d 4 | 5. vogel_paired 4
  d2_N1024  1. grid_corners 0 | 1. random 0 | 1. sobol 0 | 4. lhs 0.2 | 5. vogel2d 4 | 5. vogel_paired 4
  d4_N64    1. grid_corners 1 | 2. sobol 6 | 3. random 6.4 | 4. lhs 6.6 | 5. vogel2d* 8 | 5. vogel_paired 8
  d4_N256   1. grid_corners 1 | 2. sobol 5.6 | 3. lhs 6 | 3. random 6 | 5. vogel2d* 7 | 5. vogel_paired 7
  d4_N1024  1. grid_corners 1 | 2. random 5.6 | 2. sobol 5.6 | 4. lhs 5.8 | 5. vogel2d* 7 | 5. vogel_paired 7
  d6_N64    1. grid_corners 1 | 2. sobol 7.2 | 3. lhs 7.4 | 3. random 7.4 | 5. vogel2d* 9 | 5. vogel_paired 9
  d6_N256   1. grid_corners 1 | 2. lhs 7 | 2. random 7 | 2. sobol 7 | 5. vogel2d* 8 | 5. vogel_paired 8
  d6_N1024  1. grid_corners 1 | 2. lhs 7 | 2. random 7 | 2. sobol 7 | 5. vogel2d* 8 | 5. vogel_paired 8
  mean rank: grid_corners 1.00 | sobol 2.00 | random 2.44 | lhs 3.11 | vogel2d 5.00 | vogel_paired 5.00

[cd_centred_l2] lower is better -- centred L2 discrepancy = sqrt(scipy qmc.discrepancy(method='CD'))
  d2_N64    1. sobol 0.0126 | 2. lhs 0.02211 | 3. grid_corners 0.05331 | 4. vogel2d 0.06732 | 4. vogel_paired 0.06732 | 6. random 0.0708
  d2_N256   1. sobol 0.003307 | 2. lhs 0.01233 | 3. grid_corners 0.03556 | 4. random 0.03954 | 5. vogel2d 0.06453 | 5. vogel_paired 0.06453
  d2_N1024  1. sobol 0.0008757 | 2. lhs 0.005197 | 3. random 0.01548 | 4. grid_corners 0.02158 | 5. vogel2d 0.06405 | 5. vogel_paired 0.06405
  d4_N64    1. sobol 0.03222 | 2. lhs 0.05481 | 3. vogel_paired 0.1137 | 4. random 0.1334 | 5. vogel2d* 0.1659 | 6. grid_corners 0.169
  d4_N256   1. sobol 0.01063 | 2. lhs 0.0303 | 3. random 0.06078 | 4. vogel_paired 0.1029 | 5. grid_corners 0.1233 | 6. vogel2d* 0.1625
  d4_N1024  1. sobol 0.002935 | 2. lhs 0.0152 | 3. random 0.02651 | 4. vogel_paired 0.1007 | 5. grid_corners 0.1107 | 6. vogel2d* 0.162
  d6_N64    1. sobol 0.07307 | 2. lhs 0.1088 | 3. vogel_paired 0.1627 | 4. random 0.1882 | 5. vogel2d* 0.2825 | 6. grid_corners 1.173
  d6_N256   1. sobol 0.02354 | 2. lhs 0.05351 | 3. random 0.09589 | 4. vogel_paired 0.1419 | 5. vogel2d* 0.2779 | 6. grid_corners 0.2856
  d6_N1024  1. sobol 0.007773 | 2. lhs 0.02567 | 3. random 0.04146 | 4. vogel_paired 0.137 | 5. grid_corners 0.1941 | 6. vogel2d* 0.2774
  mean rank: sobol 1.00 | lhs 2.00 | random 3.67 | vogel_paired 4.00 | grid_corners 4.78 | vogel2d 5.22

[min_pairwise_distance] higher is better -- minimum Euclidean distance between two design points
  d2_N64    1. vogel2d 0.09663 | 1. vogel_paired 0.09663 | 3. grid_corners 0.07681 | 4. sobol 0.03986 | 5. lhs 0.02274 | 6. random 0.01174
  d2_N256   1. vogel2d 0.04831 | 1. vogel_paired 0.04831 | 3. grid_corners 0.03644 | 4. sobol 0.01286 | 5. lhs 0.005095 | 6. random 0.002669
  d2_N1024  1. vogel2d 0.02416 | 1. vogel_paired 0.02416 | 3. grid_corners 0.01925 | 4. sobol 0.004727 | 5. lhs 0.001338 | 6. random 0.0005417
  d4_N64    1. grid_corners 0.3333 | 2. sobol 0.1589 | 3. vogel_paired 0.1479 | 4. vogel2d* 0.1367 | 5. lhs 0.1079 | 6. random 0.08971
  d4_N256   1. grid_corners 0.1863 | 2. sobol 0.1095 | 3. vogel_paired 0.07582 | 4. vogel2d* 0.06833 | 5. random 0.04608 | 6. lhs 0.04039
  d4_N1024  1. grid_corners 0.1291 | 2. sobol 0.05105 | 3. vogel_paired 0.03731 | 4. vogel2d* 0.03416 | 5. lhs 0.02307 | 6. random 0.02273
  d6_N64    1. grid_corners 1 | 2. sobol 0.3049 | 3. lhs 0.2427 | 4. vogel_paired 0.2059 | 5. random 0.1812 | 6. vogel2d* 0.1674
  d6_N256   1. grid_corners 0.3909 | 2. sobol 0.2121 | 3. lhs 0.1464 | 4. vogel_paired 0.1246 | 5. random 0.1209 | 6. vogel2d* 0.08368
  d6_N1024  1. grid_corners 0.2569 | 2. sobol 0.1271 | 3. lhs 0.08716 | 4. random 0.08143 | 5. vogel_paired 0.07441 | 6. vogel2d* 0.04184
  mean rank: grid_corners 1.67 | sobol 2.67 | vogel_paired 2.78 | vogel2d 3.67 | lhs 4.44 | random 5.44

[covering_radius_ref] lower is better -- max over 20000 fixed random reference points of the distance to the nearest design point
  d2_N64    1. grid_corners 0.1009 | 2. sobol 0.1383 | 3. lhs 0.1918 | 4. random 0.214 | 5. vogel2d 0.2544 | 5. vogel_paired 0.2544
  d2_N256   1. grid_corners 0.04679 | 2. sobol 0.06904 | 3. lhs 0.1157 | 4. random 0.1264 | 5. vogel2d 0.2236 | 5. vogel_paired 0.2236
  d2_N1024  1. grid_corners 0.02268 | 2. sobol 0.03442 | 3. lhs 0.05506 | 4. random 0.05929 | 5. vogel2d 0.2082 | 5. vogel_paired 0.2082
  d4_N64    1. grid_corners 0.4651 | 2. sobol 0.5149 | 3. lhs 0.5453 | 4. vogel_paired 0.5992 | 5. random 0.6029 | 6. vogel2d* 0.9257
  d4_N256   1. grid_corners 0.3034 | 2. sobol 0.3523 | 3. lhs 0.3937 | 4. random 0.4125 | 5. vogel_paired 0.4719 | 6. vogel2d* 0.9246
  d4_N1024  1. grid_corners 0.1854 | 2. sobol 0.2254 | 3. lhs 0.2835 | 3. random 0.2835 | 5. vogel_paired 0.3634 | 6. vogel2d* 0.924
  d6_N64    1. sobol 0.7509 | 2. vogel_paired 0.8217 | 3. lhs 0.8374 | 3. random 0.8372 | 5. vogel2d* 1.063 | 6. grid_corners 1.074
  d6_N256   1. grid_corners 0.5373 | 2. sobol 0.5891 | 3. lhs 0.6432 | 4. vogel_paired 0.6614 | 5. random 0.6632 | 6. vogel2d* 1.063
  d6_N1024  1. grid_corners 0.3633 | 2. sobol 0.4414 | 3. random 0.482 | 4. lhs 0.4959 | 5. vogel_paired 0.5599 | 6. vogel2d* 1.062
  mean rank: grid_corners 1.56 | sobol 1.89 | lhs 3.11 | random 3.89 | vogel_paired 4.44 | vogel2d 5.56

[corner_fraction_hit_side0p05] higher is better -- fraction of the 2^d vertex boxes (side 0.05) hit
  d2_N64    1. grid_corners 1 | 2. random 0.15 | 3. lhs 0.1 | 3. sobol 0.1 | 5. vogel2d 0 | 5. vogel_paired 0
  d2_N256   1. grid_corners 1 | 2. sobol 0.7 | 3. lhs 0.55 | 4. random 0.45 | 5. vogel2d 0 | 5. vogel_paired 0
  d2_N1024  1. grid_corners 1 | 1. sobol 1 | 3. lhs 0.95 | 3. random 0.95 | 5. vogel2d 0 | 5. vogel_paired 0
  d4_N64    1. grid_corners 1 | 2. lhs 0 | 2. random 0 | 2. sobol 0 | 2. vogel2d* 0 | 2. vogel_paired 0
  d4_N256   1. grid_corners 1 | 2. lhs 0 | 2. random 0 | 2. sobol 0 | 2. vogel2d* 0 | 2. vogel_paired 0
  d4_N1024  1. grid_corners 1 | 2. lhs 0.0125 | 2. sobol 0.0125 | 4. random 0 | 4. vogel2d* 0 | 4. vogel_paired 0
  d6_N64    1. grid_corners 1 | 2. lhs 0 | 2. random 0 | 2. sobol 0 | 2. vogel2d* 0 | 2. vogel_paired 0
  d6_N256   1. grid_corners 1 | 2. lhs 0 | 2. random 0 | 2. sobol 0 | 2. vogel2d* 0 | 2. vogel_paired 0
  d6_N1024  1. grid_corners 1 | 2. lhs 0 | 2. random 0 | 2. sobol 0 | 2. vogel2d* 0 | 2. vogel_paired 0
  mean rank: grid_corners 1.00 | sobol 2.00 | lhs 2.33 | random 2.56 | vogel2d 3.22 | vogel_paired 3.22
```

Extended mean ranks over the nine cells, including the diagnostic and composite designs:

```
[planted_regions_missed] corners_plus_vogel_paired 1.11 | grid_corners 1.22 | corners_plus_golden_lattice 1.33 | corners_plus_sobol 1.67 | golden_lattice_paired 4.44 | sobol 4.78 | random 5.56 | lhs 6.67 | vogel2d 9.00 | vogel_paired 9.00
[cd_centred_l2] sobol 1.22 | golden_lattice_paired 1.89 | lhs 3.44 | corners_plus_golden_lattice 5.78 | corners_plus_sobol 5.78 | random 5.89 | corners_plus_vogel_paired 6.78 | vogel_paired 7.00 | grid_corners 8.11 | vogel2d 8.56
[min_pairwise_distance] grid_corners 2.67 | golden_lattice_paired 3.89 | corners_plus_golden_lattice 4.00 | corners_plus_sobol 4.44 | sobol 4.44 | corners_plus_vogel_paired 4.67 | vogel_paired 6.00 | vogel2d 7.00 | lhs 7.78 | random 9.33
[covering_radius_ref] grid_corners 2.00 | corners_plus_sobol 3.00 | sobol 3.33 | corners_plus_golden_lattice 4.00 | golden_lattice_paired 4.33 | lhs 6.22 | corners_plus_vogel_paired 6.44 | random 7.00 | vogel_paired 8.22 | vogel2d 9.56
[corner_fraction_hit_side0p05] grid_corners 1.00 | corners_plus_golden_lattice 1.11 | corners_plus_sobol 1.11 | corners_plus_vogel_paired 1.11 | sobol 4.89 | golden_lattice_paired 5.11 | lhs 5.67 | random 5.89 | vogel2d 6.56 | vogel_paired 6.56
[lowdim_slab_missed_frac] golden_lattice_paired 1.00 | lhs 1.56 | corners_plus_golden_lattice 1.67 | sobol 1.67 | corners_plus_sobol 2.33 | vogel2d 4.67 | vogel_paired 4.67 | random 5.11 | corners_plus_vogel_paired 6.00 | grid_corners 10.00
[lowdim_box2d_missed_frac] sobol 2.00 | golden_lattice_paired 2.22 | corners_plus_sobol 4.11 | corners_plus_golden_lattice 4.33 | lhs 4.33 | random 5.33 | vogel_paired 5.78 | corners_plus_vogel_paired 7.00 | grid_corners 7.11 | vogel2d 7.44
[lowdim_corner2d_missed_frac] corners_plus_golden_lattice 1.00 | corners_plus_sobol 1.00 | corners_plus_vogel_paired 1.00 | grid_corners 1.00 | sobol 2.56 | golden_lattice_paired 3.67 | lhs 4.33 | random 5.56 | vogel_paired 9.22 | vogel2d 9.44
[covering_radius_ref_plus_lattice3] grid_corners 2.00 | corners_plus_sobol 2.78 | corners_plus_golden_lattice 3.33 | sobol 3.78 | golden_lattice_paired 4.78 | corners_plus_vogel_paired 5.89 | lhs 6.56 | random 7.33 | vogel_paired 8.44 | vogel2d 9.56
[covering_radius_inside_pair_disks] grid_corners 2.00 | sobol 3.56 | vogel_paired 3.78 | golden_lattice_paired 4.56 | corners_plus_sobol 4.78 | corners_plus_vogel_paired 5.22 | corners_plus_golden_lattice 6.67 | lhs 7.22 | vogel2d 7.78 | random 8.44
[max_1d_projection_gap] golden_lattice_paired 1.00 | corners_plus_golden_lattice 2.22 | sobol 2.56 | lhs 3.56 | corners_plus_sobol 5.00 | vogel2d 6.56 | vogel_paired 6.56 | corners_plus_vogel_paired 7.78 | random 8.11 | grid_corners 10.00
[uncovered_frac_r0p03] golden_lattice_paired 1.56 | corners_plus_golden_lattice 1.89 | grid_corners 2.11 | vogel2d 2.11 | vogel_paired 2.22 | sobol 2.33 | corners_plus_sobol 2.89 | lhs 3.11 | corners_plus_vogel_paired 3.33 | random 3.78
```

## Detail tables (means over seeds)

Centred L2 discrepancy:

| method | d2 N64 | d2 N256 | d2 N1024 | d4 N64 | d4 N256 | d4 N1024 | d6 N64 | d6 N256 | d6 N1024 |
|---|---|---|---|---|---|---|---|---|---|
| vogel2d | 0.0673 | 0.0645 | 0.0641 | 0.166 | 0.162 | 0.162 | 0.282 | 0.278 | 0.277 |
| vogel_paired | 0.0673 | 0.0645 | 0.0641 | 0.114 | 0.103 | 0.101 | 0.163 | 0.142 | 0.137 |
| sobol | 0.0126 | 0.00331 | 0.000876 | 0.0322 | 0.0106 | 0.00293 | 0.0731 | 0.0235 | 0.00777 |
| lhs | 0.0221 | 0.0123 | 0.0052 | 0.0548 | 0.0303 | 0.0152 | 0.109 | 0.0535 | 0.0257 |
| random | 0.0708 | 0.0395 | 0.0155 | 0.133 | 0.0608 | 0.0265 | 0.188 | 0.0959 | 0.0415 |
| grid_corners | 0.0533 | 0.0356 | 0.0216 | 0.169 | 0.123 | 0.111 | 1.17 | 0.286 | 0.194 |
| *golden_lattice_paired* | 0.0151 | 0.00321 | 0.000871 | 0.055 | 0.0235 | 0.012 | 0.102 | 0.049 | 0.0235 |
| *corners_plus_sobol* | 0.0311 | 0.00818 | 0.00198 | 0.2 | 0.0504 | 0.0126 | 0.304 | 0.295 | 0.0738 |
| *corners_plus_vogel_paired* | 0.0431 | 0.0577 | 0.0623 | 0.148 | 0.0639 | 0.0895 | 0.238 | 0.224 | 0.0846 |
| *corners_plus_golden_lattice* | 0.0295 | 0.00742 | 0.00183 | 0.199 | 0.0538 | 0.0166 | 0.304 | 0.295 | 0.0765 |

Minimum pairwise distance:

| method | d2 N64 | d2 N256 | d2 N1024 | d4 N64 | d4 N256 | d4 N1024 | d6 N64 | d6 N256 | d6 N1024 |
|---|---|---|---|---|---|---|---|---|---|
| vogel2d | 0.0966 | 0.0483 | 0.0242 | 0.137 | 0.0683 | 0.0342 | 0.167 | 0.0837 | 0.0418 |
| vogel_paired | 0.0966 | 0.0483 | 0.0242 | 0.148 | 0.0758 | 0.0373 | 0.206 | 0.125 | 0.0744 |
| sobol | 0.0399 | 0.0129 | 0.00473 | 0.159 | 0.11 | 0.0511 | 0.305 | 0.212 | 0.127 |
| lhs | 0.0227 | 0.00509 | 0.00134 | 0.108 | 0.0404 | 0.0231 | 0.243 | 0.146 | 0.0872 |
| random | 0.0117 | 0.00267 | 0.000542 | 0.0897 | 0.0461 | 0.0227 | 0.181 | 0.121 | 0.0814 |
| grid_corners | 0.0768 | 0.0364 | 0.0192 | 0.333 | 0.186 | 0.129 | 1 | 0.391 | 0.257 |
| *golden_lattice_paired* | 0.119 | 0.0614 | 0.0296 | 0.174 | 0.0868 | 0.0418 | 0.229 | 0.13 | 0.0866 |
| *corners_plus_sobol* | 0.0391 | 0.0115 | 0.00473 | 0.156 | 0.103 | 0.0512 | 0.311 | 0.219 | 0.128 |
| *corners_plus_vogel_paired* | 0.0998 | 0.0487 | 0.0242 | 0.174 | 0.0777 | 0.0382 | 0.253 | 0.145 | 0.0677 |
| *corners_plus_golden_lattice* | 0.0825 | 0.0446 | 0.025 | 0.192 | 0.091 | 0.0421 | 0.297 | 0.162 | 0.0859 |

Covering radius (20 000-point reference set):

| method | d2 N64 | d2 N256 | d2 N1024 | d4 N64 | d4 N256 | d4 N1024 | d6 N64 | d6 N256 | d6 N1024 |
|---|---|---|---|---|---|---|---|---|---|
| vogel2d | 0.254 | 0.224 | 0.208 | 0.926 | 0.925 | 0.924 | 1.06 | 1.06 | 1.06 |
| vogel_paired | 0.254 | 0.224 | 0.208 | 0.599 | 0.472 | 0.363 | 0.822 | 0.661 | 0.56 |
| sobol | 0.138 | 0.069 | 0.0344 | 0.515 | 0.352 | 0.225 | 0.751 | 0.589 | 0.441 |
| lhs | 0.192 | 0.116 | 0.0551 | 0.545 | 0.394 | 0.284 | 0.837 | 0.643 | 0.496 |
| random | 0.214 | 0.126 | 0.0593 | 0.603 | 0.413 | 0.284 | 0.837 | 0.663 | 0.482 |
| grid_corners | 0.101 | 0.0468 | 0.0227 | 0.465 | 0.303 | 0.185 | 1.07 | 0.537 | 0.363 |
| *golden_lattice_paired* | 0.124 | 0.0571 | 0.0311 | 0.544 | 0.413 | 0.267 | 0.808 | 0.648 | 0.494 |
| *corners_plus_sobol* | 0.154 | 0.0713 | 0.0347 | 0.498 | 0.345 | 0.224 | 0.794 | 0.587 | 0.437 |
| *corners_plus_vogel_paired* | 0.168 | 0.148 | 0.13 | 0.514 | 0.394 | 0.324 | 0.849 | 0.589 | 0.512 |
| *corners_plus_golden_lattice* | 0.129 | 0.059 | 0.0313 | 0.512 | 0.39 | 0.27 | 0.825 | 0.612 | 0.484 |

Fraction of 2^d vertex boxes (side 0.05) hit:

| method | d2 N64 | d2 N256 | d2 N1024 | d4 N64 | d4 N256 | d4 N1024 | d6 N64 | d6 N256 | d6 N1024 |
|---|---|---|---|---|---|---|---|---|---|
| vogel2d | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| vogel_paired | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| sobol | 0.1 | 0.7 | 1 | 0 | 0 | 0.0125 | 0 | 0 | 0 |
| lhs | 0.1 | 0.55 | 0.95 | 0 | 0 | 0.0125 | 0 | 0 | 0 |
| random | 0.15 | 0.45 | 0.95 | 0 | 0 | 0 | 0 | 0 | 0 |
| grid_corners | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| *golden_lattice_paired* | 0 | 0.75 | 1 | 0 | 0.0125 | 0 | 0 | 0 | 0 |
| *corners_plus_sobol* | 1 | 1 | 1 | 1 | 1 | 1 | 0.25 | 1 | 1 |
| *corners_plus_vogel_paired* | 1 | 1 | 1 | 1 | 1 | 1 | 0.25 | 1 | 1 |
| *corners_plus_golden_lattice* | 1 | 1 | 1 | 1 | 1 | 1 | 0.25 | 1 | 1 |

Per-region misses at d = 4, N = 256 (designs missing / designs):

| method | corner_box_1 | corner_box_2 | corner_box_3 | corner_box_4 | corner_box_5 | slab_x1 | ball_interior | ridge_x1x2 | holdout_x3x4 |
|---|---|---|---|---|---|---|---|---|---|
| vogel2d | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 | 0/1 | 1/1 | 0/1 | 1/1 |
| vogel_paired | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 0/5 | 5/5 | 0/5 | 5/5 |
| sobol | 5/5 | 5/5 | 3/5 | 5/5 | 5/5 | 0/5 | 5/5 | 0/5 | 0/5 |
| lhs | 5/5 | 5/5 | 5/5 | 4/5 | 5/5 | 0/5 | 5/5 | 0/5 | 1/5 |
| random | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 0/5 | 5/5 | 0/5 | 0/5 |
| grid_corners | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 1/1 | 0/1 | 0/1 |
| *golden_lattice_paired* | 4/5 | 5/5 | 5/5 | 5/5 | 4/5 | 0/5 | 5/5 | 0/5 | 0/5 |
| *corners_plus_sobol* | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 | 5/5 | 0/5 | 0/5 |
| *corners_plus_vogel_paired* | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 | 5/5 | 0/5 | 0/5 |
| *corners_plus_golden_lattice* | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 | 5/5 | 0/5 | 0/5 |

All cells, per-region misses, min/max over seeds and the supplementary metrics are in
`sampling-benchmark-summary.json` (`planted_region_misses_by_seed`, `per_method_means`, `rankings`, `findings`).

## Not modelled / limits

- No physics. There is no mapping from unit-cube coordinates to physical parameters or their ranges.
- No physical probability or frequency is estimated (`UNKNOWN`).
- All designs are non-adaptive. Adaptive or sequential search was not benchmarked.
- The planted set is one fixed synthetic choice. Real counterexample sets have unknown shape, size and location. The
  key metric depends on that choice, which the low-order families only partly address.
- Five seeds per stochastic method. Differences of a fraction of one region between methods are not meaningful.
- Covering radii are lower bounds from a finite reference set.
- Categorical factors are only emulated by one continuous sub-box. Real categorical levels must be enumerated.
- Every evaluation is assumed to cost the same.
