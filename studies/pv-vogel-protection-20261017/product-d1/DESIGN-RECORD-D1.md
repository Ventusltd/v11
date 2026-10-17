# V11 PV protection — Product Design Record D1 (first testable electrical model)

**Document ID:** V11-PV-PROTECT-D1-20261017  
**Status:** DESIGN RESEARCH / HOLD FOR HARDWARE. Not a verified PCB or electrical protection product.  
**Repository:** Ventusltd/v11. Draft branch only, stacked on PR #9; V11 main and source Kuiper repositories untouched.  
**Evidence hierarchy:** arithmetic → provisional five-parameter IV simulation → SPICE/EMT verified → experimentally calibrated → independent laboratory qualified. This release is at level **provisional simulation** only.

## 1. Product objective

Prevent or limit harmful PV DC arc, insulation and connector-overheating consequences at the **module, bypass-protected substring, two-/four-module group, string and inverter-input boundaries**. The engineering criterion is net fault-site energy reduction, safe post-trip voltages and no worse failure under any tested fault topology. This record is a reusable design fragment, **not** a claim that the objective has been achieved.

## 2. Proposed hardware/electrical boundary

The assumed 660 W module contains **three 22-series-cell substrings** with a bypass diode connected anti-parallel to each. The current path and diode orientations are explicitly defined in [protection-node-manifest.json](protection-node-manifest.json).

    J_MINUS -- S1 -- N1 -- S2 -- N2 -- S3 -- J_PLUS -- [SW-M-OUT?] -- TAIL_PLUS
        |-- D1 --|   |-- D2 --|   |-- D3 --|
      Diode anodes at each substring's negative terminal, cathodes at positive terminal.

Every switch in this record is a **candidate placement**, not a selected/qualified semiconductor:
- **SW-SS2-IN** placed inside the S2 cell branch, with D2 bypass remaining connected, may redirect the string current but does not by itself isolate the string or its cable. A dark module, diode fault or other network configuration can change the voltage stress.
- **SW-M-OUT** placed in the module positive output lead outside all bypass loops can open the series string loop but **must not** be classed as a simple 50 V device; PR7 algebra showed potential string-level off-state voltage for particular circuit conditions. Its device rating is unassigned.
- **SW-STR-ARR** at the array end of the field cable removes the local string-source path; it does NOT disconnect paired-string and input-capacitor feeds.
- **SW-STR-INV** at the inverter side removes the paired string and input node; it does NOT disconnect the field cable from its own array.
- **SW-STR-ARR + SW-STR-INV**, a coordinated architecture, is the first credible **topological** containment concept for a remote positive-to-negative cable fault under the assumed two-string MPPT coupling, but needs sensing, communication/coordination, clamp energy, body-diode and post-trip-voltage proof.

The original inverter-side certified protection remains installed in every experimental system; none of these candidate devices is approved for live PV service.

## 3. Product reference inputs (all require OEM confirmation)

Inherited from V11 PR7 provisional fixture (not an actual sourced module datasheet):
- Pmax=660 Wp; Vmpp=38.13 V; Impp=17.31 A; Voc=45.75 V; Isc=18.4 A at STC.
- 3 substrings of 22 series cells each, two half-cell parallel branches assumed. No measured junction-box drawing, bypass diode part number or substring IV curve available.
- The five-parameter single-diode model sets ideality n=1.3 **as a free assumption** to close four equations. It fits four data constraints: I(V=0)=18.4 A; I(V=45.75/3)=0; I(V=38.13/3)=17.31 A; and dP/dV=0 at STC MPP. Fitting script: [fit_stc.py](fit_stc.py) (SciPy required). The exact STC fit does **not** validate cell physics or uniqueness; changing ideality, shunt response or module structure can preserve all four STC points while giving different partial-shading behaviour.
- Fixed fitted substring parameters: Iph 18.402067 A, I0 1.778242293×10^-8 A, series resistance 24.604 milliohm, shunt 219.017 ohm, n=1.3, 22 series cells.
- Temperature behaviour uses an assumed 1.121 eV silicon gap expression and +0.05%/K photo-current coefficient. It is a demonstrator, not an OEM-calibrated environmental model.
- Bypass diode is approximated as **0.45 V threshold + 0.01 ohm incremental resistance**, and dissipated watts must be evaluated from its V and I. No actual high-temperature diode characteristics or thermal coupling are included.

## 4. Actual executable model and first results

Run from this directory:

    python3 -m unittest -v test_pv_module.py
    python3 pv_module.py > pv_module_screen.json
    python3 fit_stc.py > stc_fit.json     # requires SciPy

Results from the first local test, Python 3.13, **16/16 unit tests passing** (GitHub CI must independently reproduce):
- Unshaded at 25°C: Voc **45.750 V**; at 17.31 A: Vmpp **38.130 V**; resulting 660.03 W (source fixture points effectively matched).
- With G=(1000,100,1000) W/m² and the same 17.31 A series current, S2 voltage ≈ **-0.6047 V**, bypass current ≈ **15.467 A**, cell branch ≈ **1.843 A**. Estimated bypass heat: **9.35 W** in this scenario. This is diode heat, not PV module output. Under partial shade the module delivers about **24.815 V / 429.55 W** at 17.31 A.
- Approximate maximum power for that shaded configuration: **429.56 W** around **17.28 A**, under the model assumptions. No real bypass-diode thermal validation.
- Using this alternative assumed temperature law: model Voc about **49.76 V at -10°C** and **40.48 V at 70°C**. The older V11 linear-cold-Voc fixture gave 49.59 V at -10°C. The disagreement is an **assumption/model difference** and must not be reconciled by secretly replacing either; cold rating requires an actual OEM datasheet.
- In a fully dark module carrying positive forced string current the bypass paths conduct; the model does NOT assess reverse avalanche, second earth faults or semiconductor Vds.

**Important engineering consequence:** a protection board installed inside the junction box must either coexist with and survive substantial bypass-diode heat or relocate its power electronics/sensors. It also must not assume that absence of a HF arc signature means absence of connector overheating.

## 5. Quantified initial product requirements — NOT approved acceptance thresholds

| ID | Draft objective or hard objection | Initial evidence | Gate |
|---|---|---|---|
| R-D1-01 | Normal module series power path added dissipation ≤0.5% of 660 W = 3.3 W at 17.31 A; equivalent total added R ≤11 milliohm | I²R arithmetic | Candidate target, not standards limit |
| R-D1-02 | Maintain correct bypass diode current path and quantify peak thermal energy under multiple shading patterns | pv_module.py; scenario S2 shaded 10% | Requires real diode Vf(T,I) and full junction-box thermal |
| R-D1-03 | Every off-state device rated against worst nodal Vds both polarities and common-mode insulation to module frame | PR7 X-001 conditional string-level exposure | No device approved; BLOCK |
| R-D1-04 | Parallel arc at remote string cable must not remain fed by either string or MPPT/Cdc after protective action | PR8 P0/P2/P2b/P3 cut-set tests | No real switch or arc model; BLOCK |
| R-D1-05 | Detect hot resistive connector even without arc noise | PR7/8 hot contact I²R sensitivity | Needs local sensing validation; BLOCK |
| R-D1-06 | Controls fail to a defined safe state under loss of supply, failed MOSFET, bypass diode open/short, and nighttime reverse currents | Unmodelled | BLOCK |
| R-D1-07 | Publish circuit diagrams, component ratings, actual wiring and independent fault-injection tests before any hardware | Product engineering requirement | BLOCK |
| R-D1-08 | Existing IEC/UK PV protections maintained; no patented vendor layout or copyright standards copies published | Safety/compliance requirement | BLOCK |

## 6. Procurement and actual component records

See [component-selection-record.csv](component-selection-record.csv). The list references genuine manufacturer product pages, but **none is approved** for the intended 1,500 V string environment or other specific PV placement.

- TI [TPS1685](https://www.ti.com/product/TPS1685), 9–80 V, max 20 A current limit, 3.5 milliohm typical on-resistance: useful eFuse technology example; **rejected as the module-output string interruptor** under the identified possible string-level Vds conditions. The 20 A protection limit also needs headroom checks against operating and fault currents.
- Microchip [hardware-based high-voltage eFuse](https://www.microchip.com/en-us/tools-resources/reference-designs/high-voltage-hardware-based-e-fuse-reference-design), 400/800 V DC bidirectional architecture, 1 microsecond short-circuit reference response, 12 V auxiliary supply: useful control/power-stage reference, **not certified or rated for a 1,500 V PV string or PV arc faults**.
- Microchip [bidirectional auxiliary eFuse reference](https://www.microchip.com/en-us/tools-resources/reference-designs/high-voltage-bidirectional-auxiliary-e-fuse-reference-design), 400/800 V, 15 A nominal: below the assumed 17.31 A PV nominal module current in this use case. Not selected.
- Actual PV connector, diode, sensors, gate drive, clamp and semiconductor part selection remain **OPEN** until node voltages, transient energy and 30-year packaging effects are calculated.

## 7. Engineering stop/go and next physical proof

**D1 gate:** PASS arithmetic/model repeatability only. BLOCK hardware layout/release, IEC approval, PV site integration and fire risk reduction claims.

Next must include a full schematic/netlist with diode and MOSFET body paths, current-source and bypass diode thermal network, actual source-to-fault nodes for both ends, a known OEM module and inverter electrical input diagram, two-wire distributed cable capacitance and return geometry, calibrated real arc waveforms and energy-to-fault independent checks.

Priority experiments:
1. SW-SS2-IN with D2 healthy, D2 open and D2 short; dark module on powered string and failure-to-close.
2. SW-M-OUT under inverter at Vmpp, collapsed MPPT, near/far parallel arc, and other modules shaded.
3. SW-STR-ARR and SW-STR-INV with assumed two-string MPPT and independently verified converter input capacitor under both boost and direct-bus architectures.
4. Bypass diode and junction-box heat rises under measured partial shading and connector-resistance growth (not an unsafe DIY live arc experiment).

Qualified external laboratory and electrical product safety review mandatory before any energised high-voltage prototype.

**Decision at D1:** A real, versioned and reproducible PV-module/bypass model plus product-component selection records exist. **No working solar DC arc suppression product exists yet.**
