# D9 — one million shared stress scenarios: shortlist only

**Research-only, V11 draft PR stacked on D8. The original 2025 Ventus paper is a
provisional open-hardware concept, not a proven implementation.** This study is
not a certification report or DC-arc extinction model.

## Objective

Prioritise **up to three** practical circuit topologies against the publicly
disclosed June 2025 proposal. The new protection objective is to command the
whole illuminated PV module's **PV+–PV− bypass** to lower external source
voltage without opening a high-voltage circuit. **Protective earth/frame is not
an operating DC-current sink.**

The proposed variants include pair-coordinated full-module bypass, pair-
coordinated independently switched substrings, ideal paired string-directional
blockers, optional low-current downstream isolation, and two uncoordinated
negative controls. All six variants receive **the same million sampled cases**.
Output contains **only the top three for further physical testing** and the
**original paper baseline**.

Public source reference: Ventusltd/pv-arc-protection-circuit
Open-Hardware-Disclosure.md, original 2 June 2025 public pin
a9649d2c7d8733ecf5803b94c384206d101460df. D8 original paper audit:
../product-d8/DESIGN-REVIEW-D8.md.

## Execute

From this folder:

    python -m pip install numpy==2.3.5
    python -m unittest -v test_million_topology_screen.py
    python million_topology_screen.py --iterations 1000000 --seed 20261018 \
      --chunk-size 100000 --top 3 --output results/topologies-to-test-vs-2025-original.json

The GitHub Actions PR workflow runs the CPU test suite and the full million
scenarios, publishes the JSON receipt, and deliberately does not access any
CUDA environment, confidential IEC files or inverter manuals.

## What one iteration actually does

A unique synthetic scenario specifies a 30-module string pair on **one
independent MPPT**, copper run length, two illuminated current limits, copper
temperature, effective whole-module hot shunt resistance, second-string
resistance mismatch, uncalibrated PV IV shape, cold/open-circuit voltage
multiplier, turn-on order, activation skew, deliberately injected open-switch
count and a hypothetical reverse blocker on-resistance. The two independent
positive/negative copper home-runs are included in a Kirchhoff crossover
equation. Current from a still-healthy same-MPPT peer flows **into** the
first string shunt and adds to its own photo short-circuit current.

This is a **bounded arithmetic screen**, not a circuit time-domain simulation:
the skew window's estimated shunt heat uses steady backfeed current as an
upper-level approximation, NOT real switching transients. There is no
transmission-line inductance, diode nonlinearity, semiconductor avalanche,
input-bus capacitor, plasma arc, transient inverter boost or controlled gate
source. Fault-source zones outside the bypass loops remain a separate gate.

A different synthetic sample means a different **sampled test input**, NOT
independent empirical validation. One million samples are evaluated for
every candidate; the printed output deliberately suppresses non-shortlisted
controls.

## Conditional original paper benchmark

D8's interpretation of the public 2025 schematic/proposal assumes the
original 0.1-ohm sensing resistor and two 27-milliohm series FETs are all in the
full operating-current path, implying 46.1439594 W/module at 17.31 A. This
is **conditional on that current path**, not measured module loss. In contrast,
the new shunt is normally OFF, so its fault-state I-squared-R wattage must
**not** be compared to the original continuous path wattage as a like-for-like
normal loss. Only additional hypothesised blocker/isolator on-state losses
are included for the new variants. MCU/gate/self-power and diode losses are
unknown.

## Screening and ranking: no probabilities

All ranges and limits are **study stress assumptions**, NOT observed solar
device distributions. In particular:

- String lengths: 16, 50, 100, 200 or 300 m one way.
- Two irradiance-scaled Isc values: 0.25–1.20 times 18.4 A.
- Whole-module equivalent hot shunt resistance: log-uniform 1–12 milliohms.
- Cable temperature: 20–85 Celsius; IV shape: exponent 0.35–2.5.
- Open-circuit voltage factor: 0.94–1.10 times nominal.
- Command skew: 0–20 ms; uniformly injected failures: 0–3 switches.
- Ideal reverse-current blocker; its assumed *conducting* path is
  independently costed at 5–40 milliohms per string.
- Research-only screening ceilings: 10 W/shunt during a fault, 60 V
  residual no-load string voltage. **Neither is an arc-safety threshold.**

Two physical measurements feed the triage: sample share below the heat
ceiling and sample share below the residual-voltage ceiling. An essential
architecture gate excludes designs not commanding **both strings** for a
fault on the shared MPPT bus. The displayed relative **triage score** is a
transparent weighted preference for lower heat, lower residual voltage,
paired-source containment, directional blocking, and lower component count.
It **is not an empirical probability of success** or a reliability estimate.

String reverse-blocking must be implemented in a physically valid manner.
Ideal source-direction blocking upstream of a common bus does NOT stop
the healthy peer feeding a downstream/shared-bus arc. Likewise, switching
both strings removes PV voltage contributions only **after** both respond;
a paired shunt design can see short-term backfeed during command skew.
Actual semiconductor current paths and protection power-down behaviour
must be experimentally substantiated.

## Iterative Kuiper/Furnace follow-on

1. **Iterations:** execute this deterministic 1M-case CPU sweep, reject
   uncoordinated single-string negative controls, retain only shortlisted
   architectures.
2. **Kuiper log:** use the output JSON receipt hash as the immutable study
   record and assign ranked layouts to the existing Kuiper Vogel chart.
   Reuse the established 30-module string animations; do not replace them.
3. **Algorithms:** construct real paired-string coupled differential
   circuit models, matched ngspice circuits, explicit fault locations and
   source-resolved integrals of I_fault times V_fault at the electrodes.
4. **More iterations:** use the user's separate CuPy/CUDA Furnace after
   measured/verified PV curves and realistic component, inverter and cable
   bounds become available. GPU speed does not repair a missing equation.

### Mandatory falsification before claiming PV arc protection

- Identify fault side of every switch, shunt and string blocker.
- Quantify external series-arc versus parallel-arc energy at the fault.
- Include energy from inverter/DC-link capacitor and active converter sources.
- Inject internal module arcs and earth insulation faults independently.
- Model reverse bias, hotspot temperature and real manufacturer SOA, body
  diodes, voltage withstand, gate power loss and restart.
- Perform timed switch simulation with cable L/C and clamps, then verify
  experimentally. Source-voltage reduction does not guarantee extinction.

**Confidentiality:** only public Ventus paper, original simulation code and
publicly modelled D8 fixture values are committed. No proprietary IEC PDF,
private inverter material or derived confidential information is published.
