# D11 — physically grounded switch references and reproducible ngspice fixtures

**Status:** exploratory feasibility only. These circuits are generated and run
in GitHub Actions using actual ngspice, but use **generic** MOSFET, ideal
gate-bias and hypothetical solar-harvester models. NOT genuine manufacturer
transistor/driver/comparator SPICE macro-model results. A candidate part name
does not make its approximate model a verified commercial device simulation.

## Real, independently checkable hardware references

- Infineon **IPT015N10N5** 100 V OptiMOS 5 TOLL: max Rds(on)
  1.5 milliohms under stated conditions, Ciss 12 nF, Coss 1.8 nF, typical
  Qg ~169 nC at 10 V. Product/datasheet:
  https://www.infineon.com/part/IPT015N10N5
- Infineon **EVAL_BDPS_DD_TOLL** bidirectional protection-switch
  demonstration board employs **two IPT015N10N5 MOSFETs in drain-to-drain
  configuration** for 36–75 V and 0–30 A continuous. This validates the
  manufacturer's *physical reference topology*, NOT PV junction-box safety:
  https://www.infineon.com/dgdl/Infineon-Bidirectional_protection_switch_evaluation_kit_EVAL_BDPS_DD_TOLL_G_EVAL_BDAPS_DRIVER-UserManual-v01_00-EN.pdf?fileId=8ac78c8c821f38900182395772123baf
- Texas Instruments **UCC27511A** 4 A peak source/8 A peak sink
  gate driver; PSpice transient vendor file **SLVMCJ5.ZIP** obtainable
  separately from TI product page: https://www.ti.com/product/UCC27511A
- Texas Instruments **TLV7032** low-voltage nanopower dual comparator
  (original disclosure part). TI lists a TLV7031 PSpice model and a
  TLV7032 TINA circuit, NOT a confirmed drop-in TLV7032 ngspice
  macro-model: https://www.ti.com/product/TLV7032

**Model provenance:** none of the manufacturer's protected/licensed
SPICE libraries are copied into GitHub. Before vendor verification, acquire
and examine the exact manufacturer files and licence separately, check
pin order/body diode, operating conditions and simulator compatibility.

## SPICE test circuits (written by `spice_cases.py`)

1. `d11-closed.cir`: 660 Wp three-anchor PV current-source surrogate,
   RMPP load, 10uF assumed module terminal capacitance, two generic
   back-to-back NMOS shunt elements; ideal 10V gate command rises at 1ms.
   Compare 0.5ms pre-command vs 1.7ms closed voltage.
2. `d11-power_loss.cir`: identical circuit, but gate voltage goes
   away near 2ms. Must **re-energise** module terminals: demonstrates a
   plain enhancement-FET command cannot fail-to-short without gate energy.
3. `d11-no_command.cir`: zero gate voltage baseline. Module must
   continue to show approximately normal operating terminal voltage.
4. `d11-sun_aux.cir`: a SEPARATE hypothetical PV-powered 16V
   Thevenin cell source with 256ohm source resistance (0.25W maximum),
   diode and 1000uF storage reservoir. Tests charging of a reserve
   while the main module shunt could stay held closed. This is
   **not** actual self-start/reset circuitry or a validated solar harvester.

**Important physics:** body diodes of a single NMOS make reverse blocking
nontrivial, hence two opposed MOSFETs. The reference Infineon board uses
drain-to-drain while this fixture uses source-to-source: an electrically
related back-to-back blocking arrangement, but not a replication of that
board's gate drive, PCB, thermal design, or its device models.

Provisional 660 Wp cell parameters are from existing public V11 D10.
The 10uF capacitance and ideal driven gates are explicitly unmeasured
test assumptions. No actual inverter, long cable, arc plasma, frame
leakage or externally connected energy source is present.

## Run

```sh
sudo apt-get install ngspice
python -m unittest -v test_spice_cases.py
python spice_cases.py --output-dir results
```

The script refuses to fake a SPICE run if ngspice is missing. The CI archives
four generated netlists, four real ngspice logs and a small JSON receipt.
Reported module voltage collapse, if achieved, is only a generic-device
feasibility result. Explicit measurements for gate loss **must be reported**.

## Next acceptance gates

- First, obtain the actual official Infineon/TI macro-models locally
  if licence permits, adapt the test deck syntax, and repeat ngspice
  while respecting model ownership.
- Run two same-MPPT strings with 30 independently shunted modules each,
  positive and negative home-runs, asymmetric switching and inverter
  stored-energy *uncertainty*, rather than simply multiplying one
  module's static voltages by 30.
- Build the true self-powered analogue supply: PV sun input independent
  of main shunt voltage, actual energy/UVLO, autonomous fail-to-short
  state, positive fault-clear release criterion and daylight restart.
- Qualify real thermal, transient safe-operating-area, gate drive,
  cold Voc and reverse-current, diode and module/hotspot behaviour
  before considering any hardware.

**Safety:** This is research-only unvalidated code. Never install in
an energised PV array. Main remains untouched, upstream repositories
read-only, no private or copyrighted source files committed.
