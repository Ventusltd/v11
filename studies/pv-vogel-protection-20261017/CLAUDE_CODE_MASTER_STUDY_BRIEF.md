# CLAUDE CODE MASTER STUDY BRIEF
## Autonomous DC protection for future solar PV — Kuiper/Vogel engineering investigation
**Prepared:** 17 October 2026  
**Status:** research instruction, NOT engineering approval, design certification, installed-equipment specification or evidence of laboratory validation.  
**Active repository:** https://github.com/Ventusltd/v11  
**Working draft:** https://github.com/Ventusltd/v11/pull/6  
**Ancestor research:** https://github.com/Ventusltd/v11/pull/5  
**Source Kuiper law:** https://github.com/Ventusltd/globalgrid2050/blob/main/testcode/202609151339/lib.mjs  
**Product owner's objective:** Solve fault safety for the future of solar PV; do not make this a patent/prior-art project.

# 0. EXECUTION ORDER — READ FIRST

You are the technical orchestrator for an engineering R&D investigation. Use the maximum **actually available** parallel Claude agents responsibly, with five supervisory workstreams, a shared model/evidence graph and adversarial cross-checking; do not invent access to Astra, Fable, agents, model tiers or tools. If a separate Codex/Astra service is really configured, require proof of that configuration and explicit independent outputs before calling it an Astra supervisor. Otherwise label all five as Claude review tracks.

Inspect the repository state, current draft PRs and original Kuiper source before making changes. Continue on the **existing V11 Phase 0 draft branch** 'analysis/pv-vogel-protection-20261017' or a descendant research branch based on it, and keep all changes in draft PRs. PR #6 is stacked on PR #5, not on main. **Never merge, push to main, alter the original PV arc disclosure repo, modify other Kuiper repos, or mutate the frozen historical engineering laboratory.** V11 is the sole writable project repository; Kuiper and the laboratory are read-only sources. Do not change the programme control plane. If the checked-out head or history differs, stop and reconcile before making writes.

Do not remove, bypass or represent that existing certified AFCI, SPDs, fusing, RCD/IMD or other protective systems can be replaced by this prototype. Do not undertake live high-voltage physical work. High-energy/destructive arc testing requires qualified personnel and an appropriately equipped accredited laboratory with a reviewed test method.

Read: Phase 0 README, five-track cross-examination, 'vogel_study.py' and its tests, V11 previous iteration-three design review and 'v11-reference-facts.json', the original open-hardware disclosure (read-only), the actual Kuiper Line Wafer 'lib.mjs' and README, and V11 single-repo authority note. Give every derived model, decision and result a source reference, revision ID, assumption label, and test status.

Do not prioritise intellectual-property novelty. Use existing commercial eFuse, power semiconductor, arc sensor and photovoltaic references as engineering inputs; respect manufacturers' reference-design licences.

# 1. RESEARCH QUESTIONS

Primary question: can an autonomous protection architecture provide substantial reduction in damaging **energy reaching each fault site** in realistic PV systems, without introducing new unacceptable thermal, lifetime, fault-propagation or nuisance-trip risk?

Secondary questions:
- What local isolation can be achieved for a single module, 2-module group, 4-module group, entire string and combiner/MPPT interface, separately and in coordinated hierarchical arrangements?
- What protection zones and electrical source-to-fault paths are physically controllable at each installation point?
- What classes of arc, insulation, abnormal heating, reverse current and loss of control power can actually be sensed, distinguished and interrupted?
- What current, differential switch voltage, common-mode insulation, energy absorption, pulse and gate-drive constraints apply to each candidate topology and failure sequence?
- What minimum hardware cost, dissipation, number of electronic devices, maintainability and field reliability are consistent with the measured risk reduction?
- Is additional protection better done locally, at the string/combiner, or in a hybrid design?

# 2. PROVISIONAL REAL-PLANT REFERENCE FIXTURE

Read the actual fixture under the previous V11 arc study; do not hard-code figures without provenance. As a baseline, the *illustrative*, not independently OEM-verified fixture is:
- 24 strings × 30 modules/string × 660 Wp/module = 720 modules, 475.2 kWp DC.
- One module: Vmpp 38.13 V, Impp 17.31 A, Voc at 25°C 45.75 V, Isc 18.4 A, illustrative Voc coefficient -0.24%/°C.
- 12 nominal MPPT groups of two strings; a 352 kVA inverter; provisional cable routes 78–936 m.
- At -10°C illustrative cold module Voc 49.593 V, 30-module Voc around 1487.79 V. A string's nominal Voc is NEVER automatically the voltage sustained by an opened module-local semiconductor; solve node by node and under faults.
- Existing device counts across the fixture: 720 single-module, 360 two-module, **192 four-module including last partial group**, or 24 string-level protection units. Document partial groups and distinguish pole count and redundant devices from units.
- Only the TWO strings sharing an actual MPPT electrical node can be assumed mutually connected in the nominal model, pending OEM schematic. Do not silently treat 24 strings as one parallel bus.

Obtain real module datasheets, electrical stringing and equipment/earthing diagrams before promotion from illustrative results to any plant-specific conclusion. Make input substitutions simple and reproducible.

# 3. COORDINATED SWARM, NOT INDEPENDENT SILOS

Create an orchestrator evidence board, five supervisor threads, worker queues, review barriers, an assumption/contradiction register, a versioned scenario ledger, and an evidence hierarchy. If tools support a large bounded cohort (up to the user's contemplated 200 parallel workers), orchestrate only real agents within available quotas and controlled compute costs. **Never claim agents were run that were not invoked.**

Every worker receives the SAME up-to-date system fixture, circuit manifest, scenario IDs, parameter units and unresolved contradictions. Shared tasks are divided by physics questions, not arbitrary file names. Supervisors MUST exchange findings and challenge contradictory assumptions at scheduled barriers; for example:
- Detection insists on classifying a parallel arc; topology identifies a parallel feeding path not affected by the requested local opening.
- Electronics proposes submicrosecond off-time; network shows a distant fault wave has not yet reached the sensor and inductance creates a clamp-energy constraint.
- Thermal proposes a lower-Rds device; reliability flags package power cycles and stuck-on failure.
- Probabilistic exploration produces attractive pass fractions; verification rejects any inference of actual failure probability absent field data.
- Engineering model assumes single MPPT bus; owner fixture establishes two-string MPPT grouping and changes expected backfeed.

Review track A — Power systems: PV IV and bypass substrings, conductor/fault zones, actual parallel connections, transmission-line R/L/C, inverter/DC-link, MPPT, earthing, transient energy and alternate feeds.

Review track B — Power electronics: rated controllable interruption, unidirectional vs anti-series MOSFETs, independent redundant stages, body diodes, gate referencing, HV common mode, SOA, clamps/snubbers and thermal/packaging.

Review track C — Detection and controls: current/voltage/HF/temperature sensing, calibrated leakage/insulation measurement, waveform classification, benign noise and shade, pulse delays, protection states, safe latched/recovery behaviour.

Review track D — Kuiper computational research: immutable addressing, versioned model graph, sampling algorithms, automated scenario generation, EMT/SPICE execution, reproducibility, source calibration and error budgets.

Review track E — Independent verification and lifecycle: tests, falsification, standards, hardware-lab boundary, reliability, field service and economic sensitivity. Track E must be permitted to BLOCK advancing unverified claims.

Run coordination barriers after topology models, after first three fault waveforms, after architecture comparisons and before any acceptance report. Keep a named contradiction ledger; never resolve disagreement by vote or number of agents.

# 4. KUIPER / VOGEL — EXACT MATHEMATICAL RULE AND LIMITS

Faithfully preserve the existing Kuiper Line Wafer **addressing** map for an integer permanent case key k >= 1:
  GOLDEN = pi*(3 - sqrt(5))
  r = sqrt(k)
  theta = k*GOLDEN
  x = r*cos(theta); y = r*sin(theta).

This creates a deterministic place in Kuiper for a case. It is an address and navigation geometry, NOT an electromagnetic model, statistical probability, causal relation or optimisation oracle. Permanent keys must not silently be reassigned on reorder. Implement a **versioned append-only identity ledger**; the existing Phase 0 keys 1..2560 stay stable. Add new families with new key ranges, maintain origin/parent relation, model revision and evidence links.

Use a DIFFERENT bounded Vogel construction for 2D experiment design, as in current Phase 0:
  r = sqrt((n-.5)/N); theta = n*GOLDEN
  u = .5+.5*r*cos(theta); v=.5+.5*r*sin(theta).
This bounded sample gives nonuniform coverage of the full rectangular corners and is NOT a probability distribution.

Expand to multiple parameter axes with documented, independently permuted/scrambled 2D pairings or alternative dimension-appropriate space-filling designs. Benchmark against random seeds, Sobol, Latin hypercube and grid/corner-case selections at *equal* model-evaluation budgets. Use explicit deterministic corners, boundary limits, categorical combinations and adversarial extremal conditions. Quantify input-space coverage and how many known synthetic counterexamples each search method misses. Do not declare Vogel inherently better without results.

Separate:
1. geometry/indexing;
2. search/sampling;
3. physical simulation;
4. inferred failure frequencies; and
5. safety validation.
Probability estimates are permitted ONLY with a documented stochastic model and defensible empirical distributions or priors, sensitivity intervals and calibration against observed data. Report unknown probabilities as **unknown**, not invented percentages.

# 5. NETWORK AND PHYSICAL MODEL STACK

Develop an executable model ladder:

M0. Unit/physics conservation checks. SI-unit-typed parameters, energy bookkeeping, expected analytic sanity limits. Distinguish energy delivered to arc from semiconductor dissipation, inductive/capacitive energy and dissipated surge-clamp energy.

M1. PV source, module and string topology. Reproducible single-diode (or justified equivalent) IV characteristics, series substrings, bypass and blocking diodes, temperature, partial shade, irradiance, night, module disconnection, realistic string current. Explain all model limitations.

M2. Topology graph of electrical nodes and controllable protection zones. Every fault location stores potential sources (illuminated modules, other strings at actual common node, DC-link/input capacitors, converter, conductor-to-frame capacitance and external feeds), possible conductive paths and switch/bypass status. Enumerate the state machine before assuming isolation.

M3. Cables and distributed electrical geometry. Model plus/minus conductors, their loop inductance, mutual coupling, resistance, line capacitance including to ground, wave delay and reflected energy with route lengths grounded in V11's provisional physical geometry. Treat distributed-line effects separately from lumped approximations and compare.

M4. Power-electronics and transient model. Inverter DC input capacitance, DC-link state, precharge/anti-islanding/isolation as appropriate, switching topology, MPPT control at its actual timescale, source impedance and backfeed. Model device turn-off, diode recovery, energy absorption, transient Vds, Vgs and junction temperature. Use publicly redistributable models or document licence constraints. A 936 m propagation delay at illustrative epsr=2 (~4.4 microseconds) is a sanity bound, NOT a trip prediction.

M5. Fault models. Separate series DC arcs (including evolving intermittent contacts), parallel arcs, dual-earth faults, resistive hot connectors **before arc ignition**, insulation breakdown with wet/dry changes, reverse feed, open circuit, EMI transients, switch short/open, control brownout and surge. Arc physical assumptions must be calibrated from published experimental measurements and ultimately independent laboratory traces; do not mistake a guessed piecewise resistance for a validated arc plasma model.

M6. Protection strategies. Evaluate no added device with compliant conventional protections; module-only, 2-module, 4-module, string-only, combiner-level, and hierarchical hybrid schemes. For every scheme show sensor placement, exact available protective action, post-trip voltages, source-to-fault energy, clamped energy, recovery and residual hazards.

Prefer open source and reproducible SPICE/ngspice, Python/SciPy and explicit waveform exports. If licenses are available, cross-check selected cases with a second engine such as PSCAD, LTspice, PLECS, Simscape or other recognised EMT platform, but NEVER present an unexecuted solver as validated.

# 6. FAULT CAMPAIGN AND ADVERSARIAL CASES

Start with the existing 10 labels exactly as already defined:
  internal_series_arc
  external_connector_series_arc
  parallel_arc
  insulation_or_earth_fault
  high_resistance_hot_connector
  reverse_feed
  switch_failed_short
  switch_failed_open
  control_supply_lost
  benign_inverter_or_mppt_noise

Add explicit counterexamples:
- series arc upstream and downstream of the switch;
- parallel fault between positive/negative conductors at both near and remote cable ends;
- first and second earth faults, floating and bonded frame alternatives;
- night/no irradiance backfeed; reverse polarity where physically credible;
- shorted and open bypass diode, shaded/failed substring;
- MOSFET body-diode feed when one or both switches command OFF;
- simultaneous module fault and failed-safe-supply, fail-short switch;
- high-resistance connection generating heat but no detectable HF arc signature;
- wet connectors, thermal cycling, surge, partial shading and benign high-frequency inverter transients;
- cold Voc, maximum irradiance/current and actual datasheet tolerances;
- control latency shorter than cable wave travel and energy reflection;
- fail-open and fail-short diagnostics, nuisance trips, reset/restart and remote-field voltage persistence.

For EVERY case record: source voltage/current envelope, fault location and phase, protection boundary, actual topology, all conductive and capacitive feeds, sensing channels, waveform of trip criteria, decision latency, power switch latency, node Vds/Vgs, maximum junction temperature, absorbed/dissipated energy, cumulative energy delivered TO THE FAULT, remaining live exposed conductors, false-safe risk, model uncertainty and reproducible file identifier.

An eFuse's overcurrent response does not prove arc detection. Opening the wrong path can worsen a parallel arc. An open switch does not make illuminated module cells inert. Local semiconductors may see much less or much more than nominal module voltage depending on path; never assign full string voltage by assumption. Account separately for string-wide common-mode insulation relative to frame.

# 7. ELECTRONICS SEARCH — ENGINEER A SYSTEM, NOT A PARTS CATALOGUE

Candidate archetypes to model (do not treat any as approved PV component):
A. IC-integrated low-voltage eFuse, with realistic continuous-current and transient headroom.
B. Analog eFuse/hot-swap controller with externally selected low-Rds MOSFET(s).
C. Bidirectional back-to-back MOSFET stages for module/multi-module.
D. Redundant bidirectional semiconductor stages and/or appropriately rated electromechanical isolation.
E. Higher-voltage SiC solid-state breaker, plus clamp/surge coordination, for group/string-level use.
F. Hybrid electromechanical/semiconductor interruption or hierarchical local sensor + remote interrupter.
G. Detection-only sensing at selected locations coordinating certified existing devices.

Review TI TPS1685, Analog Devices LTC4368, relevant Microchip hardware-based SiC eFuse references, Delta HVDC eFuse publications, TI PV arc signal-conditioning references and alternative parts selected by **actual electrical and thermal requirements**, not branding. Verify manufacturer datasheets, orderability, current range, losses, voltage and common-mode limits; observe design-file licence boundaries.

Use separate DC current sensor, HF arc signal chain, voltage/temperature and insulation measurement assumptions. A high-value resistor divider to a frame does not by itself determine calibrated Riso or earth-leakage current. Quantify 0.5%, 1% and lower target conduction losses, EMC rejection, self-consumption, packaging and lifespan, without presenting targets as regulatory acceptance rules.

Do NOT reproduce iteration 3's unverified 1700 V rating for the IMZA65R027M1H; the identified manufacturer device is 650 V. Do NOT reuse 0.1 ohm 1 W current shunt at 17.31 A without accounting for ~30 W dissipation. Reassess circuit from requirements and circuit nodes; do not blindly fix the original layout.

# 8. QUANTITATIVE COMPARISON AND EVIDENCE POLICY

Build a machine-readable architecture comparison for each protectable fault zone:
- coverage: % of enumerated scenarios correctly detected AND safely contained **within the validated test set only**, with denominators and exclusions;
- energy delivered to each fault relative to baseline and uncertainty band;
- maximum relevant node Vds, Vgs, surge/clamp energy and device temperature;
- residual voltage and charge persistence measured at module, section, string, field tails, MPPT/inverter boundaries;
- selectivity and outages per action; false alarms on defined benign trace set;
- nominal power loss at nameplate/STC versus annual kWh model where weather and partial-load data support it;
- total device count and failures' system consequences, comparison of fault-tolerant vs nonredundant arrangements;
- estimated BOM, manufacturing, integration, field service, reliability model and proposed lab cost per configuration;
- evidence grade: algebra / illustrative simulation / validated against trace / independent lab tested / certified. Never blur grades.

Initial acceptance targets must be **proposed engineering targets**, requiring owner/qualified reviewer approval. For instance nominal electrical series loss <=0.5% of STC nameplate is a useful study screen, NOT proof of viability; no claim of 30-year lifetime without data. Do not invent numerical safety reductions or nuisance rates.

Explicitly report Pareto fronts across safety containment, power loss, cost, component count, temperature, coverage and reliability. Do not rank solely by switch speed or lowest resistance. Register non-dominated architectures with reasons why they survive review.

# 9. STANDARDS, AUTHORITATIVE SOURCES AND SAFETY

Make a standards applicability matrix (document reference and clause only where actual licensed source has been examined). At minimum inspect IEC 62548-1 and relevant amendment, IEC 63027 (published series-arc testing scope), IEC 61730-1 and -2 (module safety), IEC 62852 (connectors), IEC 61643-31 (PV DC SPDs), IEC 62109 where relevant to converters, IEC 62446 field tests, applicable BS 7671 sections and UK/international installation contexts, and UL 1699B/NEC 690.12 where jurisdictionally applicable. Also document exclusions, contradictions and change-control dates.

Do not copy copyright-protected IEC, BS standards, textbooks or vendor simulation models into a public repository. Store permitted requirement IDs, documented interpretations, computations and verified source links. If the owner's licensed library is unavailable, label its contents **NOT EXAMINED**, request access and do not fabricate clause citations.

The system model is NOT an alternative to practical HV fault testing and legally required approvals. Request a qualified independent test laboratory for arc, thermal, HV impulse, dielectric, wet leakage, vibration, long-term thermal cycling, ageing, EMC and controlled destructive fault work.

# 10. REQUIRED REPOSITORY ARTEFACTS AND REPRODUCIBILITY

Work under 'studies/pv-vogel-protection-20261017/' in V11 (not main), preferably in the following explicit layout, with changes reviewed before overwriting Phase 0:

- 'claude-study/README.md' — operating instructions, current verified results and uncertainty summary.
- 'claude-study/manifest.json' — programme ID, baseline PR/commit, model versions, source hashes, unit system and scenario-identity algorithm.
- 'claude-study/source-register.csv' — primary source, exact URL, revision/date, access/licence, what its evidence supports.
- 'claude-study/assumptions.json' — measured, assumed, unknown or rejected values with units, origins and bounds.
- 'claude-study/contradictions.md' — challenge, owner, claim, evidence, resolution or explicit unresolved state.
- 'claude-study/topology/' — machine-readable electrical source-node graph, module/bypass/string/MPPT/inverter model, fault-zone pictures and all switch-state tables.
- 'claude-study/models/' — validated individual models, subcircuits, SPICE/EMT cases and open model licenses.
- 'claude-study/experiments/' — append-only scenario IDs, sampling design and input fixture files; include corner cases and baseline controls.
- 'claude-study/results/' — compact indexed deterministic results and diagnostic waveforms with hashes; avoid massive binary commits and respect GitHub limits.
- 'claude-study/proofs/' — SI dimension checks, energy balance, network invariants, source-isolation assertions and automated regression tests.
- 'claude-study/architecture-comparison.csv' — paired tests using the same scenarios, baselines, units and validation grades.
- 'claude-study/standards-matrix.md' — applicability, evidence source and not-reviewed entries.
- 'claude-study/laboratory-validation-plan.md' — independent lab preparation and pass/fail measurement protocol, no dangerous DIY arc instructions.
- 'claude-study/engineering-decision.md' — defend/reject options and exact next experiment needed.
- 'claude-study/supervisory-review.md' — five named review tracks, independent objections, agent execution receipts, disagreement status.

Keep reproducible code, models, scripts and small fixtures in GitHub; publish larger waveforms or heavy simulation data as versioned Actions artefacts or suitable external dataset storage, with links and hashes. Add pinned Python dependencies and a deterministic one-command execution. Separate unit tests from *real* numerical simulation and from externally corroborated physical evidence.

# 11. PHASED BUILD PLAN AND STOP CONDITIONS

**Phase A: initial 1–2 weeks — evidence/physics topology.** Confirm V11 authority, Kuiper law and fixture. Deliver voltage-source and fault-feed maps for one series arc, one parallel arc and one hot connector at a named protection zone. Build a baseline with NO additional eFuse, enumerated failure states and source-to-fault energy accounting. Gate: five supervisors agree topology is electrically coherent; unresolved topology errors BLOCK circuit claims.

**Phase B: weeks 3–5 — validated simulation foundation.** Executable PV module IV, bypass, string, cable and DC-link models; SI unit tests and energy balance; compare against known textbook analytic tests and traceable literature/measurement. Gate: numerical stability, mesh/time-step sensitivity, known-limit tests, independently reviewed model validity. No arc-extinction claims from uncalibrated arc models.

**Phase C: weeks 6–9 — candidate architectures.** Model 1, 2, 4, 30 modules, optional combiner/hybrid; fully annotated electronics, gate control, failure states, SOA and thermal power. Perform paired simulations under identical source/fault conditions. Gate: reject designs that cannot contain a fault or exceed selected physical limits. Provide sensitivity to uncertainty.

**Phase D: weeks 10–13 — Vogel and adversarial campaigns.** Deterministic sampling, negative-control waveforms, extreme cases, side-by-side sampling benchmark. Produce fault-energy comparisons, Pareto options, contradiction register and falsifiable claims. Gate: no probability inference from sample fractions and no safety claim outside tested topology/trace set.

**Phase E: weeks 14–16 — independent review and laboratory programme.** Five cross-examinations and engineering decision with option shortlist or abstention, prototype test schematic if defensible, laboratory readiness, cost/thermal/reliability budget, standards questions and an initial OEM/independent specialist briefing. Do not jump to hardware when Phase B/C fails. These durations are initial planning estimates, NOT an autonomous deadline commitment.

**Stop / abstain when:** source/branch mismatch, missing ground truth, nonphysical circuit path, gross conservation violation, unverified datasheet, no safe interrupt action, severe thermal or off-state overstress, contradictory reviewer evidence unresolved, cost/time overrun without authorisation, or unsupported external lab/certification claim.

# 12. FIRST CLAUDE EXECUTION CYCLE — DO THIS BEFORE ANY LARGE SWARM

1. Inspect PR #6 and PR #5 plus Kuiper code; reproduce 11 Phase 0 tests and summary; record live commit SHAs and observed agent/tool availability.
2. Produce an **exact topology/energy source graph** for three selected fault locations: local module series arc, external field-cable parallel arc, and high-resistance hot connector without an arc. Include actual MPPT pairing.
3. Set up a small, minimal running PV-cell/module/string and cable/DC-link model with two independent fault-energy integral checks and sanity tests; call it an illustrative electrical model until validated.
4. Have review tracks A–E individually attack the same three cases, exchange their objections, and record unresolved conflicts in the contradiction register.
5. Compare two physical protective action candidates **against baseline** for each case; if interruption cannot plausibly extinguish the fault, explicitly reject rather than force a positive conclusion.
6. Commit only code and evidence that actually run; keep the PR draft, publish exact CI checks, missing capabilities and a concise engineering decision note. No staged success reports without artefacts.

# 13. DEFINITION OF DONE

This *study phase* is complete only when a qualified reviewer can reproduce at least one fully traced model for each of the three priority fault mechanisms, inspect the exact power path, and compare fault-site energy across at least two protection architectures and an unmodified baseline. Report maximum stresses, residual voltages, uncertainty, model limitations and explicit unsafe/untested cases. Physical effectiveness remains provisional until validated with laboratory data.

The project is NOT complete when: a number of agents finish, tests pass on only arithmetic, a GitHub PR exists, a pretty Kuiper scatterplot appears, a faster eFuse is found, or the team claims theoretical protection from nonphysical simulations.

**Required response after first cycle:** exact repository/branch/commit, real agents/tools used, physical networks implemented, cases simulated, table of fault energy/temperatures/voltages with units and uncertainty, test outcomes, blockers, next experiments and evidence links. If nothing beyond Phase 0 ran, explicitly say so.

**Fundamental principle: don't optimise an eFuse; solve the PV fault-energy containment problem end to end.**
