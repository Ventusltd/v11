# Track E charter and initial attack — independent verification and lifecycle (SUP-E)

**Cycle:** 1 (2026-10-17) · **Role:** supervisor, review track E (brief §3 E, §8, §9, §11) · **Authority:** may BLOCK advancement of unverified claims at barriers B1/B2/B3 · **Status of this file:** review charter and algebra-grade attack; NOT a result, NOT a design approval.
**Fixture:** `fixture/system-fixture.json` (`V11_CYCLE1_SHARED_FIXTURE_v1`, ILLUSTRATIVE_PROVISIONAL_NOT_OEM_VERIFIED).
**Numbers in this file:** grade `algebra`, produced by `review/track_e_screen.py` (sha256 `e9062241de1afdc98064b8c0362c4c53c0723cba21bdd79904d9241e4ca37174`, run `python3 -I review/track_e_screen.py` from `claude-study/`, self-checks pass). Every constant not in the fixture is labelled ASSUMED and listed in §8. The arc law used is the fixture's UNCALIBRATED Stokes–Oppenlander form; every arc number below is therefore ILLUSTRATIVE.

---

## 1. Falsification plan for the three priority cases

The claim under test for every (case, candidate) pair is: **"the candidate reduces the energy delivered to the fault site relative to P0 without a new unacceptable risk."** A claim that survives none of the tests below may not appear in `architecture-comparison.csv` as anything but `REJECTED` or `UNRESOLVED`.

### 1.1 C1 — module-internal series arc inside the SS2 bypass loop (S20/M15)

Topology fact Track A must encode (DERIVED, algebra): the arc is in series with the SS2 cells, *inside* the branch that D2 shunts. D2 (anode N1, cathode N2) conducts only when the branch is reverse-biased; it cannot return the substring's own current around the arc. Therefore the arc current needs the **string loop** as its return path. Two consequences:

| Quantity | Value | Label/grade |
|---|---|---|
| Substring Voc (STC / −10 °C) | 15.25 V / 16.53 V | DERIVED, algebra |
| Max voltage the branch can present to the arc with D2 conducting | 16.98 V (Voc_ss,cold + Vf 0.45 V) | DERIVED (Vf ASSUMED), algebra |
| Fixture arc law minimum voltage, 1 mm gap at I_min = 0.5 A | 18.9 V | DERIVED from fixture law, ILLUSTRATIVE |
| Fixture ignition/minimum series-arc voltage | 15.0 V | fixture ASSUMED |

**Finding E-C1-a (BLOCKING until resolved):** under the fixture's own arc law the C1 arc cannot be sustained at any current ≥ I_min for any gap ≥ 1 mm, with the string closed or open, because 18.9 V > 16.98 V. So with the fixture law, **P0 already shows self-extinction and every candidate shows zero benefit for C1**. With a short-gap minimum arc voltage of order 12–13 V (metallic-contact arcs; value NOT VERIFIED here, see §5), the branch solution flips to a sustained arc at ≈ 13 V carrying the string current (≈ 225 W at STC, up to 1.1 kJ over the 5 s horizon, bounded by the substring's 220 W STC output only when D2 takes the string current). The C1 result is **bimodal on the arc-law intercept**, which the fixture leaves inconsistent (15 V vs 18.9 V). Registered as X-E1 (§7). No C1 energy claim passes B2 until W07's calibration states the intercept with a source.

Falsification tests for C1:
- **F-C1-1 (P1, SW-M-OUT):** FALSIFIED if, after SW-M-OUT opens, any return path for the SS2 branch current still exists (e.g. a shorted D2 in another substring plus frame leakage, or the string loop closed through a second earth fault). With D2 intact and the loop open the arc current is 0 A by KCL; a simulation showing ≥ I_min after opening indicates a modelling error or a path Track A has not drawn.
- **F-C1-2 (all loop-opening candidates P1, P2, P2b, P3 and P0-AFCI):** they all extinguish C1 by the same mechanism (loop open). The energy ratio to P0 is then **E_cand/E_P0 = t_trip,cand / t_trip,AFCI**, a ratio of two ASSUMED latencies (0.1/0.5/2.0 s for P0). Any "x % reduction" for C1 is a tautology of assumed trip times and is PROHIBITED as a result (§2). Only measured detect-to-open times can replace it.
- **F-C1-3 (P1b, SW-SS):** FALSIFIED as a 20 V-class device if D2 is open (ADV-open-bypass-diode-shaded-substring): the open SW-SS then holds 1487.79 V (string cold Voc, fixture) instead of 16.98 V. P1b requires a D2 integrity diagnostic or a device rated for the string.
- **F-C1-4 (detection):** FALSIFIED for string-level DC sensing if the arc runs in the bypass-shunted regime: string current unchanged, string voltage drop ≈ 13 V (1.1 % of 1143.9 V). The 2.5 % current dip (arc in the series path, dynamic resistance proxy ASSUMED) does not exist in that regime.

### 1.2 C2 — parallel arc on the S20 home run (far: 931 m from inverter; near: 5 m)

Sources at the far arc with all candidates closed (DERIVED, ILLUSTRATIVE arc law, 1 mm gap, G = 1000 W/m²): S20 modules via a 10 m loop (V_terminal ≈ 30 V → current-source region, I ≈ Isc = 18.4 A, 536 W into the arc); S19 via 600 m + 931 m (loop 10.38 Ω, V_terminal 220 V, still current-source, 536 W into the arc, 3.5 kW into cables); C_in 150 µF (98 J stored, charge-limited share to the arc 4.9 J, R-limited pulse peak 177 A, L/R rise 105 µs); V_DIRECTBUS DC link 2 mF (1309 J stored, 64.9 J share, τ 12.6 ms). Line energies at 936 m: 0.11 J inductive at Isc, 0.022 J capacitive at Vmpp.

Falsification tests for C2:
- **F-C2-1 (P2, SW-STR-INV alone, far):** FALSIFIED as containment if, after the breaker opens, S20's own modules continue to feed ≥ I_min = 0.5 A into the arc. Algebra says they feed ≈ 18.4 A: P0 = 1072 W → P2 = 536 W, i.e. at most a 50 % reduction of arc power over the horizon (5.36 kJ → 2.68 kJ in 5 s). P2 alone is a **halving, not a containment**, at C2-far; wording must say so.
- **F-C2-2 (P2b, SW-STR-ARR alone):** symmetric: S19 and C_in remain → 536 W + 4.9 J. FALSIFIED as containment.
- **F-C2-3 (P3, both ends):** survives only if (i) both devices receive a trip signal — the array-end device sees a voltage collapse (1144 V → ≈ 30–145 V) and only a +6.3 % current step (17.31 → 18.4 A); the inverter-end device sees a current reversal of 35.7 A magnitude (+17.31 → −18.4 A) — and (ii) the residual energy after both open is ≤ C_in share + line energy ≈ 5 J. Pre-trip energy at an ASSUMED 10 ms trip: 10.7 J. FALSIFIED if either sensor's trip criterion is not met in the simulated waveforms.
- **F-C2-4 (near fault, inverter-end device rating):** FALSIFIED (device unsafe) if the C_in discharge pulse through SW-STR-INV is not survivable: lumped bound with cap ESR/ESL = 0 is 7.2 kA peak, quarter period 36 µs (5 m loop, 3.6 µH). ESR/ESL and bus layout are UNKNOWN → no SW-STR-INV device-rating claim at B2.
- **F-C2-5 (action correctness):** opening the wrong path worsens nothing here only because each string stays a current source (terminal voltage ≤ 220 V ≪ Vmpp). FALSIFIED (worsening) if a candidate's post-trip state raises the arc current (e.g. opening removes a parallel path that had been diverting current from the arc). Must be checked per switch-state row of Track A's table.
- **F-C2-6 (night, G = 0):** sources are C_in and (V_DIRECTBUS) DC link only; P0 energy bound 4.9 J / 64.9 J. A candidate that trips at night must not be credited with "reduction" of a sub-100 J event as if it were a daytime fault.

### 1.3 C3 — high-resistance hot connector, no arc (S20, M12(+)/M13(−))

| R_conn | ΔV at Impp | Power | Quasi-steady ΔT (0.25 W/K ASSUMED) | Energy to 3600 s (bound) | Detectability ratio, string span vs 20 K drift | Ratio, module-lead span | t to 200 °C | t until ΔV = 15 V |
|---|---|---|---|---|---|---|---|---|
| 0.05 Ω | 0.865 V | 15.0 W | 60 K | 49.5 kJ | **0.1** | 179 | beyond ramp | never |
| 0.2 Ω | 3.46 V | 59.9 W | 240 K | 197.8 kJ | **0.4** | 715 | 414 s | never |
| 1.0 Ω | 17.3 V | 300 W | 1199 K | 988.8 kJ (non-physical bound: connector destroyed first) | **2.0** | 3577 | 83 s | 520 s |

String loop resistance 6.358 Ω (DERIVED), 20 K drift band ±0.5 Ω (ASSUMED swing); module lead + one connector 3.56 mΩ, drift 0.28 mΩ. Thermal time constant 32 s (fixture thermal ASSUMED).

Falsification tests for C3:
- **F-C3-1 (string-level electrical detection):** FALSIFIED for all three variants: the ratio is 0.1/0.4/2.0, all < 3. A string-level V/I or resistance estimator cannot see a 50 mΩ connector against cable thermal drift. Any P2/P2b "detects C3" claim is REJECTED unless it uses a different observable.
- **F-C3-2 (module-local 4-wire or temperature):** survives (ratio ≥ 179; ΔT 60 K at 50 mΩ) **only if the sense points span the mated pair**. SW-M-OUT "local terminal voltage" inside the M12 junction box does not span the M12(+)/M13(−) connector unless the sense lead is extended across it. Track C must draw the sense points; otherwise P1 is FALSIFIED for C3.
- **F-C3-3 (action selectivity):** a trip on a 15 W fault removes 19.8 kW of string output. FALSIFIED as "no new unacceptable risk" if the candidate's only action for C3 is a trip; the acceptable action class is alarm + derate + scheduled service, with trip only above a temperature threshold.
- **F-C3-4 (transition to arc):** at 1 Ω the connector reaches the ASSUMED 200 °C damage temperature at 83 s, long before ΔV reaches the fixture's 15 V ignition level (520 s). The physically likely sequence is mechanical/polymer failure → open or series arc in the string path. Energy claims beyond the damage time are bounds, not predictions; a candidate is credited only for what it does **before** 83 s / 414 s.

### 1.4 P1 SW-M-OUT voltage class (X-001) — algebra verdict

Single SW-M-OUT open, string otherwise intact, I = 0 (KVL): V_sw = Σ Voc_module − V_node.

| Condition | V_sw | Label |
|---|---|---|
| Node held near Vmpp by S19/inverter, STC / −10 °C / +70 °C | 228.6 V / 207.8 V / 255.4 V | DERIVED (Vmpp temp coeff ASSUMED), algebra |
| Node collapsed to V_arc ≈ 29 V (far parallel arc, or discharged C_in), STC / −10 °C | 1343.4 V / 1458.7 V | DERIVED, algebra |
| All 30 switches open with perfect simultaneity, node at Vmpp | 7.6 V each | DERIVED, algebra |
| Skew window a 100 V-class part survives in avalanche (E_AS 0.3 J, V_BR 120 V, 17.31 A, ASSUMED) | 144 µs | DERIVED, algebra |

**Verdict:** the 100 V-class assumption is **FALSIFIED** for any single-device opening (local trip, nuisance trip or fail-open) and for the collapsed-node condition even with all 30 open if the collapse is not simultaneous. It survives only as "all 30 open within ≪ 144 µs and the node never collapses", which Track B must then show is achievable with a string-wide signal and no single-device fail-open. The likely field sequence is fail-open → 208–1459 V → avalanche at 2.1 kW → fail-short → silent loss of protection. P1 at 100 V class cannot pass B2 without this sequence being modelled and shown benign.

---

## 2. Evidence-grade policy enforced in `architecture-comparison.csv`

| Grade | Definition (binding) | Minimum artefact |
|---|---|---|
| `algebra` | closed-form from fixture values; no time-domain solution | formula + script path + sha256 |
| `illustrative_simulation` | ngspice/Python time-domain result with the UNCALIBRATED arc law or any ASSUMED component model; network untested against hardware | scenario_id, netlist/script sha256, "NOT modelled" list, two independent fault-energy integrals agreeing within a stated tolerance |
| `validated_against_trace` | the same model reproduces a named, provenance-recorded measured waveform (published or lab) with a quantified residual; applies only to the quantities compared | trace source URL/ID, residual metric, date |
| `independent_lab_tested` | an accredited laboratory ran a reviewed method on the physical prototype; report ID held | lab, method, report ID, pass/fail per item |
| `certified` | a certification body issued a certificate against a named standard edition | certificate number, body, scope |

**Ceiling this cycle:** `illustrative_simulation`. No arc trace is available locally; `validated_against_trace` is reachable only for the electrical network (e.g. a digitised published capacitor-discharge or line-reflection trace), never for arc extinction in cycle 1. Rows in `architecture-comparison.csv` must carry a `grade` column with exactly one of the five strings, plus `trip_time_source` (ASSUMED/MEASURED) and `arc_law` (`fixture_SO_uncalibrated` or the W07 calibrated variant with its source).

**Exact wording for wave-2/3 result statements:** "Under the illustrative electrical model and the uncalibrated arc law, candidate *P* delivered *E* J to the fault in scenario *ID* versus *E0* J for P0, with an ASSUMED detect-to-open time of *t* s; not validated against any measured trace; not a safety claim." A ratio may be printed only with both absolute energies, the assumed trip times and the horizon.

**Prohibited words/phrases in any result, README, decision or PR text:** proven, guaranteed, safe, fail-safe, certified, compliant, meets IEC/UL/BS, validated (unless grade ≥ validated_against_trace with trace ID), eliminates, arc-free, zero nuisance, "x % reduction in fires", "x % safer", probability/likelihood of fault (unless a documented stochastic model exists), MTBF/lifetime/30-year (without field data), sub-microsecond protection, "replaces AFCI/SPD/fuse/IMD".

---

## 3. Lifecycle and economics screen (algebra grade; all constants ASSUMED unless fixture)

| Group size | Units | Dies, anti-series pair | Dies, redundant two-stage | R budget at 0.5 % STC | W per unit at budget | Required unit failure rate for ≤ 1 added string outage/yr (ASSUMED target) |
|---|---|---|---|---|---|---|
| 1 module (P1) | 720 | 1440 | 2880 | 11.01 mΩ | 3.30 W | 159 FIT |
| 2 modules | 360 | 720 | 1440 | 22.03 mΩ | 6.60 W | 317 FIT |
| 4 modules (8/string incl. partial group of 2) | 192 | 384 | 768 | 41.3 mΩ | 12.37 W | 595 FIT |
| 30 modules (P2/P2b) | 24 | 48 | 96 | 330.4 mΩ | 99.0 W | 4756 FIT |
| per substring (P1b) | 2160 | 2160 (unidirectional, D2 intact) or 4320 | — | 3.67 mΩ | 1.10 W | 53 FIT |

Plant conduction loss at the 0.5 % screen: 2376 W; annual ≈ 2.5 MWh (I² duty factor 0.12 ASSUMED) — a screen, not a yield model. Existing mated interfaces: 792 (33 × 24); an inline-lead retrofit of P1 adds 1440 connector ends (new C3-type failure sites: nearly doubles the connector population). Thermal screen at module level: 1.65 W per die in free air at 62 K/W (ASSUMED) → +102 K → Tj ≈ 187 °C in an 85 °C junction box (ASSUMED): **not feasible without a defined thermal path**; Track B must give R_th(j-ambient) for the actual package/box.

**FMEDA sketch (per added series unit; rates UNKNOWN):**

| Failure mode | Immediate effect | Detectability | System consequence |
|---|---|---|---|
| Fail-open (die, bond, solder, connector, driver latch) | P1/P2: string open → 19.8 kW lost until service; P1b: 220 W lost (substring bypassed) | P1/P2: obvious (string at Voc, 0 A); P1b: looks like shade | P1 at 100 V class: open device sees 208–1459 V → avalanche → fail-short (cascade, §1.4) |
| Fail-short (die short, driver stuck-on, gate shorted) | conducts normally | **none without a periodic self-test that opens the device** | silent loss of protection; fleet may be unprotected for years |
| Gate-supply loss / brownout (night, shade, aux fault) | MOSFET off (if normally-off) → string open at every dawn until supply recovers, or on (if normally-on/latched) → no protection | depends on design | nuisance outages or silent loss; P1 needs 720 self-powered supplies |
| Nuisance trip on benign HF/shade/surge | string outage per event | logged | repeated 19.8 kW outages; auto-reclose into a live arc is a hazard (ADV-reset-restart) |
| Sensor drift / offset | missed C3, false C1 | calibration only | undetected heating or nuisance |

Why added series components can raise plant failure rate: every unit is in the string current path; with series-independent failures the string outage rate is λ_string = λ_existing + N_units,string × λ_unit, i.e. **30 × λ_unit** for P1 against 1 × λ_unit for P2, for the same consequence (19.8 kW). P1 must therefore reach a unit failure rate ≈ 30× lower than P2 for parity, before counting 720 gate supplies and 1440 added connector ends. **Information needed and UNKNOWN:** field failure rates of the MOSFETs at the real Tj and cycling profile, driver/supply FIT, connector FIT, nuisance-trip rate on a real benign corpus, service cost per visit, module-level warranty interaction. **No lifetime, MTBF, FIT, availability or cost-per-avoided-fault number is permitted in any deliverable of this cycle; only the required rates above (algebra from a stated target) may be printed, labelled as targets.**

---

## 4. Hardware-laboratory boundary

**This cycle must NOT claim:** arc extinction (any grade above illustrative), nuisance-trip rate, detection probability, device survival of interruption or surge, insulation/creepage adequacy, connector temperature rating, EMC performance, lifetime, standards compliance, insurability, or that any existing certified AFCI/SPD/fuse/IMD can be removed or relaxed.

**Minimum independent-laboratory test list for the shortlisted architecture (scope-level; clauses NOT EXAMINED; accredited laboratory, reviewed method, qualified personnel):**
1. Series-arc detection and interruption per the IEC 63027:2023 published scope (series arcs, ≤ 1500 V DC), and UL 1699B type tests where the jurisdiction applies; include the in-bypass-loop C1 geometry, which the standard's generator may not represent (lab to state).
2. Parallel-arc tests — outside the IEC 63027 abstract's stated scope (series only) → separate reviewed method (load-bank, near/far, both inverter variants), measuring energy to the arc and post-trip residual sources.
3. Impulse withstand and SPD coordination (1.2/50 µs voltage, 8/20 µs current, IEC 61643-31 context) with the device open and closed.
4. Dielectric withstand and wet leakage current (IEC 61730-2 test families) on the integrated junction box / string box.
5. Thermal cycling, humidity-freeze, damp heat (IEC 61730-2 / IEC 61215 families) with device temperature logging.
6. EMC emissions/immunity (IEC 62109 context) plus a recorded benign corpus (MPPT HF, shade steps, surge, reclosure) for nuisance-trip counting.
7. Destructive fault injection: fail-short, fail-open under load, gate-supply loss under load, night reverse feed, C_in discharge pulse into a near short, inductive turn-off at Isc with the full-length loop (667 µH DERIVED) and clamp-energy measurement.
8. Connector/junction-box temperature rise and ageing with the added device (IEC 62852 / IEC 61730 context).

**Repository rule:** no DIY arc-generation, high-voltage or destructive-test instructions of any kind are permitted in this repository; the laboratory plan names measurements and pass/fail criteria only.

---

## 5. Standards applicability expectation for W07

| Document | What the study needs from it | Status here |
|---|---|---|
| IEC 62548-1:2023+AMD1:2025 (ed. 1.1, 2025-12-15, 213 pp; public abstract: PV array design incl. DC wiring, protection devices, switching, earthing) | array DC protection/switching/earthing requirements that any added device must not violate; disconnect/isolation requirement context | NOT EXAMINED (webstore abstract only) |
| IEC 63027:2023 (ed. 1.0, 2023-05-03; abstract: DC arc detection and optional interruption, series-arc test procedures, ≤ 1500 V DC) | series-arc test method scope and response-time concept; confirm parallel arcs are out of scope | NOT EXAMINED (webstore abstract only) |
| IEC 61730-1 / -2 | module construction and safety test families for a junction-box-integrated device | NOT EXAMINED |
| IEC 62852 | connector requirements and temperature/ageing context for C3 and added mates | NOT EXAMINED |
| IEC 61643-31 | PV DC SPD requirements; coordination of any clamp with the existing Type 2 SPD; a TVS is not an SPD | NOT EXAMINED |
| IEC 62109-1 / -2 | converter safety context for a device at the inverter DC input (SW-STR-INV) | NOT EXAMINED |
| IEC 62446-1 | field test/commissioning measurements (Riso, Voc, Isc) that must remain possible with devices installed | NOT EXAMINED |
| BS 7671 section 712 | UK installation context for PV; isolation and switching | NOT EXAMINED |
| UL 1699B | PV DC AFCI type tests (US jurisdiction) | NOT EXAMINED |
| NEC 690.12 | rapid-shutdown voltage/time limits as a reference for residual-voltage targets (US) | NOT EXAMINED |

W07 must write clause numbers only if a licensed copy is examined (none exists here); otherwise NOT EXAMINED. Arc-law calibration expectations for W07: Stokes & Oppenlander, *J. Phys. D: Appl. Phys.* 24 (1991) 26–35 (DOI 10.1088/0022-3727/24/1/006; original NOT fetched — access blocked); the Ammerman/NREL presentation of that law carries a transition current I_t = 10 + 0.2·z_g (z_g in mm) below which the form does not apply — for 1 mm, I_t ≈ 10.2 A, so the fixture applies the law **below its transition current** at I_min and (recalled, NOT VERIFIED) below its measured gap range. Sandia (Johnson et al., 2012) measured parallel-arc voltages 18–22 V at 1.8–8.1 A and states series/parallel HF noise is nearly identical. NREL ESW2019-13 reports experimental arc energy ≈ 10× below the S–O-based calculation. W07's calibration must state the short-gap intercept with a source; E-C1-a depends on it.

---

## 6. Acceptance checklist (applied at B1/B2/B3) and BLOCK conditions

1. B1: Track A source graph lists, per fault node, every source with its direction, including D1–D3 orientation, C_in, DC link (both variants), paired string S19 only, frame capacitance; no 24-string bus.
2. B1: switch-state table enumerates open/closed/shorted/body-diode for every device in every candidate, with post-trip node voltages solved (not assumed) for node-at-Vmpp and node-collapsed.
3. B1: fixture inconsistency X-E1 (15 V vs 18.9 V) resolved by W07 calibration or declared UNRESOLVED with C1 claims suspended.
4. B2: every waveform result carries scenario_id (ledger key), script sha256, "NOT modelled" list, and two independent fault-energy integrals agreeing within 2 % (tolerance ASSUMED).
5. B2: energy bookkeeping separates fault / semiconductor / L–C stored / clamp / conduction and closes against sources within 2 %.
6. B2: time-step and (for the 936 m line) segment-count sensitivity reported; energy integral changes < 2 % on halving the step.
7. B2: paired runs (P0 vs candidate) use identical sources, seeds, steps and horizon; trip time labelled ASSUMED with the value.
8. B2: no candidate credited for C1 beyond F-C1-2; no P2/P2b credited as containment for C2 (F-C2-1/2); no string-level C3 detection credited (F-C3-1); any electrical C3 claim re-run with a ≥ 24 h ramp (Track C O-5).
9. B2: device stress rows (max Vds, Vgs, I, clamp J, Tj estimate) exist for every candidate and every scenario, including C_in pulse for near faults and the single-open SW-M-OUT condition.
10. B2: every named part has a verified datasheet URL, voltage class and access date; IMZA65R027M1H is not reused as 1700 V (X-004); no 0.1 Ω shunt (X-005).
11. B3: `architecture-comparison.csv` has grade/trip_time_source/arc_law columns, denominators and exclusions for coverage, and no prohibited words (§2) anywhere in the deliverables (grep enforced).
12. B3: no probability, FIT, MTBF, lifetime or cost-per-fault number anywhere; Vogel/Sobol/LHS comparison reports missed known counterexamples at equal budget, not pass fractions.
13. B3: `laboratory-validation-plan.md` contains measurements and criteria only, no procedures for generating arcs or applying HV.
14. B3: evidence board receipts list only agents actually invoked; no non-Claude family named.
15. B3: residual voltages at module, section, array end, inverter end and MPPT node reported post-trip for each candidate, with the collapsed-node case.

**BLOCK conditions I will invoke (brief §11 list, made concrete):** source/branch mismatch between evidence board and files; missing ground truth for the arc law (X-E1 unresolved) while a C1 claim is advanced; a non-physical path (substring current returning through its own bypass diode; 24-string bus; DC link feeding through a boost diode in V_BOOST); conservation violation > 2 %; an unverified datasheet or voltage class; a candidate with no safe interrupt action for a scenario presented as "covered"; off-state Vds above the device class in any solved node (§1.4) or Tj estimate above the datasheet maximum; contradictory reviewer evidence left open at a barrier; any claim of lab testing, certification or standards compliance; any DIY arc instruction.

---

## 7. Objections to other tracks (for the contradiction register)

- **X-E1 → Orchestrator/Track A/W07:** the fixture's arc law (≥ 18.9 V at I_min, 1 mm) contradicts its own ignition voltage (15 V) and exceeds the substring's 16.98 V drive, making C1-P0 self-extinguishing by construction and all C1 candidate comparisons void. The law is also applied below its transition current. Blocking experiment: W07 calibration with a sourced short-gap intercept; Track A to run C1 with both intercepts and report the bimodal result.
- **X-E2 → Track A:** the C1 arc has no return path when the string loop is open (D2 cannot circulate the substring's own current); the source graph must show the arc's return path through the string loop explicitly, and the C1 result for every loop-opening candidate is set by assumed trip time only (F-C1-2). Also X-001: a single open SW-M-OUT sees 207.8–255.4 V with the node tracking and up to 1458.7 V with the node collapsed (§1.4) — Track A must solve both.
- **X-E3 → Track B:** (a) SW-M-OUT at 100 V class is falsified for single-device opening (§1.4); state the device class from the solved nodes or require simultaneous string-wide opening with a quantified skew budget; (b) SW-STR-INV must survive the C_in discharge into a near fault (kA-class bound, 36 µs quarter period) — cap ESR/ESL UNKNOWN, request from fixture owner; (c) 1.65 W per die at module level in free air gives Tj ≈ 187 °C (ASSUMED R_th) — the 0.5 % budget is thermally unproven, not just electrically tight.
- **X-E4 → Track C:** (a) string-level electrical detection of C3 is falsified (ratios 0.1/0.4/2.0 < 3); only a sense span across the mated pair or a connector temperature sensor survives; draw the sense points; (b) HF content cannot separate series from parallel arcs (Sandia 2012), so the action selector must use the DC signatures: inverter-end current reversal (35.7 A swing) and array-end voltage collapse for C2, string-voltage drop ≈ 1.1 % with unchanged current for the bypass-shunted C1 regime; (c) the correct C3 action is alarm/derate, not trip — a trip policy makes P1/P2 fail F-C3-3.
- **X-E5 → Track D:** the C1 outcome is discontinuous in the arc-law intercept and the C2 outcome in fault position relative to each switch; space-filling designs must include these as explicit corner/categorical cases and the benchmark must report which design misses them at equal budget; sample fractions remain non-probabilities; paired runs must share seeds, steps and horizon or the comparison is void.

**Cross-track status (read after writing, `review/track-C-charter-and-initial-attack.md`, 2026-10-17 20:30):** Track C independently reached E-C1-a (C1(b) cannot sustain under the fixture law; sustains at ≈ 13 V only under a lower, unsourced intercept) and F-C3-1 (D = 0.05/0.20/1.0 against a 40 K drift; mine 0.1/0.4/2.0 against 20 K — both < 3). Two independent derivations agree; X-E1 and X-008 stay OPEN only on the arc-law source, not on the algebra. Track C's O-2 (first SW-M-OUT to open under C2-far sees ≈ 1332–1448 V) agrees with §1.4 (1343–1459 V). **Track C O-5 addressed to Track E is ACCEPTED:** the 1.0 Ω variant is the pre-failure end point of the ramp, not a steady state (§1.3 already caps it at the 83 s damage time), and any electrical C3 claim must be re-tested with a ramp ≥ 24 h (ASSUMED field-like degradation time scale); added to checklist item 8.

---

## 8. Assumptions added by Track E (for `assumptions.json`)

| key | value | label | used for |
|---|---|---|---|
| vmpp_temp_coeff_per_c | −0.0034 | ASSUMED (fixture Pmpp coeff as Vmpp proxy) | §1.4 node voltages |
| bypass_diode_vf_v | 0.45 | ASSUMED (fixture text) | §1.1 |
| conductor_temp_swing_k | 20 | ASSUMED | C3 drift band |
| connector_damage_temp_c | 200 | ASSUMED (illustration) | C3 timeline |
| mosfet_avalanche_energy_j / mosfet_breakdown_v | 0.3 J / 120 V | ASSUMED (illustration of a 100 V-class part) | §1.4 skew bound |
| r_th_ja_unheatsunk_k_per_w | 62 | ASSUMED (figure quoted in PR5 review) | §3 thermal screen |
| junction_box_ambient_c | 85 | ASSUMED | §3 |
| i2_duty_factor_annual | 0.12 | ASSUMED | §3 annual loss |
| service_target_added_outages_per_year | 1.0 | ASSUMED target (owner to set) | §3 required FIT |
| assumed_trip_time_s_for_prediction | 0.010 | ASSUMED | F-C2-3 pre-trip energy |
| energy_balance_tolerance | 2 % | ASSUMED acceptance tolerance | checklist 4–6 |

Short-gap minimum arc voltage ≈ 12–13 V: **hypothesis, NOT VERIFIED, not used in any number**; W07 to source or reject.
