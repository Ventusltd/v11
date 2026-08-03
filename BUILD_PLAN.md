# V11 Simulator Build Plan

Current authority: PR 3, branch `build/v11-inverter-block-simulator`. The laboratory repository remains read-only.

## Product gate

- [x] Real Chromium workbench test with exact-head evidence.
- [x] Immutable public endpoint with HTTP/content evidence.
- [x] Editable array definition; 24 × 30 remains the default rather than a hard limit.
- [x] Confirm the V8-style full-array topology surface is green on the latest tested head and record its run, job, elapsed time and artefact.

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

## Full-array topology validation receipt

- Tested SHA: `db751da384c4ef63d6055c38a7b312b33578cc22`.
- Workflow: `V11 Control Plane Validation`, run `30855303372`, successful.
- Control-plane job: `91824804202`, successful.
- Immutable public-endpoint job: `91824804253`, successful.
- Visible pinned-Chromium job: `91824804294`, successful.
- Browser elapsed time: `2.558 seconds`, below the `100 seconds` browser cap.
- Browser evidence artefact: `8872219927`, digest `sha256:b5345015a8b48bdcd04b38b5d41195c4e793805c812154815ddb719e4f022b8a`.
- Public endpoint artefact: `8872207944`, digest `sha256:79abe1cede9b32e0f7d43e945a8a27f9a22b2969bafa583c83564cc4dca7d5e0`.
- Control-plane artefact: `8872209381`, digest `sha256:28cd70f98a4100a9e3f22219601cf94c411ffba55f091491014449a0b13260ce`.
- Default array proven: 24 string strips, 30 modules per string, 720 topology cells, 12 MPPT groups and 24 physical inputs.
- Non-default array proven: 12 string strips × 20 modules = 240 topology cells, grouped across 6 MPPTs.
- Sequential traversal proven: `1..30`.
- Leapfrog traversal proven: `1,3,5,...,29,30,28,...,4,2`.
- Safe topology scrolling retained layout hash `sha256:809f7133409b9498cbc3489c7e397b72fc73d08fec33d911d44e515e0dc2597a` while physical editing was disabled.
- Explicit physical edit moved `MOD-0709` while retaining `STR-24` and electrical index `19`; resulting layout hash `sha256:6f2f62b145f5716af7f0fd130924131a3eb508ad7ccc3f566e542cabda402939`.
- Outside-boundary movement was rejected without changing the accepted edited layout.

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

Consume the PR-visible `V11 Control Plane Validation` receipt for this documentation head. If green, update the GlobalGrid2050 `/v11/` monitor to the exact immutable tested SHA `db751da384c4ef63d6055c38a7b312b33578cc22`, then improve mobile readability with compact MPPT headers, safe horizontal strip scrolling and a sticky selected-string summary. If red, repair only the first proven defect. Do not advance to parity or deeper routing until the monitor and mobile full-array surface are green.
