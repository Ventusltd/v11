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
| `sampling_benchmark.py` (producer) | `{{SCRIPT_SHA}}` |
| `sampling-benchmark-results.csv` ({{CSV_ROWS}} rows) | `{{CSV_SHA}}` |
| `sampling-benchmark-summary.json` | `{{SUMMARY_SHA}}` |

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

{{T_REGIONS_DEF}}

Note that 6 of 7, 8 of 9 and 9 of 10 regions contain a cube vertex, which favours any design that includes vertices.
The low-order families above are reported for exactly this reason.

## Headline results

**Planted regions missed** (mean over seeds; (min-max) where seeds differ):

{{T_MISSES}}

**Mean rank over the nine (d, N) cells, six specified methods** (1 = best; competition ranking; means equal to
3 significant figures share a rank; **bold** = primary metric):

{{T_MEANRANK}}

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
{{B_RANKING}}
```

Extended mean ranks over the nine cells, including the diagnostic and composite designs:

```
{{B_EXTENDED}}
```

## Detail tables (means over seeds)

Centred L2 discrepancy:

{{T_CD}}

Minimum pairwise distance:

{{T_MIND}}

Covering radius (20 000-point reference set):

{{T_COV}}

Fraction of 2^d vertex boxes (side 0.05) hit:

{{T_CORNER}}

Per-region misses at d = 4, N = 256 (designs missing / designs):

{{T_REGIONS_D4N256}}

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
