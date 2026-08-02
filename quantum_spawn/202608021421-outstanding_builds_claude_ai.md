Repo moved while we were talking — head is now deef554, "license: adopt GPL-3.0", applied to the laboratory. So that decision has been made rather than deferred. Noting it once and leaving it.

Verified before writing: six untimed subprocess sites across five test files, `build/` is not tracked, test extras are only `build` and `pytest`, next permitted unit is still B026-07.

**B026-H — Harness repair (insert before B026-07)**
- Not in the plan; propose adding it as a lettered insert so numbering stays stable
- Add `timeout=` to six `subprocess.run` sites in `tests/test_microbuild_runner.py`, `test_programme_state.py`, `test_capsule_links.py`, `test_reference_block_command.py`, `test_end_to_end_authority_slice.py`
- Add `pytest-timeout` to `[project.optional-dependencies].test`; configure `timeout = 60`, `timeout_method = "thread"` (thread avoids SIGALRM colliding with subprocess code)
- Set `faulthandler_timeout = 90` so a hang dumps all thread tracebacks and names the test
- Bind the bridge in `scripts/local_authority_bridge.py` to port 0 in tests; read back `server_address[1]`
- Move wheel-build/browser gates in `test_end_to_end_authority_slice.py` behind `@pytest.mark.integration`, deselect by default via `addopts = -m "not integration"`
- Route all artefact-producing tests through `tmp_path`; never the checkout
- TEST: introduce a deliberate `sleep(120)`, confirm failure at ~60 s with a traceback, then remove
- Acceptance: no run can consume the 300 s ceiling silently; full suite still 377/377

**B026-D — Determinism probe (insert, minutes)**
- `PYTHONHASHSEED=0` and `PYTHONHASHSEED=1`, generate receipts in two separate processes, diff
- If hashes differ: set/dict iteration is leaking into receipts — stop and fix before any further unit
- Fix channels if found: sort all `set`/`frozenset` iteration feeding a receipt; sort `os.listdir`/`glob`; pin TZ=UTC and LC_ALL=C
- Pin `PYTHONHASHSEED` in CI and in the harness
- Acceptance: identical hashes across both seeds and across two processes

**B026-07 — Deliberate root .gitignore**
- Compose from current official GitHub Python and Node templates; do not hand-write from memory
- Cover: `__pycache__/`, `*.py[cod]`, `.venv/`, `build/`, `dist/`, `*.egg-info/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `node_modules/`, editor and OS clutter, `.microbuild/candidates/`
- `build/` is confirmed untracked, so no `git rm --cached` needed in this unit
- Do NOT untrack anything else here — any tracked file proposed for removal goes to its own reviewable unit
- TEST: no currently tracked file becomes ignored; `git status` clean after a full suite run
- Acceptance: adding the file removes nothing from tracking

**B026-08 — One clean installation and one start command**
- Add `[project.scripts]` console entry point
- Entry point starts the authority service and prints the address it actually bound to (pairs with the port-0 change)
- One documented install sequence in README; exactly one start command
- TEST: scripted fresh-clone → documented install → start → Studio reachable, with zero remembered preparation
- Acceptance: a stranger reaches a running Studio from a clean machine

**B026-09 — Quantity-kind typing**
- Add a `QuantityKind` enum: `SHORT_CIRCUIT_CURRENT`, `MAX_POWER_CURRENT`, `OPERATING_CURRENT_LIMIT`, `DAMAGE_LIMIT_CURRENT`, `OPEN_CIRCUIT_VOLTAGE`, `MAX_POWER_VOLTAGE`
- Attach kind to every qualified value in `src/solar_topology/equipment_profiles.py`
- Vocabulary borrowed from QUDT's quantity-kind model; do not import an RDF stack
- Tag at array/column granularity, never per scalar — per-scalar wrapping is fatal in hot loops
- No comparison behaviour in this unit
- TEST: every relevant field carries a kind; enumerate any serialisation or hash change
- Acceptance: no calculation result changes

**B026-10 — Comparison compatibility guard**
- A guard that raises `IncompatibleKindError` rather than returning `False`/`NotImplemented`
- Python's rich-comparison fallback is exactly what let the error propagate silently
- Provide `same_kind(a, b) -> bool` for callers legitimately wanting a boolean
- TEST: Isc vs operating-current-limit raises; Imp vs operating-current-limit permitted; error message names both kinds
- Acceptance: the four-model error becomes impossible to write down

**B026-11 — Versioned datasheet evidence fixture**
- Genuine from-scratch design: no open PV module datasheet schema exists (SunSpec covers communicating devices; CEC ships fitted coefficients; EU DPP has no adopted PV act)
- Reuse pvlib parameter naming for interoperability: `V_oc_ref`, `I_sc_ref`, `V_mp_ref`, `I_mp_ref`, `alpha_sc`, `beta_oc`, `gamma_r`, `cells_in_series`, bifaciality
- Source-identity block per document: manufacturer, model, revision, date, retrieval URL, sha256 of the source PDF
- Every value carries an evidence class (manufacturer-declared for datasheet figures)
- Canonicalise JSON before hashing so key order cannot perturb the result
- TEST: fixture round-trips to a stable sha256; no arithmetic anywhere reads a literal from prose
- Acceptance: two datasheet revisions produce different fixture hashes

**B026-12 — Rear-gain current screening**
- Load Impp and Isc for front-side and both published rear-gain bins from the B026-11 fixture
- Screen per-MPPT headroom using correctly matched kinds only
- Expected: 34.70 / 36.44 / 38.18 A on max-power current against the 40 A operating limit; 36.90 / 38.74 / 40.60 A on short-circuit current against the 60 A short-circuit ceiling
- Return a screening result with margin and evidence class — must not emit "compliant" or "exceeds"
- Handle undeclared rear gain as unresolved, never as a silent zero
- TEST: all six figures reproduce; verdict vocabulary absent from output

**B026-13 — Evidence-class monotonicity**
- Derived value inherits the weakest class among its inputs; never stronger
- Encode classes as ordered integers so the meet is `min`, not a lexical compare
- Propagate at array/batch level; fall to per-element only where an array genuinely mixes classes
- TEST: property-based — no derivation stronger than its weakest input; assumed permittivity yields assumed capacitance
- Acceptance: list any canonical result whose class is downgraded

**B026-14 — Cold Voc with explicit method**
- `temperature_case` and `tolerance_policy` as explicit, non-defaulted arguments, both recorded in the receipt
- Tolerance policy needs at least two modes: correlated worst-case, and independent/statistical
- Tolerance NOT applied by default — it must be selected
- Expected: 1377 V at STC; ~1497.5 V at the −10 °C illustrative case against the 1500 V ceiling
- TEST: changing either parameter changes result and hash; Voc strictly increases as temperature falls

**B026-15 — String-group module-profile binding**
- Scope chain: project → string-group → string, resolving narrowest first
- Receipt records which profile bound at which scope
- TEST: two groups with different power bins coexist in one block; the existing single-profile reference block produces byte-identical output

**B026-16 — Per-pole factory-lead lengths**
- Hold positive and negative lead lengths separately (350 mm / 280 mm)
- Routing consumes per-pole values; installed-length receipts change
- Expected: 2.1 m asymmetry per 30-module string; 50.4 m per 24-string block
- This corrects a real prior understatement — enumerate every changed hash explicitly
- TEST: string and block totals reproduce; receipts updated with the change declared

**B026-17 — Declared slack and coil geometry**
- Slack as a first-class declared quantity defaulting to **unresolved**, not zero
- Record whether slack is coiled; carry the loop-area caveat rather than computing an inductance nobody can source
- TEST: declared slack contributes to conductor length and appears in the receipt; undeclared slack surfaces as unresolved

**B026-18 — Named assumption register**
- One entry per assumption: id, statement, owner, status, evidence class, review date
- Seed with: relative permittivity ≈ 7, minimum temperature case, tolerance policy, bifaciality default
- MADR-style Markdown with front-matter; versions with the code
- TEST: every entry has owner and review date; an expired assumption fails the lint; each id is referenceable from a receipt

**B026-19 — Governance contradiction gate**
- Typed front-matter claims per governance doc; CI builds a name→value dict
- Fails when two docs assert different values for the same named quantity without an explicit `supersedes:` pointer
- Reuse the B026-09 kind check so different-kind values aren't compared as equal
- TEST: seeded contradiction (70 % vs 80 % bifaciality) fails; supersession clears it

**B026-20 — Snapshot expiry and verdict vocabulary gates**
- Expiry: observational claims carry the commit SHA; flag via `git merge-base --is-ancestor` when no longer an ancestor of HEAD
- Requires full-depth fetch in CI — shallow clones give wrong ancestry answers
- Verdict gate: *violation, exceeds, complies, fails* permitted only when bound to a named clause and a stated method; implement as a Vale custom style
- Exception scope for quoted standard text
- TEST: seeded stale claim and seeded unbound verdict both fail; correct cases pass
- Both linters run inside the existing envelope, not as separate ceremony

**Standing rules across all units**
- 300 s per build pass, 300 s per test pass — do not raise; exceptions per-unit with reason recorded
- Advance only on both passes recorded; timeout, unexplained red, moving origin, missing evidence or scope expansion all block
- Failed unit: abandon the branch, record blocking evidence, do not repair speculatively
- Fetch origin and record head SHA before each build pass; abandon if origin moves mid-unit
- Ledger entry plus machine receipt per unit; two closing Quantum Spawns only (quantity-kind law, evidence-monotonicity law)
- Any unit changing receipt hashes must enumerate every change — that's 12, 13, 14, 16 and 17

**Reserved to you, not to any agent**
- `current_quantum_spawn` still points at the twenty-step autopilot capsule rather than the Build 026 forty-pass law — same drift class B026-06 just fixed; worth correcting inside B026-07
- The laboratory/product split is recorded nowhere in the repository; needs one Quantum Spawn or it hasn't durably happened
- Authorisation of anything after B026-20
