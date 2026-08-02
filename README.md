# V11 Engineering Operating System

V11 is the sole active engineering and programme-authority repository for the GlobalGrid2050 solar engineering system. It is being built as a deterministic, evidence-led control plane before any laboratory capability is migrated.

<!-- V11-STATUS:START -->
## Current machine state

| Field | Authority |
|---|---|
| Active repository | `Ventusltd/v11` |
| Programme | `v11-native-control-plane-20260802` |
| Programme status | `active` |
| Active unit | `V11-001 — Active repository control plane` |
| Current objective | Establish the V11-native control plane without claiming laboratory capabilities as current V11 authority. |
| Next authorised unit | `none` |
| Validation | `pending` |
| Final V11-001 TEST PASS | **not claimed** |
| Operator-session limit | `300 seconds` |

The control-plane capability is `under_validation`. A branch, file, local execution or laboratory result does not constitute a final V11 pass.
<!-- V11-STATUS:END -->

## Repository boundary

Only `Ventusltd/v11` may receive new implementation, tests, workflows, receipts, ledgers or programme-state changes.

The former laboratory is a pinned read-only resource:

- Repository: `Ventusltd/solar-electrical-topology-analysis-engine-text-based`
- Anchor: `d3b4c497144c2c9b3e8f0e82117e7e9abe4672b9`
- Mode: `read_only`
- Licence: `GPL-3.0`

Laboratory evidence may be inspected, cited, adapted or reimplemented with exact provenance. It is not current V11 authority and must not receive commits, branches or pull requests.

## Programme units

- `V11-001` — **Active repository control plane**: `active`
- `V11-002` — **Clean installation and one start command**: `planned`
- `V11-003` — **Laboratory resource adapter**: `planned`
- `V11-004` — **First migrated engineering capability**: `planned`

`V11-002` is planned but not authorised while `next_unit` remains null.

## Capability state

- `CAP-CONTROL-PLANE` — **V11 engineering control plane**: `under_validation`
- `CAP-CLEAN-START` — **Clean installation and one start command**: `planned`
- `CAP-LAB-ADAPTER` — **Pinned read-only laboratory resource adapter**: `planned`
- `CAP-FIRST-ENGINEERING` — **First migrated engineering capability**: `awaiting_product_owner_selection`

## Deterministic projections

`index.html` and this README are rendered from:

- `programme-state.json`
- `build-plans/v11-native-control-plane.json`
- `capabilities/v11-capability-matrix.json`
- `resources/source-resource-register.json`

Regenerate them:

```bash
python -S scripts/generate_control_plane_projection.py
```

Check for drift without writing:

```bash
python -S scripts/generate_control_plane_projection.py --check
```

Validate the current machine surfaces:

```bash
python -S scripts/validate_control_plane.py
python -S -m unittest -v tests/test_control_plane.py
```

## Outstanding V11-001 work

V11-001 remains incomplete until repository-controlled validation exists and passes. The remaining governed work includes the GitHub Actions workflow, exact CI-tested SHA and artefact evidence, machine receipt, ledger closure, capability-state transition and programme advancement.

No engineering capability migration or V11-002 implementation is authorised yet.

## Governing continuity

- `quantum_spawn/202608021556-v11-single-active-repository-and-laboratory-resource-boundary-chatgpt.md`
- `trueself/202608021707-v11-does-not-get-stuck-trueself-chatgpt.md`
- `quantum_spawn/202608021855-complete-thread-record-laboratory-to-v11-control-plane-chatgpt.md`
