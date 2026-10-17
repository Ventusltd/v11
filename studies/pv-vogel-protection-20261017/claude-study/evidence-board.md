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
