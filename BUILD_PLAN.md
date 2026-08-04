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

The previous head `45fa0113c7d06d3ca44ba083183764cfbd31f8c8` passed `V11 Control Plane Validation` run `30922580856`.

- Control-plane job `92036674231`: success; artefact `8897706251`, digest `sha256:11fdbf1f311f4456758ad91309224e12147fcd03422f79b07fceee9dd9bb2fa9`.
- Visible pinned-Chromium job `92036674360`: success; artefact `8897732196`, digest `sha256:4d37c3c67fb6d7718ed6b5bd80e103f09b776a30a800f41dc6429230553d6f97`.
- Immutable public-endpoint job `92036674258`: success; artefact `8897714477`, digest `sha256:757a877664cd997b7ea4688425976681f2f3ed31e57c8a57f9ec7e1c99fd6040`.
- Chromium reconfirmed 24 strings × 30 modules, 12 MPPT groups, 24 physical inputs, authorised sequential/leapfrog traversal, mobile-safe scrolling and the 12 × 20 non-default case.

## Numbered engineering targets

- [x] 1. Connector-marker visual contract: central browser contract, black cable bodies, red/blue connector markers, orange inverter, dashed black provisional routes, unique connector IDs, computed-style validation and structured exact-head evidence.
- [ ] 2. Module/junction-box symbol V1: explicit `JBOX_NEG` and `JBOX_POS` nodes; 30 modules, 60 terminals and 60 markers for selected STR-01.
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

Target 1 is wired into the authoritative browser dependency path. Its browser module emits `globalgrid2050.v11.sld-visual-contract.v1` evidence containing the exact tested SHA, connector identities and counts, cable/marker/inverter/route computed-style mismatches and pass/fail. The existing pinned-Chromium acceptance treats a stable contract failure as a page error.

## Next pass

Resolve the new exact PR head and consume its PR-visible `V11 Control Plane Validation` receipt. If green, begin Target 2 only. If red, repair only the first proven CI defect. If pending, make no commit.
