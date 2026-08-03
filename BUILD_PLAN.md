# V11 Simulator Build Plan

Current authority: PR 3, branch `build/v11-inverter-block-simulator`. The laboratory repository remains read-only.

## Product gate

- [x] Implement a real headless Chromium workbench test covering 720-module render, 24 string results, legal drag, retained topology identity, recalculation, boundary rejection, and JSON/CSV downloads.
- [x] Confirm the latest-head Chromium E2E job is green and record its run ID, elapsed time and artefact.
- [ ] Confirm one public simulator URL with exact endpoint evidence; prefer GitHub Pages and retain the immutable raw.githack fallback.

## Chromium gate evidence

- Tested SHA: `bcc603cc9d1cef75376f63c0059e76e470e203ea`.
- Workflow run: `30835051238`.
- Chromium job: `91758073073`, successful.
- Actual browser execution: `1.853 seconds`, under the `100 seconds` cap.
- Evidence artefact: `8864492249`, digest `sha256:22d69b698676aedcbf35201ccdfb7ffa0e5231bb4cd43ed795708c3091397a29`.
- Pinned browser: Playwright Chromium 140.
- Verified: 720 modules, 24 string results, legal 0.5 m movement of `MOD-0703`, retained `STR-24` and electrical index 12, route and loss recalculation, boundary rejection, JSON/CSV downloads, and no browser page or console errors.

## Public endpoint status

- The preferred GitHub Pages endpoint remains conditional on repository Pages configuration.
- The existing Live Simulator workflow retains the stable raw.githack fallback.
- This pass adds an exact-commit rawcdn endpoint proof to the existing PR-visible Control Plane Validation workflow.
- The public endpoint item remains incomplete until the new latest-head job is green and its run, job, artefact, HTTP statuses and content hashes are recorded.

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

Read the newest PR-visible Control Plane Validation run and the `Verify immutable public simulator endpoint` job. If green, record the exact public URL and evidence, then proceed to complete per-string Python/JavaScript parity. If red, repair only the first proven endpoint or workflow defect.
