# PV arc protection: four engineering review tracks — draft 2026-10-17

**Research only. Not four Astra instances.** Four independent *disciplines reviewed by one assistant*. No validated safety claim; no V11 CAP-FIRST-ENGINEERING promotion. Source: Ventusltd/pv-arc-protection-circuit, Open-Hardware-Disclosure.md, v1.3.2.1.

## A. Series SiC MOSFETs: nominal, upset, and one-short criteria
The named Infineon IMZA65R027M1H is rated 650 V, not 1700 V. Two in series are nominally 1300 V **only with balanced voltages**. Example string cold Voc 1397.76 V: even 50/50 gives 698.88 V/device, beyond 650 V. With illustrative 50 microamp leakage difference and 10 megaohm equalising resistors, a device sees 948.88 V. This is a sensitivity example, not a measured device-leakage guarantee. Series MOSFETs require controlled static and dynamic Vds sharing, isolated and correctly referenced drives, Coss and parasitic matching and measured transient stress.

A failed-short device leaves one device holding the entire voltage. For bidirectional DC blocking, MOSFET intrinsic body diode orientation must be resolved: same-directed series devices are not automatically bidirectional disconnectors; anti-series topology requires design. A bypass diode can keep current flowing while leaving external terminals live.

At module Impp=18 A, two devices at 27 milliohms each dissipate 17.496 W (typical 25 C value only); the disclosed 0.1 ohm, 1 W series shunt would dissipate 32.4 W. Thermal ratings depend on junction box temperature and cooling, not nameplate peak currents. At 20 A: 21.6 W MOSFET pair and 40 W shunt.

**Next evidence:** verified circuit topology and part numbers, thermal impedance and Rds(T), total SOA, datasheet leakage limits, dynamic sharing with isolated gate drive, single-failure analysis and hi-pot/partial-discharge margins. 1700 V devices improve *nominal* headroom; they do not prove fail-safe isolation under lightning, cold Voc or one-short failures.

## B. Analogue detector: timing and selectivity
TI TLV7032 typical propagation delay is 3 microseconds, exceeding a <1 microsecond system-trip claim before output/gate/MOSFET delays. A nominal 1 kohm + 100 nF simple RC has a 100 microsecond time constant, if in the detection path; exact wiring and response must be established. The disclosure's current-ripple detection is not demonstrated capable of discriminating a DC series arc from converter switching, transients, shading or cable coupling. A single frame-voltage divider is not proof of measuring insulation leakage current or insulation resistance. A false-trip/fail-to-trip matrix is needed across cold, wet, night, startup, open strings and power-loss states.

**Next evidence:** hardware comparators' worst-case response over temperature and threshold sweep, arc waveforms, noise spectra, trip energy, independent ISO/IMD analysis and EMC tests.

## C. PV source -> cable -> grouped MPPT -> DC bus
Actual MPPT wiring determines whether 24 string inputs are grouped in parallel or isolated by converter stages. Model each galvanically connected fault node. With assumed three strings per group and Isc=19.5 A, other-string current bound within group is 39 A; treating *all* 24 as a single bus yields 448.5 A potential aggregate envelope, but is not credible without actual connection paths. For 80 strings arranged 4 per group, those envelope values are 58.5 A and 1540.5 A respectively (without protection). These are simplistic upper bounds, not actual prospective fault currents.

At 18 A, opening in 1 microsecond with 10 microhenry lumped inductance gives L di/dt=180 V, while 100 microhenry would give 1800 V *before clamping*; do not mistake either for device Vds. A hypothesised 2 mF DC capacitor at cold string Voc holds about 1954 J; its real voltage and fault accessibility are architecture-dependent. A 2.2 microfarad snubber at 1500 V stores 2.475 J and needs pulse-current, repetitive lifetime and dielectric qualification.

**Next evidence:** physical cable routes (including conductor separations and metallic/earth return paths), L/C matrices, device Coss, MPPT wiring, inverter DC-link data, SPDs, bypass diode circuits and experimentally validated EMT models.

## D. Full electrical plant and protection coordination
The screening model carries DC module power through assumed MPPT partitions to an inverter power cap, then 690 V AC, transformer and 33 kV grid current arithmetic. It **does not** perform grid load flow, harmonic, short circuit, earth potential rise, transformer saturation or dynamic MPPT behaviour; nameplate power balance is NOT a complete-system model. The real system requires system-specific impedance, earthing, protective zones, AC/DC interfaces, converter limits and relay selectivity. Rapid shutdown or local MOSFET isolation does not automatically discharge every live conductor or satisfy firefighter access rules.

**Next evidence:** SLD plus actual device data, per-string route schedule and wiring matrix, OEM converter and protective relay model, IEC 60909-type AC short-circuit study, DC transient/arc study, insulation coordination and qualified independent review.

## Decision and references
This is a defensible research programme for source-level protection. It is not ready for hardware construction, HV energisation, commercial deployment or a claim of <1 microsecond fail-safe fire prevention. Existing V11 programme remains in V11-001 / under validation. No laboratory modification.

- https://www.infineon.com/part/IMZA65R027M1H
- https://www.ti.com/product/TLV7032
- https://doi.org/10.1049/pel2.12744
- https://github.com/Ventusltd/pv-arc-protection-circuit/blob/main/Open-Hardware-Disclosure.md
