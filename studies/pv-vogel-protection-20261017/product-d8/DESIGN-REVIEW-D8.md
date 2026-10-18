# D8 — Original Ventus 2025 disclosure versus commanded whole-module bypass

Research only · 18 October 2026 · V11 draft branch. This document contains only original arithmetic, public-source bibliographic information and illustrative V11 module parameters. No private inverter manuals, copyrighted IEC text, private waveforms or certification claims.

## The original proposal was a series interruptor, not an actively shunted string

Original public source: Ventusltd/pv-arc-protection-circuit/Open-Hardware-Disclosure.md, version 1.3.2.1 (published 2 June 2025); pin a9649d2c7d8733ecf5803b94c384206d101460df. It proposes a self-powered analogue arc/insulation fault detection circuit, a 0.1-ohm sensing shunt, two series-connected SiC MOSFETs opened by a PNP gate drive when tripped or without supply, TVS/snubber, and passive bypass diodes.

The original file is NOT an unambiguous electrically verified manufacturer netlist. It does not demonstrate that all healthy modules across a 30-module string will enter a low-impedance shunted state when their gates lose supply. Ordinary passive substring bypass diodes need suitable electrical bias; they do not actively clamp a healthy whole module just because an inverter detects a distant arc. The newer hypothesis is fundamentally different: COMMAND the entire module's full-terminal shunt on all 30 modules.

Original power-part claim also needs correction: the disclosed Infineon IMZA65R027M1H is an officially rated 650 V, 27 milliohm typical at 25 C SiC MOSFET, not a 1700 V device. Manufacturer: https://www.infineon.com/part/IMZA65R027M1H. Two series semiconductor voltage ratings do not simply add in either static or dynamic blocking without independently engineered sharing. Never use nominal rating alone as a design proof.

## Model and assumptions

The executable Python is original_paper_comparison.py with source-corroboration tests in test_original_paper_comparison.py. CI produces a structured JSON receipt. Both use only Python's standard library.

The source-bound provisional publicly modelled 660 Wp module fixture is 45.75 V Voc, 38.13 V Vmpp, 17.31 A Impp and 18.4 A Isc; thirty such modules form a 1143.9 V MPP, 1372.5 V STC open circuit string. No actual calibrated PV IV, real weather, shade, thermal, inverter control, boost energy storage, diode avalanche, switching transient, internal common mode, wet insulation or arc plasma is simulated.

Original normal-path loss ASSUMES the proposed 0.1-ohm current-sensing resistor and both 27milliohm FETs carry all string current. If original hardware places them differently, that series-path analysis must be revised.

The hypothetical NEW entire-module bypass is 5 milliohms hot total across the illuminated entire module. This is not a selected, manufacturer-verified part, and the design must tolerate its own Isc current even when no external load is connected. A 3.3 W extra-loss target is a VOLUNTARY study target, not a standard or device warranty.

For a two-string case, one healthy string is connected to ONE SAME-MPPT paired string whose entire-module bypasses have closed. There is NO input capacitor or inverter load in this static comparison. A separate two-conductor 6mm2 copper home-run exists for each string, using an assumed 3.08 milliohms/metre per conductor at 20 C, with equal 16, 50, 100, 200 and 300m one-way lengths. Do not treat all 24 strings as one paralleled DC bus.

The photovoltaic IV interpolator uses the three stated STC anchors, with uncalibrated near-Isc curve shape. An additional 300m sensitivity sweep varies the interpolation exponent; it does NOT bound a real module design's uncertainty.

## Static findings, with conditional numerical meaning

| Comparison | Result |
|---|---:|
| Original 0.1-ohm sensing path at 17.31A | 29.96 W per module |
| Original 54milliohm total series FETs at 17.31A | 16.18 W per module |
| Original combined under declared same-current assumption | 46.14 W per module |
| Same original combination at 20A | 61.6 W per module |
| New whole-module 5milliohm shunts ON across all 30, isolated from external sources | 2.76 V string open-circuit |
| One module fails to shunt, 29 do shunt, isolated | 48.418 V string open-circuit |
| Hypothetical 150 microfarads at 1143.9V | 98.14 J stored |
| Hypothetical 150 microfarads at 1500V | 168.75 J stored |

The 150 microfarads is an EARLIER RESEARCH assumption, **not** a real inverter input capacitance value. The stored joules do not mean that amount reaches an arc.

Most importantly, the two-string Kirchhoff model shows a peer string can feed a fully shunted neighbouring string. At the assumed 16–300m cable lengths, this illustrative model calculates around 18.3–18.4A from the live peer into the bypassed string. Every bypass path also carries its own 18.4A photovoltaic current; consequently approximately 36.7–36.8A passes through the bypass. The assumed 5milliohm shunt would dissipate approximately 6.7–6.8W in EACH of thirty modules, and the full bypassed string dissipates around 200W in shunts alone. Cable losses are additional and substantially higher for the longer routes. These are not physical rated currents: the results depend strongly on the unverified IV, cable, device and inverter assumptions.

The static cross-feed relationship is:

30 × V_PV(I_peer) − I_peer × R_healthy_cable
  = 30 × R_bypass × (Isc + I_peer) + I_peer × R_bypassed_cable

The term (Isc + I_peer) is the critical shunt-current requirement. A device sized only to 17–20A continuous may be inadequate during coordinated/uncoordinated shutdown. A live partner string can continue feeding an external fault even though the first string's own voltage has collapsed.

## Fault-location requirements and real physical gates

Series arc on an isolated string home run: an all-module shunt may remove most sustaining DC voltage, but true extinction, stray storage and switching-overvoltage still require source-specific transient calculation and calibrated arc I/V.

Parallel arc or series arc on a string sharing an MPPT with a healthy peer: must coordinate BOTH strings or block reverse current before assuming the fault becomes source-free. Do not use a fictional 24-string single parallel DC bus.

Fault INSIDE a module's bypass zone: its illuminated PV cells can still provide energy at the fault even when the external terminal voltage is collapsed.

One shunt stuck OFF or open: that module can still contribute tens of volts. Contradiction with the 2025 original series-switch FAIL OPEN if supply disappears: new fail-safe whole-module short must solve gate self-power, permanent bypass or other safe state and restart.

The model must ultimately include real hot-resistance devices/body-diode directions, gate charge, power supply survival, 16–300m positive AND return cable RLGC, actual paired MPPT converter topology and energy storage, bypass diode failure, multiple source cut-sets, leakage/frame voltage, IEC physical construction and fault-location E_arc = integral(V_arc × I_arc dt). Only ngspice + measured traces can begin addressing transient arc energy. A billion CuPy arithmetic evaluations of these static formulas are NOT a billion successful arc-interruption tests.

## Execution and governance

The next engineering stage is paired-string dynamic SPICE against real manufacturer-verified device and inverter-subsystem models, with all following cases: all shunts OFF, string A shunted only, string B shunted only, both shunted, one module failing open/short, gate power lost, and internal vs external faults. Explicitly measure every PV source, MPPT/capacitor and cable contribution to fault energy. Where physical source data are unavailable, flag UNKNOWN and do not claim validated results. IEC texts and private inverter data stay outside GitHub and public artefacts.

**Decision:** The original 2025 protection intent is relevant. Its series-open/passive-bypass topology is NOT the user's now-stated whole-string-voltage-collapse architecture. The newer architecture deserves further study, but coordinated same-MPPT current management and semiconductor SOA are critical safety gates before a product claim.
