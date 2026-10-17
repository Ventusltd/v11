# Orchestrator evidence board — cycle 1 (2026-10-17)

**Repository:** Ventusltd/v11 · **Branch:** `analysis/pv-vogel-protection-20261017-cycle1` (descendant of
`analysis/pv-vogel-protection-20261017` @ `4aacee6e78e7602896619aca178533258fe5fc36`, PR #6 head; PR #6 is stacked
on PR #5 `analysis/pv-arc-four-track-20261017` @ `4fb2ce59`; `main` @ `debb30e0` untouched).
**Kuiper source:** Ventusltd/globalgrid2050 @ `da7d8f6e6a7806ad5039701f5c86637d84be0704` (read-only clone;
lib.mjs sha256 `b96c855de1f5477e0bbd46ff3a2aed6811ba074ba5da76975984fef505c06b0d`).
**Frozen laboratory:** Ventusltd/solar-electrical-topology-analysis-engine-text-based @ `d3b4c497` — NOT cloned, NOT read, NOT modified.

## Phase 0 reproduction (step 1 of §12)
- `python3 -m unittest -v test_vogel_study.py` → 11 tests OK (Python 3.13.16).
- `python3 vogel_study.py` → 2560 cases, status ILLUSTRATIVE_SCREENING_ONLY_NOT_A_PROTECTION_VALIDATION;
  summary sha256 `3d984774531834eac5bcf1aa77ae2739e6133da538c1fbde7715e14214aabaac`.
- Architectures: 720/360/192/24 units; R budgets at 0.5 % STC: 11.013/22.027/41.3/330.4 mΩ; 936 m one-way 4.415 µs.

## Tool and agent availability (observed, not assumed)
- Agent tool model families available in this session: `fable`, `opus`, `sonnet`, `haiku` (all Claude).
- **Astra, Codex, GPT, Gemini or any non-Claude model family: NOT available. None were invoked. None will be reported.**
- Workspace: Linux, 2 vCPU, 7 GB RAM; Python 3.13.16, numpy 2.5.3, scipy 1.18.1, networkx 3.6.1, pandas 3.0.5,
  matplotlib 3.11.2; ngspice 42 (apt, KLU) installed and smoke-tested; PySpice 1.5 installed (declares ngspice 42
  unsupported — batch ngspice used instead). No PSCAD, LTspice, PLECS, Simscape. No licensed IEC/BS library.
- GitHub: REST API via `gh api` works for Ventusltd/v11 (push scope); GraphQL blocked; globalgrid2050 read-only.

## Swarm plan (real invocations only; receipts appended below as agents return)
Supervisors (model `fable`, persistent across barriers): SUP-A power systems, SUP-B power electronics,
SUP-C detection/controls, SUP-D Kuiper computation, SUP-E independent verification (may BLOCK).
Workers (model `opus`), waves aligned to barriers:
- Wave 1 (topology + model foundations): W01–W08.
- Barrier B1 (after topology models).
- Wave 2 (three fault waveforms × candidates, independent integrals, adversarial): W09–W16.
- Barrier B2 (after first three fault waveforms / architecture comparison).
- Wave 3 (independent verification, decision, reproducibility): W17–W20.
- Barrier B3 (before acceptance report).

## Receipts
(appended by orchestrator as each agent returns: agent id, model, task, files, tests run, result)

### R-01 SUP-D (model `fable`, Track D supervisor) — completed 2026-10-17 ~20:19 BST
- Files: review/track-D-charter-and-initial-attack.md (239 lines); review/supd-pilot/ (place_node.mjs, verify_address_law.py, pilot_bench.py, spice_pilot/run_pilot.py, README.md — placed in-tree by orchestrator, paths made relative).
- Ran: tools/ledger.py --check MATCHES 218b25d9; lib.mjs place(key) vs ledger kuiper_xy keys 1..2959 — 2819/2966 bit-identical, 147 differ ≤2 ulp, 0 differ after round(·,8); Kuiper proof/wafer.check.mjs 30 checks PASS (read-only); Phase 0 11/11; ngspice RLC pilot 98.1390 J vs analytic 98.1380 J (h=1 µs), halving change −7.3e-6.
- Findings carried: bounded Vogel disk covers 78.54 % of the unit square (61.69 % d=4, 48.45 % d=6); corner box [0.9,1]² unreachable at any N; arc-law envelope 1.50–7.49 kJ over 5 s at 17.31 A (×5 spread); C_in energy 32.7–327 J; L_loop 0.667 mH (6.4 mm) vs 2.559 mH (1.0 m separation).
- Objections OBJ-D1..D5 logged (→ contradictions X-009..X-011 at barrier B1). Blockers: proofs/test_ledger.py missing (W08 queue); kuiper_xy lacks 2^53−1 bound (orchestrator to add); arc calibration UNKNOWN.
- Tokens 172,696; tool uses 42; duration 912 s.

### R-02 SUP-C (model `fable`, Track C supervisor) — completed 2026-10-17 ~20:30 BST
- Files: review/track-C-charter-and-initial-attack.md (294 lines); review/supc-calcs/track_c_calcs.py (placed in-tree by orchestrator, fixture path made relative; runs with `python3 -I`).
- Ran: track_c_calcs.py (deterministic, fixture-only). No ngspice (review role).
- Findings carried (algebra grade): C1 as fixtured (arc INSIDE the healthy SS2 bypass loop) is capped at V_gap ≤ Voc_ss + Vf ≈ 15.7 V STC / 17.0 V at −10 °C → cannot sustain under the fixture Stokes–Oppenlander law (≥ 18.9 V at 0.5 A); if a low-voltage Cu/Ag arc (12–13 V, ASSUMED) sustains it is ≤ ~220–290 W and its string-level DC signature (−13 V) is identical to a shaded substring; HF leakage into the string loop ≈ −100 dB at 100 kHz → NOT detectable at string level. → new contradiction X-009 and a new priority variant "C1loop" (series arc in the string loop outside any bypass loop) to be appended to the ledger at B1.
- C2-far: both strings at Isc 18.4 A into the arc; S20 inverter-end current reverses +17.31 → −18.4 A (35.7 A swing) — unambiguous sub-ms observable at the inverter end; C_in delivers ~5.5 J to the arc (79 J dissipated in the 6.3 Ω home-run); with SW-STR-INV open S20's own modules still feed ≈ 536 W → ≈ 2.7 kJ over 5 s (confirms X-002 direction).
- C3: detectability ratio vs 40 K cable drift = 0.05/0.20/1.0 for 0.05/0.2/1.0 Ω → 0.05 Ω not credible electrically; 0.2 Ω not credible without cable-temperature compensation and two-ended string voltage; thermal sensor at the connector required (X-008 verdict). 1.0 Ω is not a steady state (ΔT_ss 1199 K).
- First SW-M-OUT to open under C2-far sees 30·Voc − V_arc = 1332 V STC / 1448 V at −10 °C (input to X-001). Loop commutation floor L·I/V_clamp = 23–115 µs ≫ 4.4 µs wave delay (X-003).
- Fixture flag: 936 m × 6 mm² home-run dissipates 1.9 kW ≈ 9.6 % of string Pmpp — cable sizing of the illustrative fixture is itself questionable (→ X-010).
- Objections O-1..O-5 logged. Tokens 156,764; tool uses 23; duration 1598 s.

### R-03 SUP-E (model `fable`, Track E supervisor, BLOCK authority) — completed 2026-10-17 ~20:55 BST
- Files: review/track-E-charter-and-initial-attack.md (206 lines); review/track_e_screen.py (deterministic algebra, fixture-only, self-checks OK).
- Ran: `python3 -I review/track_e_screen.py` PASS. WebFetch: IEC 27362 and 110893 public abstracts, Sandia SAND2012-4443C, NREL ESW2019-13, MDPI reference; IOP S–O original BLOCKED (not used).
- **BLOCK E-C1-a (standing):** with the fixture arc law (≥ 18.9 V at I_min, 1 mm) the in-loop C1 arc cannot be sustained because the substring can present at most ≈ 16.98 V (Voc_ss,cold + Vf) → P0 self-extinguishes by construction and all C1 candidate comparisons are void; with a 12–13 V metallic-contact minimum (NOT VERIFIED) the branch flips to a sustained ≈ 225 W arc. Fixture is internally inconsistent (V_ignite 15 V vs law ≥ 18.9 V). No C1 energy claim passes B2 until W07 states a sourced intercept. Independently agrees with SUP-C (X-009).
- **P1 100 V-class FALSIFIED for any single-device opening:** SW-M-OUT open with node at Vmpp → 207.8/228.6/255.4 V (−10/25/70 °C); node collapsed → 1343–1459 V; all-30 simultaneous opening → 7.6 V but survival window ≈ 144 µs skew (E_AS 0.3 J ASSUMED). Input to X-001.
- C2-far: after SW-STR-INV opens, S20 keeps ≈ 18.4 A into the arc → P2 alone is a halving (5.36 → 2.68 kJ over 5 s, illustrative), not containment; P3 residual ≈ 5 J. Agrees with SUP-C (X-002 direction).
- C3: string-level electrical detection FALSIFIED (ratios 0.1/0.4/2.0 vs 20 K drift, all < 3); module-lead-span sensing survives only if sense points span the mated pair; C3 action must be alarm/derate, not trip (→ X-008 resolution path).
- Lifecycle screen (algebra, ASSUMED): dies 1440/720/384/48; required unit failure rate for ≤ 1 added outage/yr 159–4756 FIT; P1 string-outage rate scales 30× λ_unit; 1.65 W/die free-air at 62 K/W → Tj ≈ 187 °C in an 85 °C box (not feasible without a thermal path). NO reliability/lifetime number permitted (UNKNOWN).
- Objections X-E1..X-E5 logged. Tokens 180,221; tool uses 46; duration 2698 s.

### R-04 SUP-A (model `fable`, Track A supervisor) — completed 2026-10-17 ~21:30 BST
- Files: review/track-A-charter-and-initial-attack.md (258 lines, 14-item B1 checklist, 12 objections); review/track-A-check.py (deterministic reproducer, sha256 e8840777…; runs from claude-study/, exit 0).
- Ran: track-A-check.py (algebra; fixed-n single-diode cross-check fit; two-string parallel-arc node solve; loop L/R/C; stored and clamp energies; backfeed; C3 thermal). Web: S–O provenance NOT VERIFIED (IOP blocked).
- X-001 position (settles against "module Voc" for a lone SW-M-OUT): V_sw = 30·Voc_m(T) − V_node = 228.6 V (node at Vmpp, STC) / 343.9 V (S20 at −10 °C); 1372.5/1487.8 V (node 0 V); 1342.5/1457.8 V (parallel arc, node ≈ 30 V). A clamp below string class conducts continuously (11–22 kW). SW-SS: 15.70/16.98 V only with forward current and healthy D2; a dark module on a live node puts 1143.9–1487.8 V across an open SW-SS (new hazard for P1b).
- X-002 position (claim false): after SW-STR-INV opens S20 feeds the far arc at 18.40 A, 29.1–32.2 V, 536–592 W STC (246 W at 500 W/m², 88 W at 200 W/m²); extinction under the fixture law only below ≈ 27 W/m². Pre-trip two-string far arc 36.8 A, 31.6 V, 1164 W, node collapses to ≈ 148 V. P3 (both ends) required. Agrees with SUP-C and SUP-E.
- C1 as framed: D2 clamps the gap at ≤ 15.70 V STC < 18.9 V → cannot discriminate P0/P1/P2; D2-open / outside-loop variant ≈ 500 W sustained → supports appending C1loop (X-009).
- Energies: ½LI² 936 m pair 0.113 J (0.667 mH; 0.777 mH with ASSUMED 40 m row return); C_in 98.1 J (32.7–327); DC link 1309 J (654–2617); far arc receives ≈ 4.5 J of C_in energy, near arc order 10² J (Z_surge 0.154 Ω, 7.2 kA undamped bound); unclamped 1 µs loop interruption 13.4 kV; clamped t_off 32–320 µs, E_clamp 0.44–4.1 J at 1500 V clamp. Cable lumped validity f < 22.6 kHz for 936 m.
- C3: 15/60/300 W; 0.87/3.5/17.3 V vs 13.0 V cable thermal drift per 30 K at Impp; lumped thermal steady 95/275/1234 °C (model unphysical above ≈ 200 K rise).
- Backfeed: dark S20 on a live node passes 0.48–0.73 A reverse (switch closed); S19 lit into a dark-S20 series arc with inverter off: 4.4–6.3 A, 109–163 W.
- Tokens 182,127; tool uses 38; duration 3407 s.

### R-05 SUP-B (model `fable`, Track B supervisor) — completed 2026-10-17 ~21:40 BST
- Files: review/track-B-charter-and-initial-attack.md (334 lines; 16-item checklist; 13 objections; proposed variants P1-IN, P1-BYP, P1-FB, P1-uni, P1-shared requested as NEW ledger keys); review/track-B-initial-attack-calcs.py (fixture-only reproducer, self-checks OK, exit 0).
- Ran: calcs script only (algebra). Infineon product page fetch BLOCKED; RS distributor listings show IMZA65R027M1H as 650 V (manufacturer confirmation left to W04).
- Clamp trade: t = L·I/(Vc−Vs), E = ½LI²·Vc/(Vc−Vs): at Vc 1600 V, 8–19 µs and 0.12–0.26 J for Vs 229–988 V; Vs 1458 V (node collapsed, cold) → 81 µs / 1.13 J (1600 V) or 48 µs / 0.70 J (1700 V). A clamp below Voc_s − V_node conducts continuously (1.6–1.9 kW). Distributed first step I·Z0 = 2.25 kV per 8.8 µs round trip → external clamp mandatory at every series interrupter.
- SW-M-OUT: standing voltage 229 V (STC, node at Vmpp) … 1343–1488 V (parallel fault / node 0 / dawn last-to-close) → even case (a) excludes 60–200 V silicon; a 1700 V SiC pair ≈ 126 mΩ hot (ASSUMED) = 37.8 W = 5.7 % of module → **Track B prior: REJECT P1 as defined** unless Track A removes cases (c)–(e). SW-SS: off-state 16.98 V cold, bypass diode 7.8 W when open, D2-open failure puts 1343–1488 V on it (Vds-monitor re-close rule) → **KEEP**. SW-STR-INV: ±1488 V bidirectional; C2-near prospective 7.3 kA (312 A/µs) from C_in, 26.7 kA V_DIRECTBUS; 20/100 µH reactor (ASSUMED) with 1–10 µs trip → let-through 28–501 A, E_clamp 0.15–10.4 J; 330 mΩ budget easy.
- Thermal screen (Rth_ja 15/30/60 K/W ASSUMED, Ta_box 70 °C, Tj ≤ 125 °C): Rds_hot ≤ 12.2/6.1/3.1 mΩ per device; thermal runaway gain ≥ 1 for 650 V SJ and 1700 V SiC at 30 K/W.
- X-003 REJECT as a whole-circuit claim (4.7 mJ difference 1 vs 10 µs vs ≥ 0.100 J clamp and 0.52 J per ms latency), ACCEPT only as SW-STR-INV self-protection; X-004 REJECT (650 V < 873–1500 V duties); X-005 REJECT (29.96 W = 908 % of budget).
- Tokens 179,016; tool uses 42; duration 3701 s.

### R-06 W01 (model `opus`, Track A topology) — FAILED 2026-10-17 ~21:35 BST, relaunched as W01r
- Failure: agent terminated by the API (response exceeded the 128,000 output-token maximum) before writing any file; topology/ was empty. Nothing claimed from this run.
- Relaunch W01r with the rule that all large artefacts are generated by scripts, never typed; supervisors' algebra (228.6 / 1372.5 / ~1342 V for SW-M-OUT; ~15.7 V for SW-SS; S20 remains on F2far after SW-STR-INV) given as expected values to confirm or contradict explicitly.

### R-07 W06 (model `opus`, Track D sampling benchmark) — completed 2026-10-17 ~21:50 BST
- Files: experiments/sampling_benchmark.py (sha f31bd61c…), test_sampling_benchmark.py (29 tests), sampling-benchmark-results.csv (330 rows, sha 73e122ec…), sampling-benchmark-summary.json (sha e2b701b2…), README-sampling.md.
- Orchestrator re-ran: `--check` CSV and summary byte-identical; 29/29 tests OK (21 s).
- X-006 REJECTED (general claim): bounded Vogel 5th/5 on planted-region misses in all 9 (d,N) cells; corners and categorical holdout unreachable by construction; discrepancy 73× worse than Sobol at N=1024, d=2; only win is 2-D minimum point separation. Cause is the disk map, not the golden-angle sequence (golden lattice on the full square matches Sobol). Phase 0 screen understates its own worst case ×1.52 (X-012); pass counts are layout properties, not rates.
- Recommended wave-2/Phase D design: enumerated categoricals + explicit corner block (all 2^d or resolution-IV fraction) + scrambled Sobol fill shared across candidates (X-013 for the ledger).
- Tokens 368,966; tool uses 88; duration 6096 s.

### R-08 HANDOVER — orchestrator stopped the swarm 2026-10-17 ~22:00 BST (owner instruction: finalise as it stands, lose nothing, hand scope to ChatGPT)
- Stopped (partial or no in-tree output): W01r, W02, W03, W04, W05, W07, W08, W21, W22, W23, W24, W25, W26, W27, W28, W29, W30, W31, CTRL-01..CTRL-10 (all `opus`). Last status lines are in the session transcript; in-tree partial files: models/arc_model.py + .lib (W07, ngspice self-check failing at stop), models/detection.py (W05), electronics/switch_models.lib (W04), review/controls/CTRL-01 and CTRL-02 phase-1 clean-room files.
- 128 scratch prototype/probe files recovered verbatim into handover/scratch-recovered/ with MANIFEST.json (status PARTIAL_UNVERIFIED_SCRATCH).
- Barrier B1 not reached; no wave-2 simulation ran; no architecture was compared against baseline. See HANDOVER-TO-CHATGPT.md.
- Owner's session usage at the time: 82 % of the 5-hour window (screenshot 21:55 BST).
