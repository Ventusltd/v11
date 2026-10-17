# Five linked, adversarial engineering reviews

**2026-10-17 | V11 draft research | One assistant; no Astra subagents executed.**
These streams challenge each other's assumptions; no review can declare a device safe.

### Track 1 — Electrical topology and fault sources
Question: which independent energy source can feed each fault AFTER a protective device trips? Include illuminated cell substrings and bypass diodes, adjacent series modules, parallel modules sharing one MPPT, external cabling, converter DC link, conductor/frame capacitance, leakage and second earth faults. A single switched module may NOT extinguish a distant parallel arc or leave field leads safe. **Counterchallenge:** the switch's normal off Vds might be module-local, but a specific fault topology may impose string-level stress; neither assumption may be made without a validated netlist. Output gate: circuit nodes, source-to-fault graph and open/closed/shunted state table by fault.

### Track 2 — Sensing and classification
Question: how can one distinguish genuine arcs from MPPT switching without missing hot resistive contacts, quiet insulation failures, night backfeed or dual earth faults? HF arc noise alone may not distinguish series from parallel arcs, and an ordinary overcurrent eFuse does not do so. **Counterchallenge:** a perfectly fast and lossless MOSFET is useless if the detector commands the wrong action. Published Sandia work documents overlap and different mitigation strategies. Output gate: measured true-positive and nuisance-trip corpus; current, voltage, thermal, HF and calibrated Riso/earth leakage pathways separately validated.

### Track 3 — Semiconductors, power and failure tolerance
Question: can actual device SOA, gate-source references, reverse-body-diode directions and junction-box thermal performance withstand the fault waveforms? Back-to-back stages can block both polarities conditionally; neither one stage nor any single fault inherently yields redundant isolation. **Counterchallenge:** a 0.5% conduction-loss screen is not a die-temperature or impulse-survival guarantee. The early BOM's named IMZA65R027M1H is **650 V**, not the claimed 1700 V. Output gate: unambiguous schematic, device rating and modelling, fail-short/open/gate brownout, body-diode routes, calibrated transient waves, package/thermal FEA.

### Track 4 — Distributed network and protection coordination
Question: what is the time-integral of power feeding the arc, and from where? A 936 m route has ~4.415 μs one-way wave propagation at assumed relative permittivity 2. An asserted sub-1 μs *whole-circuit* response is unfounded when sensing a remote fault. **Counterchallenge:** faster switching without energy absorption coordination may create overvoltage or redirect energy. V11 provisional fixture has two strings per nominal MPPT group, NOT 24 connected in one bus. Four-module groups require a partial group per string. Output gate: geometrically consistent R/L/C cable and inverter/DC-link EMT simulations, actual protection zones, source-to-fault energy.

### Track 5 — Assurance, lifecycle and value
Question: does the modification reduce 30-year plant risk and service cost, rather than merely improve response in one experiment? Multiply device counts, expected failures, power losses, false trips, warranty and inspection burden. **Counterchallenge:** a spatial Vogel point is not an observed event, a probability, a reliability forecast or an arc-energy calculation. Output gate: qualified tests with IEC matrix, OEM integration plan, empirical fault distribution, uncertainty and FMEDA and adverse-site lifecycle economics.

## Fault-response cases requiring independent physical models

| Case | Mandatory next proof |
|---|---|
| Internal or field connector series arc | Location coverage, current paths and arc extinction energy |
| Parallel arc | Source-to-fault backfeed and validated non-worsening action |
| Hot high-resistance connection without arcing | Direct hot-contact warning before ignition; arc-only detector insufficient |
| Earth/insulation failure | Calibrated Riso/RCM including second fault; frame divider alone insufficient |
| Reverse feed/night/electronic-supply lost | Bidirectional protection and independent fail-state analysis |
| MOSFET failed-open or short | Electrical consequences, safe diagnosis, redundancy where required |
| Benign MPPT noise or shade | False-trip statistics and resilient coordination |
| Cold Voc and surge | Actual switch/node Vds and common-mode voltage, not group Voc alone |

## Scope boundary / adversarial results

Vogel Phase 0 explores **10 fault labels × 4 levels × 64 2D numeric points = 2560 immutable addresses**. The calculated properties are always the same at a given *sample* for all fault labels, because **fault mechanisms are not yet simulated**. The apparent count passing the loss screen is therefore **not** a safety pass rate and **not** a probability. The design is consciously incomplete. Do not rank architectures by lower nominal power losses alone: zone coverage, wrong-trip risk, package thermal load and short-circuit/earth faults may reverse the trade-off.

**Next executable step:** draw versioned complete PV circuits and explicitly enumerate energising sources for one chosen series arc, one parallel arc and one high-resistance connector. Only then attach SPICE/EMT and laboratory measurements to Kuiper keys. Use measured event-frequency distributions—not a geometric point layout—to estimate quantitative safety benefits.
