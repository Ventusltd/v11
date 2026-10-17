# B1 fault-energy research — conditional source-path cut sets

**2026-10-17 | Research draft. NO safety approval, no Astra agents launched.**
One assistant organised five engineering review lenses. No independent qualified electrical reviewer or laboratory has examined these results.

## Sources and assumptions

- This branch descends from draft PR #7 handover at 414e632e04da25f6be13f177cd360438b08c187d. Original data and 128 recovered scratch files remain intact.
- Read-only input: ../fixture/system-fixture.json, labelled ILLUSTRATIVE_PROVISIONAL_NOT_OEM_VERIFIED. The example has 24 strings × 30 modules × 660 Wp, paired S19/S20 on one assumed MPPT, a 936 m S20 home-run and a 600 m S19 home-run, and assumed 6 mm² conductors at 3.39 ohm/km each leg (20°C).
- b1_network.py explicitly represents positive and negative conductor nodes and ideal positive-pole switching locations. Each PV source needs a positive and negative path to the parallel fault. Each path follows wire lengths and the assumed MPPT coupling. MPPT input capacitance remains finite stored energy, NOT a sustained PV source.
- energy_ledger.py independently checks algebraic source PV energy = cable heat + fault load energy with the SAME unvalidated I-V model and an assumed fixed 30 V fault. This is not independent physical confirmation.

## C2 remote and near parallel fault: conditional source-to-fault paths

Action | S20 own modules still feed? | S19 at common MPPT still feeds? | MPPT capacitor path? | Consequence
--- | --- | --- | --- | ---
P0, no new switch | Yes | Yes | Yes | Two PV sources
P1, module-out series switch | No | Yes | Yes | Cannot isolate remote cable alone
P1b, substring switch with bypass | Yes | Yes | Yes | Bypass maintains string feed
P2, inverter-end breaker only | Yes | No | No | Own PV source remains
P2b, array-end breaker only | No | Yes | Yes | Paired PV source remains
P3, both ends | No | No | No | Sustained modelled PV paths cut; residual line energy UNKNOWN

Same source cut-set outcomes for C2-far and C2-near. P1 and P2b have a similar source cut-set under this topology, but are NOT interchangeable in voltage stress, gate drive, common-mode insulation, packaging, cost or reliability. Only the positive pole is being switched in the present graph; earth-fault/second-fault cases are not modelled.

## Illustrative fixed-voltage / fixed-horizon result

An algebraic PV current curve fitted to fixture STC points gives approximately 18.4 A from each string at the assumed fixed 30 V fault. This curve is NOT a physical single-diode model. If sources remain fixed for five seconds:

Action | Current into illustrative fault | Fault power | Five-second sustained PV fault energy
--- | --- | --- | ---
P0 | ~36.8 A | ~1,104 W | ~5.52 kJ
P2 | ~18.4 A | ~552 W | ~2.76 kJ
P2b | ~18.4 A | ~552 W | ~2.76 kJ
P3 | 0 A from modelled PV | 0 W from modelled PV | 0 J from modelled PV

**Critical:** zero from modelled sustained PV paths is NOT zero fault energy, not a guarantee of arc extinction, and not proof the conductor is safe. Existing line capacitance, transient converter feeds and switch/clamp energy are unmodelled. Cable heating is separately conserved in the energy ledger and must not be counted as energy absorbed by the arc. Source S19's loop to a C2-far fault is an assumed 10.38018 ohm at 20°C, so approximately 3.51 kW of the illustrative S19 source output is dissipated in the cables under the screen, NOT the arc.

## Fixture integrity issue

The assumed S20 936 m route in 6 mm² at 17.31 A dissipates approximately 1.90 kW in the positive-plus-negative return pair, around 9.6% of the 19.8 kW STC string power. This fixture is therefore unsuitable as a trusted representative cable design pending verification. Never silently resize the cables without OEM/engineering evidence.

## C1 and C3 limitations

C1loop is moved outside module substring bypass loops; a string-series cut set interrupts the explicitly modelled inverter load path, but C1loop's arc ignition, transient currents, source backfeed, bypass behaviour and voltages are not yet physically simulated. C1in inside a healthy bypass loop remains an unresolved, model-dependent arc case; the previous 15 V ignition threshold and >18.9 V law need reconciliation. Do not promote a generic claim that internal arcs cannot exist.

C3 is an overheating contact with no arc. At 17.31 A, resistances of 0.05, 0.2 and 1.0 ohm produce approximately 15, 60 and 300 W of local heat. The illustrative one-node thermal model assumes 8 J/K heat capacity and 0.25 W/K cooling, and becomes materially nonphysical at large temperature rises. It is not a connector-temperature prediction. No detection scheme, alarm threshold, derate action or electrical isolation for this fault is verified.

## Five coordinated adversarial reviews; one actual reviewer

A. **Network and topology:** Graph cut-set implications for C2 PASS conditionally. Real bypass paths, DC link and inverter state, PV I-V and two-earth-fault physics are missing. B1 complete physical model BLOCKED.

B. **Electronics and insulation:** P1's conditional cut set says NOTHING about required MOSFET blocking voltage, Vds, Vgs, SOA, gate reference or clamps. Open-state voltage can approach string class in particular states. Device selection and thermal qualification BLOCKED.

C. **Detection:** The test gives the protection the fault identity and triggers ideal switching; it contains NO actual detector, false-positive study or classification timings. A hot contact need not create HF arc noise. Detector performance BLOCKED.

D. **Numerical/Kuiper:** Case numbering remains in the original immutable Kuiper ledger; no keys were changed. Algebraic source and cable energy accounting is transparent. Vogel search is NOT a probability estimate and the earlier synthetic benchmark shows corner misses; use explicit corners plus scrambled Sobol for later physical campaigns. PASS only as a conditional numeric check.

E. **Safety/lifecycle:** IEC 63027 series-arc scope does not establish efficacy for parallel arcs or insulation/contact faults. No licensed standards text reviewed here, no OEM datasheets for the actual plant, no device life models, no accredited laboratory testing. Promotion/certification BLOCKED.

## Required next barriers

1. Verify module substring and bypass-diode schematics, real MPPT pairing/DC-side topology, current operating cable designs, insulation-to-frame networks, earth paths, V_BOOST and V_DIRECTBUS cases.
2. Add physical PV source (diode-based), line R/L/C, inverter input and DC-link capacitance, switching transient models, semiconductor body diodes and fault-location energy sinks.
3. Calibrate C1 arc physics to cited measurement records; compare C1loop and C1in without assuming generic self-extinction.
4. Implement sensor chains and failure/benign EMI cases, then paired time-domain studies P0/P1/P1b/P2/P2b/P3 with model error, timestep convergence and source-resolved energy.
5. Independently verify waveforms and residual dangerous node voltages with qualified power-electronics and high-voltage engineers; laboratory tests before protection claims.

## Reproduction

From this barrier-b1 directory:

    python3 -m unittest -v test_b1_network.py test_energy_ledger.py
    python3 b1_network.py > b1-illustrative-results.json
    python3 -c "from energy_ledger import energy_ledger; print(energy_ledger('C2-far','P0'))"

**Status: first conditional topology and algebraic energy subgate delivered; full Barrier B1 and remaining study NOT finished.**
