# V11 D5 — Billion-case Kuiper–Vogel–Fibonacci PV module Furnace and Phase II intelligence

**Date:** 18 October 2026. **Status:** engineering R&D scope; not a certified product, actual billion-run result, or measured PV fault reduction.
**Writable repository:** Ventusltd/v11 ONLY. Research branch analysis/pv-d5-billion-furnace-kuiper-20261018; stacked on draft PR #13. Preserve V11 main, all D1–D4 drafts, earlier Claude handover, and all external source repositories read-only.

## Objective and interpretation

Find an economical, reliable, junction-box-sized, low-loss PV module electronic protection design, with known physical fault protection zones. Its true success metric is electrical energy delivered **to the fault** and residual accessible voltage under independently verified arc, hot-contact, reverse-feed and failure conditions, not processor count or the number of plotted points.

The Kuiper/Vogel geometry maps case identities. The Fibonacci stride traverses identities. The Furnace tests a defined algorithm over combinations. Stars links evidence and contradictions. Faraday retains falsifiable experimental observations. None of these supplies unmeasured electrical truth.

## 1. Exact sources consulted and what to reuse

| Owned read-only source | Files and demonstrated role | V11 reuse constraint |
|---|---|---|
| [Kuiper Belt](https://github.com/Ventusltd/kuiper-belt) | learn-the-kuiper/202610042346/kuiper-law.js and modules/strings.js: newer LIVE Kuiper law, permanent component keys, reserved inverter slots/gaps, animation | Distinguish each physical module's component key from millions of scenario keys. Never reassign an existing key |
| [Original Line Wafer](https://github.com/Ventusltd/globalgrid2050/blob/main/testcode/202609151339/lib.mjs); [Faraday cells](https://github.com/Ventusltd/faraday/blob/main/apparatus/cells.mjs) | older continuous golden-angle law and numbered NAND gate-cell states | Version separately from live Kuiper. Neither placement geometry nor Faraday cells is a power-electronic model |
| [kuiper-drawing-engine](https://github.com/Ventusltd/kuiper-drawing-engine) | web/geometry.mjs, tests/geometry.test.mjs, docs/DRAWING-SOURCE-REVIEW.md: metre-based panel corners, tilt/orientation-dependent junction positions, unknown geometry preserved as unknown | Physical drawing coordinates distinct from case-space projection. No invented junction box positions |
| [sld](https://github.com/Ventusltd/sld) | README, docs/DRAWING-GUIDE.md, docs/FURNACE.md: pinned educational symbol sources, graphics anchors vs electrical terminals, billions of **graphical** placement checks | Do not interpret intersecting SVG wires as connected conductors or graphical units as IEC clearance |
| [particle-physics-drawing-engine](https://github.com/Ventusltd/particle-physics-drawing-engine), [graphics-engines-open-source](https://github.com/Ventusltd/graphics-engines-open-source) | coaxial fields, geometry scenes, browser/GPU checks, available sample images | Possible visual references after reviewing licence and physical topology; do not claim circuit physics |
| [gpu-drivers-for-global-grid](https://github.com/Ventusltd/gpu-drivers-for-global-grid) | engine/ventus_engine.py pinned at bfdc344289c0f03093e0c65979487e9916ea1ef4; engine/fused.py, engine/selftest.py, docs/GPU-TESTING-LESSONS-20260924.md and GPU reuse notes | Reuse exact read-only Engine/Space and its CPU/CuPy verification, bounded reduction and memory-aware batch sizing. Do not create a competing GPU engine |
| [worlds-](https://github.com/Ventusltd/worlds-) | src/furnace.py and night-results/furnace.json (historical three-channel GPU evidence); src/to_kuiper.py (compact projection); src/annihilate.py (threshold equality); night-results/KUIPER-TOPOLOGIES.txt | Furnace is a file in worlds-, not a standalone repo. Its historical case numbers are NOT PV product safety proof |
| [trillion-loop](https://github.com/Ventusltd/trillion-loop) | docs/02-the-enumeration-kernel.md, 03-the-second-channel.md, 04-the-provenance-gate.md, 05-stratified-sampling.md and 07-coverage.md | Denominators, reached cases, provenance and independent checks must be explicit |
| [Stars](https://github.com/Ventusltd/stars) | modular-star/relate.mjs, structure.mjs, proof.mjs, why.mjs, decision-record.mjs | Phase II typed evidence and decision graph; record unknowns/failures, never fabricate PROVEN |
| [Faraday](https://github.com/Ventusltd/faraday) | README, experiments/INDEX.tsv, apparatus/cells.mjs and cells.test.mjs | Experiments with question, apparatus, actions, observation, refuted_if and conclusion, including REFUTED/NO EFFECT; local D5 draft IDs are not allocated permanent Faraday numbers |
| [Ventus Grid Engine](https://github.com/Ventusltd/ventus-grid-engine) | engine/network-topology.js, compute-observer.js, voltage-drop.js and rating-envelope.js | Topology and real-computation evidence are separate from drawing and published rating; resistive I²R heat is not fault-arc energy |
| [star-maker](https://github.com/Ventusltd/star-maker), [star-quantum-twin](https://github.com/Ventusltd/star-quantum-twin) | machinery/bench/starmaker.mjs, stars records and provenance graph patterns | Later interactive relation representations, not automatic arc simulation |
| [V11 D1–D4](https://github.com/Ventusltd/v11/pull/13) | generic 3-substring PV electrical fit, bounded ngspice tests, back-to-back MOSFET/body-diode cases, insulation and IEC licensing guard | Treat simulation as generic model evidence; complete source-to-fault and real device verification remains open |

## 2. Distinct Kuiper laws, identity and Fibonacci traversal

**LIVE 2026 Kuiper Belt:** for 0-based key k, G32=2654435769 and M=(k×G32) modulo 2^32. Radius=sqrt(k+0.5), angle=2πM/2^32, x=r cos(angle), y=r sin(angle), world y-up. The angular hash wraps after 2^32 but radius continues growing; CPU float64 vs WebGL float32 placement may differ. Angular increment is about 222.49° anticlockwise, equivalent to 137.51° clockwise.

**Earlier Line Wafer and Faraday:** for positive key k, radius=sqrt(k), angle=k×π(3−sqrt(5)). This is a DIFFERENT mapping; never silently substitute one law for the other or mirror the picture.

**Fibonacci sequence:** F(44)=701408733 is coprime with 2^30. Hence index=(seed+n×701408733) modulo 2^30 visits every declared integer exactly once over a full traversal. This is selection/addressing, NOT a physical law or guaranteed better experiment design. Benchmark against random seeds, Sobol, LHS and explicit corners.

Physical module component ID and test case ID are distinct. The integer case index and string D5:<decimal> are presently a **local, non-global namespace**. Allocate a disjoint permanent Kuiper key range only through the owner's authoritative append-only ledger. Do not claim billions of existing global keys have been created or mutate earlier ones.

## 3. Exact billion-case definition and honesty rules

Nine dimensions in product-d5/billion_case_space.py:

- 8 architectures: passive bypass, two single-FET orientations, back-to-back common-source and common-drain, sensing only, and two module-output stage candidates;
- 8 proposed fault classes including shade, cell or connector series arc, parallel fault, bypass diode open/short, resistive connector and earth fault;
- 8 device/control states including stuck switches, lost gate supply, diode failures, silent sensor and reset;
- 16 irradiance points;
- 16 cell-temperature points;
- 16 assumed hot MOSFET path resistances;
- 16 externally imposed differential voltages;
- 16 putative response delays;
- 2 inverter coupling configurations.

8×8×8×16×16×16×16×16×2 = **1,073,741,824 distinct parameter tuples**. Mixed-radix indexing is reversible and stable by version; case counts are never estimated from rendered dots.

Crucial limitation: **fault class, response delay and inverter coupling do NOT yet change the first algebraic verdict**. This is a deliberate incomplete software fixture, not a completed circuit solver. It would be scientifically incorrect to report a billion physically independent simulated faults. These axes must be made electrically operative before promoting the study. Distinguish: L0 indexed case; L1 actual CPU/GPU algebraic evaluation; L2 exact electrical topology/energy-source cut; L3 time-domain ngspice/EMT with nonlinear components; L4 compared against measured OEM/lab traces; L5 independent tested/certified product.

Current L1 labels: (0) no algebraic issue detected — NOT safe; (1) hypothetical voltage-rating conflict; (2) hypothetical shunt dissipative-loss exceedance; (3) device/control failure needing review; (4) assumed passive-diode heat. The 3.3W target comes from 0.5% of an assumed 660Wp module, NOT a standards requirement. Current synthetic voltage and resistance grids are **not manufacturer ratings** and must not become product-shopping recommendations.

## 4. Meaningful module-level physics to attach to case IDs

The product is the module-integrated electronics, not a big external DC breaker. Compare (A) conventional PV passive substring bypass with optional sensors, (B) normally-off, back-to-back MOSFET bypass inside a specified substring loop plus existing bypass diode, and (C) voltage-qualified module-output device only as a separate challenging candidate. D3 suggests the as-drawn lone MOSFET's body diode may bypass normal generation; validate against actual part models and both polarities. Never assume bypassing a substring interrupts a fault outside its loop.

For a selected scenario provide a **physical circuit node manifest** containing actual PV cells/substrings, anti-parallel diodes, drain/source/body/gate orientation, separate plus/minus field cables, inverter/PV-input and DC-link distinction, paired MPPT sources, cable R/L/C and frame/earth paths. Graphical line crossings and symbol anchors from SLD resources must not create electrical edges.

Mandatory fault cases: within-substring arc and outside-bypass connector arc; positive–negative parallel arc; one and two earth faults; passive bypass open/short; module dark or partially shaded; MOSFET failed short/open; control supply brownout; reverse current from adjacent string or inverter; nuisance MPPT/EMI transient; resistive hot connection without HF arc. Record *which source still powers the fault* after each action. An active bypass may reduce diode watts without reducing fault-site energy at all.

Actual transient outputs required: time series of switch Vds/Vgs both polarities, bypass/series diode IF/VR, clamp watts/joules, I²R wiring heat, semiconductor hot resistance and junction transient thermal only with validated models, initial/final capacitive and inductive stored energy, voltage-to-frame and post-trip externally accessible voltage. Fault-site energy is ∫v_fault(t)i_fault(t)dt, separately from shunt heat. Run ngspice/SPICE and a distinct independent solver where supported, with timestep convergence and physical calibration. Fixed-resistor "arc" remains a surrogate with no extinction claim.

## 5. Phase I — Furnace execution stages

**I-A CPU and original models now:** Confirm full mixed-radix case identity; execute explicit 512 corners, Fibonacci stride and injected failures; create 4096-point bounded Kuiper projection and Phase II synthetic evidence graph. Re-run the existing 9 D3 ngspice transient cases under unchanged conditions. These verify software execution only.

**I-B manually approved CUDA 65,536-case probe:** Run cupy_furnace.py on a real device. Independently compare compiled fused CUDA RawKernel against CuPy array operators for each case and against a scalar CPU oracle for 512 corners plus Fibonacci-stride samples. Planted disagreement must be detected. A missing GPU is a FAILED/UNRUN test, never silent NumPy fallback. Include strict-versus-inclusive equality checks and track floating-point uncertainty at thresholds.

**I-C manually approved full 2^30 L1 study:** Batch using actual free VRAM, reduce verdict categories on-device, independently compare fused and CuPy graph per batch, preserve source hashes, measured conditions, every actual case count, losses and mismatches. Avoid uploading billions of raw results. Archive one compact signed/digested receipt plus representative failure IDs and exact input version. Distinguish original compile time, kernel time, reductions, host transfer and end-to-end timings. Do not claim speedups when workloads/configurations differ. Quotas and the offline/online state of MSI GPU runners are NOT known until checked when executing.

**I-D physically meaningful study:** Before advertising a billion circuit tests, turn previously inert axes into verified electrical source models and compare selected GPU computations to actual transistor-level ngspice and/or published manufacturer or laboratory waveforms. If no credible source model exists, abort promotion and mark NOT_MODELLED. It is preferable to test 10,000 correct networks than one billion unrelated threshold predicates.

The existing read-only Ventus Engine remains the default backend for small screens. The existing Furnace's fused + independent CuPy array pattern is borrowed through an ORIGINAL D5 adapter, not by cloning its code or its historic result certificates. One full billion GPU evaluation is never automatically started by a PR or chat continuation. The source SHA must be reviewed and the owner must opt in to any self-hosted GPU run.

## 6. Kuiper animation and drawing products

kuiper_projection.py includes ALL 512 nine-dimensional corners plus Fibonacci-stride sampled cases, cap 50,000. The JSON declares its numerator/denominator, coordinate-law version, local-only case keys, code labels and SHA-256 digest. A projection of 4096 **does not mean** 4096 verified real arc faults or one billion rendered objects.

viewer.html and kuiper_viewer.mjs supply an original pan/zoom/select/filter/pulsing dot viewer. Dot movement is **not real current**. To animate real electrical flow later, source each frame from voltage/current waveforms attached to explicitly typed circuit terminals and stamped with simulation time and a netlist SHA. Use kuiper-drawing-engine for metre-based panel placement and sld only with an approved source/terminal licence; do not infer terminals from symbol geometry. Use spatial tile/level-of-detail aggregation instead of instantiating a billion browser sprites.

## 7. Phase II algorithms on results

1. **Stars evidence graph:** edge vocabulary such as depends-on, checked-by, run-of, fails, produces, concerns, mixed-evidence and proven. Connect case→model→fixture→SPICE run→source/observation→decision. "PROVEN" requires a clearly described validated claim, not an arithmetic success count.
2. **Faraday numbered experimental notebook:** ask a falsifiable question, list apparatus, what actually ran, verbatim observation, exact failure/refutation threshold, and whether REFUTED, NO EFFECT, INCONCLUSIVE or CONFIRMED. New D5 IDs are LOCAL until formally registered in Faraday, preserving historical numbering.
3. **Source-to-fault graph algorithms:** evaluate all conductive paths, alternate backfeed, bypass/diode states and minimal isolating cut sets. Only actual circuit connectivity determines protected zones; Kuiper dot proximity has NO causal meaning.
4. **Boundary search and adversarial algorithms:** sweep exact inequality cases, NaN/unphysical models, bypass-open plus gate-lost, short plus reverse feed, hot-Rds tail and dual earth fault. Compare Fibonacci, Sobol, LHS, random and hand-picked corners under the same physical test budget.
5. **Disagreement clustering and root-cause tracing:** a disagreement between scalar/Furnace/SPICE/lab creates a Stars red/unstable node and a Faraday follow-up; avoid hiding bad evidence with averaged results. Include clone/duplicate-family filtering learned from Stars.
6. **Multiobjective search after calibration:** minimise actual fault joules, max thermal stress, nuisance-trip burden, component cost/size, idle watts, lifecycle failures; enforce insulation/device constraints. Pareto rankings from uncalibrated sources must remain UNKNOWN, not marketed as hardware.
7. **Active learning after measured validation:** choose next lab/SPICE tests by highest physical uncertainty, diverse fault zones and potential design falsification. Never learn a spurious "probability of safe solar panel" from synthetic sample fractions.

D5 phase2_evidence.py currently builds only a **software evidence/tracing and review shortlist**. It deliberately emits no real-device safety verdict and allocates no permanent Faraday numbers.

## 8. Acceptance gates and evidence records

| Work package | Proof required | Current meaning |
|---|---|---|
| D5-identity | exactly 2^30 reversible input IDs, no collisions, 512 corners, Fibonacci traversal without alias | CPU-testable software mathematics |
| D5-projection | correct versioned Kuiper law, local-only keys, finite coords, capped output and animation preview | browser display of synthetic screened cases |
| D5-phaseII | typed graph, distinct cases, contradiction/status tracking, falsifiable experiment proposals | original evidence machinery only |
| D5-CUDA-probe | real NVIDIA CUDA, independent fused/graph/CPU agreement, planted failure detection | not launched |
| D5-CUDA-billion | exactly 1,073,741,824 actual L1 arithmetic evaluations with receipts, mismatch zero or explained | not launched |
| D5-real-physics | per-scenario topology, calibrated MOSFET/diode and energy ledgers validated against independent SPICE | not complete |
| D5-insulation/product | qualified dielectric, wet leakage, surge, arc/thermal, EMC, ageing and independent review | not complete |

The standards licensing constraint is non-negotiable: IEC 62548-1:2023 and IEC TS 62738:2018 remain single-user restricted documents. No PDFs, page images, normative passages, proprietary tables or licence metadata in V11, GitHub Actions, GPU inputs, Stars graphs or public app files. IEC 61730, IEC 60664-1, IEC 63027 and IEC 62852 are referenced bibliographically only until separately licensed and reviewed. SPICE cannot certify insulation coordination or manufacture.

**Decision:** Begin reproducible CPU case/Kuiper/Phase II tests now, prepare but do NOT trigger CUDA billion workload, and prioritise a manufacturer-specific back-to-back MOSFET plus failed-bypass-diode ngspice transient test as the next physically discriminating experiment.
