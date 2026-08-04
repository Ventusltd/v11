# V11 Simulator Build Plan

Current authority: PR 3 on `build/v11-inverter-block-simulator`. The laboratory repository remains read-only. Work proceeds one exact-head, CI-first, atomic product commit at a time; the PR remains draft and unmerged.

## Governing SLD contract

- V11 is a complete not-to-scale DC SLD and wiring model for one inverter block.
- All factory, inter-module and field PV cable jackets are rendered black.
- Red and blue apply only to connector and termination polarity markers: red positive, blue negative.
- Connector/contact gender is independent of polarity unless manufacturer evidence establishes it.
- Every later conductor edge must terminate on an explicit connector/terminal node.
- Fixed module positions remain M1..Mn when changing wiring strategy; only electrical graph edges change.
- Paid-standard wording and confidential ER prose are not reproduced; only concise derived constraints are recorded.

## Consumed exact-head receipt

Head `4378548768f83ff0149c6cc0fa812b6db5320ebb` passed `V11 Control Plane Validation` run `30928320253`.

- Control-plane job `92056291936`: success; artefact `8900044449`, digest `sha256:add63dc998f242471353ec37288a35d5674f716d35c0c4c3245d3c2afe9bc3e8`.
- Visible pinned-Chromium job `92056291941`: success; artefact `8900067901`, digest `sha256:00ec1021833eba2d77d7bc4221d05d1c6ec8905772ecb0494dafab910f2a2477`.
- Immutable public-endpoint job `92056292059`: success; artefact `8900042903`, digest `sha256:eece86b712fcb99fbe07339e78d096634f8dacf451d4e73bdd133afc0a7b2314`.
- Chromium reconfirmed 24 strings × 30 modules, 12 MPPT groups, 24 physical inputs, authorised sequential/leapfrog traversal, the connector-marker visual contract, mobile-safe scrolling and the 12 × 20 non-default case.

## Numbered engineering targets

- [x] 1. Connector-marker visual contract: central browser contract, black cable bodies, red/blue connector markers, orange inverter, dashed black provisional routes, unique connector IDs, computed-style validation and structured exact-head evidence.
- [x] 2. Module/junction-box symbol V1: selected-string modules expose explicit `JBOX_NEG` and `JBOX_POS` nodes, black factory leads and red/blue connector markers with stable identities and structured evidence. Default STR-01 acceptance is 30 modules, 60 terminal nodes and 60 connector markers.
- [ ] 3. Sungrow PV1+/PV1− through PV24+/PV24− terminals and 12 MPPT ownership groups.
- [ ] 4. Sequential terminal-to-terminal connection graph.
- [ ] 5. Sequential selected-string SLD and connection ledger.
- [ ] 6. Leapfrog odd-outward/even-return connection graph.
- [ ] 7. Leapfrog selected-string SLD.
- [ ] 8. Aligned Sequential/Leapfrog compare mode.
- [ ] 9. Clickable connector inspector.
- [ ] 10. Full 24-string polarity- and input-explicit SLD overview.
- [ ] 11. Non-default 12 × 20 SLD proof.
- [ ] 12. Versioned connection-graph export.
- [ ] 13. Immutable topology invariant engine.
- [ ] 14. Controlled string/input mapping editor.
- [ ] 15. Module factory-lead contract.
- [ ] 16. Leapfrog lead-length calculator.
- [ ] 17. Explicit positive/negative physical route model.
- [ ] 18. Route rendering from explicit vertices.
- [ ] 19. Segment-derived route length and loop area.
- [ ] 20. Electrical calculations derived from connection and route graphs.
- [ ] 21. Separate non-daisy-chain earthing/bonding graph.
- [ ] 22. Evidence-state and export contract.
- [ ] 23. Full real-browser engineering gate for 24 × 30 and 12 × 20.
- [ ] 24. Engineering-alpha audit and PR-description consolidation.

## Current commit gate

Target 2 is integrated through the authoritative workbench dependency path. The browser module emits `globalgrid2050.v11.module-junction-box-symbol-evidence.v1` with exact tested SHA, selected string, module/terminal/connector/factory-lead counts and identities, SVG measurements, duplicate/missing IDs, computed-style mismatches and pass/fail. Connector gender is explicitly not inferred from polarity. A stable contract failure becomes a page error and therefore fails the existing pinned-Chromium acceptance.

The former analysis implementation is retained byte-for-byte as `browser/workbench-analysis-core.mjs`; `browser/workbench-analysis.mjs` is now the small browser dependency facade that installs both SLD contracts and re-exports the analysis API.

## Next pass

Resolve the new exact PR head and consume its PR-visible `V11 Control Plane Validation` receipt. If green, begin Target 3 only. If red, repair only the first proven CI defect. If pending, make no commit.
