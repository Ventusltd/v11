# Draft PV arc research — V11 review only

**Scope:** reproducible parameterised screening of two illustrative array-to-grid power chains, with numerical sanity checks and explicit gaps. **NOT** a SPICE/EMT digital twin, a complete calibrated system model, validated protection circuit, site-specific design or V11-authorised engineering capability. No edits to original PV arc disclosure, frozen laboratory or V11 control-plane programme state. Four review tracks are performed by a single assistant; no real Astra subagents were invoked.

## Files
- model.py — Python stdlib calculation engine (modules, series strings, MPPT-group topology, DC link assumed energy, inverter power cap, LV current, transformer, HV grid current).
- illustrative-input.json — invented transparent example parameters, NOT Sungrow or any OEM factual data.
- test_model.py — seven regression checks.
- four-review-findings.md — separate semiconductor, electronics logic, DC transient and grid-coordination audits.

## Run
From this folder use:

    python -S model.py --output results.json
    python -S -m unittest -v test_model.py

No project should be designed or commissioned from the example calculations. The network model is a screening envelope only. Data that remain necessary for complete system simulation: module I-V/temperature models, cable GIS geometry and mutual impedance, fault connections, real MPPT and transformer winding topology, converter control firmware/harmonics, DC link capacitors, fuses/AFCI/IMD/RCM, SPD ratings, MOSFET orientation, gate drives, real arc signatures and validated electrical transients.

## V11 source boundary
This research uses only Ventusltd/v11 as the active study repository. The old Ventusltd/solar-electrical-topology-analysis-engine-text-based is a read-only resource anchored at d3b4c497144c2c9b3e8f0e82117e7e9abe4672b9; no code was copied from it. This draft does not close V11-001, authorise V11-004, amend programme-state.json or claim any passing operator receipt. Product-owner and independent electrical/electronics review are required before any promotion.
