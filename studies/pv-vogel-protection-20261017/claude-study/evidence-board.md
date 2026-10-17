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
