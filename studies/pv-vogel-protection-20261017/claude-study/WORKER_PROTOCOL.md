# Worker protocol — V11 cycle-1 swarm (2026-10-17)

Every agent in this study, supervisor or worker, follows this protocol. Read the master brief
(`../CLAUDE_CODE_MASTER_STUDY_BRIEF.md`) and the shared fixture (`fixture/system-fixture.json`) first.

## 1. Shared truth
- The ONLY fixture is `claude-study/fixture/system-fixture.json`. Do not hard-code numbers that differ from it.
  If you need a value that is not in it, add it to your output as `{"value": ..., "label": "ASSUMED"}` and list it
  in your report so the orchestrator can append it to `assumptions.json`. Never silently invent.
- Scenario identities come from `claude-study/experiments/scenario-ledger.json`. Use the scenario_id strings exactly.
  Phase 0 keys 1..2560 are frozen. New permanent keys are appended by the orchestrator only.
- Kuiper law (read-only, exact): `GOLDEN = pi*(3-sqrt(5)); r = sqrt(k); theta = k*GOLDEN; x = r cos theta; y = r sin theta`.
  It is an address, not physics.

## 2. Files and git
- Write ONLY inside the paths assigned in your task. Never edit another worker's files; if you need a change, say so in
  your final report with the exact proposed diff.
- Do NOT run any `git` command. The orchestrator commits. Do not touch `main`, PR #5/#6 files outside `claude-study/`,
  the Kuiper repository, or the frozen laboratory repository.
- Keep committed artefacts small (< 1 MB per file; waveform CSVs decimated; record SHA-256 of any large file you
  generated but did not keep).
- Python 3.13, numpy 2.5, scipy 1.18, networkx, pandas, matplotlib are available. `ngspice` 42 is installed
  (`ngspice -b file.cir`). PySpice 1.5 is installed but reports ngspice 42 as unsupported: use batch ngspice with
  `.control ... wrdata ...` exports, parsed by Python. No PSCAD/LTspice/PLECS/Simscape exist here: never cite them as run.
- Every script must run with a single command from `claude-study/` and must be deterministic (fixed seeds, no wall-clock in
  results). Tests use `unittest` and live beside the code as `test_*.py`.

## 3. Evidence rules
- Every number you produce carries: units (SI, per fixture naming), the source or derivation, an assumption label
  (`MEASURED`, `DERIVED`, `ASSUMED`, `UNKNOWN`, `REJECTED`), and an evidence grade
  (`algebra`, `illustrative_simulation`, `validated_against_trace`, `independent_lab_tested`, `certified`).
- A result without a reproducible file identifier (path + sha256 of the producing script) is not evidence.
- Energy bookkeeping: separate (a) energy delivered to the fault, (b) semiconductor dissipation, (c) inductive and
  capacitive stored energy, (d) clamp/snubber energy, (e) conduction loss. Check totals against sources.
- State what is NOT modelled in every result file.
- Probabilities: report as `UNKNOWN` unless a documented stochastic model with empirical priors exists. Geometric
  sample fractions are never probabilities.
- Do not claim arc extinction from the uncalibrated Stokes-Oppenlander form without the word "illustrative".
- Do not copy standards text or vendor SPICE models. Cite clause numbers only if the licensed source was examined;
  otherwise write `NOT EXAMINED`.
- Web facts (datasheets, papers): record exact URL, access date, what the fact supports, in your report so the
  orchestrator can append to `source-register.csv`. Do not quote more than a short phrase from any source.

## 4. Reporting
Your final report (returned to the orchestrator) MUST contain, in this order:
1. `DELIVERABLES:` list of files written with one-line purpose each.
2. `RAN:` exact commands executed and their pass/fail result (tests, simulations).
3. `KEY RESULTS:` numbers with units, labels and grades.
4. `OBJECTIONS:` challenges to other tracks' likely assumptions (named: Track A/B/C/D/E) — at least two.
5. `ASSUMPTIONS ADDED:` list for `assumptions.json`.
6. `SOURCES:` for `source-register.csv`.
7. `BLOCKERS:` what you could not do and why (missing data, tool, licence).
Never pad. Never claim something ran if it did not.

## 5. Addendum 2026-10-17 21:40 — Kuiper core and L10 verdicts
- The live Kuiper core law (see `kuiper/KUIPER-CORE-USE.md`) is recorded for every scenario key as `kuiper_core_xy`,
  alongside the Line Wafer `kuiper_xy`. Both are addresses only.
- Every verification verdict (controllers, contradiction register, supervisory review) uses kuiper-belt LAWS.md L10:
  `HONOURED` / `OVERREACHED` (first concrete deviation named) / `NOT EVALUATED` (statements listed) / `DISCLOSED`
  (acknowledged gap, never waives a numerical contradiction). Disagreement is settled by pinned evidence only.
