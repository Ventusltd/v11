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
