# V11 Simulator Build Plan

Current authority: PR 3, branch `build/v11-inverter-block-simulator`. The laboratory repository remains read-only.

## Product gate

- [x] Implement a real headless Chromium workbench test covering 720-module render, 24 string results, legal drag, retained topology identity, recalculation, boundary rejection, and JSON/CSV downloads.
- [x] Confirm the latest-head Chromium E2E job is green and record its run ID, elapsed time and artefact.
- [x] Confirm one public simulator URL with exact endpoint evidence; GitHub Pages remains preferred when repository configuration permits it, and the immutable rawcdn fallback is proven.

## Chromium gate evidence

- Tested SHA: `bcc603cc9d1cef75376f63c0059e76e470e203ea`.
- Workflow run: `30835051238`.
- Chromium job: `91758073073`, successful.
- Actual browser execution: `1.853 seconds`, under the `100 seconds` cap.
- Evidence artefact: `8864492249`, digest `sha256:22d69b698676aedcbf35201ccdfb7ffa0e5231bb4cd43ed795708c3091397a29`.
- Pinned browser: Playwright Chromium 140.
- Verified: 720 modules, 24 string results, legal 0.5 m movement of `MOD-0703`, retained `STR-24` and electrical index 12, route and loss recalculation, boundary rejection, JSON/CSV downloads, and no browser page or console errors.

## Public endpoint evidence

- Tested SHA: `36811315cedf3b18ff990ccb696b98c8d5c3761d`.
- Workflow run: `30844241376`, successful.
- Public endpoint job: `91788477367`, successful.
- Evidence artefact: `8868003088`, digest `sha256:f4e465fe520a8beafc244949f77c11a3810eac8bfdaacabc00944c5878880dcd`.
- Immutable public demo: `https://rawcdn.githack.com/Ventusltd/v11/36811315cedf3b18ff990ccb696b98c8d5c3761d/browser/workbench.html`.
- All six required exact-commit endpoints returned HTTP 200 with correct HTML, JavaScript or JSON content types and recorded body SHA-256 hashes.
- Verified endpoints: `browser/workbench.html`, `browser/workbench.mjs`, `browser/layout-core.mjs`, `browser/layout-simulation-bridge.mjs`, `browser/workbench-analysis.mjs`, and `reference/lab_inverter_block_24_strings.json`.
- Reference boundary: 24 strings × 30 modules = 720 modules.
- Latest-head Chromium job in the same run: `91788477546`, successful in `1.832 seconds`; evidence artefact `8868016651`, digest `sha256:fd7435bb1702aa84b62bb78195f5c64e81f2cbbfc063da7ade54f0197fbc4e67`.
- The preferred GitHub Pages endpoint remains conditional on repository Pages configuration; the stable raw.githack fallback remains available through the Live Simulator workflow.

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

Consume the PR-visible `V11 Control Plane Validation` receipt for this exact documentation head. If green, implement complete Python/JavaScript parity for every per-string field joined by `string_id`, with exact identity/hash comparison, numerical tolerance for floating fields, explicit field-level mismatches, and a structured PR-visible JSON evidence artefact. Publish at most one atomic parity commit, then stop for GitHub Actions.
