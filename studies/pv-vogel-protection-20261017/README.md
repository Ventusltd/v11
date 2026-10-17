# V11 Kuiper/Vogel PV protection study — Phase 0

**Status:** research draft only (2026-10-17). **Not** SPICE, EMT, arc-plasma modelling, a safe power circuit, product recommendation or certified protection.

## Mission

Make the PV fault-management problem reproducible across **one module, two modules, four modules and one whole 30-module string**. Investigate series arcs, parallel arcs, external connectors, developing hot contact resistance, earth/insulation failures, reverse feed, gate supply loss, semiconductors failed-open/short, and inverter/MPPT false positives. The ultimate metric must be energy remaining at each fault site, not only semiconductor switching speed.

## Grounding in the actual Kuiper work

Read-only authoritative source: [Kuiper Line Wafer lib.mjs](https://github.com/Ventusltd/globalgrid2050/blob/main/testcode/202609151339/lib.mjs) and its [README](https://github.com/Ventusltd/globalgrid2050/blob/main/testcode/202609151339/README.md).

The exact immutable-key **address law** is `r = sqrt(key); theta = key * pi * (3-sqrt(5)); x = r*cos(theta), y = r*sin(theta)`. It is an **indexing geometry** and the source explicitly says it does not imply physical meaning. Each unique key in this study refers to one version-1 research scenario.

For *bounded 2D experiment sampling only*, use `r = sqrt((sample-0.5)/64)`, `theta = sample * golden-angle`; map the resulting disk to two illustrative axes **8–24 A** and **1–50 milliohm added series resistance**. This is not a probability distribution, a Monte Carlo simulation or a simulation of any fault class. The disk does not cover Cartesian corner combinations: those must be added explicitly in the EMT/qualification phase.

## Provenance and study arithmetic

Read-only numeric provenance: [V11 earlier draft PR #5](https://github.com/Ventusltd/v11/pull/5), `studies/pv-arc-four-track-20261017/v11-reference-facts.json`, drawn from provisional V11 PR #3. **24 strings × 30 modules × 660 Wp = 475.2 kWp**, 17.31 A Impp, 45.75 V Voc at 25°C, Voc temperature coefficient -0.24%/°C, 12 nominal two-string MPPT groups. No OEM has verified the fixture.

At an illustrative -10°C, module Voc is **49.593 V**. Group Voc is **49.593 × N** for group size N, but **this is NOT the semiconductor Vds**. The latter depends on the actual switching and fault network, as does the full array common-mode voltage relative to frame.

One device per group gives **720, 360, 192 or 24** devices for group sizes 1, 2, 4 or 30. The four-module case correctly includes the final partial group in each 30-module string: 8 devices/string, not 7.5. Illustrative conduction per device `P = I²R`; plant total `P × devices`. Ratio to STC **nameplate** power is not operating efficiency, energy yield, thermal qualification or safety. A 0.5%-of-nameplate *illustrative* loss allowance translates into resistance budgets at Impp using `R_budget = .005*475200 / (devices*17.31²)`.

Separate illustration: at dielectric relative permittivity 2, a **936 m** cable wave travels one way in approximately **4.415 μs**; this is not a coupled-EMT model or a full trip latency. Detection has to precede action and source-to-fault energy must be tracked.

## Reproduce and falsify

From this directory: `python -m unittest -v test_vogel_study.py` and `python vogel_study.py > phase0-summary.json`. The workflow runs the tests and uploads the machine-readable summary. Only the **two-axis numeric trade-off and unique key ledger** are tested; all faults are unmodelled labels.

See [five-track-cross-examination.md](five-track-cross-examination.md) for five interconnected adversarial reviews, missing physics and laboratory gate criteria. There are no independently executable Astra subagent tools exposed in this chat; the five roles are **one assistant's coordinated analytical review**, not five independent model runs.

## Hard limitations and next gates

Passing a static loss threshold proves **nothing** about detecting/extinguishing arcs, isolating both directions, reverse feeds, safe post-opening voltage, EMI, semiconductor SOA, lifetime or nuisance trips. A module switch does not automatically de-energise field conductors or illuminated cells.

G0: complete node-level power schematics/fault-zone/source graphs. G1: validated PV I-V, bypass, cable two-wire L/C, MPPT, inverter DC link in EMT. G2: device body diode, gate-power/driver and fail-short behaviour. G3: series/parallel/ground/thermal detection discrimination with negative examples. G4: energy-to-fault vs protective response. G5: qualified impulse, EMC, climatic, thermal and IEC tests. G6: independent OEM/insurer/laboratory review and measured cost/reliability distributions.

Standards source: [IEC 63027:2023 published scope](https://webstore.iec.ch/en/publication/27362) (series-arc testing), [IEC 62548-1:2023+AMD1:2025](https://webstore.iec.ch/en/publication/110893); research: [Sandia analysis](https://www.sandia.gov/research/publications/details/electrical-simulations-of-series-and-parallel-pv-arc-faults-2013-06-01/), [Sandia experimental testing](https://www.sandia.gov/research/publications/details/series-and-parallel-arc-fault-circuit-interrupter-tests-2013-07-01/); [TI arc analogue front end](https://www.ti.com/tool/TIDA-010955). These links are references, not source-licensed standards copies. Never remove existing certified protection based on this study.
