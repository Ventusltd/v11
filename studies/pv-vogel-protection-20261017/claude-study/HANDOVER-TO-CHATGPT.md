# HANDOVER — V11 PV protection study, cycle 1, from Claude orchestrator to ChatGPT

**Written:** 2026-10-17 ~22:10 BST, at the product owner's instruction ("finalise the work as it stands, don't lose anything, hand the scope back to ChatGPT to finish").
**Status:** research draft only. Barrier B1 was NOT reached. No fault-waveform campaign (wave 2) ran. No protection architecture has been evaluated against baseline yet. Nothing here is engineering approval, certification or laboratory evidence.

## 1. Where everything is
- Repository `Ventusltd/v11`, branch `analysis/pv-vogel-protection-20261017-cycle1`, **draft PR #7** (base `analysis/pv-vogel-protection-20261017`, i.e. stacked on PR #6 @ 4aacee6e, which is stacked on PR #5; `main` untouched; the PV arc disclosure repo, Kuiper repos and the frozen laboratory were never modified).
- All study artefacts live under `studies/pv-vogel-protection-20261017/claude-study/`. `manifest.json` carries every pin (commits, sha256, tool versions). `evidence-board.md` carries the per-agent receipts R-01..R-08. `contradictions.md` is the disagreement register (X-001..X-013). `assumptions.json` has 55 labelled entries. `source-register.csv` has S-001..S-017.
- Read-only clones used (not committed): `/home/claude/ventusltd/globalgrid2050` (da7d8f6e), `/home/claude/ventusltd/kuiper-belt` (40df5a3e). Re-clone shallow if needed.

## 2. What exists, and how far each item was verified
Verified = the orchestrator re-ran it and the result matched the author's report.

| Item | Path | Author | Verification |
|---|---|---|---|
| Phase 0 reproduction | `../test_vogel_study.py`, `../vogel_study.py` | PR #6 | **Verified**: 11/11 tests; 2560 keys; summary sha256 3d984774… |
| Shared fixture (illustrative, labelled) | `fixture/system-fixture.json` | orchestrator | Verified by use; see §5 for the two known defects |
| Append-only scenario ledger (keys 2561..2959, both Kuiper addresses) | `tools/ledger.py`, `experiments/scenario-ledger.json` | orchestrator | **Verified**: `--check` MATCHES 9cba84ac…; address laws checked bit-level vs lib.mjs and vs the live shell's keyPlace (`review/supd-pilot/`, `kuiper/verify_core_law.py`) |
| Kuiper core adoption note | `kuiper/KUIPER-CORE-USE.md` | orchestrator | Verified (laws, key law, L9/L10) |
| Track A–E supervisor charters + reproducer scripts | `review/track-{A..E}-charter-and-initial-attack.md`, `review/track-A-check.py`, `review/track-B-initial-attack-calcs.py`, `review/supc-calcs/track_c_calcs.py`, `review/supd-pilot/`, `review/track_e_screen.py` | 5 Fable supervisors | Scripts **run clean** (orchestrator); numbers are algebra-grade and were NOT yet independently cross-checked (CTRL-01/02/03 phase 1 exists, phase 2 not done) |
| Sampling benchmark (Vogel vs Sobol/LHS/random/grid) | `experiments/sampling_benchmark.py` + 29 tests + CSV/JSON/README | W06 (Opus) | **Verified**: byte-identical `--check`; 29/29 tests |
| CTRL-01 and CTRL-02 clean-room recomputations (phase 1 only) | `review/controls/CTRL-01/`, `review/controls/CTRL-02/` | controllers (Opus) | Scripts compile; phase 2 (diff vs target) NOT done |
| Arc model (Stokes–Oppenlander) Python + ngspice lib | `models/arc_model.py`, `models/arc_model.lib` | W07 (Opus), stopped | **PARTIAL**: compiles; its ngspice self-verification currently fails (agent was mid-task; its own probe reported series 18.5555 A / 30.670 V match before stop) |
| Detection library | `models/detection.py` | W05 (Opus), stopped | **PARTIAL**: compiles; no tests, no benign set, no latency JSON yet |
| Switch subcircuits | `electronics/switch_models.lib` | W04 (Opus), stopped | **PARTIAL**: drafted, unverified; no device register produced |
| Recovered scratch prototypes (128 files) | `handover/scratch-recovered/` + `MANIFEST.json` | W02, W03, W06, W07, W08, W22, W24, W25, W27, W28, W30, supervisors | **UNVERIFIED** prototypes/probes copied verbatim so nothing is lost; not deliverables |
| manifest, requirements, protocol, registers | `manifest.json`, `requirements.txt`, `WORKER_PROTOCOL.md`, `contradictions.md`, `assumptions.json`, `source-register.csv` | orchestrator | Current |

**Not produced at all** (planned, never delivered): topology graph (`topology/`), PV module/string model (`models/pv_*`), cable + DC-side models, standards matrix, laboratory validation plan, energy-ledger/units library and `proofs/`, campaign harness, any C1/C2/C3 simulation, `architecture-comparison.csv`, `engineering-decision.md`, `supervisory-review.md`, CI workflow for `claude-study/`.

## 3. Findings established so far (algebra grade unless stated; all ILLUSTRATIVE on the uncalibrated arc law)
1. **The fixtured C1 (series arc inside substring SS2 of M15, with a healthy bypass diode) cannot sustain under the fixture's own arc law**: the gap can see at most Voc_ss + Vf ≈ 15.7 V (STC) / 17.0 V (−10 °C) while the law needs ≥ 18.9 V at 0.5 A for a 1 mm gap. Three supervisors (A, C, E) reached this independently. With a 12–13 V metallic-contact minimum (NOT VERIFIED) the branch flips to a sustained ≈ 225 W arc that looks like a shaded substring at string level. → **X-009 / BLOCK E-C1-a**: C1 must be re-sited to the string loop ("C1loop", outside any bypass loop, ≈ 500 W sustained) and the arc-voltage intercept must be sourced before any C1 energy claim.
2. **A lone module series switch (SW-M-OUT, candidate P1) is string-voltage class, not module class**: opened with the inverter holding Vmpp it sees 228.6 V (STC) / 344 V (cold); with the inverter side at 0 V, 1372.5–1487.8 V; under a parallel fault, 1342–1458 V. **X-001 settled against "module Voc"**; Track B's prior is REJECT P1 as defined (a 1700 V SiC pair ≈ 38 W ≈ 5.7 % of module power). The per-substring switch inside the bypass loop (SW-SS, P1b) sees only ≈ 16–17 V with forward current and healthy D2 — but string-level voltage if the module is dark on a live node (new hazard, needs a Vds-monitor re-close rule).
3. **The inverter-end string breaker alone (P2) cannot clear a far-end parallel arc**: after it opens, S20's own modules keep ≈ 18.4 A into the arc (536–592 W at STC; 2.7 kJ over 5 s) — X-002 claim false; both ends (P3) are required. The paired string's current reversal at the inverter end (+17.31 → −18.4 A) is the one unambiguous sub-ms observable. C_in (150 µF) delivers only ≈ 5 J to a far arc (≈ 79 J lost in the 6.3 Ω home-run), order 10² J to a near arc (7.2 kA prospective, ESR/ESL UNKNOWN).
4. **Hot connector without arc (C3) is not credibly detectable electrically at string level**: 0.05/0.2/1.0 Ω give 0.87/3.5/17.3 V against ≈ 13–25 mΩ/K cable thermal drift (ratios 0.05–2 vs 20–40 K swings); a connector temperature sensor is required; the protective action is alarm/derate, not trip (X-008 verdict, Tracks C and E).
5. **Bounded Vogel sampling is not superior** (X-006 REJECTED): last of five on planted-counterexample misses in all nine test cells; corners and categorical holdouts unreachable by construction; recommended design = enumerated categoricals + explicit corner block + scrambled Sobol fill, paired across candidates. Phase 0's disk screen understates its own worst case ×1.52 (X-012).
6. **Timing**: wave travel 4.4 µs (936 m) ≪ loop commutation 23–115 µs ≪ ms classification windows; sub-µs switch off-time buys ≈ nothing in fault energy (X-003 rejected as a whole-circuit claim); every series interrupter needs a clamp (unclamped 1 µs opening ≈ 11–13 kV; clamp energy 0.1–4 J per event).
7. **Fixture defects found**: 936 m × 6 mm² home-run dissipates 1.9 kW ≈ 9.6 % of string power (cable sizing questionable); arc law V_ignite 15 V vs law ≥ 18.9 V is internally inconsistent; MPPT pairing, module internal structure, C_in, DC architecture, row-return length and V_DIRECTBUS bus membership are all ASSUMED/UNKNOWN (ids A-004..A-009, A-040, A-045).

## 4. Agents and models that actually ran (brief §12 requirement)
- Claude **Fable 5.1** orchestrator (this session) and 5 Fable supervisors SUP-A..E: completed (receipts R-01..R-05).
- Claude **Opus**: W06 completed (R-07). W01 failed by exceeding the 128k output-token limit before writing anything (R-06). W01r, W02, W03, W04, W05, W07, W08, W21–W31 and CTRL-01..CTRL-10 were **stopped by the orchestrator at handover** (R-08) with partial files as in §2. In total 36 Opus agents were invoked; 1 completed, 1 failed, 34 stopped.
- **Astra, Codex, GPT, Gemini: not available in this session, not invoked, not simulated.**
- Session caps: 20 concurrent subagents (raised to 30 at 21:50); workspace 2 vCPU / 7 GB; ngspice 42 installed from the Ubuntu archive (`apt-get install ngspice libngspice0-dev`); PySpice 1.5 declares ngspice 42 unsupported (use batch `ngspice -b`).

## 5. Exact next steps (in order) for whoever continues
1. **Fixture v2** (append, do not overwrite history): add `C1loop` (series arc in M15's positive lead / junction-box terminal, outside all bypass loops) as the primary C1; keep the in-loop case as `C1in` (a negative result worth keeping); fix the arc-law intercept inconsistency once W21-type calibration exists (see `handover/scratch-recovered` has nothing from W21 — redo: minimum arc voltage for Cu/Ag/Sn contacts at 5–20 A, short gaps, from Sandia SAND2013 AFCI tests, NREL 73213, Paukert, Ammerman). Append new ledger family `cycle1-physical-v2` for C1loop/C1in and SUP-B's P1 variants (P1-IN, P1-BYP, P1-FB, P1-uni, P1-shared) via `tools/ledger.py` (append-only; keys continue at 2960).
2. **Finish wave 1**: topology graph + switch-state tables (must reproduce the §3 node voltages or state the disagreement); single-diode module/string model + ngspice `PVSUB/PVMOD/PVSTR`; two-wire cable (π-ladder and LTRA; W03's probe found LTRA stalls when a stiff clamp engages — use the π-ladder for clamp cases) + DC side (V_BOOST/V_DIRECTBUS); finish `arc_model.py` verification; detection + SYNTHETIC benign set; device register with datasheet URLs; units/energy-ledger library and `proofs/`; campaign harness (W30's probes in `handover/scratch-recovered/ngtest/`).
3. **Barrier B1**: apply the five supervisors' acceptance checklists (each charter §4/§6) to those outputs; close or carry X-001, X-002, X-009 with pinned evidence; use L10 verdicts.
4. **Wave 2**: ngspice campaigns C1loop/C1in, C2-far, C2-near, C3 × {P0, P1b, P2, P2b, P3} (P1 as defined is rejected pending a string-class or bypass variant) with two independent energy integrals, step halving, device stresses, residual voltages; adversarial ADV-* cases; `architecture-comparison.csv` with evidence grades.
5. **Wave 3**: clean-room verification (CTRL phase 2), `engineering-decision.md`, `supervisory-review.md`, CI workflow, README; keep PR #7 draft; update its body with the results table, test outcomes and blockers.

## 6. Rules that must survive the handover
`WORKER_PROTOCOL.md` (labels, grades, no probabilities from sample fractions, no string-Voc-by-assumption, no standards text, no vendor SPICE models, no agents reported that did not run), the brief's stop/abstain list, and kuiper-belt L9/L10 (reproducibility; verdicts settled by pinned evidence only). The owner's objective is fault-energy containment end to end, not an eFuse optimisation and not a patent project.

## 7. One-command reproduction of what is verified
```
cd studies/pv-vogel-protection-20261017 && python3 -m unittest -v test_vogel_study.py && cd claude-study
python3 tools/ledger.py --check
node kuiper/core_place_node.mjs > /tmp/core.json && python3 -I kuiper/verify_core_law.py /tmp/core.json
python3 -B experiments/sampling_benchmark.py --check && python3 -B -m unittest experiments/test_sampling_benchmark.py
python3 review/track-A-check.py; python3 -I review/track-B-initial-attack-calcs.py; python3 -I review/supc-calcs/track_c_calcs.py; python3 -I review/track_e_screen.py
```
