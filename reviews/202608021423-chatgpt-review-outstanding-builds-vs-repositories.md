# ChatGPT Review — Outstanding Builds Against the Actual Repositories

**Date:** 2026-08-02 14:23 Europe/London  
**Status:** Repository-grounded design review; not machine authority  
**Source reviewed:** [`quantum_spawn/202608021421-outstanding_builds_claude_ai.md`](../quantum_spawn/202608021421-outstanding_builds_claude_ai.md)  
**V11 source commit:** `c898ad3771540f2745a8dd446414ac823bc22375`  
**Laboratory boundary inspected:** `deef5545996dc068e054e6cb14204d30541ffe61`  

## Review boundary

I compared the Claude outstanding-builds document against the files actually present in both repositories. In V11 I inspected the current Trueself, the outstanding-builds document, the ChatGPT handover, the licence and the minimal README state. In the laboratory I inspected the Build 026 machine plan, `programme-state.json`, `pyproject.toml`, the named subprocess-bearing tests, the authority bridge and end-to-end harness, the equipment-profile model and the existing evidence-class definition.

I did not execute the test suite or inspect new GitHub Actions artefacts in this review. Statements about code structure are verified from repository content. Statements about runtime behaviour remain proposals unless already represented by recorded laboratory evidence.

## Overall judgement

The document is a strong engineering design review, especially on timeout containment, determinism, quantity meaning, datasheet provenance and evidence monotonicity. Its broad technical direction is consistent with the real weaknesses and planned work in the laboratory.

It is not, however, an authoritative Build 026 Quantum Spawn. It is stored in V11 while directing work in the laboratory; it proposes units that do not exist in the laboratory machine plan; and several implementation prescriptions either duplicate code already present, introduce unacknowledged dependencies or exceed the acceptance boundary of the existing units.

The correct treatment is therefore:

> retain it as valuable cross-repository research input; do not execute it verbatim as the laboratory build plan.

The laboratory machine plan remains authoritative. V11 may explain and review laboratory state, but it cannot silently redefine it. This is especially important because the V11 founding handover states that V11 references the laboratory and the laboratory never depends on V11.

## What the document verifies correctly

### The licence decision is complete

The opening note is correct. GPL-3.0 is now present in both V11 and the laboratory. This is no longer a reserved undecided item in practical repository state, although the old Build 026 plan text still records the licence as reserved because the plan predates the Product Owner decision.

### B026-07 remains the only machine-authorised next unit

The laboratory Build 026 plan still states:

- `programme_status`: `active`;
- `next_unit`: `B026-07`;
- B026-01 through B026-06: passed;
- B026-07: planned.

`programme-state.json` also names `B026-07 — Deliberate root gitignore` as the next single goal. A root `.gitignore` is absent at the inspected head.

### The test dependency observation is correct

The test optional dependencies in `pyproject.toml` are currently only:

- `build>=1.2`;
- `pytest>=8`.

`pytest-timeout`, Hypothesis, Vale and the other tools mentioned in the proposal are not currently declared.

### Six untimed subprocess call sites exist in the five named test files

The named test files do contain six syntactic `subprocess.run` call sites without explicit timeouts:

- two in `tests/test_microbuild_runner.py`;
- one in `tests/test_programme_state.py`;
- one in `tests/test_capsule_links.py`;
- one helper call site in `tests/test_reference_block_command.py`;
- one in `tests/test_end_to_end_authority_slice.py`.

The concern is real. The observation is nevertheless narrower than the full execution path: `scripts/run_authority_slice.py` itself also starts subprocesses without explicit timeouts for authority-bundle generation, browser checks and clean-wheel validation. Adding timeouts only to the test wrappers would not bound every child process reached by the direct `run_authority_slice()` test.

### The current Quantum Spawn pointer is inconsistent with the named current build

`programme-state.json` names Build 026 as current but still points `current_quantum_spawn` at the completed TS-005 twenty-step autopilot document. The Build 026 machine plan correctly points at `docs/quantum-spawn/202608011536-build-026-forty-pass-small-step-law.md`.

This is a genuine continuity inconsistency. The Claude document is right to identify it. It is wrong to place its repair inside B026-07, whose declared scope is limited to root ignore hygiene.

## The principal governance defect

### B026-H and B026-D do not exist

The actual machine plan requires:

- twenty BUILD PASS receipts;
- twenty TEST PASS receipts;
- forty total passes;
- units B026-01 through B026-20;
- one fixed test identifier per unit.

The proposed `B026-H` and `B026-D` lettered insertions have no machine-plan entries, ordinals, receipt paths, allowlisted test identifiers or place in the forty-pass completion arithmetic. Executing either from this V11 document would bypass the system the work is meant to protect.

There are only two legitimate routes:

1. leave Build 026 unchanged and defer the additional harness and determinism programme to a later authorised build; or
2. have the Product Owner formally amend the laboratory machine plan, totals, unit sequence, evidence rules and ledger before any inserted work begins.

A lettered shadow sequence is the worst option because it appears to preserve numbering while actually creating unrepresented engineering state.

The V11 handover already records the opposite governing decision: existing build numbering should remain stable, with later improvements incorporated only where they genuinely fit or deferred to later programmes. The outstanding-builds document should therefore be treated as a proposal to the Product Owner, not an amendment.

## Review of the proposed harness repair

### Timeout containment is high value, but the root cause remains unproven

The laboratory evidence proves that one serial run consumed the 300-second boundary after 184 of 377 tests and that sharded runs completed. It does not prove whether the cause was a full pipe, a child-process deadlock, a fixed port, a shared directory or another resource interaction.

Adding timeouts is justified as containment even without a confirmed diagnosis. The review should describe it as making hangs bounded and observable, not as repairing a proven pipe-buffer deadlock.

### Port zero is already used in the end-to-end harness

The proposal says to bind the bridge to port zero in tests and read `server_address[1]`. The actual `running_bridge()` context manager already does exactly that:

```python
server = create_server(host="127.0.0.1", port=0, strategy=strategy)
host, port = server.server_address[:2]
```

The bridge CLI still defaults to port `8765`, but the current end-to-end test path already uses an ephemeral port. This item is therefore partly complete and should not be represented as wholly outstanding.

### Timeouts belong at the process-owning layer

The proposal targets the six test call sites. That is useful but incomplete. The direct end-to-end test calls `run_authority_slice()` in-process, and that function launches several subprocesses internally. The robust rule is:

> every code path that owns a child process owns its timeout, error conversion and diagnostic output.

Test-level timeouts remain a final containment boundary; subprocess-level timeouts provide the actionable failure location.

### Default deselection of integration tests would weaken the declared envelope

The proposal marks the wheel and browser gates as integration tests and then adds default `-m "not integration"`. That would make a normal `pytest` run exclude part of the authority journey while the repository continues to speak of a full 377-test envelope.

Separating a fast developer profile from a complete authority profile is reasonable. Silently redefining the default suite is not. Any split must preserve an explicit repository-controlled command that still runs the complete declared envelope and must update test counts and programme claims truthfully.

### A 120-second deliberate sleep is unnecessary

A timeout mechanism can be tested with a deliberately short child process and a test timeout of one or two seconds in the focused fixture. Spending approximately sixty seconds to prove a sixty-second ceiling is valid but wasteful under a bounded-pass regime. The production ceiling may remain sixty seconds while the mechanism test uses a smaller controlled value.

## Review of the determinism probe

The proposed cross-seed, cross-process comparison is one of the strongest additions in the document. The existing repository performs deterministic serialisation carefully in many places, but the current evidence proves specific reference outputs, not general independence from Python hash randomisation.

The probe should use the actual authoritative command or bundle generator and compare canonical bytes and receipt hashes under at least two different `PYTHONHASHSEED` values in separate processes.

A fixed CI seed is not a substitute for this test. Pinning one seed can make one environment repeatable while masking sensitivity to another seed. The higher-value gate is equality across deliberately different seeds; a fixed seed may then be retained for reproducible diagnostics.

This work still cannot be inserted into Build 026 without an authorised plan amendment.

## Review of B026-07

The proposed `.gitignore` contents are broadly sensible. The actual unit acceptance is more important than the precise template source:

- no tracked engineering file becomes ignored;
- no tracked file is removed;
- a complete declared validation run leaves the tree clean;
- untracking is deferred.

The suggestion to repair `current_quantum_spawn` inside this unit must be rejected. That is unrelated programme-state work and would violate the exact scope and the programme's own anti-expansion law.

## Review of B026-08

The proposal is well aligned with the machine plan. The actual bridge already:

- accepts a host and port;
- accepts port zero;
- reads back the actual bound address;
- prints a JSON object containing the Studio URL;
- exposes a ready health route.

What is genuinely missing is the supported package-level console entry point, one documented installation sequence, one documented start command and a clean-clone smoke test. B026-08 should build on the existing bridge rather than replace it.

## Review of B026-09 and B026-10

### Quantity-kind typing is correctly prioritised

`QualifiedValue` currently carries value, unit, evidence class, verification state, source reference, source revision and note. It does not carry quantity kind. This makes it the natural schema boundary for B026-09.

The proposed enum should not be frozen from this review before exact source terminology is established. The current equipment model uses names such as:

- `isc_a`;
- `imp_a`;
- `voc_v`;
- `vmp_v`;
- `maximum_overcurrent_protection_rating_a`;
- `maximum_dc_voltage_v`.

The current generic inverter profile does not yet contain the operating-current and short-circuit-current limit fields needed for the intended comparison examples. B026-09 therefore needs either to extend the qualified equipment schema or to bind those limits through the B026-11 fixture. Merely adding an enum to existing values is not enough to make B026-10 executable.

### The explanation involving Python rich-comparison fallback is unsupported

The four-model error documented in the laboratory occurred in prose and AI reasoning: `Isc` was compared conceptually with an operating-current limit, then repeated and embellished. It was not caused by Python returning `False` or `NotImplemented` from a rich comparison.

A code guard remains valuable because it can prevent the same semantic error in future calculations. The rationale should be corrected: it prevents a class of future software error; it did not cause or catch the original prose error.

An explicit comparison function may be safer than overloading ordinary scalar comparison, because it forces the method, conditions and limit semantics to remain visible.

## Review of B026-11 and B026-12

The datasheet-fixture direction is correct, but the repository already has an evidence-qualified value model and deterministic payload machinery. B026-11 should extend and reuse those contracts rather than create a parallel provenance system.

The claims about the absence of an open PV datasheet schema and the proposed use of pvlib naming are external design research, not facts established by the repositories inspected here. They may be good choices, but they require their own cited decision record.

The six rear-gain figures are legitimate acceptance targets from the continuity review, but they are not current laboratory authority. The actual equipment profile still marks module `Voc`, `Isc`, `Vmp`, `Imp`, bifaciality, dimensions and factory-lead lengths unresolved. B026-12 must obtain them through the versioned fixture before reproducing or presenting them.

## Review of B026-13

This is the most important technical correction to the Claude proposal.

The existing `EvidenceClass` is a categorical `StrEnum` containing:

- manufacturer declared;
- field measured;
- public observation;
- user created;
- derived;
- generic example;
- assumed;
- external reference.

These values do not form one obvious universal strength ordering. `DERIVED` describes how a value was produced, while `FIELD_MEASURED` and `MANUFACTURER_DECLARED` describe source origin. `EXTERNAL_REFERENCE` may be stronger or weaker depending on the question. Turning them into ordered integers and taking `min` would collapse provenance category and evidential confidence into one axis.

Evidence monotonicity is still essential, but the implementation should first separate or explicitly model:

- evidence origin;
- verification state;
- assumption status;
- derivation lineage;
- any confidence or authority ordering actually required.

A meet operation should be an explicit table or structured propagation rule, not lexical comparison and not an assumed total order. The derived output should preserve its source lineage while refusing to claim a verification or authority status stronger than its weakest required input.

The proposed property-based test also implies an undeclared Hypothesis dependency. A small table-driven invariant suite can establish the first contract without broadening the toolchain; property-based testing can be a separately authorised enhancement.

## Review of B026-14 through B026-17

The cold-Voc unit is correctly method-bound and should keep tolerance off unless selected. The proposed statistical tolerance mode goes beyond the current machine-plan requirement and should not be invented without a documented engineering method.

String-group profile binding is well aligned with the plan. The byte-identical legacy requirement must remain conditional on schema compatibility; a necessary schema-version change should be enumerated rather than suppressed.

The per-pole lead calculation is a valid expected correction, but the actual equipment contract still marks both lead lengths unresolved. The 350 mm and 280 mm values cannot become production authority until B026-11 binds them to an exact source revision.

Slack defaulting to unresolved is correct. A simple coiled/not-coiled flag may be insufficient for later electromagnetic work, but B026-17 should remain narrow and avoid inventing inductance from unevidenced geometry.

## Review of B026-18 through B026-20

The assumption register is valuable, but it should record assumptions already used by the engine rather than seed new defaults merely because they appeared in discussion. Relative permittivity, minimum temperature, tolerance policy and bifaciality must each retain their real source and current status. Date-expiry checks also need an explicit clock and timezone to remain deterministic.

The contradiction gate should begin with named claims in authoritative machine-readable or deliberately structured governance documents. Attempting to mine every prose document into a value dictionary would create a large and brittle interpretation layer.

Commit ancestry is not the same as observation expiry. A commit can remain an ancestor while the observed file or fact has changed later. Conversely, a non-ancestor commit can still be a valid historical observation. A stronger snapshot contract binds the observation to:

- repository;
- commit;
- target path or object;
- content hash where applicable;
- statement of what was observed;
- rule for determining whether the observation is still being presented as current.

The proposed Vale verdict gate introduces a new external tool and configuration system into a repository that is currently predominantly Python plus small JavaScript gates. A repository-local Python validator is the proportionate first implementation unless Vale is separately selected and pinned.

## The laboratory/product split is now recorded, but not yet machine-enforced

The Claude source ends by saying the laboratory/product split is recorded nowhere. That statement became stale almost immediately. V11 now contains `quantum_spawn/202608021305-chatgpt-handover.md`, which explicitly states:

- the long repository is the laboratory;
- V11 is the product;
- V11 references the laboratory;
- the laboratory never depends on V11;
- Python calculates;
- GitHub validates;
- V11 presents and supervises.

What remains missing is a concise V11 Genesis Quantum Spawn, a V11 machine-readable state model and a browser implementation that enforces that boundary. The split is now documented in V11, but the laboratory itself still does not carry a forward dependency on V11, which is correct.

This rapid invalidation of the Claude observation is itself evidence for the proposed snapshot-bound claim discipline.

## Recommended disposition

### Accept as design input

Retain the following ideas:

- explicit subprocess timeouts at the process-owning layer;
- a final test-level hang boundary with diagnostics;
- cross-seed and cross-process determinism proof;
- B026-07 through B026-20's existing broad sequence;
- quantity-kind compatibility;
- versioned datasheet evidence;
- evidence monotonicity;
- explicit cold-voltage method;
- per-pole leads, slack and assumptions;
- contradiction and verdict controls.

### Reject as current authority

Do not execute:

- `B026-H` or `B026-D` as lettered hidden units;
- programme-state correction inside B026-07;
- default exclusion of authority integration gates while preserving old full-suite claims;
- ordered-integer `EvidenceClass` without redesigning the taxonomy;
- unverified external schema and tooling claims as though selected;
- Vale, Hypothesis or other new dependencies without explicit scope and lock/version decisions.

### Exact next action under the repositories as they stand

The only authorised laboratory action remains:

> **B026-07 — Deliberate root `.gitignore`**, exactly within its existing scope.

If the Product Owner decides timeout containment or the determinism probe must occur first, the next action is not code. It is a formal laboratory plan amendment that gives those units real ordinals, tests, receipts, totals and stop conditions. V11 cannot provide that authority by hosting a persuasive document.

## Final position

The Claude outstanding-builds document improves the engineering discussion and identifies several high-value controls. Its strongest contributions are the timeout boundary, deterministic perturbation test and detailed translation of the planned semantic units into implementable shapes.

Its weakness is the same weakness the programme is designed to prevent: good reasoning begins to outrun authoritative state. It proposes extra work outside the machine plan, places a programme-state repair inside the wrong unit, repeats a port-zero change already present, under-bounds the actual subprocess-owning layer and simplifies evidence classes into an ordering the current model does not support.

The correct outcome is not to discard it. It is to preserve it as a witness, take its strongest ideas through Product Owner selection, and then express selected work in the appropriate repository's machine-authoritative plan before implementation begins.
