# V11 Simulator Build Plan

Current authority: PR 3, branch `build/v11-inverter-block-simulator`. The laboratory repository remains read-only.

## Product gate

- [x] Implement a real headless Chromium workbench test covering 720-module render, 24 string results, legal drag, retained topology identity, recalculation, boundary rejection, and JSON/CSV downloads.
- [ ] Confirm the latest-head Chromium E2E job is green and record its run ID, elapsed time and artefact.
- [ ] Confirm one public simulator URL with exact endpoint evidence; prefer GitHub Pages and retain the immutable raw.githack fallback.

## Chromium gate status

- Exact branch-push run and job enumeration remains unavailable through the connected GitHub run lookup; the only visible run for the prior head was Control Plane Validation `30812392124`, which passed and did not exercise the Chromium gate.
- The prior E2E workflow still depended on a system-browser probe in the Finish Gate and allowed Playwright Chromium installation to occur inside the outer 100-second test command.
- This repair provisions the pinned Playwright Chromium browser before the 100-second command in both authoritative workflows, makes the test require that exact browser, and makes rejection verification compare the complete post-rejection layout hash.
- Implementation is not complete until a latest-head Chromium run is green and its run ID, elapsed time and evidence artefact are recorded.

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

Read the newest head and exact Chromium E2E logs. Do not advance to parity, topology, routing or other build-plan work until the latest-head browser gate is green. Repair only a proven browser or workflow defect.
