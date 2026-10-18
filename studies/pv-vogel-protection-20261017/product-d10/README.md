# D10: De-energise an individual 660 Wp module by a commanded terminal short

**Research question:** Can a module close a low-impedance PV-positive to
PV-negative shunt, retain that connection after control power is lost, and
subsequently reopen for generation?

The Python test is a source-limited feasibility calculation, **not a real
switch, gate-driver, relay, DC-arc or product-qualification test**.

## Reproduce

```sh
python -m pip install numpy==2.3.5
python -m unittest -v test_module_shunt_power_loss.py
python module_shunt_power_loss.py --output results/module-power-loss.json
```

The model fits an idealised single-diode curve to the provisional 660 Wp
STC anchors (45.75 V Voc, 38.13 V Vmpp, 17.31 A Impp, 18.4 A Isc).
It assumes an isolated module with a resistive output load and an
unmeasured terminal capacitance. A smooth voltage-collapse trajectory
is prescribed, then the required shunt current and energy are obtained
by a Kirchhoff energy balance. Whether a real semiconductor can follow
this pulse is **unknown**; transient safe-operating-area must be tested.

At a hypothetical 5 milliohm ON resistance, the calibrated module's
terminal voltage falls from 38.13 V to roughly 0.0918 V, with about
1.685 W continuous short-path loss. For the 200 microsecond, 10 uF
illustrative ramp, the switching path briefly reaches over 200 W of
instantaneous power; this is NOT the long-term heating figure.

## Loss of all control power is the actual design discriminator

- Ordinary enhancement-mode MOSFET gate bias disappears: it **cannot
  be assumed to stay shorted**.
- A mechanically latched short can remain closed without coil power
  once it was successfully triggered. The *assumed* 50 mJ actuation
  pulse can be supplied from a hypothetical 1000 uF capacitor charged
  from 12 V to 6 V (54 mJ usable), but not 470 uF (~25 mJ).
  These are **not supplier actuator specifications**.
- A normally closed mechanical bypass defaults shorted on loss of power
  but requires a separate start/hold-open source for production.
- None of these simplistic mechanisms demonstrates safe automatic
  reopening or sunrise power-up while the module is at ~0.09 V.
  A power source or a validated energy harvester and reset sequence
  must be provided.

One idealised, isolated string with all 30 individual 5 milliohm
shunts closed gives ~2.76 V no-load; with one shunt stuck open,
~48.418 V can remain. A paired string or inverter can still energise
the conductors; these figures are **not safe isolation**.

## False claims explicitly excluded

This does not validate 30-year component endurance, device SOA,
electromechanical contact switching, cable inductance, inverter
backfeed, module internal faults, shaded-cell hot spots, live DC arcs
or safety compliance. Model capacitance, switching time, closing pulse
energy and control power are research assumptions, not measured data.

Only previously public source-model parameters are present.
Confidential standards and privately shared inverter documentation
are excluded. V11 main is untouched and this work remains a
stacked draft PR on D9.


## Correction: original 2025 sunlight logic is the intended energy source

The publicly disclosed source at
https://github.com/Ventusltd/pv-arc-protection-circuit/blob/main/Open-Hardware-Disclosure.md
explicitly uses PV terminal voltage above about 15 V as a sunlight-present
analogue gate and powers its ORIGINAL **series-opening** circuit from PV.
It additionally says that its original series circuit fails OPEN when
power is lost. This is not the same circuit as the NEW normally-short
hypothesis.

**Sunlight can provide the restart energy. It is not necessary to assume
a mains-fed or external supply.** The physical question is how to access
it while the active whole-module terminal shunt holds PV+ to PV− at
~0.09 V: the original >15 V terminal gate would see no voltage.

The additional `sunlight_powered_bootstrap` tests compare:

1. **Original 15 V PV-terminal gate:** cannot sense light or supply the
   control circuit from the *hard-shorted* terminal voltage.
2. **Independent auxiliary sun harvester:** one possible solar-sourced
   means to charge a control-energy reservoir while the module stays
   shunted. Illustrative 0.25 W full-sun harvester, 60% power conversion,
   5 mW control draw and 1000 uF/12 V reservoir; these are NOT
   identified components or hardware measurements.
3. **Hypothetical converter from the 0.09 V shunt drop:** solar-powered
   without a separate cell, but assumes conversion from below 100 mV
   with unknown starting circuit, efficiency and thermal impact.
   This is a falsification target, NOT a known viable design.

The model's conditional *reset possible* result requires the reservoir
to charge AND an independently credible **fault-cleared** indication.
Illumination alone is not permission to re-energise a damaged string.
The analog sensing and safe reopening mechanism are not demonstrated.

**Next test:** simulate the harvest/start circuit with real device
datasheets, including a shunted cold start, then test the actuator
releasing and promptly re-closing the shunt under persistent faults.
