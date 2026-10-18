# V11 D2 — verified SPICE execution receipts / engineering interpretation

**Date:** 18 October 2026. **Status:** ACTUAL NGSPICE RUN / ELECTRICAL SCREEN ONLY.
**GitHub Actions:** https://github.com/Ventusltd/v11/actions/runs/39128256675
**CI artefact:** pv-d2-ngspice-dc-stress-not-certification, GitHub artefact ID 12137321005.
**Runner:** Ubuntu, ngspice 42. **Checks:** 11/11 passed; 15 .op decks actually ran, status SUCCESS. The source deck/log file for every case, JSON numerical results and six-boundary insulation HOLD worksheet were archived.

## Test A — module-output open-switch differential stress

These are externally **imposed** PV-string and inverter node voltages, not a solved real MPPT transient. Independent source algebra and ngspice .op agreed. They show why the MODULE OUTPUT SWITCH MUST NOT be selected from module 50V Voc alone.

| State | Imposed module-out switch Vds (V) |
|---|---:|
| STC 30-module equivalent, MPPT node 1143.9 V | +228.60 |
| STC string positive, MPPT collapsed 0 V | +1372.50 |
| -10°C illustrative cold Voc, MPPT collapsed | +1487.79 |
| -10°C illustrative cold Voc, MPPT at 1143.9 V | +343.89 |
| Dark module, 29 neighbouring cold module open sources, MPPT collapsed | +1438.20 |
| PV side 0 V, reverse external bus at 1500 V | -1500.00 |

Voltage stress is **bidirectional**. A 1200V device fails the 1487.79V screening condition by rating before any transient margin; a nominal 1700V device cannot be approved until the transient overshoot and repeated/avalanche stress are known. No common-mode or real grounded-frame node was simulated.

## Test B — series blocking diode reverse voltage

This is NOT the module's antiparallel bypass diode. Each reverse diode was placed between two separately controlled electrical boundaries. The synthetic diode model has no rated breakdown/surge/thermal validity.

| Imposed electrical nodes | Reverse voltage across series blocking diode (V) |
|---|---:|
| Array 0 V, bus 1500 V | 1500.00 |
| Array 45.75 V, bus 1500 V | 1454.25 |
| Array 1143.9 V, bus 1143.9 V | 0 |
| Array 0 V, bus 1487.79 V | 1487.79 |

**Consequence:** A string-position series blocking diode might need string-class VRRM, whereas a healthy substring bypass diode can be tested around the substring Voc. The extra passive blocking diode's continuous forward loss is a separate commercial obstacle: hypothetical 0.8V at 17.31A equals 13.85W, far above the study's 3.3W extra-loss target. The diode does not grant bidirectional isolation or dielectric approval.

## Test C — substring, bypass and normally-off active shunt

An ngspice one-substring DC circuit with an assumed PV recombination diode/source, one passive Schottky diode and a 5mΩ ON shunt represented by **a resistor** produced:

| Substring case | Substring terminal V | Passive bypass A | Active shunt A (signed pos→neg) | Passive bypass W | Active shunt W |
|---|---:|---:|---:|---:|---:|
| Full irradiance, shunt OFF | +12.7979 | ~0 | ~0 | ~0 | ~0 |
| 10% irradiance, shunt OFF | -0.8114 | 15.4663 | ~0 | 12.549 | ~0 |
| 10% irradiance, shunt ON (5mΩ) | -0.07735 | ~0 | -15.4696 | ~0 | 1.197 |
| Full irradiance, shunt ON (5mΩ) | +0.00545 | ~0 | +1.0900 | ~0 | 0.00594 |
| Dark substring, passive bypass OPEN, shunt ON | -0.08655 | ~0 | -17.3096 | ~0 | 1.498 |

**Promising conditional engineering result:** At fixed 17.31A string current, this resistor-based active shunt could transfer about 15.47A from the shaded passive bypass path and dissipate around 1.20W in the switch instead of the example synthetic bypass diode's 12.55W. With normal generation, the shunt is OFF and adds no nominal series R, apart from parasitic power/control requirements. This **does not** demonstrate an implementable FET: on/off blocking polarity, body diode, gate power, transient safe operating area, cell reverse bias, fast switching, clamp and temperature remain unresolved.

The illustrative diode in D2 predicts about 0.811V forward at 15.47A, differing materially from D1's assumed approximately 0.605V and its 9.35W bypass estimate. A published Vishay PV diode datasheet lists about 0.39V at IF=15A for another part under specified conditions (https://www.vishay.com/docs/89365/vt3045cb.pdf). **The disagreement is proof of model dependence**, not a contradiction to conceal. Replace the synthetic model with a *verified actual OEM junction-box bypass diode* and temperature-dependent manufacturer model before thermal or selection conclusions.

## Six insulation boundaries — all HOLD

The generated results/insulation-boundary-worksheet.csv includes MODULE_OUT_SWITCH_DIFF, BYPASS_DIODE_VRRM, SERIES_BLOCKING_DIODE_VRRM, SUBSTRING_LOGIC_TO_FRAME, MODULE_CIRCUIT_TO_FRAME, SENSOR_COMM_TO_FRAME.

Every record has transient peak = UNKNOWN, rated impulse = UNKNOWN, creepage and clearance = TBD, CTI/material group/pollution/altitude/encapsulation = UNKNOWN, and device/product state = HOLD. The 1500V frame/logic values are **assumed system-class input ratings**, not solved frame-voltage waveforms. This is deliberately non-certifying.

## Immediate product conclusions

- **GO for further simulation** of active substring bypass integrated at the module, with realistic bidirectional MOSFET and bypass diode thermal models.
- **HOLD** for direct module-output protection: must withstand named string-voltage-class differential states in both polarities, voltage surges and bidirectional current; hardware alternatives must also meet <3.3W normal added loss.
- **NO-GO at this stage** for a passive series blocking diode as the primary 17.31A module output element under the 3.3W total loss budget, absent measured extraordinary low Vf and validated thermal architecture.
- **NO-GO for certification claim** from these .op results: physical dielectric, creepage, solid insulation ageing, moisture, partial discharge, EMC, independent PV arc tests and device qualification not performed.

## Next acceptance gates

1. Obtain real module manufacturer IV, topology and bypass diode part; re-fit all PV/diode SPICE models.
2. Simulate **actual** active bypass switch turn-on/off, gate-driver referencing, body diodes, 15–20A conduction and FET thermal under shade/open-bypass fault; add waveform-time energy integrals.
3. Couple the complete module to 30-module string, actual inverter source/capacitor topology, two-wire cable RLC and surge; replace imposed voltages by network solutions and test both normal and reverse fault directions.
4. Determine physical insulation system inputs and interpret the *licensed* IEC 60664-1 + AMD1:2025 and IEC 61730 requirements, with qualified lab dielectric, impulse and wet leakage programme.
5. Extend the original append-only Kuiper scenario registry for a corner-forced physics campaign. No probabilities inferred from geometric sample fractions.

**Evidence grade: electrical operating-point SPICE simulation only, not a working protection product.**
