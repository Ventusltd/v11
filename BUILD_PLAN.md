# V11 Simulator Build Plan

Current authority: PR 3, branch `build/v11-inverter-block-simulator`. The laboratory repository remains read-only.

## Product gate

- [x] Real Chromium workbench test with exact-head evidence.
- [x] Immutable public endpoint with HTTP/content evidence.
- [x] Editable array definition; 24 × 30 remains the default rather than a hard limit.
- [x] Confirm the V8-style full-array topology surface is green on the latest tested head and record its run, job, elapsed time and artefact.
- [x] Confirm compact mobile MPPT headers, safe horizontal strip scrolling and sticky selected-string summary in pinned Chromium.

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

## Documentation-head validation receipt

- Tested SHA: `913253216d23e70997faa4534a11b4d2434b3de0`.
- Workflow: `V11 Control Plane Validation`, run `30857251084`, successful.
- Control-plane job: `91831014989`, successful.
- Visible pinned-Chromium job: `91831015013`, successful.
- Immutable public-endpoint job: `91831015033`, successful.
- Browser elapsed time: `2.628 seconds`, below the `100 seconds` browser cap.
- Browser evidence artefact: `8872943720`, digest `sha256:8e165fe88b8497ae627fcdd46ff46ff3af10fbec78f07e993a39a8919d9e4812`.
- Public endpoint artefact: `8872934826`, digest `sha256:defcbab1c21d30f104b1e289942113ce37d493f8cb508fd2ab55401fcd2aa514`.
- Control-plane artefact: `8872933406`, digest `sha256:f6b35f27a310944a41d053e43bcb138e3efc758fbbeb35be743ef09442762b1b`.
- Reconfirmed: 24 strips, 720 cells, 12 MPPTs, 24 physical inputs, authorised sequential/leapfrog traversal, safe scrolling, explicit edit identity retention and 12 × 20 non-default operation.

## Mobile full-array validation receipt

- Tested SHA: `f870883dfdfcabf2edcc800ff7a17e41fb0aa05a`.
- Workflow: `V11 Control Plane Validation`, run `30861254944`, successful.
- Control-plane job: `91843503081`, successful.
- Immutable public-endpoint job: `91843503115`, successful.
- Visible pinned-Chromium job: `91843503135`, successful.
- Browser elapsed time: `2.524 seconds`, below the `100 seconds` browser cap.
- Browser evidence artefact: `8874417285`, digest `sha256:3e25f195e1fcdda4f64935e24134a892bfe04b93f7c1a576aea0e383f88cee4f`.
- Public endpoint artefact: `8874409833`, digest `sha256:2139dda2feca7b395cfacae92a64ad5e88c6d004cd70b14bb4b987160db972bc`.
- Control-plane artefact: `8874409187`, digest `sha256:3bcad3bc98835016e8cf506daea39d9af719e7018251f52afb115678a1209472`.
- Mobile contract proven: compact MPPT headers, safe horizontal strip scrolling and sticky selected-string summary.
- Measured mobile styles: MPPT header `11px`, top padding `5px`, strip `overflow-x: auto`, strip `touch-action: pan-x pan-y`, selected summary `position: sticky`.
- Default array reconfirmed: 24 strips, 720 cells, 12 MPPTs and 24 physical inputs.
- Non-default array reconfirmed: 12 strips × 20 modules = 240 cells across 6 MPPTs.
- Sequential and leapfrog traversal orders, safe-scroll hash, explicit-edit identity retention and outside-boundary rejection all remained green.

## Mobile documentation-head validation receipt

- Tested SHA: `dd19fcf8225fea3620e8dbfd46e814aeaca84c9b`.
- Workflow: `V11 Control Plane Validation`, run `30864411791`, successful.
- Control-plane job: `91853031839`, successful.
- Immutable public-endpoint job: `91853031872`, successful.
- Visible pinned-Chromium job: `91853031877`, successful.
- Browser elapsed time: `2.722 seconds`, below the `100 seconds` browser cap.
- Browser evidence artefact: `8875557685`, digest `sha256:e2dc8c4e295e61d6909c4726e33fb7b4ce799e5970710f8a33628ed1bece020d`.
- Public endpoint artefact: `8875544711`, digest `sha256:75b60f4b57e1baf70a9cb77cc732bc28586e7113f8bfbb9d4e6ad3dc088d5691`.
- Control-plane artefact: `8875544538`, digest `sha256:2cb6b8b0cc0ef8c26ac2169930d2946ab017b5fb5605c104ec6e175c195b91b8`.
- Reconfirmed: 24 strips, 720 topology cells, 12 MPPT groups, 24 physical inputs, authorised sequential and leapfrog traversal, safe scrolling, locked physical editing, explicit edit identity retention, outside-boundary rejection and 12 × 20 operation.
- Mobile styles reconfirmed: MPPT header `11px`, top padding `5px`, strip `overflow-x: auto`, strip `touch-action: pan-x pan-y`, selected summary `position: sticky`.
- Safe-scroll layout hash remained `sha256:809f7133409b9498cbc3489c7e397b72fc73d08fec33d911d44e515e0dc2597a`.
- Explicit edit retained `MOD-0709`, `STR-24` and electrical index `19`; accepted layout hash `sha256:6f2f62b145f5716af7f0fd130924131a3eb508ad7ccc3f566e542cabda402939`.

## Latest exact-head validation receipt

- Tested SHA: `060391f3e60100352db48bd264895ec73d3c28af`.
- Workflow: `V11 Control Plane Validation`, run `30867622687`, successful.
- Control-plane job: `91862782089`, successful.
- Visible pinned-Chromium job: `91862782134`, successful.
- Immutable public-endpoint job: `91862782199`, successful.
- Browser elapsed time: `2.73 seconds`, below the `100 seconds` browser cap.
- Browser evidence artefact: `8876705056`, digest `sha256:900277f1bf1806ad3ae02c5f8c0edc0440521324a72d236862a311bed32afddb`.
- Public endpoint artefact: `8876700903`, digest `sha256:5d3915666f95b717eec43161e4711c9a6c84854c615e1cd4d4c5aa19e945c59c`.
- Control-plane artefact: `8876693978`, digest `sha256:659b55119c7a0295a976bb521047875d7d57e1047e6ddef13752e8df26ed2052`.
- Reconfirmed: 24 separate string strips, 720 topology cells, 12 MPPT groups, 24 physical inputs, correct sequential and leapfrog traversal, safe mobile scrolling, locked editing, explicit edit identity retention, outside-boundary rejection and 12 × 20 operation.
- Mobile contract reconfirmed: MPPT header `11px`, top padding `5px`, strip `overflow-x: auto`, strip `touch-action: pan-x pan-y`, selected summary `position: sticky`.
- Safe-scroll layout hash remained `sha256:809f7133409b9498cbc3489c7e397b72fc73d08fec33d911d44e515e0dc2597a`.
- Explicit edit retained `MOD-0709`, `STR-24` and electrical index `19`; accepted layout hash `sha256:6f2f62b145f5716af7f0fd130924131a3eb508ad7ccc3f566e542cabda402939`.

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

Consume the PR-visible `V11 Control Plane Validation` receipt for this latest receipt head. If green, update the GlobalGrid2050 `/v11/` monitor to the exact immutable mobile-readability SHA `f870883dfdfcabf2edcc800ff7a17e41fb0aa05a` and verify the public monitor URL. Keep its homepage entry only inside the Solar & BESS Topology nest after V10. Do not advance to explicit terminal routing until the monitor points at this green immutable build.