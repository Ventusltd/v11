# V11 Simulator Build Plan

Current authority: PR 3, branch `build/v11-inverter-block-simulator`. The laboratory repository remains read-only.

## Product gate

- [x] Implement a real headless Chromium workbench test covering 720-module render, 24 string results, legal drag, retained topology identity, recalculation, boundary rejection, and JSON/CSV downloads.
- [ ] Confirm the latest-head Chromium E2E job is green and record its run ID, elapsed time and artefact.
- [ ] Confirm one public simulator URL with exact endpoint evidence; prefer GitHub Pages and retain the immutable raw.githack fallback.

## Engineering authority

- [ ] Compare every Python and JavaScript per-string field by `string_id`, not only totals and hashes.
- [ ] Formalise immutable `module_id`, `string_id`, `electrical_index`, `physical_dc_input_id` and `mppt_id` contracts.
- [ ] Consolidate layout representations into one versioned canonical schema.
- [ ] Add persistent provisional-model warnings and evidence-state fields to the browser and every export.
- [ ] Replace the centroid route proxy with the first laboratory-faithful terminal, inverter-input and route-vertex adapter slice.
- [ ] Version JSON/CSV schemas and document canonicalisation.
- [ ] Rename the interruption output as a provisional travelling-wave estimate and state its limits.
- [ ] Consolidate duplicate workflows around one product surface and one engineering gate.

## Next pass

Read the newest head and exact Chromium E2E logs. Repair only a proven test, browser or workflow defect; otherwise proceed to complete per-string parity.
