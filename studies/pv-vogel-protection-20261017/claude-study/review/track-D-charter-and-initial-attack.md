# Track D charter and initial attack — Kuiper computational research (SUP-D)

Date 2026-10-17 · cycle 1 · author SUP-D (Claude, model `fable`; persistent across barriers B1–B3).
Status: supervisory review and binding criteria for W06 (sampling benchmark) and W08 (SI/energy bookkeeping,
reproducibility). Nothing here is a physical result; grades are `algebra` or `illustrative_simulation` only.
Inputs: master brief §3 track D and §4; WORKER_PROTOCOL.md; fixture `V11_CYCLE1_SHARED_FIXTURE_v1`
(sha256 2027dd71…fea6a3); Kuiper lib.mjs @ da7d8f6e (sha256 b96c855d…06b0d); Phase 0 vogel_study.py (sha256 655a54d9…cd21a).

## 1. Verification of the address law, the frozen keys and the ledger

RAN (all from `claude-study/` unless stated; nothing in the Kuiper tree was modified):
- `python3 tools/ledger.py --check` → `ledger MATCHES 218b25d9293526fbe38d4430e2db556d5a833bf6b0f44c38a46a288d6bfec6b3`, exit 0.
- `node place_node.mjs` (scratch, sha256 90af56bd…6e9b) imports the ACTUAL `lib.mjs` and evaluates `place(key)` for
  keys 1..2959 plus 8285, 100000, 100001, 342795, 1e6, 1e7, 2^31−1 (2966 rows, full-precision doubles).
- `python3 -I verify_address_law.py` (scratch, sha256 f7bd0380…5ea5ed) compares `ledger.kuiper_xy(key)` and
  Phase 0 `vogel_study.kuiper_xy(key)` with those doubles → `ALL ASSERTIONS PASSED`.
- `node proof/wafer.check.mjs` in the read-only Kuiper folder → `wafer proof PASS — 30 checks` (reads `../202609142202/data/`).
- `python3 -m unittest test_vogel_study.py` in Phase 0 → 11 tests OK.

Findings (label DERIVED, grade algebra unless stated):
1. Constant: `GOLDEN = pi*(3-sqrt(5)) = 2.399963229728653 rad` is bit-identical in lib.mjs (V8), tools/ledger.py and
   vogel_study.py. `SPACING = 1.0` in lib.mjs is implicit (=1) in both Python copies.
2. `place(key)` vs `kuiper_xy(key)`: 2819 of 2966 rows bit-identical; 147 rows differ by at most 2 ulp
   (max relative difference 3.3e-16, dimensionless) because V8 and glibc `sin/cos` are different libm implementations
   (neither guarantees correct rounding). After the ledger's stored rounding `round(x, 8)` the two agree on ALL 2966 rows.
   |(x,y)| = sqrt(key) holds within 4 ulp for every row. Verdict: the law is reproduced exactly at the level the ledger
   stores; the IDENTITY of a scenario is the integer key, never the float pair (float pairs are derived, not primary).
3. Phase 0 keys 1..2560: `vogel_study.one_case` still yields keys 1..2560 in the frozen tuple order FAULTS×LEVELS×64,
   `vogel_study.kuiper_xy(k) == ledger.kuiper_xy(k)` for every k ≤ 2560, and no Phase 0 key appears in the new family.
4. Family `cycle1-physical-v1`: keys contiguous 2561..2959, 399 entries, 399 unique `scenario_id`s, every stored
   `kuiper_xy == [round(place(key),8)]`, `phase0_frozen_keys == [1, 2560]`; `ledger.build()` regenerates
   `entries_sha256` byte-identically (deterministic enumeration).
5. Distinct keys land in distinct places: minimum pairwise distance over all pairs for keys 1..2959 is 1.60195
   (dimensionless address units; full pdist, not a window); r_max = sqrt(2959) = 54.397.
6. Two gaps for W08 (not failures of the law): (a) `tools/ledger.py` docstring cites `test_ledger.py`, which does not exist
   in `tools/`; (b) `--check` proves EXACT reproduction, not append-only-ness: a future family appended by the orchestrator
   would also "MISMATCH". Append-only must be a separate test: the previous ledger's entries are a strict PREFIX of the
   new one and no key below `last_key` changed. (c) lib.mjs refuses keys above 2^53−1 (`parseKey`); `ledger.kuiper_xy`
   accepts any Python int, but `math.sqrt` is exact only below 2^53. Add the same bound.

What the address law IS and IS NOT. The law `r = sqrt(k); theta = k*GOLDEN; x = r cos theta; y = r sin theta` is a
pure, stateless, injective map from a permanent integer key to a point; it exists so that "a number is a place" on every
device, for ever, with nothing stored. The Kuiper README's own "What is not claimed" states it: "That the arrangement
means anything physically. It is an address scheme chosen so that a number is a place." The README also warns that a
shared number is "not a dependency, a call, or a reuse worth acting on". In this study, therefore: a key names ONE
versioned scenario (case, protection candidate, variants, model revision, evidence links); the radius sqrt(k) is issue
order, not severity; angular neighbours are not similar cases; density of points on the wafer is not probability, not
frequency, not risk; the picture carries no voltage, current, energy or likelihood. Any sentence of the form "the Kuiper
map shows that …" about physics is out of bounds for every track.

## 2. Separation discipline (brief §4) — binding for every worker

| Layer | Owns | Legitimate outputs | FORBIDDEN inference out of this layer |
|---|---|---|---|
| L1 geometry / indexing | Kuiper keys, ledger, bounded Vogel 2-D construction | identity, provenance, stable addresses | key order or wafer position → similarity, severity, probability, causality (FORBIDDEN) |
| L2 search / sampling | Vogel/Sobol/LHS/random/grid designs, corners, categorical combos | which input points were EVALUATED; coverage metrics of the input box | "pass fraction of sampled points → failure probability" (FORBIDDEN); "no counterexample found → safe" (FORBIDDEN); coverage of the design → coverage of physics (FORBIDDEN) |
| L3 physical simulation | ngspice/SciPy models M0–M6 at the evaluated points | E_fault [J], Vds [V], Tj [°C] bands with model revision, step-halving and sha256 | a simulated E_fault → field-observed E_fault without `validated_against_trace` (FORBIDDEN); uncalibrated arc law → extinction claim (FORBIDDEN unless "illustrative") |
| L4 inferred failure frequencies | documented stochastic model, empirical priors, calibration data | rates WITH intervals, or `UNKNOWN` | any rate derived from L2 fractions or L3 counts (FORBIDDEN); a percentage without a named empirical distribution (FORBIDDEN) |
| L5 safety validation | lab traces, standards matrix, Track E block | "validated within tested set T", exclusions listed | L3/L4 → "safe", "certified", "replaces AFCI/SPD/IMD" (FORBIDDEN); extrapolation beyond T (FORBIDDEN) |

Enforcement: every result file carries `layer: L1..L5`; a number that crosses a layer boundary must cite the file that
earned it in the lower layer. Track E may block any file whose text performs a forbidden arrow.

## 3. Benchmark protocol required from W06 (equal model-evaluation budgets)

Designs, all in the unit cube [0,1]^d then affine-mapped to fixture ranges (document the map per axis):
- V0 bounded Vogel, Phase 0 construction: `r = sqrt((n-0.5)/N); theta = n*GOLDEN; u = 0.5+0.5 r cos theta; v = 0.5+0.5 r sin theta`.
- V1 scrambled Vogel pairings for d = 4 and d = 6: each 2-D pair is V0 with an INDEPENDENT seeded permutation of n;
  record the pairing (axis_i, axis_j) and the permutation seed.
- S scipy.stats.qmc.Sobol(d, scramble=True, seed) ; L scipy.stats.qmc.LatinHypercube(d, seed) ;
  R numpy.random.default_rng(seed).random((N,d)) ; G full factorial m^d ≤ N − 2^d plus the 2^d explicit corners.
Budgets: N ∈ {64, 256, 1024} model evaluations, identical for every design; seeds {20261017, 20261018, 20261019} for
every seeded design (3 replicates; report mean and min/max, never a single seed).
Metrics (per design, per N, per seed): `qmc.discrepancy(X, method="CD")` and `"L2-star"` (dimensionless);
minimum pairwise Euclidean distance and covering radius (largest empty-ball radius, estimate on a 10^5-point
reference grid, dimensionless); corner coverage = fraction of the 2^d boxes [0,δ]/[1−δ,1] per axis, δ = 0.1,
containing ≥ 1 point; and the number of planted synthetic counterexample regions with ZERO points. Planted regions
(≥ 5 shapes, each with its analytic volume and expected uniform hit count N·vol written beside it):
R1 corner box [0.9,1]^2 on one pair (vol 0.01); R2 thin slab u1 ≤ 0.02 (vol 0.02); R3 interior ball centre (0.37,0.61)
radius 0.06 (vol 0.0113); R4 diagonal ridge |u1−u2| ≤ 0.02 (vol 0.0396); R5 categorical holdout: 4 levels per axis,
cell (level 3, level 0, level 3, level 0) (vol 4^−d); R6 cross-pair corner u1 ≥ 0.95 ∧ u3 ≥ 0.95 (vol 0.0025, d ≥ 4).
A region whose volume is zero or whose expected hit count N·vol is < 0.2 for every N is a protocol error, not a finding
(SUP-D made exactly this error in the pilot below and corrected it).
Deliverable: `experiments/sampling-benchmark.csv` with columns design, d, N, seed, pairing, CD, L2star, min_dist,
cover_radius, corner_cov, misses, missed_ids, script_sha256; plus `test_sampling_benchmark.py` (unit tests on the
region volumes, the V0 formula against Phase 0 `vogel_disk`, and determinism under a fixed seed).
Required plain statement in the CSV header and in W06's report: "No method is declared superior without these numbers;
superiority is metric-specific and budget-specific." Closing X-006 requires this file.

SUP-D pilot (scratch `pilot_bench.py`, sha256 4de6a918…b062, seed 20261017, one replicate, grade algebra; NOT W06's
deliverable, shown only to set expectations). Values dimensionless.

| d | N | design | CD disc | min dist | corner cov | regions missed |
|---|---|---|---|---|---|---|
| 2 | 64 | V0 Vogel | 0.00453 | 0.0966 | 0.00 | R1, R2 (2 of 4 valid) |
| 2 | 64 | Sobol | 0.00016 | 0.0324 | 1.00 | R3 (1 of 4) |
| 2 | 64 | LHS | 0.00030 | 0.0267 | 0.50 | R1 (1 of 4) |
| 2 | 64 | random | 0.00755 | 0.0104 | 0.50 | R3 (1 of 4) |
| 2 | 64 | grid+corners | 0.00403 | 0.1010 | 1.00 | none (0 of 4) |
| 2 | 1024 | V0 Vogel | 0.00410 | 0.0242 | 0.00 | R1 (1 of 4) |
| 2 | 1024 | Sobol | 0.00000 | 0.0086 | 1.00 | none |
| 4 | 64 | V1 scrambled pairs | 0.01231 | 0.1543 | 0.00 | R1, R2, R5, R6 (4 of 6) |
| 4 | 64 | Sobol | 0.00109 | 0.1046 | 0.00 | R5, R6 (2 of 6) |
| 4 | 64 | grid+corners | 0.15616 | 0.5000 | 1.00 | R3 (1 of 6) |
| 4 | 1024 | V1 scrambled pairs | 0.01015 | 0.0379 | 0.00 | R1, R5 (2 of 6) |
| 4 | 1024 | Sobol | 0.00001 | 0.0615 | 0.06 | none |
| 4 | 1024 | LHS | 0.00024 | 0.0320 | 0.19 | none |
| 4 | 1024 | grid+corners | 0.01587 | 0.2000 | 1.00 | R3 (1 of 6) |

Pilot corrections and readings: in the 2-D run R5 was mis-specified as an empty set (impossible conjunction), so the
2-D counts above are "of 4 valid regions"; the corrected categorical count (4 levels/axis, cell (3,0)) at d = 2,
N = 1024 is Vogel 24, Sobol 64, LHS 60, random 72 against expected uniform 64 — the disk under-samples a corner
category by ×2.7. Analytic, independent of N: the bounded Vogel disk has radius 0.5 about (0.5,0.5); the nearest point
of R1 = [0.9,1]^2 to the centre is (0.9,0.9) at distance 0.5657 > 0.5, so R1 is unreachable at ANY N; the disk covers
π/4 = 78.54 % of the square, and a product of disks covers 61.69 % (d = 4) and 48.45 % (d = 6) of the cube. Vogel's
genuine strength is 2-D point spread (largest min-distance of the non-grid designs at every N in 2-D, and in 4-D only at
N = 64: at N = 256 and 1024 scrambled Sobol has the larger min-distance, 0.078 vs 0.076 and 0.062 vs 0.038, because the
independent pairing destroys the spread across pairs); its CD discrepancy does not fall with N (0.0045 → 0.0041 in 2-D)
because the unsampled corners are a systematic bias, not noise. Grid+corners wins corners
and loses interior resolution (R3 missed at all N in 4-D with m ≤ 5 levels/axis). So "better" is metric-specific —
which is the point of requiring the full table from W06 before any sentence about Vogel's merit.

## 4. Reproducibility requirements for wave 2 (ngspice 42 batch)

R1 Netlists committed as text under `models/` or `results/<scenario_id>/`, named by `scenario_id` and
`model_revision`; every `.param` traceable to a fixture key; `.options` line (reltol, abstol, vntol, method, itl4,
gmin) and `.tran tstep tstop tstart tmax` recorded in the result JSON, not only in the netlist.
R2 Time-step halving: run with tmax = h and h/2; report `E_fault_h`, `E_fault_h2` [J] and
`rel_change = (E_h2 − E_h)/E_h`. Accept the h result only if |rel_change| ≤ 1 % for E_fault and ≤ 2 % for peak Vds;
otherwise halve again. Record the final h in the result file.
R3 Exports via `.control … wrdata …`, parsed by Python; committed waveform CSV decimated (state the factor and the
anti-alias rule, e.g. keep every k-th row AND every row within ±20 µs of a switching/ignition/extinction event);
sha256 of the decimated CSV AND of the full `.dat` (which is not committed; > 1 MB). Pilot scale: a 5 s horizon at
h = 1 µs is 5.0e6 rows; C3's 3600 s at 1 ms is 3.6e6 rows — decimation or event windows are mandatory.
R4 Independent integral: `E_fault = scipy.integrate.trapezoid(v_fault*i_fault, t)` on the exported (un-decimated)
arrays, computed outside ngspice, compared with ngspice's own `integ()` or energy variable. Accepted tolerance
≤ 2 % relative on E_fault for the SAME netlist and revision (≤ 0.1 % for linear closed-form regression cases).
Why this is a model-consistency check and NOT a validation: both numbers integrate the same solver trajectory; agreement
proves the export, the sign convention, the decimation and the integrator are consistent with the solver — it cannot
detect a wrong arc law, a wrong topology or a wrong capacitor value, because those errors are in the trajectory itself.
Validation is Layer L5 (trace from a laboratory) and is not available in cycle 1.
R5 Sign convention test: every current used in an energy integral is asserted against a closed-form case
(0.5·C·V0² discharge) in `test_*.py`; the pilot below produced E = −98.14 J on the first run from the SPICE source-
current convention (`i(Vsense)` positive from + to − THROUGH the source) and +98.14 J after correction — a silent sign
error would flip "energy delivered to the fault" into "energy absorbed from it".
R6 One-command, deterministic: `python3 run_<scenario>.py` from `claude-study/` with no wall-clock values in results;
`ngspice -v` first line and the script sha256 written into the result JSON.
Pilot of R2/R4/R5 (scratch `spice_pilot/run_pilot.py`, sha256 9c7138f7…5ffa3; grade illustrative_simulation; NOT a
fault model): C_in = 150 µF (fixture `mppt_input_capacitance_f`, ASSUMED) pre-charged to 1143.9 V (fixture
`vmpp_string_v`, DERIVED) discharging through L = 0.6674 mH (0.713 µH/m × 936 m, fixture DERIVED) into R = 2 Ω
(fixture constant-R arc cross-check, ASSUMED); ζ = 0.474. Closed form E = 0.5·C·V0² = 98.1380 J. ngspice + SciPy
trapezoid: h = 1 µs → 98.1390 J (+9.8e-6 rel); h = 0.5 µs → 98.1383 J (+2.5e-6 rel); halving change −7.3e-6.
Decimated (×10) exports: 152 kB sha256 b00c40b5…f82f99 and 304 kB sha256 3a90a475…98173b; full `.dat` 1.30 MB / 2.60 MB
(not to be committed). The mechanism works; the 2 % tolerance is reserved for the nonlinear arc/diode cases where
event detection interacts with the step.

## 5. Error-budget framework (wave 2 must report E_fault as a band, never a single number)

Dominant uncertainties, with the fixture variant ranges that DEFINE the band (all ASSUMED unless noted; grade algebra):
- Arc V-I law: fixture Stokes–Oppenlander form `V_arc = (20 + 0.534·gap_mm)·I^0.12`, UNCALIBRATED. At I = 17.31 A and
  gap 1/3/5 mm: V_arc = 28.9/30.4/31.9 V, P = 500/527/553 W, E over the 5 s C1 horizon = 2.50/2.63/2.76 kJ.
  Constant-R cross-check 1/2/5 Ω at 17.31 A: 1.50/3.00/7.49 kJ. Spread between fixture-permitted laws: ×5.0.
  Calibration uncertainty beyond that: UNKNOWN until Track E supplies published traces; the ±? stays ± UNKNOWN.
- Minimum sustaining current 0.5 A and ignition voltage 15 V (ASSUMED): they decide WHETHER the arc extinguishes under
  P1b/P2; any extinction sentence must carry "illustrative" and both values.
- Single-diode fit: residuals of models/pv_module.py on (Voc, Isc, Vmpp, Impp) must be reported; SUP-D accepts ≤ 0.5 %
  per point for use, and the datasheet I-V curve stays `ASSUMED_until_datasheet_IV_curve_obtained`. Low-irradiance
  current: 200 W/m² gives Impp ≈ 3.46 A if linear in G (ASSUMED) — the C1 arc power then drops to ≈ 90 W.
- Cable L′/C′: pair separation 6.4 mm vs 1.0 m (both in fixture): L′ext = 0.613 vs 2.634 µH/m (×4.3), C′ = 36.3 vs
  8.45 pF/m, Z0 = 130 vs 558 Ω, L_loop(936 m) = 0.667 vs 2.559 mH. Stored 0.5·L·I² at 18.4 A = 0.113 vs 0.433 J
  (small against capacitor energies) but unclamped L·di/dt at 1 µs interruption of 17.31 A = 11.5 vs 44.3 kV — the
  geometry uncertainty lands on Track B's clamp, not on E_fault.
- C_in range 50–500 µF: 0.5·C·V² = 32.7–327 J at 1143.9 V and 55–553 J at 1487.79 V (×10). DC-link 1–4 mF:
  654–2617 J at 1143.9 V, feeding the fault ONLY in V_DIRECTBUS (adversarial variant).
- Irradiance/temperature: Voc_string 1487.79 V (−10 °C) to 1224.3 V (+70 °C), ±10 %; current ∝ G (ASSUMED).
- Numerical: step-halving ≤ 1 %, integral consistency ≤ 2 % (§4) — an order of magnitude below the physical spread.
Reporting rule: `E_fault_j: {min, nominal, max, variants: [...], dominant_term, grade}` per source (PV, paired string,
C_in, DC-link, line) per scenario_id; the band is the envelope over the fixture variants actually run, and the file
states which variants were NOT run. A reviewer who sees a bare number rejects the file.

## 6. Acceptance checklist (W06, W08, wave-2 reproducibility)

1. `python3 tools/ledger.py --check` passes and a new `tools/test_ledger.py` proves prefix-append-only (old entries a
   strict prefix of new; keys ≤ last_key unchanged) and rejects keys > 2^53−1, bool, float.
2. `vogel_study.kuiper_xy(k) == tools.ledger.kuiper_xy(k)` for k = 1..2560 asserted in a test; no file re-derives GOLDEN
   from a decimal literal.
3. Every scenario result file carries `scenario_id`, `key`, `model_revision`, `layer`, `grade`, `label`, script sha256.
4. W06 CSV per §3 with 3 seeds × 3 budgets × ≥ 6 designs × d ∈ {2,4,6}; region volumes unit-tested; expected uniform
   hit counts printed beside misses; the "no method superior without numbers" sentence present verbatim.
5. W06 states, with its numbers, which regions the bounded Vogel disk cannot reach at any N, and the explicit
   corner/boundary/categorical set that is appended deterministically to EVERY campaign regardless of design.
6. W08 bookkeeping library: SI-typed quantities with the fixture suffix naming; a dimension check that rejects
   `J + W`; energy balance `E_sources = E_fault + E_semiconductor + E_L + E_C + E_clamp + E_conduction` with the residual
   reported in J and as a fraction (accept ≤ 2 %); the closed-form 0.5·C·V0² case (§4 pilot values) as a regression.
7. Sign convention of every exported current asserted against that closed-form case (R5).
8. Step-halving results (h, h/2, rel_change) present for every wave-2 scenario; |rel_change| ≤ 1 % on E_fault.
9. Independent SciPy trapezoid vs ngspice energy ≤ 2 % (≤ 0.1 % for linear cases), labelled "model-consistency, not
   validation".
10. Netlist, `.options`, `.tran`, `ngspice -v` line, decimation rule, sha256 of decimated CSV and of the uncommitted
    full export all present; no committed file > 1 MB.
11. E_fault reported as a band per source with the variants run and NOT run (§5); any bare single number is rejected.
12. No file contains a probability, rate or percentage derived from a sample fraction or a simulated count; the word
    `UNKNOWN` is used where no empirical distribution exists.
13. No result says "validated" without a trace file path and sha256 from a laboratory source; the uncalibrated arc
    law is always accompanied by "illustrative".
14. Determinism: two consecutive runs of each script produce identical sha256 for every committed result.

## 7. Objections to other tracks

OBJ-D1 (Tracks A, C, E): "Vogel coverage" is a property of a 2-D disk of radius 0.5 inside the unit square. It covers
78.54 % of the square and NONE of the four corner boxes [0.9,1]^2 at any budget (distance 0.5657 > 0.5, algebra, §3);
in d = 6 the paired product covers 48.45 % of the cube. A campaign that says "Vogel covered the input space" has not
covered cold-Voc × max-irradiance × longest-route × smallest-C_in style corners; those are the cases Track A and C are
arguing about. Corners, boundaries and categorical combinations must be appended explicitly (brief §4) and counted as
separate evaluations, and I will block any coverage sentence that is not backed by W06's CSV.
OBJ-D2 (Tracks C and E, and any engineer): calling a pass fraction of sampled points a probability is a Layer L2→L4
forbidden arrow. Phase 0's "passed_nominal_loss_screen_count" is identical for all ten fault labels because no physics
was evaluated; wave-2 counts of "scenarios contained" are counts over a designed, non-random, non-representative point
set and carry no frequency. The permitted statement is "k of N designed scenarios, listed by scenario_id, met criterion
X under model revision Y"; anything with the words probability, rate, likelihood, risk reduction or % safer is to be
blocked by Track E and will be flagged by SUP-D at B2.
OBJ-D3 (Track B): "sub-microsecond off-time" has no computable benefit for E_fault until the time budget is written in
the same units. One-way wave delay on the 936 m route is 4.415 µs (fixture, DERIVED); at the fixture arc law a 17.31 A
arc dissipates ≈ 0.5 mJ per µs (500 W × 1 µs), while C_in alone holds 33–327 J (ratio 6.6e4 to 6.5e5).
Track B must report the energy that its off-time actually denies the fault, per source, against the detection latency
Track C quotes, with the loop inductance variant (0.667 vs 2.559 mH) and its unclamped L·di/dt (11.5 vs 44.3 kV at
1 µs) — otherwise switching speed is being ranked on a number that does not appear in the figure of merit.
OBJ-D4 (Track A): the single-diode fit and the module internal layout are ASSUMED (fixture); until
models/pv_module.py publishes residuals, every string current in a wave-2 netlist is an unlabelled number. Track A must
pass the fit residuals and the irradiance→current assumption (linear, ASSUMED) into each netlist header, or the E_fault
band in §5 cannot be formed.
OBJ-D5 (Track E): a time-step and integral agreement is not a validation; I will object to any evidence-grade promotion
from `illustrative_simulation` to `validated_against_trace` that cites §4 agreements as its evidence.

## 8. Open items for SUP-D at barrier B1
- Receive W06 CSV and W08 library; run the checklist; append X-006 evidence or keep it OPEN.
- Propose to orchestrator (exact diff in report): copy the four scratch pilot scripts into `claude-study/review/supd-pilot/`
  with their sha256 so the numbers in §3–§4 have an in-tree reproducible identifier.
- Request the orchestrator to add the three ledger gaps (§1 item 6) to W08's queue.
