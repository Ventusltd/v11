# PV arc protection iteration 3: five-track design review
Date: 2026-10-17.
Status: RESEARCH DRAFT ONLY — no claim of safe equipment, certified protection, V11 programme promotion, or independent Astra-agent execution.
Evidence: Ventusltd/pv-arc-protection-circuit at 8c74069d192741f07d36752381e14a39328f002a, Open-Hardware-Disclosure.md.
System reference: Ventusltd/v11 draft PR3 commit 89731abb7a678e1c0e9861e2be34886013a5ad7f, reference/lab_inverter_block_24_strings.json.
Method: five distinct analytical review tracks conducted by one assistant; no access to five actual Astra agents.

## Review 1: semiconductor and circuit topology — P0 HOLD

The disclosure calls Q1/Q1B dual 1700 V SiC MOSFETs in series; its named part IMZA65R027M1H is **650 V**, 27 milliohms typical at 25 C and approximately 38 milliohms typical at 175 C. The manufacturer's product site says not for new design. Two same-direction series devices do not inherently block reverse body-diode conduction. An anti-series two-device pair may provide bidirectional off blocking but cannot ensure both polarities under any single shorted-device fault. Redundant bidirectional isolation requires another independent stage or other rated isolating element plus its own failure analysis.

**Important correction:** A switch within an isolated module circuit does not automatically block 1500 V merely because the complete string is rated 1500 V. True Vds depends on placement, diodes, cable/fault network and inverter; a local voltage case may be near 50 V, whereas a fault may impose much more. Common-mode insulation relative to the grounded module frame can still be at full array voltage.

The text-only iteration-2 and iteration-3 ASCII diagrams are ambiguous as to actual Q1/Q1B series connections, source/gate references, bypass paths, and the voltages at OUT+ and OUT-. One BC327 pull-down is not sufficient evidence of safe independent control of two floating gate nodes. Require full power schematic and netlist, fail-short, fail-open, failed-gate-drive and brownout state tables, actual Vds waveforms, SOA and creepage clearance before final device-class selection.

## Review 2: sensing and trip logic — P0 HOLD

0.1 ohm shunt at 17.31 A dissipates ~29.96 W/module; at 20 A, 40 W. At 720 modules this is ~21.6 kW at V11 reference Impp alone. Replace as a **research direction** with a far lower loss, four-terminal Kelvin shunt (e.g. 0.5 milliohm: 0.15 W at 17.31 A; 1.51 W at 55 A) plus instrumentation that passes EMC/fault tests, or separate non-contact DC/HF sensing. A 0.5 mOhm example only illustrates heat/noise trade-offs and is NOT a validated design.

TLV7032 comparator typical propagation time is 3 microseconds; a less-than-1-microsecond full-trip claim cannot be supported by this sensing chain. A 1kohm and 100nF simple lowpass cutoff is 1.59 kHz and attenuates the claimed 30–100 kHz signal (30 kHz to ~5.3% of input amplitude). If used as envelope smoothing AFTER a bandpass/detector this is different; the schematic must show that.

A resistor divider between module negative and frame measures voltage, not independently calibrated leakage current or Riso. Frame potential may float; any measuring reference may itself change the fault conditions. Replace the broad all-fault sun-current-ripple trip gate with separately verified response paths for series arc, parallel arc, insulation failure, reverse current, external cable fault, open-circuit, brownout and no-light backfeed. Require a stated fail-to-trip/nuisance-trip matrix and no automatic rejoin after suspected arcing without risk assessment.

## Review 3: electrical network, fault propagation, switching transients — P0/P1

Sandia research distinguishes series from parallel PV arcs; correct actions can differ. Blindly opening one circuit may not extinguish parallel arc energy. Map exact fault zones and source feeding paths from PV cell strings and bypass diodes through internal switch, factory tails, mated connectors, field cables, MPPT and inverter DC link, including second earth fault and reverse feed.

Pinned V11 draft PR3 has 24 strings, 30 modules/string, 12 nominal two-string MPPT groups and per-string routing lengths 78–936 m; equipment numbers remain provisional. Do not treat all 24 strings as electrically parallel on a single input. If one other string in a two-string group contributes Isc=18.4 A, the hypothetical group contribution is 18.4 A. The unsupported all-strings aggregate would be 23*18.4=423.2 A only if a common electrical path existed.

Study actual mutual L/C route geometry and converter behavior. Illustrative 10uH and 17.31A interruption in 1us gives Ldi/dt 173 V **unclamped**, not a semiconductor Vds prediction; 100uH would give 1731 V. A capacitor at 2.2uF stores 2.475 J at 1500 V, but only 0.00275 J at 50 V. Voltage exposure must be solved from the circuit. Include snubber/TVS re-injection, junction/ground capacitance, bypass diode behavior and inverter DC-link discharge. These are exactly why a complete EMT model is required before a fast interruption time target.

## Review 4: physical implementation, passive components and standards — P0/P1

A real WIMA MKP10 2.2uF 1600VDC part is approximately 35x50x57 mm, larger than the claimed 35x45x under-10-mm complete PCB. This specification cannot simultaneously be true. Recalculate the required clamp energy and select layout-compatible, pulse-rated parts only after nodal transient modelling.

The TVS designated SMCJ1000CA and described as a 1000V clamp needs an exact verified manufacturer orderable part and breakdown/clamping ratings; VRWM, VBR and Vc must not be confused. A 100 ohm 2 W snubber resistor is not automatically rated for joule-scale pulses. A 10Mohm 0.25W resistor exposed to 1500V would dissipate 0.225W and may violate maximum **working voltage** even below its wattage; at 1700V it dissipates 0.289W. Such stresses are conditional on the actual circuit nodes.

Relevant standards have distinct scopes. IEC 63027:2023 is PV DC arc detection/interruption and tests series arcs. IEC TS 62738:2018 is ground-mounted PV power-plant design recommendations, not as labelled in the disclosure an arc-protection technical specification. IEC 62548-1:2023+AMD1:2025 covers array design incl protection. IEC 61730-1:2023 covers PV module construction including junction boxes. IEC 61643-31:2018 covers PV DC SPD; a MOV or TVS alone does not make a qualified Type 2 SPD. IEC 62852 addresses PV DC connectors. Independent qualification and HV laboratory testing will be necessary.

## Review 5: economic, reliability, human safety and claims — P0/P1

For the V11 draft 720-module, 475.2kWp array, 2x27 milliohm MOSFETs at Impp=17.31 A produce 16.18 W/module, about 11.65kW total; 0.1 ohm shunt adds 29.96 W/module, about 21.57kW; combined ~33.22kW (7.0% of nameplate power at that operating point). At hot 38 milliohm MOSFET resistance, losses increase further. This excludes gate supply and switching losses. These numbers invalidate the existing 1.80 USD/module and negligible-loss assumption unless the architecture is materially changed and parts physically selected.

Two hot TO247 transistors dissipating ~8W each need measured thermal resistance and safe enclosure cooling. Manufacturer datasheet unheatsunk junction-to-ambient thermal resistance is around 62 K/W (not suitable for assuming 8W continuous in sealed junction box). Thousands of extra parts may introduce new field failure modes. Design an FMEDA, fault injection and service-replacement plan. Do not claim nuclear-grade, no false alarms, submicrosecond shutdown, automatic healing, full isolation, 70% fire prevention or regulatory compliance without test evidence.

### Recommended V4 research configuration and staged gates

G0: Define measurable safety objectives and protectable zones. State exactly what voltage remains on module internal cells, OUT terminals, external string and inverter link for every fault and time window.
G1: Publish a complete schematic (not an ASCII block diagram), bypass paths, body diodes, reference ground, two switching device directions, isolation requirement, fail-short/off and gate-drive architecture.
G2: Compare unidirectional pair vs true bidirectional pair vs redundant bidirectional stages using actual per-node voltage and transient stress, loss, cost and thermal dimensions.
G3: Eliminate the 0.1ohm series shunt; separate DC current and arc HF observation paths; verify fault classification and safe response on benchtop signals.
G4: Determine snubber and clamp from absorbed energy, not arbitrary values; provide 3D package and IEC insulation envelope.
G5: Simulate full PV-cell -> module -> cable and mating interfaces -> MPPT/DC link -> inverter -> transformer -> grid topology; retain true cable GIS and phase/mutual parameters from V11. Separate load-flow from EMT and safety validation.
G6: Evaluate reset-after-fault, local diagnostics, inspection process, protection coordination and surviving stored energy.
G7: Only then conduct qualified laboratory tests for arc/plasma detection, parallel faults, EMI, temperature cycling, wet insulation, impulses, failed MOSFETs and false-trips.
G8: Complete IEC/UK codes, independent review, insurer/OEM sign-off prior to hardware integration. Preserve existing certified AFCI/SPD/fusing/IMD arrangements during development.

### Sources
Infineon IMZA65R027M1H: https://www.infineon.com/part/IMZA65R027M1H
Datasheet: https://www.infineon.com/assets/row/public/documents/24/49/infineon-imza65r027m1h-datasheet-en.pdf
TI TLV7032: https://www.ti.com/product/TLV7032
WIMA: https://www.mouser.co.uk/en/ProductDetail/WIMA/MKP1T042209FD4MSSD
IEC 63027: https://webstore.iec.ch/en/publication/27362
IEC TS 62738: https://webstore.iec.ch/en/publication/26942
IEC 62548 current: https://webstore.iec.ch/en/publication/110893
IEC 61643-31 scope: https://webstore.ansi.org/standards/iec/IEC6164331Ed2018
Sandia: https://www.sandia.gov/research/publications/details/electrical-simulations-of-series-and-parallel-pv-arc-faults-2013-06-01/
