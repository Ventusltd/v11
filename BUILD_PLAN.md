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

Head `9d39db6485def72c5189b8976977ee5563b25310` passed `V11 Control Plane Validation` run `30948072103`.

- Control-plane job `92122927993`: success; artefact `8907902976`, digest `sha256:aadf27231946a8eeb7ceceb58c882e2f96d7a9f4b29484f31f997428b4d2fffa`.
- Visible pinned-Chromium job `92122927866`: success; artefact `8907909776`, digest `sha256:1ff75b101b6d497845b0b704a819631cbda4ba3dd078e1ce536f70d890933a9d`.
- Immutable public-endpoint job `92122927980`: success; artefact `8907903828`, digest `sha256:39a23ddaf57b8ad5deb474608b4bf351f9f27a8a10e4e802201871167b88b620`.
- Chromium reconfirmed the 24 × 30 and 12 × 20 workbench cases after the pinned-browser cache change.

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

The provisional resistance policy currently applies one declared contact resistance to all `N + 3` completed mated interfaces. Manufacturer-specific resistance evidence remains incomplete. The legacy `connector_count_per_string` input is retained only as a deprecated compatibility projection and must equal `total_mated_interface_count`; it is no longer allowed to carry an unexplained value of 31.

## Numbered engineering targets

- [x] 1. Connector-marker visual contract: central browser contract, black cable bodies, red/blue connector markers, orange inverter, dashed black provisional routes, unique connector IDs, computed-style validation and structured exact-head evidence.
- [x] 2. Module/junction-box symbol V1: selected-string modules expose explicit `JBOX_NEG` and `JBOX_POS` nodes, black factory leads and red/blue connector markers with stable identities and structured evidence. Default STR-01 acceptance is 30 modules, 60 terminal nodes and 60 connector markers.
- [x] 2A. Versioned connector-accounting authority: Python/browser parity, explicit subsystem counts, complete-system formulae, provisional interface-class resistance policy and dedicated CI evidence for 30-, 28- and 20-module strings.
- [ ] 2B. Remove the deprecated simulation compatibility count and make Python/JavaScript simulations consume the named connector-resistance policy directly.
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

The connector-accounting contract is authoritative in `reference/connector_accounting_contract.json` and is implemented independently in Python and browser modules. The default fixture's compatibility count is corrected from 31 to 33, matching `N + 3` completed mated interfaces for `N = 30`. Dedicated CI proves:

- `N = 30`: 66 ends, 33 interfaces, 33 red and 33 blue ends;
- `N = 28`: 62 ends, 31 interfaces, 31 red and 31 blue ends;
- `N = 20`: 46 ends, 23 interfaces, 23 red and 23 blue ends.

## Next pass

Resolve the new exact PR head and consume its PR-visible validation receipt. If green, complete Target 2B by removing direct simulation dependence on `connector_count_per_string` and consuming the named interface policy in both Python and JavaScript. If red, repair only the first proven CI defect. If pending, make no commit.
