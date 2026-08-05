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

Head `bd0d77cd8925838fa0294f4bd12483ccf17cabd8` passed `V11 Control Plane Validation` run `30959012979`.

- Control-plane job `92158561669`: success; artefact `8912193391`, digest `sha256:d9678821d065e19f6fb3151b52a33dd99d11b746b90db253109095bd17e8bd9c`.
- Visible pinned-Chromium job `92158561762`: success; artefact `8912238353`, digest `sha256:8969bac93145939ffa7bbf861158ee07d07ab8f561a512907dc7edc56866f280`.
- Immutable public-endpoint job `92158561717`: success; artefact `8912191624`, digest `sha256:528db76055099b180c618eff41fdb6d7dea61efd1b273fea66a173b628a720b9`.
- Connector-accounting job `92158561747`: success; artefact `8912196433`, digest `sha256:c03e1418952739707e3d18fa598c0f17df42dd2633d52c6bb6debb5ae82b3c59`.
- Exact-head evidence confirms both simulation engines ignore injected legacy counts and continue to agree on the named `N + 3` interface policy.

## Connector-accounting authority

For `N` modules in one completed string:

- module connector ends: `2N`;
- two string cables: `4` connector ends;
- inverter positive and negative sockets: `2` connector ends;
- complete-system connector ends: `2N + 6`;
- module-to-module mates: `N - 1`;
- module-to-string-cable mates: `2`;
- string-cable-to-inverter mates: `2`;
- total mated interfaces: `N + 3`;
- positive/red ends: `N + 3`;
- negative/blue ends: `N + 3`.

The provisional resistance policy currently applies one declared contact resistance to all `N + 3` completed mated interfaces. Manufacturer-specific resistance evidence remains incomplete. The deprecated `connector_count_per_string` and status fields are removed from the authoritative fixture; Python and JavaScript derive the interface count from `array.modules_per_string` and consume the named resistance policy directly.

## Numbered engineering targets

- [x] 1. Connector-marker visual contract: central browser contract, black cable bodies, red/blue connector markers, orange inverter, dashed black provisional routes, unique connector IDs, computed-style validation and structured exact-head evidence.
- [x] 2. Module/junction-box symbol V1: selected-string modules expose explicit `JBOX_NEG` and `JBOX_POS` nodes, black factory leads and red/blue connector markers with stable identities and structured evidence. Default STR-01 acceptance is 30 modules, 60 terminal nodes and 60 connector markers.
- [x] 2A. Versioned connector-accounting authority: Python/browser parity, explicit subsystem counts, complete-system formulae, provisional interface-class resistance policy and dedicated CI evidence for 30-, 28- and 20-module strings.
- [x] 2B. Remove the deprecated simulation compatibility count and make Python/JavaScript simulations consume the named connector-resistance policy directly.
- [ ] 2C. Project four string-cable connector ends plus two inverter connector ends into the selected-string SLD, proving 66 complete-system ends and 33 red/33 blue markers for 30 modules.
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

The connector-accounting contract is authoritative in `reference/connector_accounting_contract.json` and is implemented independently in Python and browser modules. The authoritative fixture now contains only the named resistance policy; no compatibility count or compatibility-status field remains. Both simulation engines derive the completed-interface count from module cardinality. Dedicated CI proves:

- `N = 30`: 66 ends, 33 interfaces, 33 red and 33 blue ends;
- `N = 28`: 62 ends, 31 interfaces, 31 red and 31 blue ends;
- `N = 20`: 46 ends, 23 interfaces, 23 red and 23 blue ends.

## Next pass

Resolve the new exact PR head and consume its PR-visible validation receipt. If green, begin Target 2C by projecting the four string-cable connector ends and two inverter connector ends into the selected-string SLD with stable graph IDs and complete 66-end/33-red/33-blue evidence. If red, repair only the first proven CI defect. If pending, make no commit.
