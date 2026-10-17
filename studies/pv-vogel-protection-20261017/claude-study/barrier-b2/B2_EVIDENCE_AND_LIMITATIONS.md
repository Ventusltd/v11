# B2 — provisional time-domain PV fault energy and switching sensitivity

**2026-10-17 | Research-grade model only | NOT an electrical protection certification, qualified arc model, or real hardware simulation.**

## Source and execution

- Parent: V11 [draft PR #8](https://github.com/Ventusltd/v11/pull/8), stacked on Claude cycle 1 draft PR #7. Original results and 128 scratch recovery files left unchanged.
- Code: `pv_rlc_time_domain.py`, `test_pv_rlc_time_domain.py` and `parameter_sensitivity.py` in this folder. Run `python -m unittest -v test_pv_rlc_time_domain.py` and `python pv_rlc_time_domain.py` and `python parameter_sensitivity.py`.
- [Latest CI numerical evidence](https://github.com/Ventusltd/v11/actions/runs/39071773598): 13 tests passed, source-resolved JSON receipt and sensitivity JSON receipt archived.
- Actual tooling: **one assistant** authored/reviewed these models, GitHub Actions independently ran the tests. No independently executing Astra/Codex agents or qualified HV engineer was employed.
- Fixture: `../fixture/system-fixture.json` is PROVISIONAL and non-OEM-verified; two strings S19 and S20 are assumed to share one MPPT node. 936m S20 and 600m S19 routes and the 6mm² 20°C copper parameter are *screening assumptions*, not approved cable design.

## Circuit and energy accounting

C2-far (5m from array end) and C2-near (5m from inverter end) are modeled as a two-wire resistive shunt of **0.8 ohm**; this is NOT plasma or an arc current/voltage law. Two PV source branches, S20 and S19, feed the fault through distance-specific lumped RL pairs. An assumed MPPT input capacitor (150 µF nominal in the fixture) can feed the fault through its own cable RL. The model uses an illustrative STC current-source I(V) curve fitted to Isc/Voc/Impp/Vmpp and a **new assumption of 20 µF terminal capacitance per complete string** to regularise dynamics and explicitly conserve PV-side energy. No claim is made that an actual string has that terminal capacitance.

Initial state: PV branches carry 0 A into the new fault (sources initially at Voc), and the MPPT input capacitor starts at fixture Vmpp = 1143.9 V. This is NOT a loaded inverter at operating MPP. There is no real control system: a commanded trip at 3ms instantly and ideally transfers existing branch inductor current to an *imaginary* 1-ohm dissipation loop and excludes that branch from the fault. This provides consistent algebraic energy accounting but **does not prove that a MOSFET, contactor or snubber can physically perform the transfer**. No Vds, Vgs, gate SOA, insulation, EMC, ground faults or actual residual safe voltage calculations are implemented.

Tracked energy terms: source photovoltaic injection + initial MPPT and PV terminal capacitor stored energy = resistive-fault energy + copper losses + assumed switching dump losses + final capacitor and inductor energies. Checks enforce numerical conservation and basic timestep agreement, but neither check validates the chosen physical model or unknown starting conditions. A negative-current/diode-blocking approximation excludes reverse current.

## First paired experiment: C2 at 0.8Ω, horizon 10ms, ideal command 3ms

| Treatment | C2-far fault resistor energy (J) | C2-near fault resistor energy (J) |
|---|---:|---:|
| P0 baseline / no new switch | 55.553 | 126.641 |
| P2 inverter-end only | 49.315 | 120.962 |
| P2b array-end only | 49.687 | 121.043 |
| P3 both ends | 47.401 | 119.057 |

Results are conditional on ALL assumptions above; comparison is **not an empirical improvement percentage**, nor evidence the DC arc was extinguished. Switching both ends eliminates both **sustained** modelled PV source paths after trip, but input/PV-side stored energy can already have arrived at the fault beforehand.

## P3 ideal disconnection timing sweep (fault energy in joules, fixed 10ms horizon)

| Trip command after fault | C2-far | C2-near |
|---|---:|---:|
| 0 ms (unphysical perfectly anticipatory/instant) | 0.000 | 0.000 |
| 0.2 ms | 22.425 | 99.747 |
| 1 ms | 39.497 | 116.859 |
| 3 ms | 47.401 | 119.057 |
| 7 ms | 52.295 | 123.390 |
| Never / P0 baseline | 55.553 | 126.641 |

P3 at 0ms is a numerical boundary/control, **not a physically attainable response**. No detection time, propagation or gate switching is included. The near-end transient's input-capacitor energy can be deposited rapidly, meaning a millisecond-scale switch command may arrive after most energy has been delivered.

## Capacitance sensitivity (unverified, the major source of uncertainty)

With P3 3ms trip and the same fault/shunt/RL model:

- **C2-near:** changing the hypothetical MPPT input capacitance from **50/150/500 µF** produces modelled fault energies of **47.221/119.057/358.874 J**, respectively. These are not a quantitative prediction of any inverter architecture.
- **C2-far:** changing the new assumed PV string-terminal capacitance from **2/20/100 µF** produces **24.959/47.401/141.789 J** of modelled fault energy. No physically grounded PV capacitance or power-converter response exists yet.

The large sensitivities mean the nominal simulation's absolute energy and "benefit" figures **must not be used to select a protection circuit or advertise fault mitigation**. Real equivalent capacitance is frequency-, topology-, temperature- and bias-dependent and cannot be accepted from these arbitrary values.

## Coordinated engineering review (five analytical lenses; no Astra agents)

**A — Electrical topology:** C2 source-cut truth table from PR8 remains coherent under the assumed paired MPPT connection. Lumping an entire 936m pair misses 4.4µs one-way wave propagation, distributed conductor-to-frame capacitance and inter-string current topology under real control states. Complete circuit physical acceptance: BLOCK.

**B — Power electronics:** Tripping is an ideal source diversion to a 1Ω sink. No physically demonstrated MOSFET current commutation, bidirectional blocking, snubber rating or semiconductor transient stress. Very fast local switching alone cannot guarantee fault energy containment. Component selection: BLOCK.

**C — Detection and protection:** An omniscient controller knows the fault immediately but commands switching after a chosen fixed delay. No HF arc measurement, insulation monitoring, hot connector temperature, reverse feed, nuisance-trip set or false-trip probability. Detection validation: BLOCK.

**D — Numerical and Kuiper:** Dynamic Kirchhoff equations have explicit source/storage/dissipation ledgers and 13 passing arithmetic/convergence tests. This model does not yet simulate a single real Kuiper-keyed fault waveform with validated IEC/OEM parameters; model-scenario identity and waveform provenance must be added before claiming full Kuiper integration. Vogel address geometry is unrelated to the physical equations. Conditional numerical result: PASS with limitations.

**E — Independent verification:** There are no accredited high-voltage/arc tests, no actual inverter capacitor or internal module junction-box data, no licensed standards clause-level matrix, and no validated thermal/long-term failure model. Certification, suitability for real PV, and industry-wide fire risk reductions: BLOCK.

## Unresolved priority defects and next action

1. Acquire verified OEM module/substrings/bypass and inverter/MPPT/DC input source/energy data; replace 936m/6mm² example after obtaining a real cable design. Real operating pre-fault MPP voltage/current must be initialised from a solved steady-state electrical network.
2. Replace phenomenological PV fit/assumed terminal capacitance with a validated physical single-diode PV model and documented PV/output capacitance. Separate the inverter input capacitor (on the PV side of boost) from the higher-voltage shared DC link; explore actual V_BOOST and V_DIRECTBUS.
3. Introduce two-wire cable π ladder/distributed travelling-wave model; verify timestep independence against an independently implemented SPICE/EMT solver before treating sub-ms transients as meaningful.
4. Require calibrated series and parallel arc models, and represent high-resistance connector heating *without* presupposing arc noise.
5. Explicitly model switch placement, body diodes, double-earth/reverse backfeed, gate power loss and switching-clamp energy, and show post-trip exposed node voltages and time to discharge.
6. Only after those tasks, compare candidate module/multi-module/string/dual-ended architectures and calculate fault-energy bounds under verified physical uncertainty. Independent electrical engineering review and controlled laboratory tests remain mandatory.

**Decision:** B2 is a reproducible, conditional transient investigation; it is NOT a completed physical Barrier B1 or B2 and does NOT demonstrate a safe prototype. Preserve the original certified protections in any real installation.
