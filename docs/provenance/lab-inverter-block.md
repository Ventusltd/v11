# Laboratory provenance — complete 24-string inverter block

This V11 simulation slice does not replace or dismiss the pinned laboratory work. It adapts the laboratory's reference inverter-block boundary and its electrical traversal separation into an independent V11 implementation.

Source repository: `Ventusltd/solar-electrical-topology-analysis-engine-text-based`

Pinned source commit: `d3b4c497144c2c9b3e8f0e82117e7e9abe4672b9`

Primary source paths inspected:

- `src/solar_topology/inverter_block.py`
- `src/solar_topology/array/array_topology.py`
- `src/solar_topology/array/array_routing.py`

Retained laboratory boundary:

- 24 strings;
- 30 modules per string;
- 720 modules;
- 660 Wp generic bifacial reference modules;
- 475.2 kWp DC nameplate;
- 352 kVA inverter;
- 24 physical DC inputs;
- 12 MPPT labels with two strings per MPPT in the generic fixture;
- sequential traversal as physical order;
- leapfrog traversal as alternate modules forward followed by the remaining modules in reverse;
- explicit distinction between topology, field-installed routing, factory leads and inverter allocation;
- incomplete equipment evidence remains visible rather than promoted to manufacturer fact.

V11 additions in this slice:

- interactive browser comparison of the entire 24-string block;
- field-cable, factory-lead, connector, voltage-drop and loss calculations;
- cold string Voc;
- two-wire characteristic impedance, capacitance, external inductance, propagation velocity and route delay;
- interruption envelope `I × Z0` and external magnetic energy;
- Python/JavaScript parity tests;
- deterministic repeated-run tests;
- a sequential overnight property and parity campaign lasting more than six hours in total.

The default module electrical values, conductor resistance fixtures, connector resistance, effective permittivity and route bands are provisional engineering fixtures. The browser exposes the main assumptions for simulation and does not describe the result as project approval or manufacturer-certified performance.
