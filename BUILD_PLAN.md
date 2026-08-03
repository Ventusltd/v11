# V11 Simulator Build Plan

Current authority: PR 3, branch `build/v11-inverter-block-simulator`. The laboratory repository remains read-only.

## Product gate

- [x] Implement a real headless Chromium workbench test covering 720-module render, 24 string results, legal drag, retained topology identity, recalculation, boundary rejection, and JSON/CSV downloads.
- [ ] Confirm the latest-head Chromium E2E job is green and record its run ID, elapsed time and artefact.
- [ ] Confirm one public simulator URL with exact endpoint evidence; prefer GitHub Pages and retain the immutable raw.githack fallback.

## Chromium gate status

- Latest reviewed head before this observability repair: `48f9693aee8dc999f62d99886100ed4f91173046`.
- The only connector-visible run for that head was Control Plane Validation `30830593451`, which completed successfully but did not execute Chromium.
- The Live Simulator and Tonight Finish Gate already run the same pinned Playwright Chromium E2E, but branch-push run enumeration remains unavailable through the connected lookup.
- This repair adds the identical bounded browser gate as a second job in the existing PR-visible Control Plane Validation workflow. It does not create another workflow and keeps the browser command capped at 100 seconds inside a five-minute job.
- Implementation is not complete until the new latest-head PR run is green and its browser job ID, elapsed time, first failing line if any, and evidence artefact are recorded.

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

Read the newest PR-visible Control Plane Validation run and the `Visible pinned-Chromium workbench E2E` job. Do not advance to parity, topology, routing or other build-plan work until that job is green. Repair only the first proven browser or workflow defect.
