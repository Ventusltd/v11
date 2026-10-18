# V11 PV module active bypass — D3 design and verification record

**18 October 2026 | DRAFT | Engineering evidence grade: generic transistor-level ngspice only.**
**Research branch:** analysis/pv-d3-active-bypass-transient-20261018. **Parent:** V11 D2 draft PR #11, including standards-licensing controls. Main and all prior draft studies untouched.
**Simulator execution:** [GitHub Actions D3](https://github.com/Ventusltd/v11/actions/runs/39133036541) using installed ngspice on Ubuntu. Nine transient decks, twelve Python source/record tests passed, simulator-generated circuit and log receipts archived.

## Product-level objective

Explore semiconductor protection **integrated into the PV module/junction box**, not an external string breaker. A module may consist of three ~22-cell photovoltaic substrings, each with an existing anti-parallel bypass diode. A speculative low-loss enhancement is a controlled electronic bypass **in parallel with a substring**, which would normally be OFF and contribute no additional main-series electrical loss. It could limit a developing substring fault only where the circuit topology and source-to-fault path make that protective action possible; it cannot be assumed to interrupt every module-lead, connector, or external string parallel arc.

The current bench model drives one substring from the inherited *provisional* 660Wp, 17.31A, D1/D2 current/voltage fixture, with 10% or 100% incident irradiance and a prescribed string current. This is a source and forced load scenario, **not a complete PV array/inverter transient**.

## Two topologies compared, including internal MOSFET body diode

**SINGLE:** one N-channel MOSFET with drain at substring minus (0), source/body at substring plus. In this particular orientation, an intrinsic body diode conducts positive substring output toward minus even while gate commanded OFF. This **unwanted normal operation shunt** makes the single MOSFET architecture unsuitable *as drawn*. Reversing the MOSFET orientation swaps the undesirable diode path to the intended bypass path, which can create unwanted current when a substring is shaded and no active control is requested. A single MOSFET must be analysed in both directions, not called universally impossible.

**PAIR:** two identical N-channel MOSFETs arranged **back-to-back with sources tied together** and their gates driven together from the floating common-source reference. The opposed body-diode orientations can block both directions in their OFF state and provide a low-resistance bypass while ON, given *valid real* gate drive, actual manufacturer blocking characteristics and fault conditions. The test uses MOSFET LEVEL=1 KP/VTO surrogate, **not a manufacturer part model**. One ideal floating 0–12V drive, arbitrary parasitic gate capacitances, and a 17.31A forced string load are assumed. The supply insulation and package Vds/Vgs are not qualified.

The forced substring shunt is represented by a two-MOSFET source-to-source electrical netlist, not an electrolytic capacitor, arc plasma, mechanical disconnect or certified insulation system.

## Executed primary numerical findings

| Case | D3 model result | Correct interpretation |
|---|---:|---|
| Single shunt MOSFET OFF, full sun | 0.7168 V substring terminal | Illustrative MOSFET body diode **undesirably bypasses** the normally generating substring in this orientation |
| Opposing pair OFF, full sun | 12.7978 V substring terminal | Normal substring is **not** body-diode-clamped in this test |
| Opposing pair ON, one substring at 10% sunlight | 15.4697 A through active bypass | Gate drive diverts current through the active bypass path |
| Opposing pair ON, 10% sunlight | 1.1965 W dissipated in **both** MOSFETs combined (from -Vsub × shunt current) | Electrical loss screen only. Does not include gate supply, silicon junction transient temperature, snubber, package, PCB or heat-sink dissipation |
| Passive diode in the same ON state | ~0 W | In the approximate model active bypass steals its forward current; no implication this is a reliable thermal-control strategy |

All figures derive from the **synthetic MOSFET and bypass diode** parameters and forced-current state. The previous D2 model gave about 12.55W in the synthetic passive bypass when ON-stage bypass is absent, while the earlier D1 approximation gave about 9.35W. These conflicting diode losses stem from **model assumptions**, and must not be hidden or treated as observed performance. No OEM diode, module geometry or board thermal design has been verified.

## Included adverse tests (explicit status)

The nine case netlists include: paired MOSFET in full sun/partial shade; dark substring with failed-OPEN passive bypass; shaded substring with failed-OPEN bypass; lost gate/auxiliary control; full-sun shunt stuck SHORT; bypass diode failed SHORT; a lone FET held OFF under full sun; and a single FET gated in partial shade. These are **first-order input cases**, not proofs of safe behaviour. Results were generated and archived as machine-readable output and full simulator logs. Their engineering significance must be reviewed individually before proposing that the shunt is fail-safe.

Potential showstoppers:
- A stuck-ON active shunt can deliberately remove a healthy substring's output indefinitely. This is a **power-loss**, diode/cell thermal and potentially fault-routing problem; count the lost substring watt-hours and detect the failure.
- An OPEN passive bypass and lost electronic drive could expose shaded cells to dangerous reverse voltage; the present generic diode model does **not** implement cell avalanche, hot spots or breakdown.
- A failed-SHORT passive bypass makes the substring effectively permanently bypassed; the MOSFET controller may not recover it.
- The MOSFET common source and floating drive can sit at near string-to-frame potential even when **local Vds is 15–20V**. Any gate supply, communications, temperature sensor and enclosure require independent insulation design.
- An active shunt may reduce diode loss but may **not interrupt an arc located outside the protected cell/bypass loop**. There is no real arc ignition, fault discrimination or real inverter source path in D3.

## IEC insulation and licensing control

Public V11 work contains original design descriptions, original SPICE code, electrical observations and public standard identifiers only. No single-user licensed IEC 62548-1:2023 or IEC TS 62738:2018 PDF, page image, normative table, extracted text, watermark/order information, or other substantial protected content is distributed. The existing D2 [standards policy](../product-d2/STANDARDS-LICENSING-POLICY.md) and automated public-release guard remain binding. The CI guard was passed before and after ngspice runs. A licence-guard PASS only means no **obvious** prohibited content was detected; human/contractual review remains mandatory.

The **subsystem electrical rating** question and **insulation-to-frame** question are separate:
- Substring switch local differential Vds/Vgs/diode VRRM, avalanche, leakage(T), safe operating area, gate driver power and thermal.
- Insulation of floating substring electronics, gate driver, sensing and communications to PV frame, other accessible conductors and external test ports. Working and impulse voltage, humidity/condensation, pollution, CTI/material group, coating/potting, altitude, clearances, creepage and ageing remain **UNKNOWN / HOLD**.

IEC 62548-1 and IEC TS 62738 are the owner's licence-protected references for array and utility-scale installation considerations respectively, not an electronic-shunt certification. Applicable IEC 61730 module safety, IEC 60664 insulation coordination and IEC 63027 series-arc function require exact editions and suitably authorised reviews; these additional licensed texts were not supplied to this V11 research. Do not invent clause requirements or clearance/creepage millimetres.

## Next actionable barriers, ranked

1. **Real component physics:** obtain OEM bypass-diode datasheet and a power-MOSFET SPICE model with documented body diode, Rds(on)(T), Qg/Qgd, avalanche, reverse leakage and switching energy; explicitly check per-FET Vds and transient Vgs under OFF/ON, including gate supply loss and brownout. No vendor product approved.
2. **Actual PV reverse-bias/cell physics:** calibrate three-substring module with dark/faulted cells, bypass open and short, reverse avalanche/hotspot and temperature. Never extrapolate the current diode model beyond calibrated range.
3. **Fault-containment proof:** identify an actual in-module series or connector arc location. Place sensors and shunt at explicit schematic nodes; calculate \(\int V_{\mathrm{fault}}(t) I_{\mathrm{fault}}(t)\,\mathrm dt\) with physically valid source paths, not merely shunt loss.
4. **Module-to-frame insulation:** use a qualified safety engineer to establish independently licensed IEC 61730/60664 insulation barrier selections and applicable impulse/dielectric/leakage/environmental tests; no numbers copied from the IEC PDFs to GitHub.
5. **Product economics/reliability:** component count, driver idle consumption, self-powered fail-state behaviour, 30-year humidity/thermal cycling, junction-box form factor, estimated failure frequency and BOM all UNKNOWN.
6. **Kuiper case registry:** append stable new case IDs under the existing governance only once the new physical models are reviewed; no Vogel geometry used as a substitute for circuit correctness.

**Decision:** GO for a manufacturer's MOSFET/body-diode and gate-drive transient investigation of the source-to-source pair. NO-GO for the tested lone MOSFET orientation in a normal PV substring. BLOCK product/safety claims, insulation approval and fabrication until independent physical and dielectric validation.
