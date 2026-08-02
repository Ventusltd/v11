from __future__ import annotations
import argparse, html, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def load_surfaces(root: Path) -> tuple[dict, dict, dict, dict]:
    state = load(root / "programme-state.json")
    return (
        state,
        load(root / state["build_plan"]),
        load(root / state["capability_matrix"]),
        load(root / state["source_resource_register"]),
    )

def render_readme(state: dict, plan: dict, caps: dict, register: dict) -> str:
    active = next(unit for unit in plan["units"] if unit["id"] == state["current_unit"])
    resource = register["resources"][0]
    capability_lines = "\n".join(
        f"- `{item['id']}` — **{item['name']}**: `{item['state']}`"
        for item in caps["capabilities"]
    )
    unit_lines = "\n".join(
        f"- `{item['id']}` — **{item['title']}**: `{item['status']}`"
        for item in plan["units"]
    )
    return f"""# V11 Engineering Operating System

V11 is the sole active engineering and programme-authority repository for the GlobalGrid2050 solar engineering system. It is being built as a deterministic, evidence-led control plane before any laboratory capability is migrated.

<!-- V11-STATUS:START -->
## Current machine state

| Field | Authority |
|---|---|
| Active repository | `{state['active_repository']}` |
| Programme | `{state['programme_id']}` |
| Programme status | `{state['programme_status']}` |
| Active unit | `{active['id']} — {active['title']}` |
| Current objective | {state['current_objective']} |
| Next authorised unit | `{'none' if state['next_unit'] is None else state['next_unit']}` |
| Validation | `{state['validation']['status']}` |
| Final V11-001 TEST PASS | **not claimed** |
| Operator-session limit | `{plan['operator_protocol']['session_limit_seconds']} seconds` |

The control-plane capability is `under_validation`. A branch, file, local execution or laboratory result does not constitute a final V11 pass.
<!-- V11-STATUS:END -->

## Repository boundary

Only `Ventusltd/v11` may receive new implementation, tests, workflows, receipts, ledgers or programme-state changes.

The former laboratory is a pinned read-only resource:

- Repository: `{resource['repository']}`
- Anchor: `{resource['anchor_commit']}`
- Mode: `{resource['mode']}`
- Licence: `{resource['licence']}`

Laboratory evidence may be inspected, cited, adapted or reimplemented with exact provenance. It is not current V11 authority and must not receive commits, branches or pull requests.

## Programme units

{unit_lines}

`V11-002` is planned but not authorised while `next_unit` remains null.

## Capability state

{capability_lines}

## Deterministic projections

`index.html` and this README are rendered from:

- `programme-state.json`
- `{state['build_plan']}`
- `{state['capability_matrix']}`
- `{state['source_resource_register']}`

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

- `{state['current_quantum_spawn']}`
- `trueself/202608021707-v11-does-not-get-stuck-trueself-chatgpt.md`
- `quantum_spawn/202608021855-complete-thread-record-laboratory-to-v11-control-plane-chatgpt.md`
"""

def render_index(state: dict, plan: dict, caps: dict, register: dict) -> str:
    active = next(unit for unit in plan["units"] if unit["id"] == state["current_unit"])
    resource = register["resources"][0]
    units = "".join(
        f"<tr><td><code>{html.escape(item['id'])}</code></td><td>{html.escape(item['title'])}</td><td><span class='state'>{html.escape(item['status'])}</span></td></tr>"
        for item in plan["units"]
    )
    capabilities = "".join(
        f"<tr><td><code>{html.escape(item['id'])}</code></td><td>{html.escape(item['name'])}</td><td><span class='state'>{html.escape(item['state'])}</span></td></tr>"
        for item in caps["capabilities"]
    )
    next_unit = "None authorised" if state["next_unit"] is None else state["next_unit"]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>V11 Control Plane</title>
<style>
:root{{--bg:#0b0d10;--panel:#14181d;--text:#edf1f5;--muted:#9da8b3;--line:#2a3139;--accent:#f2c94c}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--text);font:16px/1.5 system-ui,sans-serif}}
main{{max-width:1100px;margin:auto;padding:48px 24px 80px}} h1{{font-size:clamp(2.4rem,7vw,5.5rem);line-height:.95;margin:0 0 18px}}
h2{{margin-top:40px}} .eyebrow,.state{{color:var(--accent);font-weight:700;text-transform:uppercase;letter-spacing:.08em}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}} .card{{background:var(--panel);border:1px solid var(--line);padding:20px}}
.card strong{{display:block;font-size:1.25rem;margin-top:6px}} table{{width:100%;border-collapse:collapse;background:var(--panel)}}
th,td{{text-align:left;padding:12px;border-bottom:1px solid var(--line)}} code{{overflow-wrap:anywhere}} .warning{{border-left:4px solid var(--accent);padding:14px 18px;background:var(--panel)}}
a{{color:var(--text)}} footer{{color:var(--muted);margin-top:48px}}
</style>
</head>
<body><main>
<p class="eyebrow">GlobalGrid2050 engineering authority</p>
<h1>V11 Control Plane</h1>
<p>Deterministic status projection from V11 machine-state files. This page displays authority; it does not create it.</p>
<div class="warning"><strong>V11-001 is under validation.</strong> No final TEST PASS is claimed and no later unit is authorised.</div>
<section class="grid">
<div class="card">Active repository<strong>{html.escape(state['active_repository'])}</strong></div>
<div class="card">Active unit<strong>{html.escape(active['id'])} — {html.escape(active['title'])}</strong></div>
<div class="card">Validation<strong>{html.escape(state['validation']['status'])}</strong></div>
<div class="card">Next unit<strong>{html.escape(next_unit)}</strong></div>
</section>
<h2>Current objective</h2><p>{html.escape(state['current_objective'])}</p>
<h2>Programme units</h2><table><thead><tr><th>ID</th><th>Unit</th><th>State</th></tr></thead><tbody>{units}</tbody></table>
<h2>Capabilities</h2><table><thead><tr><th>ID</th><th>Capability</th><th>State</th></tr></thead><tbody>{capabilities}</tbody></table>
<h2>Read-only laboratory resource</h2>
<div class="card"><p><strong>{html.escape(resource['repository'])}</strong></p><p>Anchor: <code>{html.escape(resource['anchor_commit'])}</code></p><p>Mode: <span class="state">{html.escape(resource['mode'])}</span></p><p>Laboratory results are not current V11 authority.</p></div>
<h2>Validation commands</h2>
<pre><code>python -S scripts/validate_control_plane.py
python -S -m unittest -v tests/test_control_plane.py
python -S scripts/generate_control_plane_projection.py --check</code></pre>
<footer>Programme <code>{html.escape(state['programme_id'])}</code> · generated deterministically with no runtime timestamp.</footer>
</main></body></html>
"""

def projections(root: Path) -> dict[Path, str]:
    state, plan, caps, register = load_surfaces(root)
    return {
        root / "README.md": render_readme(state, plan, caps, register),
        root / "index.html": render_index(state, plan, caps, register),
    }

def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    expected = projections(args.root.resolve())
    drift = [str(path.relative_to(args.root.resolve())) for path, content in expected.items() if not path.is_file() or path.read_text(encoding="utf-8") != content]
    if args.check:
        if drift:
            raise SystemExit("projection drift: " + ", ".join(drift))
        print("projection check passed: README.md, index.html")
        return 0
    for path, content in expected.items():
        path.write_text(content, encoding="utf-8")
    print("generated: README.md, index.html")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
