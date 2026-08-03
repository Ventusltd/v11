# V11 Simulator Build Plan

Current authority: PR 3, branch `build/v11-inverter-block-simulator`. The laboratory repository remains read-only.

## Product gate

- [x] Real Chromium workbench test with exact-head evidence.
- [x] Immutable public endpoint with HTTP/content evidence.
- [x] Editable array definition; 24 × 30 remains the default rather than a hard limit.
- [ ] Confirm the V8-style full-array topology surface is green on the latest head and record its run, job, elapsed time and artefact.

## Current product correction

The primary browser surface is now the full inverter-block topology rather than a packed anonymous module field:

- 24 separate string strips by default;
- 30 visible module cells per string;
- 12 MPPT groups and 24 physical input identities;
- Leapfrog, Sequential and Compare modes;
- selected-string fully numbered traversal;
- east/west face and band labels;
- non-default arrays such as 12 × 20;
- physical coordinate layout retained as a secondary debug view;
- physical editing locked by default so mobile scrolling cannot move modules;
- view contract included in engineering JSON exports.

The V8 laboratory page is a read-only visual/behaviour reference. No laboratory source is modified or promoted.

## Existing evidence

- Chromium authority: run `30835051238`, job `91758073073`, artefact `8864492249`.
- Public endpoint authority: run `30844241376`, job `91788477367`, artefact `8868003088`.
- Editable array-definition head `ae145505bf3f256300d4444d442c21dead4a4a36`: run `30853395656`, successful.

## Engineering authority still outstanding

- [ ] Replace provisional physical centroid routes with explicit positive/negative terminal and inverter-input route vertices.
- [ ] Formalise immutable `module_id`, `string_id`, `electrical_index`, `physical_dc_input_id` and `mppt_id` contracts.
- [ ] Compare every Python and JavaScript per-string field by `string_id`.
- [ ] Consolidate layout representations into one versioned canonical schema.
- [ ] Add persistent provisional-model warnings and evidence-state fields to the browser and every export.
- [ ] Version JSON/CSV schemas and document canonicalisation.
- [ ] Rename the interruption output as a provisional travelling-wave estimate and state its limits.
- [ ] Consolidate duplicate workflows around one product surface and one engineering gate.

## Next pass

Consume the PR-visible `V11 Control Plane Validation` receipt for the full-array topology commit. If green, record the exact browser evidence and update the GlobalGrid2050 monitor to the immutable tested SHA. If red, repair only the first proven browser or workflow defect. Do not advance to parity or deeper routing until the visible 24-strip product surface is green.
