# D11 — Real ngspice PV terminal-shunt circuits based on actual component part numbers

**Purpose:** move V11 from a million static arithmetic screens to **actual circuit solutions** for
a 660 Wp module's controlled terminal short, a two-MOSFET opposed topology,
the decisive gate-supply-failure test, and two 30-module strings on ONE MPPT.

**Important provenance:** all devices below are real manufacturer part numbers.
However the four executable decks currently use an **author-created, datasheet-
anchored Level-1 MOSFET approximation**, not a manufacturer-verified SPICE
macromodel. The gate driver is a controlled voltage stimulus rather than the
actual UCC27511A model. The two 30-module strings are lumped PV/switch
proxies, never a physical 150V MOSFET connected across 1500V.

## Part selection (manufacturer sources)

| Actual part | Role and manufacturer-published attributes | Validation in these decks |
|---|---|---|
| [Infineon IPT034N15NM6](https://www.infineon.com/part/IPT034N15NM6) | 150V TOLL N-MOSFET; 3.4mOhm **maximum** Rds(on) at Vgs=10V/Tj=25C, specified Id=84A; typical Qg 69nC; Ciss 4.9nF, Coss 1.5nF, Crss 19pF | **Parametric LEVEL1 surrogate**, approximated Cgs/Cgd/body diode, not actual thermal/SOA vendor SPICE |
| [TI UCC27511A](https://www.ti.com/product/UCC27511A) | 4A source / 8A sink gate driver, powered from 4.5–18V; output held LOW under UVLO | **Gate waveform is forced**; failure case tests effect of UVLO-style loss, not actual TI macro |
| [TI TLV7032](https://www.ti.com/product/TLV7032) | Low-power dual analogue comparator; 1.6–6.5V power input; 3us typical delay | Real candidate from original 2025 disclosure; **not yet wired** |
| [ADI LTC3108](https://www.analog.com/en/products/LTC3108.html) | Ultralo-voltage step-up harvester, input as low as 20mV **with a transformer** | Candidate for sunlight-powered recovery; **not yet wired or proven from ~0.1V module** |
| [Littelfuse SMBJ58CA](https://www.littelfuse.com/) | 58V standoff, max 93.6V clamp *at specified surge test* | Candidate transient TVS; not yet wired, NOT continuous PV power sink |

Also consider comparing the lower-loss [100V Infineon IPT015N10N5](https://www.infineon.com/part/IPT015N10N5)
(1.5mOhm maximum under its specified 10V test); its lower voltage
headroom may be unsuitable under switching transients. Device ratings do
not follow merely from dimensions or peak advertised drain current.

**Do NOT substitute a 150V shunt device across the 1500V string.**
Every MOSFET belongs only across its own module's PV+–PV− terminals.
The 30-module aggregate short in test 04 is a mathematical replacement
for THIRTY separately rated local switches.

## Test deck map

- `01_single_150v_shunt.cir` — 660 Wp PV operating near MPP; one
  low-resistance MOSFET shunt closes. Read module voltage and shunt current.
- `02_back_to_back_150v.cir` — two common-source opposing MOSFETs
  to block opposite-polarity body-diode conduction while OFF.
- `03_driver_uvlo_negative_control.cir` — deliberately lose gate
  drive after closing; an ordinary enhancement MOSFET re-opens and
  the module **re-energises**. This is an expected failure result.
- `04_two_strings_peer_backfeed.cir` — 30-module distributed short
  proxies; shunt string A while partner B remains live, then shunt
  both. Observe A's reverse-fed shunt current and bus-voltage reduction.
  Input converter/capacitors are ABSENT; no arcs are modelled.

## Run

```bash
sudo apt-get install ngspice
python -m unittest -v test_spice_structure.py
python run_component_spice.py --output-dir results
```

GitHub Actions repeats all four SPICE transient calculations and stores
the raw simulator logs plus a deterministic receipt. No GPU is needed.
A `D11` failure is a failure of this model/test, **not proof** that
the physical architecture is impossible.

## Missing proof and next circuit iterations

1. Obtain and independently run the **actual manufacturer SPICE models**
   for IPT034N15NM6 and UCC27511A. Manufacturer models are intentionally
   NOT embedded, copied or falsely attributed to this repository.
2. Compare measured and simulated effective R_on versus temperature,
   Vgs and 18.4A own Isc plus 18.4A paired-string reverse current.
3. Validate real gate power while the module output is shorted.
   The original 2025 paper's **>15V PV-terminal sun-gate** cannot use
   that same voltage while the new module shunt holds it below ~0.1V.
   Test LTC3108 *including its specified transformer and source impedance*,
   or a separately illuminated miniature solar cell/harvester.
4. Add inverter input energy, cable L/C, array distributed nodes,
   switching waveforms and unclamped/transient surge voltage. A TVS
   must never be modelled as a continuously rated 660W energy drain.
5. Injection of real PV series/parallel arcs, internal faults, hot
   connectors, shading, insulation faults, gate power disappearance,
   single shunt failures and latch/relay welded state.
6. Hardware thermal and environmental tests in actual junction boxes.
   A modelled voltage collapse does NOT establish safe isolation.

**Source restriction:** this PR uses only independently sourced public
manufacturer attributes, the original public Ventus research paper, and
authored code. User-provided IEC PDFs, private Sungrow/inverter PDFs and
derived confidential data are excluded; no V11 main change.
