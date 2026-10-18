# V11 D4 — verified CPU-only Furnace readiness receipt, 18 October 2026

**V11 draft PR #13**, branch analysis/pv-d4-cupy-engine-readiness-20261018, stacked on D3 PR #12; main unchanged.

**Actual successful workflow:** https://github.com/Ventusltd/v11/actions/runs/39136794629
**D4 job:** 117702822779. **D4 archive:** pv-d4-furnace-kuiper-CPU-only-receipts, artefact ID 12139987464. Historical Phase 0 job also passed in the same run. Real CPU, no GPU allocated.

## What executed, with evidence classifications

| Evidence | Observation |
|---|---|
| GitHub CI Python unit tests | 37 Python tests completed, ONE intentional GPU-opt-in skip, no failures |
| Original pinned Kuiper address law JavaScript tests | 4 Node tests passed, 0 failed |
| NumPy + pure Python independent oracle | 17,640 / 17,640 small screening cases evaluated, zero differences after explicit threshold handling |
| Small screen counts | [6,324, 1,581, 4,620, 5,084, 31] across the five published hypothetical/equality classes |
| Numerical threshold issue found and retained | **31 near-equality cases** are counted separately; formerly CPU factored and NumPy expanded arithmetic had different zero-margin verdicts |
| Billion-case scheme | **1,000,000,000 unique deterministic integer *addresses***, 12 fixed axes; schema SHA-256 3454a2b6f027b775f12f5e6fb461883338f1b621e101d1aa088eee695f07f38b |
| Actually examined in billion-lattice pilot | **4,096 distinct CPU algebra/case-integrity probes** (NOT a billion numerical solves) |
| Phase II replay queue | **48 unique case stars** with evidence graphs and Faraday-compatible **proposed** experiments, not executed laboratory tests |
| True CUDA runs in this D4 work | **ZERO** — opt-in workflow prepared but not dispatched and existing runner online state unverified |
| New ngspice simulations in D4 | **ZERO** — nine earlier generic MOSFET D3 simulations were separately verified and are referenced, not re-counted |
| Licensed IEC texts distributed | NONE — limited automated licence guard passed; manual review still mandatory |

## The 31-case Furnace witness, not swept under the rug

At **20 A**, hypothetical combined MOSFET path resistance **0.020 Ω**, duty **0.1**, and passive diode Vf **0.4 V**:

  active shunt P = I^2 × R × duty = 0.8 W
  passive diode P = I × Vf × duty = 0.8 W

One independently written scalar route evaluated its near-equal floating value slightly below 0.8 W; the vectorised route saw exact equality. The initial test **FAILED** with category totals [6355,1581,4620,5084] versus [6324,1581,4620,5115]. Instead of rewriting the scalar route to mask the difference, D4 now defines a fifth category **NUMERIC_BOUNDARY** for tolerance-level equality; it keeps ZERO-current and ZERO-duty as 'no active action'. The new independently computed five-bin counts match perfectly: [6324,1581,4620,5084,31].

The 31 are **repeated parameter combinations at one hypothetical formula boundary**, not 31 measured hardware faults. Explicit vendor/device rating headroom and electrothermal margins remain unknown. Treat all "bin 0" as a *conditional algebra screen*, NEVER a hardware PASS.

## Versioned source genealogy

- Original pinned reusable GPU arithmetic: https://github.com/Ventusltd/gpu-drivers-for-global-grid/blob/bfdc344289c0f03093e0c65979487e9916ea1ef4/engine/ventus_engine.py
- Original GPU fused demonstration: https://github.com/Ventusltd/gpu-drivers-for-global-grid/blob/bfdc344289c0f03093e0c65979487e9916ea1ef4/engine/fused.py
- Original Furnace: https://github.com/Ventusltd/worlds-/blob/main/src/furnace.py and independent published historical receipt night-results/furnace.json.
- Original LIVE Kuiper mathematical mapping: https://github.com/Ventusltd/kuiper-belt/blob/main/learn-the-kuiper/202610050010/kuiper-law.js
- Array geometry and bounded drawing examples: https://github.com/Ventusltd/kuiper-drawing-engine
- Stars graph and decision vocabulary: https://github.com/Ventusltd/stars/tree/main/modular-star
- Faraday immutable experimental ledger: https://github.com/Ventusltd/faraday
- Grid topology/observer semantics: https://github.com/Ventusltd/ventus-grid-engine

These were read as references. No historical repos, personal runner machines, shared GPU infrastructure, previous Kuiper registry or GPL-protected third-party code was modified by D4.

## Scope status

D4's complete detailed scope is BILLION-FURNACE-KUIPER-PHASES.md. The virtual test viewer is wafer/index.html with exact live law in wafer/kuiper_core.mjs, immutable display schema wafer/case-schema.json, and Node tests. This viewer intentionally renders a bounded 2,048 address-point PREVIEW, not 1bn physical points; point colours do not claim simulated results. In a local read-only checkout of the draft PR, launch a static HTTP server in wafer/ (e.g. Python's built-in http.server) and open index.html; no copyrighted standards files are needed.

The Phase II code phase2_replay.py performs research FOLLOW-UP PRIORITY ranking of hypothetical warning tags and constructs 48 deterministic replay seeds/evidence graph nodes/Faraday experiment proposals. It is **NOT** an independently validated electrical graph solver, machine-learning model, cluster discovery proof, or executed hardware experiment. Those tasks require real physical circuit/arc input.

## Remaining hard blockers before real billion-case CuPy

1. Verify OEM module bypass diode, MOSFET thermal/failure parameters and MPPT/DC input energy; no physical model or simulation can claim 30-year field results from invented numbers.
2. Implement and verify real node-level PV module source-to-fault graph, calibrated arc/high-resistance/insulation fault models and failed-gate/failed-bypass scenarios against independent ngspice/EMT and lab cases.
3. Build V11-specific fused NVRTC counterexample/energy kernel and independent CuPy array-graph plus expanded algebra routes; prove agreement over boundary-saturated subspaces, not only uniform random probes.
4. Manually confirm existing MSI runner ONLINE with a functioning CuPy environment, free GPU memory and watchdog time. Only then seek explicit owner authorisation to dispatch bounded 10k→1m→10m→100m→1bn runs, if physically justified.
5. Promote only evidence-supported survivors to Star graph and append-only V11 Faraday-compatible lab planning records. Existing Faraday repo remains untouched.
6. Licence-authorised IEC 61730/60664 module/PCB/insulation engineering and accredited environmental/fire/arc testing remains independent and HOLD.

**This is a verified computational FOUNDATION, not yet a billion-case physical GPU Furnace or solar DC electronic arc-protection product.**
