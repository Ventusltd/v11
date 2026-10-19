# D11 — parasitic capacitance is central to the PV module short

This stage directly responds to the requirement for **parasitic-capacitance
analysis** inside the 660 Wp smart junction box. Real **ngspice** transient
solving is provided by GitHub Actions. The test scripts and decks remain
draft and are not a product design, field-ready electrical plan, or
manufacturer device model.

## Component source and what is real

- **Infineon IPT015N10N5:** real 100 V TOLL power MOSFET candidate;
  official https://www.infineon.com/part/IPT015N10N5. Datasheet
  Ciss 12,000 pF, Coss 1,800 pF, Crss 80 pF at VDS=50 V/f=1 MHz;
  RDS(on) max 1.5 mΩ at VGS=10 V and specified temperature/test
  current. Effective model Cgs 11,920 pF, Cds 1,720 pF, Cgd 80 pF.
  **These are fixed-cap equivalent values**, not a manufacturer
  PSpice model, C(V) curve or actual transient/linear-region SOA.
- **Texas Instruments UCC27511A:** manufacturer publishes a separate
  PSpice transient model at https://www.ti.com/product/UCC27511A.
  Not redistributed, downloaded or claimed to be running here.
  D11 approximates the driver as a 10 V control source, gate resistor,
  pulldown and the real candidate FET's Ciss/Crss.
- **Original 2025 paper:** https://github.com/Ventusltd/pv-arc-protection-circuit/blob/main/Open-Hardware-Disclosure.md
  Sun logic uses PV terminal voltage exceeding ~15 V as its
  sunshine proxy. The new *shorted* module has ~0.09 V terminals, so
  the original terminal-voltage threshold would stop reporting sun.
  An independent solar-side harvester or proven low-input converter is
  a separate, **unsolved** recovery circuit; parasitic charge alone
  cannot sustain DC power with no source.

## Actual dynamic circuits

Generated decks model a Norton/diode PV module anchored at 45.75 V Voc,
38.13 V Vmpp, 17.31 A Impp and 18.4 A Isc; a low-R bypass including
the datasheet-based MOSFET and explicit copper R + board loop L;
module/junction effective PV capacitance, external differential cable
capacitance, PV+ to frame and PV− to frame capacitance; finite gate
resistance/Miller coupling; body-diode surrogate and a resistive load.
Negative terminal is referenced to PE ONLY through a **1 GΩ simulator
reference**; frame current path is capacitive, not an intentional
shunt-to-earth. No real outdoor insulation failure behaviour.

Ten cases compare an open control, progressively larger module
capacitance, slower gate, larger lead inductance, more frame
capacitance and removal of the MOSFET's gate drive. The output retains
actual ngspice measured voltage before and after, FET gate voltage,
peak shunt current, inferred short-path power and integrated energy.
Lumped cap/lead values are hypotheses, NOT manufacturer PV module or
Sungrow inverter characteristics.

```sh
python -m unittest -v test_d11_parasitic_spice.py
python d11_parasitic_spice.py --prepare-only --out results
# with ngspice installed:
python d11_parasitic_spice.py --out results
```

**The 100 µF hypothetical cell/cable-capacitance test fixture contains
~0.0727 J at 38.13 V.** That stored energy can discharge rapidly into
a low-resistance shunt; a module's ~18.4 A photocurrent limit does NOT
bound momentary capacitor current. By comparison, the sourced
IPT015N10N5 1,800 pF Coss stores ~1.31 µJ under a linear-C assumption
at the same voltage. However, real Coss is nonlinear and Qoss is a
more relevant manufacturer charge metric.

## Important failure to prove

Closing the MOSFET and holding its gate at 10 V can collapse external
PV voltage. Disconnecting ordinary gate drive causes gate discharge
and **the shunt opens again**. That is the deliberate negative control.
An auxiliary light harvester or sun-powered latch is a next-stage
actual circuit, not simulated here.

More essential unproved items: real Infineon/driver PSpice model
validation; diode/nonlinear Coss, real RDS(on)(T), current/voltage
stress against pulsed SOA; original self-powered analogue fault
comparator including shorted-module bootstrap; 30-module
coordination; shared-MPPT backfeed; long-cable RLGC and inverter
capacitance; cable-to-frame leakage, thermal hotspots; IEC
compliance and actual arc energy. No secret files or privately
provided standards data are committed. V11 main stays unchanged.

**Iteration plan:** (1) compute parasitic transients; (2) record
source/case/receipt hash in Kuiper; (3) optimise R/L/C and safe
sun-powered gate/actuator choice with SOA guards; (4) run more
physical iterations, later on the user's own CuPy/Furnace if warranted.

## Verified GitHub Actions observations (19 October 2026)

CI succeeded on the actual ngspice CPU runner: 10 transient decks executed
and 9 Python negative-control tests passed. Run:
https://github.com/Ventusltd/v11/actions/runs/39272913713

| Unmeasured PV capacitance fixture | NGSPICE peak bypass current |
|---|---:|
| 1 nF | 18.3583 A |
| 100 nF | 61.1908 A |
| 1 uF | 179.9927 A |
| 100 uF | 1242.152 A |

All four fixtures include additional cable, device and frame capacitance.
The 100 uF / 50 nH case showed V_module=-2.3153 V at 80 us and
V_module=0.0314 V at 150 us, while changing 50 nH to 500 nH left
V_module=17.242 V at 80 us and -5.1026 V at 150 us.
These are **consequences of our specific unverified circuit parameters**;
the simplified PV diode has no validated reverse-bias or avalanche cell
physics, and the fixed-C behavioural MOSFET has no manufacturer SOA model.
**Do not claim 1242 A is a real module inrush prediction, or that negative
voltages can be tolerated.** The relevant finding is that charge storage
and cable/lead inductance can dominate the transient and invalidate an
Isc-only switch-current rating.

Power-loss control: case 09 showed ~0.0918 V at 80 us while the externally
powered gate was on, then 38.1314 V at 150 us after gate supply was
removed. This falsifies any claim that an ordinary enhancement-mode
MOSFET alone remains fail-to-short. A latching contact or separately
sun-powered gate/hold circuit still needs its own verified schematic.

**Next highest-value experiment:** measure actual small- and large-signal
module-terminal capacitance as a function of voltage and irradiance,
then use vendor PSpice models (under their licence), a measured gate-drive
source and a realistic series inductance/R-C network. Until then the
capacitance range is a sensitivity study, NOT a vendor-validated stress
prediction or hardware component qualification.
