# V11 D2 — SPICE insulation coordination and module-level protection

**Study date:** 18 October 2026. **Active repository:** Ventusltd/v11, draft research branch stacked on D1 PR #10. Other repositories are read-only.

## 1. Product question and boundaries

Design a protection assembly that can physically fit within or adjacent to a 660 Wp solar module junction box, drawing on the D1 three-bypassed-substring model: 45.75 V Voc, 38.13 V Vmpp, 17.31 A Impp, 18.4 A Isc, and illustrative 30-module/1500 V-class strings. All data are **provisional, not OEM verified**.

Can an *active low-loss bypass inside a substring* protect the local fault while remaining a genuinely low-voltage semiconductor, given the full string common-mode voltage? Can a separate module-output device interrupt faults outside that bypass zone without experiencing intolerable string-class Vds or adding unacceptable heat?

**Do not confuse three independent ratings:**

1. Bypass diode reverse voltage VRRM: normally opposite one illuminated substring (roughly 15 V in the V11 fixture); failure/backfeed cases must be tested before treating 45 V as sufficient.
2. String series blocking diode reverse VRRM or module-output FET Vds: can be the entire reverse-driven string/DC bus voltage in named states, approaching 1500 V in the illustrative system.
3. PCB/module insulation to frame/accessible structure: potentially system-voltage common-mode even if an internal control IC only has 15 V across its pins.

Opening a solid-state switch is not galvanic isolation. A passive blocking diode blocks one direction only, and its nominal VRRM does not establish creepage or clearance.

## 2. Phase D2.1 — actual executable ngspice work package

The file d2_spice_campaign.py generates and optionally runs **15 distinct .op SPICE decks**:

- Six externally imposed module-output OFF boundary states: normal string at MPPT, MPPT collapsed, cold Voc with MPPT collapsed, cold with MPPT at Vmpp, dark module with 29 illuminated cold modules, and a high external DC bus reverse-feed case.
- Four distinct series *blocking*-diode reverse-bias cases: night array and live 1500 V bus; low-array and live high bus; balanced normal source; cold-string reverse exposure.
- Five low-voltage *bypass*-diode and active-shunt circuits with a photovoltaic Norton-source approximation, PV recombination diode, series/shunt resistances, passive Schottky approximation, forced string current and 5 milliohm ON active shunt: normal unshaded, 10% irradiance shaded, shaded active shunt, illuminated active shunt, and dark-active case with passive bypass diode intentionally OPEN.

All circuit assumptions are exposed in the source. These are **DC operating-point tests**, not yet a transistor-gate-drive, destructive fault, distributed transmission-line, hot-junction or physical arc model. The module-output voltage cases deliberately use independent ideal sources to screen plausible electrical node boundary stresses; they do not prove an inverter will create every case in service.

From this folder execute:

    python3 -m unittest -v test_d2_spice_campaign.py
    python3 d2_spice_campaign.py --run --out results

The second command requires a functioning ngspice installation. The workflow pv-d2-ngspice-insulation.yml installs actual ngspice on Ubuntu, executes every deck, checks explicit module-output and series-diode reverse voltage, and archives the exact netlists/logs/JSON/CSV. Generated source without a successful runner execution is **NOT** claimed as simulated.

## 3. Engineering loss and diode-rating kill tests

The 0.5% additional electrical loss research target is 3.3 W for a nominal 660 Wp module. At Impp 17.31 A, added series R must be at most approximately 11.0 milliohm, before controller consumption.

A passive string blocking diode with a hypothetical 0.8 V hot forward drop produces Vf × 17.31 A = **13.85 W** whenever carrying normal current; even 0.4 V gives **6.92 W**. To satisfy 3.3 W from the diode alone would demand Vf ≤ 0.191 V at 17.31 A, with *zero* other added consumption. So a passive series blocking diode is a poor baseline architecture, irrespective of whether its VRRM is 1200 or 1700 V.

A substring bypass diode typically has near-zero forward loss in normal unshaded operation; when one substring is shaded it can carry about 15–17 A and dissipate many watts, requiring real junction-box thermal analysis. An *active* shunt across the substring may bypass without added nominal series conduction loss, but the shunt transistor still requires credible ratings under shorted/open passive bypass, dark-module and common-mode cases.

**Relevant verified manufacturer reference records (not selected products):**

| Item | Publicly documented values | Relevance / hold |
|---|---|---|
| Vishay VT3045CBP / VIT3045CBP PV bypass diode | VRRM 45 V, 2 × 15 A average current circuit and IFSM 200 A; Vf 0.39 V at If 15 A under datasheet test conditions | Local substring reference only; dual-leg sharing and actual junction-box part unknown. Datasheet: https://www.vishay.com/docs/89365/vt3045cb.pdf |
| Vishay EFUSE-800V20AUNI | 800 V/20 A unidirectional SiC eFuse reference with 1200 V semiconductor class and ~10 milliohm total conduction | Architecture reference, not 1500 V PV. https://www.vishay.com/en/landingpage/reference-designs/800V-20A-eFuse/ |
| Vishay EFUSE-800V40ABI | 800 V bidirectional eFuse reference, ~20 milliohm stage | At 17.31 A this is ~6 W before controller heat. https://webapp-qa.vishay.com/en/resources/reference-designs/800V-40A-eFuse |
| Texas Instruments TPS1685 | 9–80 V, 20 A, 3.5 milliohm typical | Potential low-voltage substring control only; NOT module-output switch. https://www.ti.com/product/TPS1685 |
| ST SCT045W17KAG | 1700 V SiC MOSFET, 55 milliohm typical at specified conditions | A **single** such main path produces ~16.5 W at 17.31 A, illustrating thermal/economics difficulty. https://www.st.com/resource/en/datasheet/sct045w17kag.pdf |

Manufacturer data is not approval to use the device in this configuration, and no OEM SPICE models or protected datasheets are copied into V11.

## 4. Phase D2.2 — physically coupled SPICE transients (NOT yet completed)

Create a complete 30-module two-pole netlist with a real 3-substring cell circuit, bypass diode open/short, physically modelled body diodes and bidirectional MOSFET pair, realistic gate driver referenced to its floating source, current sensor and snubber/clamp. Add the true inverter input and DC-link source topology and a calibrated distributed π/RLC cable. Test full sun, shade, cold Voc, dark module, one/two earth faults, backfeed, inverter collapsed, diode failed, MOSFET stuck on/off and loss of drive.

Export for every component and scenario: positive and negative Vds, Vgs, VRRM, reverse leakage, If, junction loss, E_clamp, fault-site integral of v(t)i(t), capacitor and inductor energy, voltage to frame, timestep sensitivity and after-trip residual voltage. Include at least two independent models or traces where available. Never claim arc extinction from a resistor or uncalibrated plasma law.

## 5. Physical insulation coordination is a separate qualification track

IEC 60664-1:2020 + AMD1:2025 covers insulation coordination of equipment up to 1500 Vdc and calls for clearance, creepage, and solid insulation rules and tests; exact application to integrated PV module electronics is to be reviewed under IEC 61730-1:2023 and the actual installation/environment. The 60664 published scope also notes that the minimum air clearance tables are not applicable in ionised gases (so a live arc is not 'cleared' by nominal clearance arithmetic).

For every identified boundary D2's output worksheet includes:
- circuit differential or assumed common-mode voltage, and the provenance;
- transient peak/impulse withstand **UNKNOWN**, until EMT surge studies;
- package VRRM/Vds, diode reverse leakage(T), IFSM/I²t, avalanche, MOSFET SOA and fault thermal impedance;
- basic/supplementary/reinforced insulation definition, PCB CTI/material group and pollution degree;
- humidity/condensation, altitude, coating/potting, connector/frame dielectric, wet leakage and ageing;
- actual creepage and clearance in millimetres **TBD**, not fabricated;
- all product/insulation decisions HOLD.

Qualified review must use the licensed applicable IEC table versions and actual materials/altitude/environmental inputs. Laboratory dielectric/impulse, wet leakage, environmental ageing and product approval must follow. ngspice cannot simulate electrical tracking, long-term moisture ageing, moulding cracks, dielectric puncture or the legal meaning of safety certification.

IEC/public references:
- https://webstore.iec.ch/en/publication/107319 (IEC 60664-1:2020+A1:2025)
- https://webstore.iec.ch/en/publication/59803 (IEC 61730-1:2023)
- https://webstore.iec.ch/en/publication/64171 (IEC 62548-1:2023)
- https://webstore.iec.ch/en/publication/27362 (IEC 63027:2023; arc equipment)

## 6. Objective acceptance and stop gates

| Gate | Required real evidence | Status after authoring D2.1 |
|---|---|---|
| D2-OP | 15 ngspice decks execute in CI; source-voltage boundary independent checks agree; logs and source hashes archived | Subject to CI |
| D2-INS | Six voltage/insulation boundaries assessed, with no guessed millimetre spacing; all remain HOLD until material and IEC review | Automated |
| D2-EMT | Coupled transistor/diode/cable/MPPT time-domain models with physical stress, energy balance, measured parameter bounds | NOT DONE |
| D2-FAIL | Bypass open/short, switch stuck, no gate power and earth faults with source-to-fault voltage and current demonstrated | NOT DONE |
| D2-LAB | Competent IEC reviewer and independent insulation, arc, environmental and EMC laboratory programme | NOT DONE |
| D2-PRODUCT | Junction-box PCB/BOM/thermal test and 30-year reliability plan compatible with <3.3 W research target | NOT DONE |

**Decision:** Continue module-level research using the active substring bypass as the low-loss benchmark and the bidirectional string-voltage-rated output device as a more challenging branch. The current practical deliverable is an automated SPICE voltage-stress register, not a working PV protective product. Kuiper keys remain stable and Vogel geometry has no special authority over electrical physics.
