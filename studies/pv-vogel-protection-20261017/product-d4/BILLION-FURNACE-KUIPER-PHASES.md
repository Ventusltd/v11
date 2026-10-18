# V11 D4/5/6 — one-billion-case PV module circuit Furnace, Kuiper visualisation and Phase II discovery

**Scope approved for implementation as research, NOT hardware or compliance approval.** Date: 2026-10-18. **One active write repository: Ventusltd/v11.** This document is a reproducible engineering protocol, not a claim that one billion circuits have already been solved or that one billion valid protective topologies exist. D3 PR #12 contains the preliminary active-substring FET work. D4 draft PR #13 is stacked on D3. All other GitHub repos remain READ-ONLY and remain the source authority for their own code.

## A. The actual prior systems inspected, with precise reuse contracts

**Kuiper geometry and animation.** The live mathematical source is Ventusltd/kuiper-belt, learn-the-kuiper/202610050010/kuiper-law.js, blob SHA c506a252f27fa8b80e849eb63bbb6699eaf674f0. It derives its placement from the live index.html. For nonnegative integer key k:

- m = (k × 2654435769) modulo 2^32 as an unsigned 32-bit product;
- theta = 2 pi m / 2^32, counterclockwise in mathematical world coordinates;
- radius = sqrt(k + 0.5);
- (x,y) = radius × (cos(theta), sin(theta)).

The 32-bit multiplication wraps for k >= 2^32, while radius continues to grow. The older globalgrid2050 202609151339 Line Wafer source uses a continuous golden-angle formula and sqrt(key), with 1-based keys; **THESE ARE DISTINCT HISTORICAL IMPLEMENTATIONS.** For the virtual billion-case viewer, follow the *20261005 live Kuiper Belt law above*, with JS/Python coordinate test witnesses. Do not combine them into an undocumented pseudo-formula and do not treat Vogel placement as a physical circuit relation. A position is an ADDRESS, not a safety verdict or topology adjacency.

Other drawing/template sources:
- Ventusltd/kuiper-drawing-engine web/geometry.mjs and web/app.mjs; tests/geometry.test.mjs; docs/DRAWING-SOURCE-REVIEW.md: independent metre-based module geometry; unknown junction positions are ABSENT, not invented; render a bounded selection, keep full virtual-address population separately. This geometry is *module-table layout*, not PV circuit connectivity.
- Ventusltd/kuiper-belt learn-the-kuiper animations and scale logic: time-indexed zoom, key selection, 4-million point bounded draw calls in its live code; adapt the architecture, not copy a large third-party asset tree.
- Ventusltd/worlds- README.md and src/to_kuiper.py: Kuiper archive-order positions versus parameter-adjacent layout; a Hilbert-style presentation can be useful to see neighbours, but MUST be a distinct visual transform and not a change to immutable study IDs. A change of layout never changes which test the point names.
- Ventusltd/particle-physics-drawing-engine sample images, Ventusltd/graphics-engines-open-source GPU screening and Ventusltd/sld shared symbol source: drawing and symbol templates, not proof of galvanic electrical terminal connections. Source graphics licences/attribution must be separately reviewed before any code/assets are imported.

**Furnace and numerical verifier.** Ventusltd/worlds-/src/furnace.py and night-results/furnace.json are the actual Furnace, with 1,000,000,000 evaluations across **49.355293% of its OWN declared lattice** and three numerical comparisons. That historic receipt is not a PV arc result. The pinned Ventusltd/gpu-drivers-for-global-grid main commit bfdc344289c0f03093e0c65979487e9916ea1ef4 contains engine/ventus_engine.py (CPU/CuPy backend, closed-form gate, mixed radix index, compact reduction, no fake GPU fallback), engine/fused.py (NVRTC fused kernel) and its GPU reuse/restart notes. D4 already reuses its source via read-only pinned checkout. Ventusltd/trillion-loop documents GPU residency, survivor compaction, boundary sampling, source-based limit provenance, closed-form witnesses. DO NOT create a second GPU engine, auto-start paused MSI workflows or report raw kernel timings as an end-to-end gain.

**Phase II prior logic.** Ventusltd/stars modular-star/{sense,relate,decisions,proof,coherence}.mjs provides evidence/decision graph schemas, relationship vocabulary, why the graph says what it says, and source-linked proof nodes. Ventusltd/star-maker machinery/bench/starmaker.mjs uses stable composition seeds, live browser checks and bounded workers; adapted here as stable **electrical case replay seeds**, NOT a GPU factory for generating drawings. Ventusltd/faraday bench/tests.py, experiments/INDEX.tsv and apparatus/grid_finder.py provide repeatable experiment questions, apparatus, observed result, explicit REFUTED/NO EFFECT as well as positive findings, and contiguous numbered logs. Ventusltd/ventus-grid-engine engine/network-topology.js formalises nodes/edges and the distinction between a physical conductor versus a diagram; engine/compute-observer.js distinguishes request, attempted, completed, failed, unsupported computations; engine/rating-envelope.js refuses unjustified sums of independent circuit ratings. We will adapt these **data contracts** to DC source-to-fault graphs, not treat grid-substation topology as an interchangeable PV-module topology.

## B. Physical objectives BEFORE any billion-case count

A 660Wp, 17.31A provisional PV module with THREE bypassed substrings and an illustrative 30-module string is our fixture, not a particular approved OEM model. Relevant actual boundaries: substring positive/negative terminals, bypass diode anode/cathode, individual FET drain/source/gate, module junction output leads, positive/negative mated connectors, string home-run, frame, protective earth, paired string and actual inverter PV input capacitor. The external string is a **boundary condition**, never the proposed hardware product.

Test four architectures:
A0: passive OEM-style bypass network only (baseline; no new electronic protection).
A1: back-to-back low-voltage MOSFET ACTIVE SUBSTRING BYPASS (normal OFF, may conduct 15–25A in shading); preserve body-diode direction and floating common-mode insulation.
A2: bidirectional MODULE OUTPUT SWITCH (unverified near-string Vds, surge and loss budget; never assume module Voc is rating).
A3: HYBRID active substring bypass plus physically separate module-output protective element; higher cost and unknown controller failure coupling.

Test ten physically distinct fault/heat zones, each tied to explicit nodes: cell/interconnect series; substring ribbon; bypass-diode branch; junction-box solder; module positive connector; module negative connector; module lead-to-lead shunt; remote string cable shunt; hot resistive connector without arc; module-to-frame insulation. **An arc waveform does not follow merely from naming the fault.** A parallel short at a lead and a series connector arc differ in fault sources. Any zone lacking a calibrated physical model returns UNSUPPORTED and must be handed to SPICE/lab, not presented as safe.

The source-to-fault GRAPH is a prerequisite: bypass shunt opening cannot inherently isolate an arc located OUTSIDE its electrical loop. Reconstruct nodes, branches, diode and FET body paths, and explicit PV/source and capacitor contributions. Pass only if graph connectivity, Kirchhoff constraints and post-fault source cuts have independent witnesses.

## C. Billion-case, deterministic Cartesian lattice (exact denominator)

Define twelve axes. *Each case is a parameter-state combination, not necessarily a different valid circuit topology.*

| Axis | n | Definition and required provenance |
|---|---:|---|
| Protection architecture | 4 | A0/A1/A2/A3 described above; design alternatives, not built parts |
| Fault/heat zone | 10 | named graph location, NOT interchangeable physics |
| Bypass diode state | 5 | healthy, open, short, high-series-R, high-reverse-leakage; unverified failure models |
| Irradiance profile | 5 | full, middle substring at 10%, middle substring dark, uniform low, whole module dark |
| Cell temperature °C | 5 | -30, -10, 25, 65, 85; illustrative design limits, actual module source needed |
| Forced source/string current A | 5 | 0, 3, 10, 17.31, 25; externally forced current may be inconsistent with irradiance, flag rather than conceal |
| Pair hot Rds(on) Ω | 4 | 0.002, 0.005, 0.020, 0.050 TOTAL for path; no manufacturer selected |
| External input capacitance F | 5 | 0, 50µ, 150µ, 500µ, 1000µ; assumptions not OEM verified |
| Trip command latency s | 5 | 2µ, 20µ, 200µ, 2m, 20m; zero detection time is never inferred |
| External bus condition | 5 | isolated, illustrated MPPT, collapsed, 1500V backfeed, source-reverse; exact node graph TBD |
| Control/gate state | 4 | commanded correct, power lost, stuck ON, unwanted activation |
| Illustrative fault/contact R Ω | 20 | 0.05 through 120 discrete values; physical relevance varies by zone; series arc R is NOT fixed resistor |

**Count = 4×10×5×5×5×5×4×5×5×5×4×20 = 1,000,000,000 unique 12-dimensional tuples.** This does NOT imply one billion physically independent failure mechanisms, one billion netlists, or one billion high-fidelity SPICE arc simulations. Some combinations are contradictory or physically unsupported; retain a separate ABSTAIN count. Never label the denominator "total possible PV failures".

Each case has an immutable zero-based integer index k in [0,999999999], decoded by a documented mixed-radix order; the index serves as the stable REPLAY SEED. Include a versioned axis schema SHA-256 in every receipt. When dimensions/values change, create schema v2, never reinterpret an old key. Keep a local virtual namespace "v11.pv.d4-billion/v1/<k>"; **DO NOT** insert or reserve a billion new permanent keys in the global Kuiper append-only ledger without separate explicit product-owner authorisation. Render the virtual namespace using the same Kuiper Belt mathematical placement but DO NOT claim it is an actual historical line-wafer coordinate.

## D. Phase I - honest GPU and SPICE test ladder

**Gate P0: physical calibration and truth table.** Rerun D1/D2/D3 exact SPICE inputs and measured numerical receipts, including the known lone-MOSFET body-diode counterexample. Acquire verified bypass diode V-I(T), module PV IV/T data, real MOSFET Rds(on)(I,T), diode Qrr, Vds/Vgs/SOA, gate supply & controller brownout, and actual inverter input capacitance/DC-link interface. Mark missing numbers UNVERIFIED; they may be swept hypothetically but cannot be accepted as rated design.

**Gate P1: pure CPU pilot, forced corners.** Implement versioned encoder/decoder, SOURCE-TO-FAULT reachability checker, closed-form arithmetic (Pshunt=I²R, Pconnector=I²R, Ecap=½CV² as a stored-energy inventory NOT delivered-fault energy), source voltage versus insulation common-mode, and model-domain validity. Execute small bounded CPU pilot with all endpoints, off-by-one threshold equalities, voltage reversals, shading/bypass failure, gate failure and samples near predicted boundaries. Independent scalar result, all indices unique, one digest, counts by OBSERVED/ASSUMED/ABSTAIN.

**Gate P2: actual ngspice small high-value cohort.** Convert 100–10,000 ranked *supported* scenarios into original explicit two-wire netlists by electrical topology family, not by blindly substituting parameters into wrong graphs. Measure source current, fault voltage/current, energy at fault INTEGRAL, clamped semiconductor energy, Vds/Vgs and reverse diode stress, residual voltage, and independent timestep convergence. Candidate models that lack actual arc plasma, coupling or reverse bias go in a declared uncertainty class. A toy shunt resistor is NOT an electronic arc interrupter.

**Gate P3: CuPy Furnace preflight.** Existing pinned Engine first compares NumPy to scalar CPU on every manageable sub-grid and stratified/replay probes. Create one V11 PV-specific fused NVRTC evaluator *only after physics gate*, with a second CuPy array-graph channel and a third independently expanded algebra form; start from deterministic 10k, 1m, 10m, 100m case runs on VERIFIED hardware and available memory. Stop immediately on mismatch or missing input, report worst offending keys and threshold distance, keep all disagreements for analysis; do not certify from zero disagreements. GPU batches chosen from live free VRAM and watch-dog limits, no static huge 1bn allocation, synchronized timing including transfer/warmup. No host/device round trip per candidate.

**Gate P4: entire one-billion declared lattice.** Only once P0–P3 are validated, run all 1,000,000,000 case INDEX tuples exactly once on real CuPy (without assuming current self-hosted runner online). Return compact histogram by architecture × fault zone × physical-source class × epistemic status; record visited count, ABSTAIN count, disagreement count, wall time, source and kernel digests, bounds, VRAM, device, and a capped ranked witness list. 1bn-case count is an arithmetic enumeration claim, not a certification or a probability of arc events. Repeat passes separately as soak tests, never add them to unique coverage.

**Candidate engineering metrics:** I²R and VfI losses, actual vendor on-voltage at 15-25A hot, fail-short energy paths, array-side versus bus-side capacitor energy and delay, source-to-fault graph cuts, gate-power loss, cell reverse breakdown and bypass thermal, false-positive/false-negative sensor trials against real recorded switching noise. Permanent product-go gates require traceable manufacturer input and independent lab/dielectric testing.

## E. Kuiper / Vogel / Fibonacci visual information architecture

The visualization **must never allocate a billion SVG/DOM elements or store a billion x,y pairs**. Map key k to the exact source-pinned G32/sqrt(k+0.5) coordinates in the GPU vertex shader or bounded CPU interactive viewer, with key range/sector/window culling, fixed per-frame budget, responsive pan/zoom, and a search field to reproduce any individual case ID. The Kuiper belt example draws in 4,000,000-vertex batches; a small proof viewer should draw only 500–3000 visible/sampled cases per frame and state this LIMIT, not claim all billion are displayed at once.

Two distinct views:
1. **VOGEL archive-address view:** x,y based only on immutable key. Colours show evidence classes (not red=unsafe by assumption); unrun cases remain grey. Cases that share a fault family are intentionally scattered by address. Radius increases with case index; the chart is not a heatmap of physical electrical distances.
2. **Electrical-neighbourhood view:** put architecture on one axis, fault zone on the other, overlay a parameter/threshold signature; eventually reuse the Hilbert/parameter-adjacency approach from worlds- where feasible. The morph animation moves **the same IDs** between address and parameter views without changing the underlying tests.

For 1bn candidates: persist only multidimensional aggregate tile counts, bounded evidence witnesses and verified case manifests; a click resolves [schema hash, key, axes, topology, fault, recorded result or NOT_RUN]. No server request or giant client blob is needed for a synthetic case coordinate, but any status/result must be sourced to a verified receipt. For visualisation, avoid nearest-neighbour geometrical meaning implied by the golden spiral. Explicit test at keys 0,1,2,2^32-1,2^32, and 999,999,999 for hash wrap, float shader tolerance and Python/JS parity.

## F. Phase II - run actual algorithms on evidence, not just a picture

When Phase I has a real receipt, the next software should operate on bounded **verified survivors**, not all billion raw cases:

**F1. Pareto risk/frontier selection.** Keep cases closest to switching voltage/rating equality, hot semiconductor loss limits, capacitor energy thresholds, voltage reversals and source cuts, separately by topology and fault family. Explicitly mark thresholds as OEM-verified or assumed. Pareto dominance is only meaningful within a comparable physical model; never rank totally unknown arc classes as though measured.

**F2. Falsification and counterexamples (Furnace + trillion-loop).** Group numerical disagreements by near-equality and floating-point precision, preserve exact case keys and reconstruct their inputs. Mutate each retained case through neighboring parameter bins; use *both* strict and inclusive comparisons to probe thresholds while independently recomputing physics with SPICE/EMT. Do not suppress ABSTAIN or physically inconsistent cases to improve success fractions. Discover minimal *counterexamples* to the hypothesis that a substring shunt removes a given source-to-fault path.

**F3. Source-path graph analysis (Ventus Grid Engine reuse).** Build a small explicit module graph with nodes for each PV cell substring, passive diode, active shunt, module connector, frame, string source, MPPT and capacitor, and typed directed branches. Compute reachability / minimum source-cut sets before and after commanded interruption, including FET body diodes and reverse feed; independently verify Kirchhoff. This is not the deployed transmission network and cannot reuse its connectivity data as though it were PV.

**F4. Reproducible Stars.** A retained case becomes a stable content-addressed "star": hash(schema version, index, physical netlist template digest, solver and input digest). Store CASE statuses NOT_RUN, NUMERIC_ONLY, SPICE_VERIFIED, LAB_OBSERVED, REFUTED, ABSTAIN; avoid "pass" unless the passed check is named. Link arcs and edges from the original Stars relationship vocabulary: case -> variant -> source assumption -> simulation receipt -> finding -> unresolved decision. Browser/diagram visual experiments may be replayed with the star-maker seed pattern but never portrayed as electrical hardware tests.

**F5. Faraday laboratory entries.** For every promoted claim, preserve an append-only numbered experiment with question, apparatus+simulation versions, action performed, original observation/uncertainty, status including REFUTED/NO EFFECT, and links to cases/source hashes and lab operator. A simulation record must never pretend to be a laboratory result. Never renumber or rewrite historical Faraday experiments; V11 publishes its own Faraday-compatible experiment registry, separately numbered with explicit namespace and provenance.

**F6. Independent recommendations and contradiction register.** Rank the greatest physical *unknowns* blocking viability: (i) can gate supply be genuinely self-powered and survive shading/brownout; (ii) does the device remain within differential Vds in every bypass fault; (iii) can local shunting extinguish an internally sited series arc without backfeed; (iv) can a hot connector be diagnosed without HF arc noise; (v) is 30-year junction-box thermal/reliability/cost viable; (vi) do multi-source parallel arcs remain fed? Publish both pro/con scenarios, not a single flattering success score.

The Phase II public deliverables are: anonymised bounded case graph JSON; tile/histogram data; 100–1000 traceable adversarial "stars" with full original test input references (NOT confidential OEM PDFs); a dozen explicitly falsifiable Faraday experiment cards; next targeted SPICE/lab test queue; no claims of certified IEC distances or a mass-produced protection circuit.

## G. Change control, copyright and failure gates

- Only V11 code/PR/workflows change; historical GPU, drawing, Stars, Faraday, GlobalGrid2050, Kuiper and laboratory repositories are read-only.
- Keep IEC 62548-1:2023 and IEC TS 62738:2018 single-user copyright PDFs/tables out of the public GitHub source, prompts, CI artifacts and agent workspaces. Public code contains only original equations, test assumptions and bibliographic pointers. Physical IEC 61730 / IEC 60664 creepage, clearances and environmental tests stay HOLD until authorised review.
- The active module bypass study is NOT a photovoltaic arc fault interrupter just because an I²R screen has favourable results. Success would require **measured reduction of fault-site energy** in explicit topologies without introducing a worse hazard under switch stuck ON/OFF, diode failed OPEN/SHORT, sensor outage, wet/frame leakage and inverter backfeed.
- Do not start a recurring GPU workflow or a 1bn GPU job by default. Before real CUDA testing, obtain owner approval, verify GPU online state and actual CuPy kernel execution and cap RAM/time; report failure rather than false success.
- Any model class that lacks calibrated physics must state "UNSUPPORTED" or "NEEDS_LAB"; no universal percentage safety claim from a Cartesian enumeration.

**Definition of Done for THIS V11 D4 scope package:** publicly reviewable billion-index schema and virtual-Kuiper address tests; bounded verified CPU witness/receipt; animation viewer using actual law and limited memory; Phase II graph/experiment schema samples; prepared—but not run—manual CuPy workflow; numerical and copyright CI passing; draft PR only. **One billion high-fidelity SPICE or GPU simulations are NOT included in this phase.**
