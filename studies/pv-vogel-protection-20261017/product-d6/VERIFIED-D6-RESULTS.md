# V11 D6 — actual ngspice fault-zone results

**18 October 2026 — Research result; NOT a proven solar safety product or arc-extinction test.**

Source: draft PR #15, branch analysis/pv-d6-physical-fault-zone-20261018.
Actual ngspice run: https://github.com/Ventusltd/v11/actions/runs/39138782496
GitHub artifact: pv-d6-actual-ngspice-ohmic-fault-zones-not-arc-certification, ID 12140399318. This contains the 12 exact SPICE decks, logs, a case manifest and a complete JSON measurement receipt. ngspice v42, Python 3.12, 11/11 structural software tests passed.

## What was tested

An illustrative 660 Wp PV module has three explicitly wired photovoltaic substrings (S1, S2, S3), each with an anti-parallel bypass diode. An active **back-to-back MOSFET pair** is connected only across the middle substring S2. One artificially degraded 0.2-ohm connector is either in S2's cell current path **inside** its bypass loop or at the module output **after** all three bypass loops. Cases include full sun/10% sun on S2 and active shunt commanded ON/OFF; clean-contact controls also included.

The module is connected to an **ideal forced 17.31-ampere current sink**, not an electrically solved real inverter. Models use generic photovoltaic, diode and LEVEL=1 MOSFET parameters from D1/D2/D3; no manufacturer semiconductor, cell hot-spot physics or real electric arc.

Integrated observation interval: 60–200 microseconds, i.e. 140 microseconds. Joules are electrical dissipation in the **specific resistor/diode/shunt**, not fire-risk or plasma arc measures.

## Full paired findings from ngspice measured outputs

| Physical fault | S2 illumination | Hot defect OFF energy (mJ) | Hot defect ON energy (mJ) | Electrical interpretation |
|---|---:|---:|---:|---|
| 0.2-ohm INSIDE S2 branch | 100% | 8.38981 | 9.46236 | **+12.78%** hot-contact energy with the shunt ON |
| 0.2-ohm INSIDE S2 branch | 10% | 0.09501 | 0.09466 | Nearly unchanged contact energy |
| 0.2-ohm OUTSIDE module bypasses | 100% | 8.38981 | 8.38981 | Identical external hot-contact energy |
| 0.2-ohm OUTSIDE module bypasses | 10% | 8.38981 | 8.38981 | Identical external hot-contact energy |

For the external fault in this fixed-current model, independent arithmetic gives I²R = 17.31² × 0.2 ≈ 59.93 W. Over 140 µs this is about 8.388 mJ, consistent with the ngspice numerical integration of 8.38981 mJ (numerical integration tolerance).

Why the full-sun internal hot connection is WORSE: at 1000 W/m² with S2 0.2-ohm internal defect and the active shunt ON, the measured S2 cell-branch current rises from **17.310 A to 18.383 A** even though the external module current stays **17.310 A**. A portion of the illuminated S2 photocurrent circulates via the active shunt. That increases resistive heating of the actual defective contact. It also collapses this substring's modelled voltage from 9.336 V to about 0.005 V, costing its normally generated power.

At 10% irradiance, the passive S2 bypass diode dissipated **1.757 mJ** over the observation interval with the MOSFET OFF. Commanding the active bypass ON diverted its current and reduced modelled passive diode energy toward zero, while dissipating approximately **0.168 mJ in the transistor shunt**. This supports a *conditional diode thermal-load reduction*, NOT local contact safety, arc extinction, or less fire risk. In the 0.2-ohm internal defect model S2 cell current remains ~1.84 A with or without the active bypass.

The model may be wrong outside its parameter assumptions. The result is important because it is a **falsifying counterexample** to a general statement that a cheap substring shunt protects every PV connector or internal defect. We should preserve the negative finding rather than choose a favourable simulation case.

## Product architecture decision (research only)

- **NO-GO as a standalone solution for external module-lead hot connectors or series arcs.** The shunt is not physically connected in series with the failed external component, cannot isolate it, and the forced source still delivers 17.31 A.
- **HOLD for an internal full-sun high-resistance failure.** This illustrative MOSFET/shunt network increased the actual defective branch's energy by approximately 12.8%; protection must distinguish circulating PV-cell current and real fault location before commanding a shunt.
- **GO for further engineering study** of bypass-diode thermal reduction under shade, provided OEM diode/FET parameters, terminal Vds/Vgs, gate power, thermal conduction and device fail states are obtained.
- **BLOCK all safety/IEC claims.** SPICE fault energy is not dielectric clearance, equipment insulation coordination, residual safe voltage, an IEC 63027 arc test or a 30-year field reliability prediction.

## Immediate next physical test gates

1. Replace the ideal 17.31 A current sink with a solved PV string + inverter MPPT and the assumed paired-string/backfeed paths, and separately report source-to-fault contributions.
2. Obtain manufacturer-specific MOSFET, bypass-diode and photovoltaic reverse-breakdown curves to simulate hot operation, stuck ON/OFF and loss of auxiliary supply; include actual junction-box thermal impedance.
3. Place calibrated high-resistance connectors at *multiple external terminals* and demonstrate whether temperature sensing provides protective discrimination where current/arc sensing cannot.
4. Introduce **measured arc waveforms** for an internal and external series arc and a parallel cable fault, with a legitimate circuit energy sink and explicit extinction criterion.
5. Feed both positive and negative outputs into the D5 Kuiper/Stars/Faraday evidence relationships as local case IDs, without allocating or re-keying any existing permanent Kuiper key. Large CuPy arithmetic only after physical model validation.
6. Review IEC product and array standards through separately licensed sources and a qualified dielectric and PV safety laboratory. No single-user licensed IEC PDF, text, table or figure is in these public artefacts.

**Reproduction:** run the standard GitHub CI workflow pv-d6-physical-fault-zones.yml on PR #15 or execute the Python D6 generator with ngspice v42. The workflow verifies the full external heat-energy equality and refuses claims of successfully isolated external faults. Source input manifest and ngspice output logs are downloadable from the listed GitHub Actions run.
