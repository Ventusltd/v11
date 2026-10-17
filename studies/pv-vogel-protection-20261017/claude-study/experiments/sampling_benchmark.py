#!/usr/bin/env python3
"""Equal-budget sampling / search-strategy benchmark -- Track D, worker W06, V11 cycle 1 (2026-10-17).

STATUS: illustrative numerical experiment on SYNTHETIC geometry in the unit hypercube [0,1]^d.
No PV, arc, EMT, cable, inverter or protection physics is modelled. The planted "counterexample regions" are
synthetic sets in [0,1]^d (master brief section 4, task W06); they are NOT fault mechanisms.

These metrics are properties of point layouts in a unit cube and say NOTHING about physical fault probabilities.
Fractions of seeds, points, placements or volume are never probabilities of anything physical.

Question (contradiction register X-006, "Vogel sampling is inherently superior"): at EQUAL evaluation budgets N, how
do point layouts compare on coverage metrics and on how many planted synthetic counterexample regions they miss?
No method is assumed better.

Specified methods (on [0,1]^d, d in {2,4,6}, N in {64,256,1024}; seeds 0..4 where a method is stochastic):
  vogel2d        Phase 0 bounded Vogel disk, sample s=1..N: r=sqrt((s-0.5)/N), theta=s*GOLDEN,
                 u=0.5+0.5 r cos(theta), v=0.5+0.5 r sin(theta) (arithmetic identical to vogel_study.vogel_disk).
                 d=2: exactly Phase 0.  d>2: the SAME disk with the SAME sample index on every axis pair
                 (identity tiling, x3=x1, x4=x2, ...): a deliberately degenerate control.
  vogel_paired   axis pairs (x1,x2),(x3,x4),(x5,x6) each carry the N-point Phase 0 disk; pair 1 keeps the Phase 0
                 order, pair p>=2 uses the (p-1)-th draw of numpy default_rng(seed).permutation(N).  Metrics are
                 invariant to row order, so leaving pair 1 unpermuted loses no generality.  At d=2 it is the
                 identical point set to vogel2d (seed-invariant, evaluated once).
  sobol          scipy.stats.qmc.Sobol(d, scramble=True, rng=seed).random_base2(log2 N).
  lhs            scipy.stats.qmc.LatinHypercube(d, rng=seed).random(N) (scramble=True, strength 1, no optimisation).
  random         numpy default_rng(seed).random((N, d)).
  grid_corners   all 2^d vertices + full factorial with k cell-centred levels (i+0.5)/k per axis, k = largest
                 integer with 2^d + k^d <= N; the remaining N - 2^d - k^d points are padded by greedy maximin
                 (farthest point, ties -> lowest lexicographic index) from the (k+1)-level cell-centred factorial.
                 If 2^d >= N the vertices alone are used, truncated lexicographically (d=6, N=64: exactly 64).
Supplementary diagnostic (NOT one of the six specified methods):
  golden_lattice_paired  pre-image of the Phase 0 disk: s_i=(i-0.5)/N, t_i=frac(i*GOLDEN/(2*pi)).  The Phase 0 disk
                 point i is exactly (0.5+0.5*sqrt(s_i)cos(2*pi*t_i), 0.5+0.5*sqrt(s_i)sin(2*pi*t_i)), an equal-area
                 polar map of this golden-ratio lattice.  Same pairing/permutation rule as vogel_paired.  It separates
                 the effect of the golden-angle ordering from the effect of the disk mapping.
Composite candidates for the wave-2 / Phase D recommendation (same equal budgets N, explicit set counted in N):
  corners_plus_sobol, corners_plus_vogel_paired, corners_plus_golden_lattice:
  explicit vertex set E + (N-|E|) points of the named method (Sobol: prefix of a 2^ceil(log2) scrambled sequence).
  E = all 2^d vertices if 2^d <= N/4, else a regular two-level fractional factorial with the largest power-of-two
  run count <= N/4 (only needed at d=6, N=64: 2^(6-2) resolution IV, generators E=ABC, F=BCD, the textbook choice).
  E is generic: it was NOT chosen with knowledge of which planted corner boxes exist.

Run from claude-study/:   python3 -B experiments/sampling_benchmark.py          (writes CSV + summary JSON)
                          python3 -B experiments/sampling_benchmark.py --check  (regenerate in memory, compare bytes)
"""
import csv
import hashlib
import io
import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np
import scipy
from scipy.spatial import cKDTree
from scipy.stats import qmc

HERE = Path(__file__).resolve().parent
CSV_PATH = HERE / "sampling-benchmark-results.csv"
SUMMARY_PATH = HERE / "sampling-benchmark-summary.json"
FIXTURE_PATH = HERE.parent / "fixture" / "system-fixture.json"   # read-only; only plant counts/nameplate are used

BENCHMARK_ID = "V11-cycle1-W06-sampling-benchmark-v1"
DISCLAIMER = ("These metrics are properties of point layouts in a unit cube and say NOTHING about physical "
              "fault probabilities.")

# Same expression as Phase 0 vogel_study.GOLDEN_ANGLE and Kuiper lib.mjs GOLDEN.
GOLDEN = math.pi * (3 - math.sqrt(5))

DIMS = (2, 4, 6)
BUDGETS = (64, 256, 1024)
SEEDS = (0, 1, 2, 3, 4)
REF_POINTS = 20000          # dense random reference set for the covering-radius estimate (NOT reduced)
REF_SEED = 20261017         # reference set for dimension d = default_rng([REF_SEED, d]).random((REF_POINTS, d))
CORNER_METRIC_SIDE = 0.05   # coverage metric: axis-aligned box of side 0.05 at each of the 2^d vertices
EXTREME_BAND = 0.05         # diagnostic: share of coordinates within 0.05 of either face (uniform marginal: 0.10)
RANK_SIG_FIGS = 3           # mean values equal to 3 significant figures share a rank
# Exhaustive low-order synthetic feature families (no RNG): robustness check on the fixed planted placements.
LOWDIM_SLAB_T = 0.02        # 1-D slabs [k/100, k/100+0.02], k=0..98, on every axis           (d*99 placements)
LOWDIM_BOX_S = 0.10         # 2-D boxes, lower corner on the grid k/20, k=0..18, every axis pair (C(d,2)*361)
LOWDIM_CORNER_S = 0.10      # 2-D pair-corner boxes of side 0.1, every axis pair x 4 corners    (C(d,2)*4)
# Phase 0 illustrative screening axes, copied from vogel_study.one_case (ASSUMED there; used here only to quantify
# what the disk's corner gap does to Phase 0's own screen): I = 8 + 16u A, R = 0.001 + 0.049v ohm, P = I^2 R.
PHASE0_SAMPLES = 64
PHASE0_I_A = (8.0, 16.0)
PHASE0_R_OHM = (0.001, 0.049)
PHASE0_LEVELS = (1, 2, 4, 30)          # modules per protection unit (vogel_study.LEVELS)
PHASE0_SCREEN_FRACTION = 0.005         # Phase 0 0.5 %-of-STC-nameplate conduction screen (a study screen only)

BASE_METHODS = ("vogel2d", "vogel_paired", "sobol", "lhs", "random", "grid_corners")
DIAGNOSTIC_METHODS = ("golden_lattice_paired",)
COMPOSITE_METHODS = ("corners_plus_sobol", "corners_plus_vogel_paired", "corners_plus_golden_lattice")
ALL_METHODS = BASE_METHODS + DIAGNOSTIC_METHODS + COMPOSITE_METHODS
ALWAYS_STOCHASTIC = frozenset({"sobol", "lhs", "random", "corners_plus_sobol"})
STOCHASTIC_ABOVE_2D = frozenset({"vogel_paired", "golden_lattice_paired", "corners_plus_vogel_paired",
                                 "corners_plus_golden_lattice"})
METHOD_DESCRIPTIONS = {
    "vogel2d": "SPECIFIED. Phase 0 bounded Vogel disk (deterministic); d>2 = identity tiling of the same disk on "
               "every axis pair (degenerate control, duplicated axes)",
    "vogel_paired": "SPECIFIED. Phase 0 disk on each axis pair; pair 1 Phase 0 order, pair p>=2 sample order permuted "
                    "by numpy default_rng(seed).permutation(N), (p-1)-th draw; seed-invariant at d=2",
    "sobol": "SPECIFIED. scipy.stats.qmc.Sobol(d, scramble=True, rng=seed).random_base2(log2 N)",
    "lhs": "SPECIFIED. scipy.stats.qmc.LatinHypercube(d, rng=seed).random(N), strength 1, no optimisation",
    "random": "SPECIFIED. numpy.random.default_rng(seed).random((N, d))",
    "grid_corners": "SPECIFIED. 2^d vertices + k^d cell-centred factorial (largest k with 2^d+k^d<=N) + greedy-maximin "
                    "padding from the (k+1)^d cell-centred factorial; vertices truncated lexicographically if 2^d>=N",
    "golden_lattice_paired": "DIAGNOSTIC. Pre-image of the Phase 0 disk under the equal-area polar map: "
                             "((i-0.5)/N, frac(i*GOLDEN/2pi)) per axis pair, same permutation rule as vogel_paired",
    "corners_plus_sobol": "COMPOSITE CANDIDATE. explicit vertex set E + first N-|E| scrambled Sobol points",
    "corners_plus_vogel_paired": "COMPOSITE CANDIDATE. explicit vertex set E + vogel_paired with N-|E| points",
    "corners_plus_golden_lattice": "COMPOSITE CANDIDATE. explicit vertex set E + golden_lattice_paired with N-|E| "
                                   "points",
}

# ---------------------------------------------------------------------------------------------------------------
# Planted synthetic counterexample regions: fixed, documented, identical for every method.  Fixed a priori (before
# any result was computed) and NOT tuned afterwards.  Axis names are 1-based in text (x1..xd), 0-based in code.
# ---------------------------------------------------------------------------------------------------------------
CORNER_BOX_SIDE = 0.08
CORNER_BOX_VERTICES = {
    # d=2 has only 2^2 = 4 vertices, so only four corner boxes can exist there.
    2: ((0, 0), (1, 0), (0, 1), (1, 1)),
    4: ((0, 0, 0, 0), (1, 1, 1, 1), (1, 0, 1, 0), (0, 1, 0, 1), (1, 1, 0, 0)),
    # d=6: the all-high vertex is deliberately NOT among the five; it is the separate 'corner6d' region.
    6: ((0, 0, 0, 0, 0, 0), (1, 0, 1, 0, 1, 0), (0, 1, 0, 1, 0, 1), (1, 1, 1, 0, 0, 0), (0, 0, 0, 1, 1, 1)),
}
SLAB_LO = 0.98                  # slab_x1: 0.98 <= x1 <= 1 (thickness 0.02 along axis 1 near 1.0)
BALL_CENTRE = (0.71, 0.29, 0.37, 0.63, 0.58, 0.42)   # first d components; each pair projection lies inside the
BALL_RADIUS = 0.03                                   # inscribed disk, so the ball is reachable by every method
RIDGE_HALF_WIDTH = 0.02         # ridge_x1x2: |x1 - x2| < 0.02
HOLDOUT_LO = 0.9                # holdout_x3x4 (d>=4): 0.9 <= x3 <= 1 and 0.9 <= x4 <= 1 (categorical holdout proxy)
CORNER6D_LO = 0.92              # corner6d (d=6): all x_i > 0.92
REGION_COLUMNS = ("corner_box_1", "corner_box_2", "corner_box_3", "corner_box_4", "corner_box_5",
                  "slab_x1", "ball_interior", "ridge_x1x2", "holdout_x3x4", "corner6d")

NOT_MODELLED = [
    "any PV, arc, cable, inverter, EMT or protection physics",
    "any mapping from unit-cube coordinates to physical parameters or their ranges",
    "any probability or frequency of a physical fault (UNKNOWN; geometric fractions are never probabilities)",
    "adaptive / sequential / physics-guided search (all designs here are non-adaptive, fixed in advance)",
    "regions other than the planted and low-order synthetic sets; real counterexample sets have unknown shape, "
    "size and location",
    "true categorical factors (emulated here by one continuous sub-box; real categorical levels are enumerated)",
    "model-evaluation cost differences between points (equal cost per point assumed)",
]


# ---------------------------------------------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------------------------------------------
def _check_args(n, d):
    if isinstance(n, bool) or int(n) != n or n < 1:
        raise ValueError("budget n must be a positive integer")
    if isinstance(d, bool) or int(d) != d or d < 2 or d % 2:
        raise ValueError("dimension d must be an even integer >= 2 (axis pairs)")


def vogel_disk(n_total):
    """Phase 0 bounded Vogel disk for samples 1..n_total (same arithmetic as vogel_study.vogel_disk).

    NOT a probability distribution: a deterministic point layout filling the disk inscribed in the unit square."""
    if isinstance(n_total, bool) or int(n_total) != n_total or n_total < 1:
        raise ValueError("n_total must be a positive integer")
    n_total = int(n_total)
    pts = np.empty((n_total, 2), dtype=float)
    for sample in range(1, n_total + 1):
        r, theta = math.sqrt((sample - .5) / n_total), sample * GOLDEN
        pts[sample - 1, 0] = .5 + .5 * r * math.cos(theta)
        pts[sample - 1, 1] = .5 + .5 * r * math.sin(theta)
    return pts


def golden_lattice(n_total):
    """Pre-image of vogel_disk(n_total) under the equal-area polar map (s, t) -> disk."""
    if isinstance(n_total, bool) or int(n_total) != n_total or n_total < 1:
        raise ValueError("n_total must be a positive integer")
    n_total = int(n_total)
    pts = np.empty((n_total, 2), dtype=float)
    for sample in range(1, n_total + 1):
        pts[sample - 1, 0] = (sample - .5) / n_total
        turns = sample * GOLDEN / (2 * math.pi)
        pts[sample - 1, 1] = turns - math.floor(turns)
    return pts


def polar_equal_area_map(st):
    """(s, t) in [0,1)^2 -> point of the disk inscribed in the unit square (uniform -> uniform)."""
    r = np.sqrt(st[:, 0])
    ang = 2 * np.pi * st[:, 1]
    return np.column_stack([.5 + .5 * r * np.cos(ang), .5 + .5 * r * np.sin(ang)])


def _paired(block, d, seed):
    rng = np.random.default_rng(seed)
    blocks = [block]
    for _pair in range(1, d // 2):
        blocks.append(block[rng.permutation(len(block))])
    return np.hstack(blocks)


def vogel2d(n, d=2):
    """d=2: Phase 0 disk.  d>2: identity tiling (same sample index on every pair) -- degenerate control."""
    _check_args(n, d)
    return np.tile(vogel_disk(n), (1, d // 2))


def vogel_paired(n, d, seed):
    _check_args(n, d)
    return _paired(vogel_disk(n), d, seed)


def golden_lattice_paired(n, d, seed):
    _check_args(n, d)
    return _paired(golden_lattice(n), d, seed)


def sobol(n, d, seed):
    _check_args(n, d)
    m = int(round(math.log2(n)))
    if 2 ** m != n:
        raise ValueError("Sobol budget must be a power of two to keep the (t,m,s)-net balance")
    return qmc.Sobol(d, scramble=True, rng=seed).random_base2(m)


def lhs(n, d, seed):
    _check_args(n, d)
    return qmc.LatinHypercube(d, rng=seed).random(int(n))


def random_uniform(n, d, seed):
    _check_args(n, d)
    return np.random.default_rng(seed).random((int(n), d))


def all_vertices(d):
    """The 2^d vertices of [0,1]^d in lexicographic order (0 before 1)."""
    return np.array(list(itertools.product((0.0, 1.0), repeat=d)), dtype=float)


def cell_centred_factorial(k, d):
    """Full factorial with k cell-centred levels (i+0.5)/k per axis, lexicographic order; empty if k == 0."""
    if k == 0:
        return np.empty((0, d), dtype=float)
    levels = [(i + 0.5) / k for i in range(k)]
    return np.array(list(itertools.product(levels, repeat=d)), dtype=float)


def greedy_maximin_pad(design, candidates, n_add):
    """Append n_add candidates, each the one farthest from the current design (ties -> lowest index)."""
    if n_add <= 0:
        return design
    d2 = np.full(len(candidates), np.inf)
    for p in design:
        d2 = np.minimum(d2, ((candidates - p) ** 2).sum(axis=1))
    chosen = []
    for _ in range(n_add):
        j = int(np.argmax(d2))
        if not d2[j] > 0.0:
            raise RuntimeError("greedy maximin ran out of distinct candidates")
        chosen.append(j)
        d2 = np.minimum(d2, ((candidates - candidates[j]) ** 2).sum(axis=1))
    return np.vstack([design, candidates[chosen]])


def grid_corners_plan(n, d):
    """(k, n_pad): factorial levels per axis and greedy-maximin padding count; (0, 0) if 2^d >= n."""
    n_vert = 2 ** d
    if n_vert >= n:
        return 0, 0
    k = 0
    while n_vert + (k + 1) ** d <= n:
        k += 1
    return k, n - n_vert - k ** d


def grid_corners(n, d):
    _check_args(n, d)
    verts = all_vertices(d)
    if len(verts) >= n:
        return verts[:n]
    k, n_pad = grid_corners_plan(n, d)
    design = np.vstack([verts, cell_centred_factorial(k, d)])
    return greedy_maximin_pad(design, cell_centred_factorial(k + 1, d), n_pad)


def fractional_factorial_6_2():
    """Regular 2^(6-2) design, resolution IV, generators E=ABC, F=BCD (+/-1 coding mapped to {0,1})."""
    base = np.array(list(itertools.product((-1, 1), repeat=4)), dtype=int)
    a, b, c, dd = base.T
    runs = np.column_stack([a, b, c, dd, a * b * c, b * c * dd])
    return (runs + 1) / 2.0


def explicit_vertex_set(n, d):
    """Generic explicit extreme set for the composite candidates (not tailored to the planted regions)."""
    if 2 ** d <= n // 4:
        return all_vertices(d), f"all_{2 ** d}_vertices"
    runs = 2 ** int(math.floor(math.log2(n // 4)))
    if (d, runs) == (6, 16):
        return fractional_factorial_6_2(), "16_run_2^(6-2)_resIV_fraction_E=ABC_F=BCD"
    raise NotImplementedError(f"no fractional factorial defined for d={d}, runs={runs}")


def corners_plus_sobol(n, d, seed):
    _check_args(n, d)
    verts, _ = explicit_vertex_set(n, d)
    rest = int(n) - len(verts)
    m = int(math.ceil(math.log2(rest)))
    return np.vstack([verts, qmc.Sobol(d, scramble=True, rng=seed).random_base2(m)[:rest]])


def corners_plus_vogel_paired(n, d, seed):
    _check_args(n, d)
    verts, _ = explicit_vertex_set(n, d)
    return np.vstack([verts, vogel_paired(int(n) - len(verts), d, seed)])


def corners_plus_golden_lattice(n, d, seed):
    _check_args(n, d)
    verts, _ = explicit_vertex_set(n, d)
    return np.vstack([verts, golden_lattice_paired(int(n) - len(verts), d, seed)])


GENERATORS = {
    "vogel2d": lambda n, d, seed: vogel2d(n, d),
    "vogel_paired": vogel_paired,
    "sobol": sobol,
    "lhs": lhs,
    "random": random_uniform,
    "grid_corners": lambda n, d, seed: grid_corners(n, d),
    "golden_lattice_paired": golden_lattice_paired,
    "corners_plus_sobol": corners_plus_sobol,
    "corners_plus_vogel_paired": corners_plus_vogel_paired,
    "corners_plus_golden_lattice": corners_plus_golden_lattice,
}


def is_stochastic(method, d):
    return method in ALWAYS_STOCHASTIC or (method in STOCHASTIC_ABOVE_2D and d > 2)


def generate(method, n, d, seed):
    return GENERATORS[method](n, d, seed)


def variant_note(method, n, d):
    if method == "vogel2d":
        return "phase0_disk" if d == 2 else "phase0_disk_identity_tiled_on_every_pair_DEGENERATE_control"
    if method in ("vogel_paired", "golden_lattice_paired"):
        base = "phase0_disk" if method == "vogel_paired" else "golden_lattice_preimage_of_phase0_disk"
        return f"{base}_single_pair_seed_invariant" if d == 2 else f"{base}_pairs2plus_permuted_default_rng_seed"
    if method == "sobol":
        return "scipy_qmc_Sobol_scrambled_random_base2"
    if method == "lhs":
        return "scipy_qmc_LatinHypercube_scrambled_strength1_no_optimisation"
    if method == "random":
        return "numpy_default_rng_uniform_iid"
    if method == "grid_corners":
        if 2 ** d >= n:
            return f"{n}_of_{2 ** d}_vertices_lexicographic_no_interior_points"
        k, n_pad = grid_corners_plan(n, d)
        return f"{2 ** d}_vertices+{k}^{d}_cell_centred_factorial+{n_pad}_greedy_maximin_from_{k + 1}^{d}"
    verts, kind = explicit_vertex_set(n, d)
    tail = {"corners_plus_sobol": "scrambled_sobol_prefix", "corners_plus_vogel_paired": "vogel_paired",
            "corners_plus_golden_lattice": "golden_lattice_paired"}[method]
    return f"{kind}+{n - len(verts)}_{tail}"


# ---------------------------------------------------------------------------------------------------------------
# Regions and metrics
# ---------------------------------------------------------------------------------------------------------------
def region_masks(x):
    """{region: boolean mask over design rows} for the planted regions defined at this dimension."""
    n, d = x.shape
    out = {}
    for j, vertex in enumerate(CORNER_BOX_VERTICES[d], start=1):
        m = np.ones(n, dtype=bool)
        for i, vi in enumerate(vertex):
            m &= (x[:, i] <= CORNER_BOX_SIDE) if vi == 0 else (x[:, i] >= 1.0 - CORNER_BOX_SIDE)
        out[f"corner_box_{j}"] = m
    out["slab_x1"] = x[:, 0] >= SLAB_LO
    centre = np.array(BALL_CENTRE[:d])
    out["ball_interior"] = ((x - centre) ** 2).sum(axis=1) <= BALL_RADIUS ** 2
    out["ridge_x1x2"] = np.abs(x[:, 0] - x[:, 1]) < RIDGE_HALF_WIDTH
    if d >= 4:
        out["holdout_x3x4"] = (x[:, 2] >= HOLDOUT_LO) & (x[:, 3] >= HOLDOUT_LO)
    if d == 6:
        out["corner6d"] = np.all(x > CORNER6D_LO, axis=1)
    return out


def region_volume(name, d):
    """Exact Lebesgue measure of each planted region inside [0,1]^d (DERIVED, algebra)."""
    if name.startswith("corner_box_"):
        return CORNER_BOX_SIDE ** d
    if name == "slab_x1":
        return 1.0 - SLAB_LO
    if name == "ball_interior":
        return math.pi ** (d / 2) / math.gamma(d / 2 + 1) * BALL_RADIUS ** d
    if name == "ridge_x1x2":
        return 1.0 - (1.0 - RIDGE_HALF_WIDTH) ** 2
    if name == "holdout_x3x4":
        return (1.0 - HOLDOUT_LO) ** 2
    if name == "corner6d":
        return (1.0 - CORNER6D_LO) ** d
    raise KeyError(name)


def vertex_containing_regions(d):
    """Planted regions that contain at least one cube vertex (hit by any design that includes all vertices)."""
    return [name for name, mask in region_masks(all_vertices(d)).items() if mask.any()]


def region_definitions(d):
    defs = {}
    for j, vertex in enumerate(CORNER_BOX_VERTICES[d], start=1):
        bounds = [f"x{i + 1} in [0, {CORNER_BOX_SIDE}]" if vi == 0 else f"x{i + 1} in [{1 - CORNER_BOX_SIDE:.2f}, 1]"
                  for i, vi in enumerate(vertex)]
        defs[f"corner_box_{j}"] = {"vertex": list(vertex), "definition": " and ".join(bounds)}
    defs["slab_x1"] = {"definition": f"x1 in [{SLAB_LO}, 1] (thin boundary slab, thickness {1 - SLAB_LO:.2f})"}
    defs["ball_interior"] = {"definition": f"||x - c|| <= {BALL_RADIUS}", "centre": list(BALL_CENTRE[:d])}
    defs["ridge_x1x2"] = {"definition": f"|x1 - x2| < {RIDGE_HALF_WIDTH} (diagonal ridge)"}
    if d >= 4:
        defs["holdout_x3x4"] = {"definition": f"x3 in [{HOLDOUT_LO}, 1] and x4 in [{HOLDOUT_LO}, 1] "
                                              "(emulated categorical holdout)"}
    if d == 6:
        defs["corner6d"] = {"definition": f"all six axes > {CORNER6D_LO} (6-D corner)"}
    with_vertex = set(vertex_containing_regions(d))
    for name in defs:
        vol = region_volume(name, d)
        defs[name]["volume_fraction_of_cube"] = _r(vol)
        defs[name]["iid_uniform_expected_points_inside"] = {f"N{n}": _r(n * vol, 4) for n in BUDGETS}
        defs[name]["contains_a_cube_vertex"] = name in with_vertex
    return defs


def inside_pair_disks(x):
    """True where every axis pair (x1,x2),(x3,x4),... lies in the disk inscribed in its unit square."""
    inside = np.ones(len(x), dtype=bool)
    for p in range(x.shape[1] // 2):
        inside &= (2 * x[:, 2 * p] - 1) ** 2 + (2 * x[:, 2 * p + 1] - 1) ** 2 <= 1.0
    return inside


def corner_fraction_hit(x, side=CORNER_METRIC_SIDE):
    """Fraction of the 2^d vertex boxes (side `side`) that contain at least one design point."""
    lo = x <= side
    hi = x >= 1.0 - side
    in_some_box = np.all(lo | hi, axis=1)
    codes = {tuple(row) for row in hi[in_some_box].astype(np.int8).tolist()}
    return len(codes) / 2 ** x.shape[1]


def max_1d_projection_gap(x):
    """Largest empty interval in any single-axis projection, faces 0 and 1 included as interval ends.

    An axis-aligned slab thinner than this, placed in that gap, contains no design point."""
    worst = 0.0
    for i in range(x.shape[1]):
        col = np.concatenate([[0.0], np.sort(x[:, i]), [1.0]])
        worst = max(worst, float(np.diff(col).max()))
    return worst


def max_abs_axis_correlation(x):
    """Largest |Pearson correlation| between two axes (explicit sums; no BLAS); 1.0 flags duplicated axes."""
    xc = x - x.mean(axis=0)
    norms = np.sqrt((xc ** 2).sum(axis=0))
    best = 0.0
    for i in range(x.shape[1]):
        for j in range(i + 1, x.shape[1]):
            best = max(best, abs(float((xc[:, i] * xc[:, j]).sum() / (norms[i] * norms[j]))))
    return best


def pair_corner_hits(x, i, j, side=LOWDIM_CORNER_S):
    """[hit?] for the four side x side corner boxes of axis pair (i, j), order (lo,lo), (lo,hi), (hi,lo), (hi,hi)."""
    out = []
    for ci, cj in itertools.product((0, 1), repeat=2):
        mi = (x[:, i] <= side) if ci == 0 else (x[:, i] >= 1.0 - side)
        mj = (x[:, j] <= side) if cj == 0 else (x[:, j] >= 1.0 - side)
        out.append(bool((mi & mj).any()))
    return out


def lowdim_missed_fractions(x):
    """Exhaustive low-order synthetic feature families: share of placements containing no design point.

    slab: [k/100, k/100 + 0.02] on each axis, k = 0..98; box2d: [a, a+0.1] x [b, b+0.1] on each axis pair with a, b on
    the grid k/20, k = 0..18; corner2d: the four 0.1 x 0.1 corner boxes of each axis pair.  No RNG.  These fractions
    are shares of an enumerated placement grid, NOT probabilities."""
    n, d = x.shape
    slab_lo = np.arange(99) / 100.0
    slab_missed = 0
    for i in range(d):
        inside = (x[:, i, None] >= slab_lo[None, :]) & (x[:, i, None] <= slab_lo[None, :] + LOWDIM_SLAB_T)
        slab_missed += int((~inside.any(axis=0)).sum())
    box_lo = np.arange(19) / 20.0
    box_missed = corner_missed = 0
    for i, j in itertools.combinations(range(d), 2):
        in_i = ((x[:, i, None] >= box_lo[None, :]) & (x[:, i, None] <= box_lo[None, :] + LOWDIM_BOX_S)).astype(np.int64)
        in_j = ((x[:, j, None] >= box_lo[None, :]) & (x[:, j, None] <= box_lo[None, :] + LOWDIM_BOX_S)).astype(np.int64)
        box_missed += int((in_i.T @ in_j == 0).sum())          # integer matmul: exact counts, no BLAS
        corner_missed += sum(1 for hit in pair_corner_hits(x, i, j) if not hit)
    n_pairs = d * (d - 1) // 2
    return {"lowdim_slab_missed_frac": slab_missed / (d * 99),
            "lowdim_box2d_missed_frac": box_missed / (n_pairs * 361),
            "lowdim_corner2d_missed_frac": corner_missed / (n_pairs * 4)}


class Reference:
    """Fixed reference sets for covering-radius estimates (one per dimension)."""

    def __init__(self, d):
        self.d = d
        self.points = np.random.default_rng([REF_SEED, d]).random((REF_POINTS, d))
        self.inside = inside_pair_disks(self.points)
        # {0, 0.5, 1}^d: vertices, edge/face midpoints and the cube centre (catches both corner and centre holes)
        self.lattice3 = np.array(list(itertools.product((0.0, 0.5, 1.0), repeat=d)), dtype=float)


def evaluate(x, ref):
    """All metrics for one design. Deterministic (cKDTree exact queries, scipy CD with workers=1)."""
    n, d = x.shape
    tree = cKDTree(x)
    nn, _ = tree.query(x, k=2)
    d_ref, _ = tree.query(ref.points, k=1)
    d_lat, _ = tree.query(ref.lattice3, k=1)
    cd2 = float(qmc.discrepancy(x, method="CD"))
    hits = {name: bool(mask.any()) for name, mask in region_masks(x).items()}
    return {
        "n_points": n,
        "cd_squared_scipy": cd2,
        "cd_centred_l2": math.sqrt(cd2),
        "min_pairwise_distance": float(nn[:, 1].min()),
        "covering_radius_ref": float(d_ref.max()),
        "covering_radius_ref_plus_lattice3": float(max(d_ref.max(), d_lat.max())),
        "covering_radius_inside_pair_disks": float(d_ref[ref.inside].max()),
        "uncovered_frac_r0p03": float((d_ref > BALL_RADIUS).mean()),
        "corner_fraction_hit_side0p05": corner_fraction_hit(x),
        "frac_points_outside_pair_disks": float(1.0 - inside_pair_disks(x).mean()),
        "frac_coords_in_extreme_bands": float(((x <= EXTREME_BAND) | (x >= 1.0 - EXTREME_BAND)).mean()),
        "max_1d_projection_gap": max_1d_projection_gap(x),
        **lowdim_missed_fractions(x),
        "max_abs_axis_correlation": max_abs_axis_correlation(x),
        "planted_regions_total": len(hits),
        "planted_regions_missed": sum(1 for hit in hits.values() if not hit),
        "hits": hits,
    }


def validate_design(x, n, d):
    if x.shape != (n, d):
        raise AssertionError(f"design shape {x.shape} != {(n, d)} (equal-budget rule)")
    if not (np.all(x >= 0.0) and np.all(x <= 1.0)):
        raise AssertionError("design leaves the unit cube")
    if len(np.unique(x, axis=0)) != n:
        raise AssertionError("duplicate design points waste budget")


def load_fixture_plant():
    """Plant counts and nameplate from the shared fixture (read-only)."""
    plant = json.loads(FIXTURE_PATH.read_text())["plant"]
    return {"strings": int(plant["strings"]), "modules_per_string": int(plant["modules_per_string"]),
            "dc_nameplate_wp": float(plant["dc_nameplate_wp"])}


def phase0_power_w(u, v):
    """Phase 0 per-unit screening dissipation P = I^2 R on its illustrative axes (ASSUMED in vogel_study.one_case)."""
    return (PHASE0_I_A[0] + PHASE0_I_A[1] * u) ** 2 * (PHASE0_R_OHM[0] + PHASE0_R_OHM[1] * v)


def phase0_unit_thresholds_w(plant):
    """Per-unit dissipation threshold of the Phase 0 screen for each level: 0.5 % x nameplate / unit count."""
    out = {}
    for level in PHASE0_LEVELS:
        units = plant["strings"] * math.ceil(plant["modules_per_string"] / level)
        out[level] = (units, PHASE0_SCREEN_FRACTION * plant["dc_nameplate_wp"] / units)
    return out


def phase0_screen_corner_gap():
    """What the disk's corner gap does to Phase 0's own loss screen (vogel_study.one_case axes, ASSUMED there).

    P = (8 + 16u)^2 (0.001 + 0.049v) increases in u and v, so its maximum over the unit square is the vertex (1, 1)
    and its maximum over the inscribed disk lies on the upper-right boundary arc (scanned at 100001 angles).
    The screen pass fraction is then compared across layouts: it is a property of the layout, never a probability."""
    disk = vogel_disk(PHASE0_SAMPLES)
    p_samples = phase0_power_w(disk[:, 0], disk[:, 1])
    j = int(np.argmax(p_samples))
    ang = np.linspace(0.0, 0.5 * np.pi, 100001)
    p_disk = float(phase0_power_w(0.5 + 0.5 * np.cos(ang), 0.5 + 0.5 * np.sin(ang)).max())
    p_corner = float(phase0_power_w(1.0, 1.0))
    plant = load_fixture_plant()
    # exact-in-the-limit area shares by a 2001 x 2001 midpoint grid (deterministic)
    g = (np.arange(2001) + 0.5) / 2001
    uu, vv = np.meshgrid(g, g, indexing="ij")
    pp = phase0_power_w(uu, vv)
    in_disk = (2 * uu - 1) ** 2 + (2 * vv - 1) ** 2 <= 1.0
    pass_table = {}
    for level, (units, thr) in phase0_unit_thresholds_w(plant).items():
        sob = [int((phase0_power_w(*sobol(PHASE0_SAMPLES, 2, s).T) <= thr).sum()) for s in SEEDS]
        pass_table[f"level_{level}"] = {
            "units": units, "unit_threshold_w": _r(thr, 6),
            "phase0_disk_64_samples_pass": int((p_samples <= thr).sum()),
            "sobol_64_full_rectangle_pass_seeds_0_4": sob,
            "grid_area_share_full_rectangle": _r(float((pp <= thr).mean()), 4),
            "grid_area_share_inscribed_disk": _r(float((pp[in_disk] <= thr).mean()), 4),
        }
    return {
        "label": "DERIVED", "grade": "algebra",
        "axes": "Phase 0 illustrative screening axes from vogel_study.one_case: I = 8..24 A, R = 0.001..0.050 ohm, "
                "P = I^2 R per unit (ASSUMED in Phase 0; not fixture values, not a device loss prediction)",
        "fixture_values_used": {"plant.strings": plant["strings"],
                                "plant.modules_per_string": plant["modules_per_string"],
                                "plant.dc_nameplate_wp": plant["dc_nameplate_wp"]},
        "max_unit_w_over_64_phase0_samples": _r(float(p_samples[j]), 6),
        "argmax_phase0_sample": j + 1,
        "argmax_current_a": _r(PHASE0_I_A[0] + PHASE0_I_A[1] * disk[j, 0], 6),
        "argmax_series_r_ohm": _r(PHASE0_R_OHM[0] + PHASE0_R_OHM[1] * disk[j, 1], 6),
        "max_unit_w_over_continuous_disk": _r(p_disk, 6),
        "max_unit_w_at_rectangle_corner_24a_0p05ohm": _r(p_corner, 6),
        "corner_over_sampled_max_ratio": _r(p_corner / float(p_samples[j]), 4),
        "screen_pass_counts_depend_on_layout": pass_table,
        "reading": "the Phase 0 disk screen's worst sampled case is below the screen's own worst corner; explicit "
                   "corner points are needed even for monotone screens. Pass counts and area shares differ between "
                   "layouts of the same axes: a sample pass fraction is a property of the layout, NOT a probability.",
    }


# ---------------------------------------------------------------------------------------------------------------
# Benchmark run, CSV and summary
# ---------------------------------------------------------------------------------------------------------------
NUMERIC_METRICS = ("planted_regions_missed", "cd_centred_l2", "cd_squared_scipy", "min_pairwise_distance",
                   "covering_radius_ref", "covering_radius_ref_plus_lattice3", "covering_radius_inside_pair_disks",
                   "uncovered_frac_r0p03", "corner_fraction_hit_side0p05", "frac_points_outside_pair_disks",
                   "frac_coords_in_extreme_bands", "max_1d_projection_gap", "lowdim_slab_missed_frac",
                   "lowdim_box2d_missed_frac", "lowdim_corner2d_missed_frac", "max_abs_axis_correlation")
CSV_COLUMNS = (("method", "method_role", "variant", "d", "budget_n", "seed", "n_points", "planted_regions_total")
               + NUMERIC_METRICS + tuple(f"hit_{r}" for r in REGION_COLUMNS)
               + ("assumption_label", "evidence_grade", "scope"))
RANKED_METRICS = (
    # (metric, better, primary?, description)
    ("planted_regions_missed", "lower", True,
     "KEY METRIC: planted synthetic regions containing no design point (of 7 at d=2, 9 at d=4, 10 at d=6)"),
    ("cd_centred_l2", "lower", True, "centred L2 discrepancy = sqrt(scipy qmc.discrepancy(method='CD'))"),
    ("min_pairwise_distance", "higher", True, "minimum Euclidean distance between two design points"),
    ("covering_radius_ref", "lower", True,
     f"max over {REF_POINTS} fixed random reference points of the distance to the nearest design point"),
    ("corner_fraction_hit_side0p05", "higher", True, "fraction of the 2^d vertex boxes (side 0.05) hit"),
    ("lowdim_slab_missed_frac", "lower", False,
     "SUPPLEMENTARY: share of the d*99 enumerated 1-D slabs (thickness 0.02) containing no point"),
    ("lowdim_box2d_missed_frac", "lower", False,
     "SUPPLEMENTARY: share of the C(d,2)*361 enumerated 2-D boxes (side 0.1, any axis pair) containing no point"),
    ("lowdim_corner2d_missed_frac", "lower", False,
     "SUPPLEMENTARY: share of the C(d,2)*4 two-dimensional pair-corner boxes (side 0.1) containing no point"),
    ("covering_radius_ref_plus_lattice3", "lower", False,
     "SUPPLEMENTARY: covering radius with the {0,0.5,1}^d lattice (vertices, midpoints, centre) added"),
    ("covering_radius_inside_pair_disks", "lower", False,
     "SUPPLEMENTARY: covering radius over reference points inside every inscribed pair disk (Vogel's own domain)"),
    ("max_1d_projection_gap", "lower", False,
     "SUPPLEMENTARY: largest empty interval in any 1-D axis projection (exposes projection collapse of grids)"),
    ("uncovered_frac_r0p03", "lower", False,
     "SUPPLEMENTARY: share of reference points farther than 0.03 from every design point (volume share, not a "
     "probability; saturates near 1 at d>=4)"),
)
SCOPE = "synthetic_unit_cube_geometry_only;no_physics;not_a_probability"


def _r(v, sig=9):
    """Round a float to `sig` significant digits for stable, readable output."""
    v = float(v)
    return 0.0 if v == 0.0 else float(format(v, f".{sig}g"))


def _fmt(v):
    if v is None:
        return "NA"
    if isinstance(v, (bool, np.bool_)):
        return "1" if v else "0"
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    if isinstance(v, (float, np.floating)):
        v = float(v)
        return "0" if v == 0.0 else format(v, ".9g")
    return str(v)


def method_role(method):
    if method in BASE_METHODS:
        return "specified"
    return "diagnostic" if method in DIAGNOSTIC_METHODS else "composite_candidate"


def run_designs(dims=DIMS, budgets=BUDGETS, methods=ALL_METHODS, seeds=SEEDS):
    rows = []
    for d in dims:
        ref = Reference(d)
        for n in budgets:
            for method in methods:
                for seed in (seeds if is_stochastic(method, d) else (None,)):
                    x = generate(method, n, d, seed)
                    validate_design(x, n, d)
                    rows.append({"method": method, "method_role": method_role(method),
                                 "variant": variant_note(method, n, d), "d": d, "budget_n": n, "seed": seed,
                                 **evaluate(x, ref)})
    return rows


def rows_to_csv(rows):
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(CSV_COLUMNS)
    fixed = {"assumption_label": "DERIVED", "evidence_grade": "illustrative_simulation", "scope": SCOPE}
    for row in rows:
        out = []
        for col in CSV_COLUMNS:
            if col.startswith("hit_"):
                region = col[4:]
                out.append(_fmt(row["hits"][region]) if region in row["hits"] else "NA")
            elif col in fixed:
                out.append(fixed[col])
            else:
                out.append(_fmt(row[col]))
        writer.writerow(out)
    return buf.getvalue()


def _ranks(scores, better):
    """Competition ranking (1 = best; values equal to RANK_SIG_FIGS significant figures share a rank)."""
    sign = -1.0 if better == "higher" else 1.0
    keyed = {m: float(format(sign * v, f".{RANK_SIG_FIGS}g")) for m, v in scores.items()}
    ordered = sorted(scores, key=lambda m: (keyed[m], m))
    ranks = {m: 1 + sum(1 for o in scores if keyed[o] < keyed[m]) for m in scores}
    return ordered, ranks


def vogel_representative(d):
    return "vogel2d" if d == 2 else "vogel_paired"


def _g(v):
    return f"{v:.3g}"


def build_conclusion(groups, mean_of, phase0):
    """Candid conclusion; every number is interpolated from the computed results (no hand-typed values)."""
    cells = [(d, n) for d in DIMS for n in BUDGETS]
    others = ("sobol", "lhs", "random", "grid_corners")

    def series(method, metric, d):
        return "/".join(_g(mean_of(d, n, method, metric)) for n in BUDGETS)

    def designs(d, method, budgets=BUDGETS):
        return [g for n in budgets for g in groups[(d, n, method)]]

    def misses(d, method, region, budgets=BUDGETS):
        ds = designs(d, method, budgets)
        return f"{sum(1 for g in ds if not g['hits'][region])}/{len(ds)}"

    def rank6(d, n, method, metric, better):
        return _ranks({m: mean_of(d, n, m, metric) for m in BASE_METHODS}, better)[1][method]

    def ranks6(d, method, metric, better):
        return "/".join(str(rank6(d, n, method, metric, better)) for n in BUDGETS)

    s_star = 0.5 - 0.5 / math.sqrt(2)
    floor2 = (math.sqrt(2) - 1) / 2
    corner_boxes = {d: [f"corner_box_{j}" for j in range(1, len(CORNER_BOX_VERTICES[d]) + 1)] for d in DIMS}
    vog_corner_zero = sum(1 for d, n in cells if mean_of(d, n, vogel_representative(d),
                                                           "corner_fraction_hit_side0p05") == 0.0)
    vog_all_corner_boxes_missed = all(not g["hits"][r] for d in DIMS for g in designs(d, vogel_representative(d))
                                      for r in corner_boxes[d])
    vog_last_key = sum(1 for d, n in cells
                       if _ranks({m: mean_of(d, n, m, "planted_regions_missed")
                                  for m in (vogel_representative(d),) + others}, "lower")[1][vogel_representative(d)] == 5)
    tiling_cov_ranks = [rank6(d, n, "vogel2d", "covering_radius_ref", "lower") for d in (4, 6) for n in BUDGETS]
    paired_ranks = [rank6(d, n, "vogel_paired", m, b) for d in (4, 6) for n in BUDGETS
                    for m, b in (("cd_centred_l2", "lower"), ("min_pairwise_distance", "higher"))]

    def regions_missed_in_any(d, method, budgets=BUDGETS):
        ds = designs(d, method, budgets)
        return [r for r in ds[0]["hits"] if any(not g["hits"][r] for g in ds)]
    box64 = {m: mean_of(2, 64, m, "lowdim_box2d_missed_frac") for m in BASE_METHODS}
    box_runner_up = min((m for m in BASE_METHODS if m not in ("vogel2d", "vogel_paired")), key=lambda m: box64[m])
    box_margin = (box64[box_runner_up] - box64["vogel2d"]) / box64[box_runner_up]
    cd_ratio = mean_of(2, 1024, "vogel2d", "cd_centred_l2") / mean_of(2, 1024, "sobol", "cd_centred_l2")
    h = 2 * SLAB_LO - 1
    seg = 0.25 * (math.acos(h) - h * math.sqrt(1 - h ** 2))
    slab_ratio = (1 - SLAB_LO) / (seg / (math.pi / 4))
    hh = 2 * HOLDOUT_LO - 1
    hold_ratio = (0.25 * (math.acos(hh) - hh * math.sqrt(1 - hh ** 2)) / (math.pi / 4) / (1 - HOLDOUT_LO)) ** 2
    pair_floor = {d: 1.0 / (d - 1) for d in (4, 6)}
    pair_floor_ok = all(g["lowdim_corner2d_missed_frac"] >= pair_floor[d] - 1e-12 for d in (4, 6)
                        for g in designs(d, "vogel_paired"))
    with_vertex = {d: len(vertex_containing_regions(d)) for d in DIMS}
    totals = {d: groups[(d, 64, "sobol")][0]["planted_regions_total"] for d in DIMS}
    grid_first = sum(1 for d, n in cells if rank6(d, n, "grid_corners", "planted_regions_missed", "lower") == 1)
    sobol_cd_first = sum(1 for d, n in cells if rank6(d, n, "sobol", "cd_centred_l2", "lower") == 1)
    sobol_gap_first = sum(1 for d, n in cells if rank6(d, n, "sobol", "max_1d_projection_gap", "lower") == 1)
    sobol_cov_top2 = sum(1 for d, n in cells if rank6(d, n, "sobol", "covering_radius_ref", "lower") <= 2)

    def any_corner_hit(d, method):
        ds = designs(d, method)
        return f"{sum(1 for g in ds if any(g['hits'][r] for r in corner_boxes[d]))}/{len(ds)}"

    ball_missed_everywhere = {d: all(not g["hits"]["ball_interior"] for m in ALL_METHODS for g in designs(d, m))
                              for d in (4, 6)}
    disk_cov_rank = [rank6(2, n, "vogel2d", "covering_radius_inside_pair_disks", "lower") for n in BUDGETS]
    disk_cov_better = sorted({m for n in BUDGETS for m in BASE_METHODS
                              if rank6(2, n, m, "covering_radius_inside_pair_disks", "lower")
                              < rank6(2, n, "vogel2d", "covering_radius_inside_pair_disks", "lower")})
    ball_area_2d = math.pi * BALL_RADIUS ** 2
    ball_expected_disk = "/".join(_g(n * ball_area_2d * 4 / math.pi) for n in BUDGETS)

    # head-to-head of the two bulk choices behind the SAME explicit vertex block, over all 9 (d, N) cells
    h2h_metrics = (("covering_radius_ref", "lower"), ("lowdim_box2d_missed_frac", "lower"),
                   ("lowdim_slab_missed_frac", "lower"), ("min_pairwise_distance", "higher"),
                   ("cd_centred_l2", "lower"), ("planted_regions_missed", "lower"))
    h2h_table, h2h_text = {}, []
    for metric, better in h2h_metrics:
        sob, vog, tie = [], [], []
        for d, n in cells:
            _o, rk = _ranks({"corners_plus_sobol": mean_of(d, n, "corners_plus_sobol", metric),
                             "corners_plus_vogel_paired": mean_of(d, n, "corners_plus_vogel_paired", metric)}, better)
            (sob if rk["corners_plus_sobol"] < rk["corners_plus_vogel_paired"]
             else vog if rk["corners_plus_vogel_paired"] < rk["corners_plus_sobol"] else tie).append(f"d{d}_N{n}")
        h2h_table[metric] = {"better": better, "sobol_bulk_better": sob, "vogel_bulk_better": vog, "tie": tie}
        h2h_text.append(f"{metric}: Sobol bulk better in {len(sob)}/9, Vogel bulk in {len(vog)}/9"
                        f"{' (' + ', '.join(vog) + ')' if vog else ''}, ties {len(tie)}")
    why_sobol_bulk = (
        "Same explicit vertex block, Sobol bulk (corners_plus_sobol) vs scrambled-paired Vogel bulk "
        "(corners_plus_vogel_paired), over the 9 (d, N) cells: " + "; ".join(h2h_text) + ". "
        f"The Vogel-bulk wins on centred L2 discrepancy are at small N (d=4 N=64: "
        f"{_g(mean_of(4, 64, 'corners_plus_vogel_paired', 'cd_centred_l2'))} vs "
        f"{_g(mean_of(4, 64, 'corners_plus_sobol', 'cd_centred_l2'))}; d=6 N=256: "
        f"{_g(mean_of(6, 256, 'corners_plus_vogel_paired', 'cd_centred_l2'))} vs "
        f"{_g(mean_of(6, 256, 'corners_plus_sobol', 'cd_centred_l2'))}). Interpretation (not measured): the vertex "
        f"block over-weights the corners relative to the uniform reference and the disk bulk under-weights them, so the "
        f"two errors partly cancel in a discrepancy; this is compensation, not better coverage, since the covering "
        f"radius favours the Sobol bulk in {len(h2h_table['covering_radius_ref']['sobol_bulk_better'])}/9 cells. The "
        f"disk bulk does not converge (vogel_paired centred L2 discrepancy d=4 {series('vogel_paired', 'cd_centred_l2', 4)}"
        f" vs sobol {series('sobol', 'cd_centred_l2', 4)}), so its relative position worsens as the budget grows.")

    wins = [
        f"Separation (d=2): vogel2d has the largest minimum pairwise distance of the six specified methods (ranks "
        f"{ranks6(2, 'vogel2d', 'min_pairwise_distance', 'higher')} at N=64/256/1024): "
        f"{series('vogel2d', 'min_pairwise_distance', 2)} vs grid_corners "
        f"{series('grid_corners', 'min_pairwise_distance', 2)}, sobol {series('sobol', 'min_pairwise_distance', 2)}, "
        f"lhs {series('lhs', 'min_pairwise_distance', 2)}, random {series('random', 'min_pairwise_distance', 2)}.",
        f"Coverage of its own inscribed disk (d=2): covering radius over reference points inside the disk "
        f"{series('vogel2d', 'covering_radius_inside_pair_disks', 2)} (ranks "
        f"{'/'.join(map(str, disk_cov_rank))} of 6; better: {', '.join(disk_cov_better) or 'none'} "
        f"{'/'.join(series(m, 'covering_radius_inside_pair_disks', 2) for m in disk_cov_better)}; sobol "
        f"{series('sobol', 'covering_radius_inside_pair_disks', 2)}, random "
        f"{series('random', 'covering_radius_inside_pair_disks', 2)}).",
        f"Key metric with 4 explicit vertices added (d=2): corners_plus_vogel_paired misses "
        f"{series('corners_plus_vogel_paired', 'planted_regions_missed', 2)} planted regions vs corners_plus_sobol "
        f"{series('corners_plus_sobol', 'planted_regions_missed', 2)} (N=64/256/1024): its {64 - 4}/{256 - 4}/"
        f"{1024 - 4}-point disk hits the interior ball (missed in "
        f"{misses(2, 'corners_plus_vogel_paired', 'ball_interior')} composite designs), which the Sobol composite "
        f"misses in {misses(2, 'corners_plus_sobol', 'ball_interior', (64,))} seeds at N=64 and "
        f"{misses(2, 'corners_plus_sobol', 'ball_interior', (256,))} at N=256. Candidly, this is layout luck: one "
        f"deterministic layout per N against one fixed ball. The pure 64-point Phase 0 disk misses the same ball "
        f"({misses(2, 'vogel2d', 'ball_interior', (64,))}); the disk density is 4/pi = 1.27x uniform inside the disk, "
        f"giving only {ball_expected_disk} expected points in the ball at N=64/256/1024; and the full-square "
        f"golden-lattice composite misses it at N=64 ({misses(2, 'corners_plus_golden_lattice', 'ball_interior', (64,))}).",
        f"Smallest budget (d=2, N=64): fewest missed 2-D boxes of side 0.1 ({_g(box64['vogel2d'])} vs runner-up "
        f"{box_runner_up} {_g(box64[box_runner_up])}, a {100 * box_margin:.1f}% margin; sobol {_g(box64['sobol'])}, "
        f"random {_g(box64['random'])}). From N=256 this reverses ({series('vogel2d', 'lowdim_box2d_missed_frac', 2)} vs "
        f"sobol {series('sobol', 'lowdim_box2d_missed_frac', 2)}) because boxes near the square's corners are "
        f"unreachable.",
        f"vogel_paired (d=4, 6) is mid-table on discrepancy and separation, ranks {min(paired_ranks)}-"
        f"{max(paired_ranks)} of 6: centred L2 discrepancy ranks d=4 {ranks6(4, 'vogel_paired', 'cd_centred_l2', 'lower')}"
        f", d=6 {ranks6(6, 'vogel_paired', 'cd_centred_l2', 'lower')}; minimum distance ranks d=4 "
        f"{ranks6(4, 'vogel_paired', 'min_pairwise_distance', 'higher')}, d=6 "
        f"{ranks6(6, 'vogel_paired', 'min_pairwise_distance', 'higher')}; covering radius d=6 N=64 rank "
        f"{rank6(6, 64, 'vogel_paired', 'covering_radius_ref', 'lower')} ({_g(mean_of(6, 64, 'vogel_paired', 'covering_radius_ref'))}"
        f" vs sobol {_g(mean_of(6, 64, 'sobol', 'covering_radius_ref'))}).",
    ]
    losses = [
        f"Corners (structural): the Vogel representative (vogel2d at d=2, vogel_paired at d>2) hits no vertex box "
        f"(side 0.05) in {vog_corner_zero}/9 (d,N) cells; every planted corner box (side 0.08) is missed in every "
        f"design: {vog_all_corner_boxes_missed}. Any vertex box of side < {_g(s_star)} lies wholly outside the inscribed "
        f"disk, so no budget N can fix it. It ranks 5th of 5 on planted regions missed in {vog_last_key}/9 cells "
        f"(mean misses d=2 {series('vogel2d', 'planted_regions_missed', 2)} of {totals[2]}, d=4 "
        f"{series('vogel_paired', 'planted_regions_missed', 4)} of {totals[4]}, d=6 "
        f"{series('vogel_paired', 'planted_regions_missed', 6)} of {totals[6]}).",
        f"Categorical-holdout proxy (structural): vogel_paired misses holdout_x3x4 in "
        f"{misses(4, 'vogel_paired', 'holdout_x3x4')} designs at d=4 and {misses(6, 'vogel_paired', 'holdout_x3x4')} at "
        f"d=6 (x3, x4 are one Vogel pair here and the box x3,x4 >= {HOLDOUT_LO} is "
        f"{_g(math.sqrt(2) * (HOLDOUT_LO - 0.5))} from the disk centre, radius 0.5; with x3, x4 in different pairs it "
        f"would be reachable but at {_g(hold_ratio)}x the uniform density); sobol "
        f"{misses(4, 'sobol', 'holdout_x3x4')} / {misses(6, 'sobol', 'holdout_x3x4')}, lhs "
        f"{misses(4, 'lhs', 'holdout_x3x4')} / {misses(6, 'lhs', 'holdout_x3x4')}, random "
        f"{misses(4, 'random', 'holdout_x3x4')} / {misses(6, 'random', 'holdout_x3x4')}. Every pair-corner box (side "
        f"0.1) of its own axis pairs is unreachable, a floor of 1/(d-1) of all pair-corner placements "
        f"({_g(pair_floor[4])} at d=4, {_g(pair_floor[6])} at d=6; floor respected in every design: {pair_floor_ok}); "
        f"observed {series('vogel_paired', 'lowdim_corner2d_missed_frac', 4)} (d=4) vs sobol "
        f"{series('sobol', 'lowdim_corner2d_missed_frac', 4)}.",
        f"No convergence: vogel2d centred L2 discrepancy at d=2 is {series('vogel2d', 'cd_centred_l2', 2)} for "
        f"N=64/256/1024 (sobol {series('sobol', 'cd_centred_l2', 2)}; {cd_ratio:.0f}x at N=1024). Its covering radius "
        f"{series('vogel2d', 'covering_radius_ref', 2)} tends to the analytic floor {_g(floor2)} (vertex-to-disk "
        f"distance), not to zero (sobol {series('sobol', 'covering_radius_ref', 2)}): the layout converges to the "
        f"uniform law on the disk, not on the square.",
        f"Boundary slabs: the disk places {slab_ratio:.1f}x fewer points in the slab x1 >= {SLAB_LO} than a uniform "
        f"layout (analytic). slab_x1 missed: vogel2d {misses(2, 'vogel2d', 'slab_x1', (64,))} at N=64, vogel_paired "
        f"{misses(4, 'vogel_paired', 'slab_x1', (64,))} (d=4) and {misses(6, 'vogel_paired', 'slab_x1', (64,))} (d=6) "
        f"at N=64, vs sobol {misses(4, 'sobol', 'slab_x1', (64,))} / {misses(6, 'sobol', 'slab_x1', (64,))} and lhs "
        f"{misses(4, 'lhs', 'slab_x1', (64,))} / {misses(6, 'lhs', 'slab_x1', (64,))}. Enumerated 0.02-thick 1-D slabs "
        f"missed at N=64, d=2: vogel2d {_g(mean_of(2, 64, 'vogel2d', 'lowdim_slab_missed_frac'))} vs sobol "
        f"{_g(mean_of(2, 64, 'sobol', 'lowdim_slab_missed_frac'))}, lhs {_g(mean_of(2, 64, 'lhs', 'lowdim_slab_missed_frac'))}"
        f". Share of coordinates within {EXTREME_BAND} of a face: {_g(mean_of(2, 1024, 'vogel2d', 'frac_coords_in_extreme_bands'))}"
        f" vs sobol {_g(mean_of(2, 1024, 'sobol', 'frac_coords_in_extreme_bands'))} (d=2, N=1024).",
        f"Identity tiling (the Phase 0 2-D index reused on every axis pair, d>2) duplicates axes (max |corr| "
        f"{_g(mean_of(4, 64, 'vogel2d', 'max_abs_axis_correlation'))}) and ranks {'/'.join(map(str, tiling_cov_ranks))} "
        f"of 6 on covering radius in the six d>2 cells: never reuse one 2-D index on several axis pairs.",
        f"Phase 0's own screen: with the Phase 0 axes (I = 8..24 A, R = 1..50 mOhm, P = I^2 R) the worst of the 64 disk "
        f"samples is {_g(phase0['max_unit_w_over_64_phase0_samples'])} W (sample {phase0['argmax_phase0_sample']}), "
        f"the continuous disk maximum {_g(phase0['max_unit_w_over_continuous_disk'])} W, but the rectangle corner "
        f"(24 A, 0.05 ohm) gives {_g(phase0['max_unit_w_at_rectangle_corner_24a_0p05ohm'])} W: the screened worst case "
        f"is understated {phase0['corner_over_sampled_max_ratio']:.2f}x (algebra on illustrative axes). The screen's "
        f"pass count is a layout property: single-module level passes "
        f"{phase0['screen_pass_counts_depend_on_layout']['level_1']['phase0_disk_64_samples_pass']}/64 disk samples vs "
        f"{'/'.join(map(str, phase0['screen_pass_counts_depend_on_layout']['level_1']['sobol_64_full_rectangle_pass_seeds_0_4']))}"
        f" of 64 for Sobol seeds 0-4 on the full rectangle (never a probability).",
    ]
    diagnostic = (
        f"Attribution: the losses come from the inscribed-disk map, not from the golden-angle sequence. "
        f"golden_lattice_paired (the disk's pre-image on the full square) has centred L2 discrepancy d=2 "
        f"{series('golden_lattice_paired', 'cd_centred_l2', 2)} (sobol {series('sobol', 'cd_centred_l2', 2)}), minimum "
        f"distance d=2 {series('golden_lattice_paired', 'min_pairwise_distance', 2)} (vogel2d "
        f"{series('vogel2d', 'min_pairwise_distance', 2)}), and misses holdout_x3x4 in "
        f"{misses(4, 'golden_lattice_paired', 'holdout_x3x4')} designs at d=4. With random pair permutations it is "
        f"LHS-like at d=6 (centred L2 discrepancy {series('golden_lattice_paired', 'cd_centred_l2', 6)} vs lhs "
        f"{series('lhs', 'cd_centred_l2', 6)}, sobol {series('sobol', 'cd_centred_l2', 6)}) and, like every "
        f"space-filling design, it still misses the full-dimensional corner boxes.")
    others_text = [
        f"grid_corners has the fewest planted misses in {grid_first}/9 cells because it contains all 2^d vertices "
        f"whenever 2^d <= N and {with_vertex[2]}/{totals[2]}, {with_vertex[4]}/{totals[4]}, {with_vertex[6]}/{totals[6]} "
        f"planted regions (d=2/4/6) contain a cube vertex (all except ball_interior): the key metric rewards explicit "
        f"vertices, not interior quality. Its 1-D projections collapse: max 1-D gap "
        f"{series('grid_corners', 'max_1d_projection_gap', 4)} (d=4) and {series('grid_corners', 'max_1d_projection_gap', 6)}"
        f" (d=6) vs sobol {series('sobol', 'max_1d_projection_gap', 4)} (d=4); enumerated thin 1-D slabs missed "
        f"{series('grid_corners', 'lowdim_slab_missed_frac', 4)} (d=4) vs sobol "
        f"{series('sobol', 'lowdim_slab_missed_frac', 4)}; at d=6, N=64 all 64 points are vertices (centred L2 "
        f"discrepancy {_g(mean_of(6, 64, 'grid_corners', 'cd_centred_l2'))}, sobol {_g(mean_of(6, 64, 'sobol', 'cd_centred_l2'))}).",
        f"Sobol has the lowest mean centred L2 discrepancy in {sobol_cd_first}/9 cells, the smallest max 1-D "
        f"projection gap in {sobol_gap_first}/9 (ties at 3 s.f. included) and a top-2 covering radius in "
        f"{sobol_cov_top2}/9, and it converges with N. Without explicit vertices it still misses full-dimensional "
        f"corners: designs hitting at least one planted corner box (side 0.08): d=4 {any_corner_hit(4, 'sobol')}, "
        f"d=6 {any_corner_hit(6, 'sobol')}; 2-D pair-corner boxes missed d=4 {series('sobol', 'lowdim_corner2d_missed_frac', 4)}.",
        f"Not found by any method here: ball_interior (radius {BALL_RADIUS}) is missed in every design of every method "
        f"at d=4 ({'yes' if ball_missed_everywhere[4] else 'no'}) and d=6 ({'yes' if ball_missed_everywhere[6] else 'no'}); "
        f"its volume {_g(region_volume('ball_interior', 4))} (d=4) / {_g(region_volume('ball_interior', 6))} (d=6) "
        f"means an iid uniform design of N=1024 would hold {_g(1024 * region_volume('ball_interior', 4))} / "
        f"{_g(1024 * region_volume('ball_interior', 6))} points in it in expectation. Small full-dimensional interior "
        f"features are not found by any non-adaptive design at these budgets.",
    ]
    composite = {
        "design": [
            "1. Categorical factors (protection P0..P3, inverter V_BOOST/V_DIRECTBUS, fault location near/far, "
            "night/day, case family) are ENUMERATED as a full factorial over their levels, as the cycle-1 scenario "
            "ledger already does (or a strength-2 covering array if the product grows too large); never emulated as "
            "a continuous sub-box and never left to a space-filling design.",
            "2. Per categorical combination, an explicit deterministic extreme block on the continuous axes: all 2^d "
            "vertices when 2^d <= N/4, otherwise a resolution-IV two-level fraction PLUS the physically named "
            "corners (e.g. cold Voc x maximum irradiance, 0 A night, longest route, minimum sustaining current) "
            "listed by the physics tracks, plus face points for one-at-a-time limits.",
            "3. Remaining budget: scrambled Sobol (power-of-two N, seeds recorded), the same Sobol block reused across "
            "protection candidates so that architecture comparisons are paired.",
            "4. Targeted adversarial cases (brief section 6) and adaptive refinement around observed near-failures, "
            "because small interior features are not found by any non-adaptive design at these budgets.",
            "5. Kuiper r=sqrt(k) stays an identity/address only. The Phase 0 bounded Vogel disk is not used for "
            "coverage claims (it never samples "
            + ", ".join(f"{_g(1 - (math.pi / 4) ** (d / 2))} of the {d}-D cube volume" for d in DIMS)
            + "). If a golden-angle construction is wanted for a 2-D screen, use the full-square golden lattice, "
              "plus the 4 vertices.",
        ],
        "why_explicit_vertices": (
            f"The vertex block, not the bulk method, removes corner and holdout misses: planted misses d=4 sobol "
            f"{series('sobol', 'planted_regions_missed', 4)} -> corners_plus_sobol "
            f"{series('corners_plus_sobol', 'planted_regions_missed', 4)}; vogel_paired "
            f"{series('vogel_paired', 'planted_regions_missed', 4)} -> corners_plus_vogel_paired "
            f"{series('corners_plus_vogel_paired', 'planted_regions_missed', 4)} (N=64/256/1024; regions still missed in "
            f"any d=4 composite design: {', '.join(regions_missed_in_any(4, 'corners_plus_sobol'))}). Cost: centred L2 "
            f"discrepancy d=4 rises from {series('sobol', 'cd_centred_l2', 4)} to "
            f"{series('corners_plus_sobol', 'cd_centred_l2', 4)} because 16 of N points sit on vertices. At d=6, N=64 the "
            f"generic 16-run fraction leaves {_g(mean_of(6, 64, 'corners_plus_sobol', 'planted_regions_missed'))} planted "
            f"regions missed ({', '.join(regions_missed_in_any(6, 'corners_plus_sobol', (64,)))}): name the physically "
            f"critical corners explicitly, or raise N."),
        "why_sobol_bulk": why_sobol_bulk,
        "head_to_head_same_vertex_block": h2h_table,
        "caveats": [
            f"The key metric is region-set dependent: {with_vertex[4]} of {totals[4]} planted regions at d=4 contain a "
            "cube vertex, which favours designs with vertices. The exhaustive low-order families (1-D slabs, 2-D boxes, "
            "2-D pair corners) are reported to show robustness beyond the fixed placements.",
            "5 seeds per stochastic method: min/max over seeds are in per_method_means; mean differences of a "
            "fraction of one region between methods are not meaningful.",
            "Covering radii are lower bounds from a finite reference set; in 6-D 20000 points resolve them coarsely.",
            DISCLAIMER,
        ],
    }
    vog_first_key = sum(1 for d, n in cells
                        if _ranks({m: mean_of(d, n, m, "planted_regions_missed")
                                   for m in (vogel_representative(d),) + others}, "lower")[1][vogel_representative(d)] == 1)
    holdout_always_missed = all(not g["hits"]["holdout_x3x4"] for d in (4, 6) for g in designs(d, "vogel_paired"))
    if vog_last_key > len(cells) // 2 and vog_all_corner_boxes_missed:
        status = "REJECTED as a general claim on this benchmark"
    elif vog_first_key > len(cells) // 2:
        status = "SUPPORTED on the key metric of this benchmark"
    else:
        status = "NOT SUPPORTED (mixed results)"
    verdict = (
        f"X-006 'Vogel sampling is inherently superior': {status}. The bounded Vogel representative ranks 5th of 5 "
        f"on planted regions missed in {vog_last_key}/9 cells and 1st in {vog_first_key}/9; it misses every planted "
        f"corner box in every design ({vog_all_corner_boxes_missed}) and the categorical-holdout proxy in every d>2 "
        f"design ({holdout_always_missed}), by construction. It wins narrowly on 2-D point separation and on "
        f"coverage of its own inscribed disk (d=2). Evidence grade: illustrative_simulation on synthetic geometry; "
        f"no physical meaning.")
    augmentation = [
        "Add all 4 vertices of every Vogel axis pair (the square corners are unreachable for any N), or for d>2 the "
        "full 2^d vertex block / a resolution-IV fraction plus the physically named corners.",
        f"Add face points for one-at-a-time limits on every axis: the disk holds {slab_ratio:.1f}x fewer points in a "
        f"0.02-thick boundary slab than a uniform layout.",
        "Enumerate categorical factors as separate levels; never map a categorical level to a continuous sub-box "
        "(holdout_x3x4 is unreachable for paired Vogel).",
        "Permute the sample order independently per axis pair (documented seed); never reuse the Phase 0 2-D index "
        "on several pairs (duplicated axes).",
        "Do not use Vogel coverage statistics as evidence of anything physical; Kuiper keys remain addresses only.",
    ]
    return {"verdict_x006": verdict, "vogel_wins": wins, "vogel_losses": losses,
            "golden_lattice_diagnostic": diagnostic, "other_methods": others_text,
            "augmentation_if_vogel_is_kept": augmentation, "recommended_composite_wave2_phaseD": composite}


def summarise(rows, csv_text, script_sha):
    groups = {}
    for row in rows:
        groups.setdefault((row["d"], row["budget_n"], row["method"]), []).append(row)

    def mean_of(d, n, method, metric):
        grp = groups[(d, n, method)]
        return sum(g[metric] for g in grp) / len(grp)

    means, seed_misses = {}, {}
    for (d, n, method), grp in groups.items():
        cell = f"d{d}_N{n}"
        stats = {"designs": len(grp), "variant": grp[0]["variant"]}
        for metric in NUMERIC_METRICS:
            vals = [g[metric] for g in grp]
            stats[metric] = {"mean": _r(sum(vals) / len(vals), 6), "min": _r(min(vals), 6), "max": _r(max(vals), 6)}
        means.setdefault(cell, {})[method] = stats
        seed_misses.setdefault(cell, {})[method] = {
            region: f"{sum(1 for g in grp if not g['hits'][region])}/{len(grp)}" for region in grp[0]["hits"]}

    # ---- plain-text rankings --------------------------------------------------------------------------------
    lines, rankings = [DISCLAIMER], {}
    lines.append(f"Ties: mean values equal to {RANK_SIG_FIGS} significant figures share a rank (competition "
                 "ranking). '*' marks vogel2d at d>2 = identity tiling, a degenerate control.")
    for scope_name, methods in (("specified_methods", BASE_METHODS), ("all_methods", ALL_METHODS)):
        rankings[scope_name] = {}
        lines.append("")
        if scope_name == "specified_methods":
            lines.append("=== RANKING of the six specified methods per metric and (d, N) cell (value = mean over "
                         "seeds) ===")
        else:
            lines.append("=== EXTENDED: mean rank over the 9 (d, N) cells, incl. diagnostic + composite candidates ===")
        for metric, better, primary, desc in RANKED_METRICS:
            per_cell, rank_sums = {}, {m: 0 for m in methods}
            for d in DIMS:
                for n in BUDGETS:
                    scores = {m: mean_of(d, n, m, metric) for m in methods}
                    ordered, ranks = _ranks(scores, better)
                    per_cell[f"d{d}_N{n}"] = [{"method": m, "rank": ranks[m], "value": _r(scores[m], 6)}
                                              for m in ordered]
                    for m in methods:
                        rank_sums[m] += ranks[m]
            n_cells = len(DIMS) * len(BUDGETS)
            mean_rank = {m: rank_sums[m] / n_cells for m in methods}
            overall = sorted(methods, key=lambda m: (mean_rank[m], m))
            entry = {"better": better, "primary_metric": primary, "description": desc,
                     "mean_rank_over_cells": [{"method": m, "mean_rank": _r(mean_rank[m], 4)} for m in overall]}
            if scope_name == "specified_methods":
                entry["per_cell"] = per_cell
                lines.append("")
                lines.append(f"[{metric}] {better} is better -- {desc}")
                for cell, entries in per_cell.items():
                    d_cell = int(cell.split("_")[0][1:])
                    parts = [f"{e['rank']}. {e['method']}{'*' if e['method'] == 'vogel2d' and d_cell > 2 else ''} "
                             f"{e['value']:.4g}" for e in entries]
                    lines.append(f"  {cell:9s} " + " | ".join(parts))
                lines.append("  mean rank: " + " | ".join(f"{m} {mean_rank[m]:.2f}" for m in overall))
            else:
                lines.append(f"[{metric}] " + " | ".join(f"{m} {mean_rank[m]:.2f}" for m in overall))
            rankings[scope_name][metric] = entry

    # ---- Vogel representative vs the four non-Vogel specified methods (rank out of 5) ------------------------
    others = ("sobol", "lhs", "random", "grid_corners")
    vogel_table, wins, losses = [], [], []
    for metric, better, _primary, _desc in RANKED_METRICS:
        for d in DIMS:
            rep = vogel_representative(d)
            for n in BUDGETS:
                scores = {m: mean_of(d, n, m, metric) for m in (rep,) + others}
                ordered, ranks = _ranks(scores, better)
                best_other = [m for m in ordered if m != rep][0]
                tied_with = sorted(m for m in others if ranks[m] == ranks[rep])
                entry = {"metric": metric, "better": better, "cell": f"d{d}_N{n}", "vogel_method": rep,
                         "rank_of_5": ranks[rep], "tied_with": tied_with, "vogel_value": _r(scores[rep], 6),
                         "best_other_method": best_other, "best_other_value": _r(scores[best_other], 6)}
                vogel_table.append(entry)
                tie = f" (tied with {', '.join(tied_with)})" if tied_with else ""
                text = (f"{metric} {entry['cell']}: {rep} rank {ranks[rep]}/5{tie}, {scores[rep]:.4g} vs best other "
                        f"{best_other} {scores[best_other]:.4g} ({better} is better)")
                if ranks[rep] == 1:
                    wins.append(text)
                elif ranks[rep] >= 4:
                    losses.append(text)

    always_missed_by_vogel = {}
    for d in DIMS:
        rep = vogel_representative(d)
        always_missed_by_vogel[f"d{d}:{rep}"] = [
            r for r in groups[(d, BUDGETS[0], rep)][0]["hits"]
            if all(not g["hits"][r] for n in BUDGETS for g in groups[(d, n, rep)])]
    missed_by_every_specified = {
        f"d{d}_N{n}": [r for r in groups[(d, n, "sobol")][0]["hits"]
                       if all(not g["hits"][r] for m in BASE_METHODS for g in groups[(d, n, m)])]
        for d in DIMS for n in BUDGETS}
    key_cols = ("planted_regions_missed", "cd_centred_l2", "min_pairwise_distance", "covering_radius_ref",
                "lowdim_slab_missed_frac", "lowdim_box2d_missed_frac", "lowdim_corner2d_missed_frac")
    composite_table = {
        f"d{d}_N{n}": {m: {k: _r(mean_of(d, n, m, k), 4) for k in key_cols}
                       for m in ("sobol", "lhs", vogel_representative(d), "golden_lattice_paired", "grid_corners")
                       + COMPOSITE_METHODS}
        for d in DIMS for n in BUDGETS}
    headline = {f"d{d}_N{n}": {"regions_total": groups[(d, n, "sobol")][0]["planted_regions_total"],
                               **{m: _r(mean_of(d, n, m, "planted_regions_missed"), 4) for m in ALL_METHODS}}
                for d in DIMS for n in BUDGETS}

    # ---- analytic geometry of the bounded Vogel disk (DERIVED, algebra; independent of N) --------------------
    s_star = 0.5 - 0.5 / math.sqrt(2)
    h_slab = 2 * SLAB_LO - 1
    seg_slab = 0.25 * (math.acos(h_slab) - h_slab * math.sqrt(1 - h_slab ** 2))
    h_band = 1 - 2 * EXTREME_BAND
    seg_band = 0.25 * (math.acos(h_band) - h_band * math.sqrt(1 - h_band ** 2))
    h_hold = 2 * HOLDOUT_LO - 1
    seg_hold = 0.25 * (math.acos(h_hold) - h_hold * math.sqrt(1 - h_hold ** 2))
    analytic = {
        "label": "DERIVED", "grade": "algebra",
        "note": "Properties of the inscribed-disk construction for ANY budget N; geometric volumes, not probabilities.",
        "disk_area_fraction_of_unit_square": _r(math.pi / 4),
        "volume_fraction_never_sampled_by_disk_based_vogel": {f"d{d}": _r(1 - (math.pi / 4) ** (d / 2)) for d in DIMS},
        "largest_vertex_box_side_entirely_outside_disk": _r(s_star),
        "corner_boxes_side_0p08_reachable": CORNER_BOX_SIDE > s_star,
        "corner_metric_boxes_side_0p05_reachable": CORNER_METRIC_SIDE > s_star,
        "corner6d_reachable": (1.0 - CORNER6D_LO) > s_star,
        "pair_corner_boxes_side_0p1_reachable_on_vogel_pairs": LOWDIM_CORNER_S > s_star,
        "pair_corner_missed_share_floor_vogel_paired": {f"d{d}": _r(1.0 / (d - 1)) for d in DIMS},
        "holdout_x3x4_nearest_point_distance_from_disk_centre_vs_radius_0p5": _r(math.sqrt(2) * (HOLDOUT_LO - 0.5)),
        "holdout_x3x4_reachable": math.sqrt(2) * (HOLDOUT_LO - 0.5) <= 0.5,
        "holdout_alignment_note": "x3, x4 form Vogel pair 2 under the consecutive pairing used here, so the holdout "
                                  "is a joint extreme of ONE disk (unreachable). If x3 and x4 sat in different pairs "
                                  "the box would be reachable but under-sampled by the factor below relative to a "
                                  "uniform layout (independent permutations)",
        "holdout_density_vs_uniform_if_axes_in_different_pairs": _r((seg_hold / (math.pi / 4) / (1 - HOLDOUT_LO)) ** 2, 4),
        "vertex_distance_floor_any_N": {f"d{d}": _r(math.sqrt(d / 2) * (math.sqrt(2) - 1) / 2) for d in DIMS},
        "slab_x1_share_of_disk_area": _r(seg_slab / (math.pi / 4)),
        "slab_x1_expected_vogel_points": {f"N{n}": _r(n * seg_slab / (math.pi / 4), 4) for n in BUDGETS},
        "slab_x1_points_uniform_layout": {f"N{n}": _r(n * (1 - SLAB_LO), 4) for n in BUDGETS},
        "axis_extreme_band_share_disk_marginal_vs_uniform_0p10": _r(2 * seg_band / (math.pi / 4)),
        "non_convergence": "the disk layout converges to the uniform law on the disk, not on the square, so its "
                           "centred discrepancy tends to a positive constant and its covering radius stays >= the "
                           "vertex distance floor for every N",
    }
    phase0 = phase0_screen_corner_gap()

    return {
        "benchmark_id": BENCHMARK_ID,
        "status": "ILLUSTRATIVE_NUMERICAL_EXPERIMENT_ON_SYNTHETIC_UNIT_CUBE_GEOMETRY_NO_PHYSICS",
        "disclaimer": DISCLAIMER,
        "contradiction_addressed": "X-006 'Vogel sampling is inherently superior'",
        "producer": {
            "script": "claude-study/experiments/sampling_benchmark.py", "script_sha256": script_sha,
            "python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__,
            "command": "python3 -B experiments/sampling_benchmark.py  (from claude-study/)"},
        "outputs": {"csv": "claude-study/experiments/sampling-benchmark-results.csv",
                    "csv_sha256": hashlib.sha256(csv_text.encode()).hexdigest(), "csv_rows": len(rows)},
        "labels": {
            "units": "all benchmark metrics are dimensionless (unit-cube coordinates, Euclidean distances in the unit "
                     "cube, counts and shares); only phase0_screen_corner_gap carries SI units (A, ohm, W)",
            "benchmark_metric_values": {"label": "DERIVED", "grade": "illustrative_simulation",
                                        "basis": "computed on synthetic point layouts; exact for the given designs"},
            "covering_radius_estimates": {"label": "DERIVED", "grade": "illustrative_simulation",
                                          "basis": f"max over {REF_POINTS} random reference points: a LOWER bound on "
                                                   "the true covering radius (sup over the cube); coarse in 6-D"},
            "planted_regions_and_benchmark_parameters": {"label": "ASSUMED",
                                                         "basis": "synthetic, fixed a priori by brief s4 / W06 task"},
            "analytic_geometry": {"label": "DERIVED", "grade": "algebra"},
            "probabilities": {"label": "UNKNOWN", "basis": "no physical probability is estimated or implied"},
        },
        "config": {
            "dims": list(DIMS), "budgets": list(BUDGETS), "seeds": list(SEEDS),
            "reference_set": {"points": REF_POINTS, "seed": f"numpy default_rng([{REF_SEED}, d])", "reduced": False,
                              "plus_lattice3_for_supplementary_metric": "{0, 0.5, 1}^d"},
            "corner_metric_side": CORNER_METRIC_SIDE,
            "lowdim_families": {"slab": f"thickness {LOWDIM_SLAB_T}, lower edge k/100 k=0..98, every axis",
                                "box2d": f"side {LOWDIM_BOX_S}, lower corner on k/20 k=0..18, every axis pair",
                                "corner2d": f"side {LOWDIM_CORNER_S}, 4 corners of every axis pair",
                                "rng": "none (exhaustive enumeration)"},
            "rank_tie_significant_figures": RANK_SIG_FIGS,
            "methods": METHOD_DESCRIPTIONS,
            "variants_per_cell": {f"d{d}_N{n}": {m: variant_note(m, n, d) for m in ALL_METHODS}
                                  for d in DIMS for n in BUDGETS},
            "axis_pairs_for_vogel": "(x1,x2), (x3,x4), (x5,x6)",
            "planted_regions": {f"d{d}": region_definitions(d) for d in DIMS},
            "hit_rule": "a region is hit if any design point lies inside it",
        },
        "headline_planted_regions_missed_mean_over_seeds": headline,
        "conclusion": build_conclusion(groups, mean_of, phase0),
        "analytic_vogel_geometry": analytic,
        "phase0_screen_corner_gap": phase0,
        "ranking_text": lines,
        "findings": {
            "regions_missed_by_vogel_in_every_design": always_missed_by_vogel,
            "regions_missed_by_every_specified_method_every_seed": missed_by_every_specified,
            "vogel_rank1_of_5": wins,
            "vogel_rank4or5_of_5": losses,
            "vogel_vs_four_non_vogel_specified_methods": vogel_table,
            "composite_candidates_vs_pure_methods_means": composite_table,
        },
        "planted_region_misses_by_seed": seed_misses,
        "rankings": rankings,
        "per_method_means": means,
        "not_modelled": NOT_MODELLED,
    }


def script_sha256():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def run_benchmark():
    rows = run_designs()
    csv_text = rows_to_csv(rows)
    summary = summarise(rows, csv_text, script_sha256())
    summary_text = json.dumps(summary, indent=1) + "\n"
    return rows, csv_text, summary, summary_text


def main(argv):
    _rows, csv_text, summary, summary_text = run_benchmark()
    if "--check" in argv:
        ok_csv = CSV_PATH.exists() and CSV_PATH.read_text() == csv_text
        ok_sum = SUMMARY_PATH.exists() and SUMMARY_PATH.read_text() == summary_text
        print("csv", "MATCHES" if ok_csv else "MISMATCH", summary["outputs"]["csv_sha256"])
        print("summary", "MATCHES" if ok_sum else "MISMATCH")
        return 0 if (ok_csv and ok_sum) else 1
    with open(CSV_PATH, "w", newline="") as fh:
        fh.write(csv_text)
    with open(SUMMARY_PATH, "w", newline="") as fh:
        fh.write(summary_text)
    print("\n".join(summary["ranking_text"]))
    conc = summary["conclusion"]
    print("\n=== CONCLUSION (numbers interpolated from the results) ===")
    print("\n" + conc["verdict_x006"])
    for key in ("vogel_wins", "vogel_losses", "other_methods", "augmentation_if_vogel_is_kept"):
        print(f"\n[{key}]")
        for s in conc[key]:
            print(" - " + s)
    print("\n[golden_lattice_diagnostic]\n - " + conc["golden_lattice_diagnostic"])
    rec = conc["recommended_composite_wave2_phaseD"]
    print("\n[recommended_composite_wave2_phaseD]")
    for s in rec["design"]:
        print(" " + s)
    print(" WHY EXPLICIT VERTICES: " + rec["why_explicit_vertices"])
    print(" WHY SOBOL BULK: " + rec["why_sobol_bulk"])
    print(f"\nwrote {CSV_PATH.name} ({summary['outputs']['csv_rows']} rows, sha256 "
          f"{summary['outputs']['csv_sha256']}) and {SUMMARY_PATH.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
