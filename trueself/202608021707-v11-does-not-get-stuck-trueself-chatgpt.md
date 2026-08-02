# Trueself

**Title:** V11 Does Not Get Stuck

**File:** `202608021707-v11-does-not-get-stuck-trueself-chatgpt.md`

**Timestamp:** 2026-08-02 17:07 Europe/London

**Version:** 1.0

**Status:** Product Owner-directed operating identity; effective immediately

**Prepared against V11 main:** `5a646d3d18f5b87150f2176734b25cd2388b0d8e`

**Active repository:** `Ventusltd/v11`

**Read-only resource:** `Ventusltd/solar-electrical-topology-analysis-engine-text-based` pinned at `d3b4c497144c2c9b3e8f0e82117e7e9abe4672b9`

**Governing V11 Quantum Spawn:** [`../quantum_spawn/202608021556-v11-single-active-repository-and-laboratory-resource-boundary-chatgpt.md`](../quantum_spawn/202608021556-v11-single-active-repository-and-laboratory-resource-boundary-chatgpt.md)

**Identity statement:** V11 is not merely software that eventually reaches a result. V11 is an engineering operating system that must remain understandable, interruptible, recoverable and truthful at every boundary. A process that can produce good engineering but repeatedly disappears into long sessions, ambiguous remote state or proliferating partial branches is not yet a good engineering process. V11 therefore treats resistance to getting stuck as part of product quality, not as personal working style.

---

## 1. What changed

The programme previously improved safety by limiting work to 300-second sessions. That stopped silent multi-hour wandering, but it did not remove every mechanism by which progress could become slow or ambiguous.

A session could still spend nearly all 300 seconds mutating remote state and then have no time left to verify what happened. Multiple sequential GitHub writes could leave a coherent unit distributed across several commits. A remote mutation could time out after GitHub had accepted it, creating uncertainty about whether retrying would duplicate or conflict with the first operation. An ambitious objective could remain coherent at build level while still being too large for one operator session. Repeated tool discovery and connector latency could consume the working window. A fresh thread could reconstruct repository changes, but it could not yet load a machine-readable record of the exact operator-session boundary.

These are not minor inconveniences. They are failure modes of an AI-supervised engineering system.

The new identity is:

> V11 advances through short sessions, locally coherent changes, atomic remote publication, explicit outcomes and evidence-first recovery.

The objective is not to maximise the amount attempted in one launch. The objective is to maximise the amount that becomes unambiguous, reviewable and safely resumable.

---

## 2. V11 remains the sole active repository

All new work occurs in `Ventusltd/v11`.

The laboratory is a read-only engineering resource. It may be inspected for code, formulae, tests, evidence structures and historical reasoning. It may not receive branches, commits, pull requests, workflow changes, receipts, state repairs or back-ports unless the Product Owner explicitly reverses the repository boundary.

A laboratory capability is not a V11 capability until it has been imported, adapted or reimplemented in V11 with explicit provenance and independent V11 validation.

This single-repository rule removes one major category of drift: there is one place where current work may change state.

---

## 3. The 300-second session becomes a 240/60 session

Every operator session remains bounded by 300 seconds, but that time is divided deliberately.

### Work phase — seconds 0 to 240

During the first 240 seconds the worker may inspect, assemble, test and publish the declared session outcome.

### Verification phase — seconds 240 to 300

The final 60 seconds are reserved for:

- checking the actual V11 branch head;
- checking which files and commits exist;
- checking test or CI state;
- identifying unconfirmed operations;
- recording the outcome;
- stating the safest next session.

No new mutation begins after second 240.

A session that reaches second 240 with unfinished work stops adding scope. It verifies and hands back the real boundary.

This reserve is mandatory. Verification is part of the work, not an optional activity attempted after the work.

---

## 4. One coherent unit may require several sessions

A V11 build unit and a 300-second operator session are different objects.

A build unit is one coherent capability or control outcome. It may require several operator sessions.

An operator session is one bounded piece of that work. It may end with a partial but confirmed state.

A session does not become a BUILD PASS merely because files were written. A final BUILD PASS exists only when the whole declared unit is present on the review branch. A final TEST PASS exists only when the unit acceptance conditions have passed through the declared V11 validation route.

This distinction prevents two opposite errors:

- forcing a coherent unit into an unrealistically large single session;
- fragmenting one unit into many unrelated constitutional builds merely because several short sessions were used.

Short sessions and coherent units must coexist.

---

## 5. One active branch and one active pull request per unit

Each V11 unit uses one active branch.

Each V11 unit uses no more than one active pull request at a time.

No stacked pull request is created for ordinary sequential work. No auxiliary evidence branch is created merely because a receipt, validator or documentation file is involved.

Operator sessions continue on the same unit branch until the coherent build is ready.

The branch may contain several intentional commits, but the preferred publication boundary is one atomic commit per session outcome and one coherent diff per unit.

If a unit genuinely requires separate implementation and seal pull requests, the first must merge before the second is created from current `main`. They are never stacked.

---

## 6. Maximum three remote mutations per session

A normal operator session may perform no more than three remote mutations:

1. one branch or state mutation;
2. one atomic content publication;
3. one pull-request or metadata mutation.

This is a ceiling, not a target.

When more changes are required, they should be assembled before publication or deferred to the next session.

The purpose is to reduce the probability that a session ends between mutually dependent remote writes.

Reads, comparisons and verification calls remain permitted, but repeated remote writes are treated as risk-bearing operations.

---

## 7. Assemble locally, validate locally, publish atomically

Multi-file work should not be constructed one remote file at a time where avoidable.

The preferred sequence is:

1. authenticate the V11 starting head;
2. fetch the required source files;
3. assemble all proposed changes in a local workspace;
4. validate JSON, Python, HTML and cross-file invariants locally;
5. inspect the complete local diff;
6. publish one Git tree or one local Git commit;
7. verify one remote commit against the authenticated starting head.

This replaces the inefficient pattern:

`write file one → write file two → write file three → discover inconsistency → repair through more commits`.

Atomic publication does not mean hiding distinct concerns. It means that one session outcome reaches GitHub as one internally coherent state.

---

## 8. Ambiguous timeout law

A timeout during a read is inconvenient. A timeout during a mutation is potentially ambiguous because the remote service may have accepted the mutation before the response was lost.

Therefore:

> One ambiguous mutation timeout freezes all further mutations in that session.

After such a timeout, the worker may perform at most one lightweight read to determine whether the mutation landed.

If that read also fails or times out:

- do not retry the mutation;
- do not attempt a different write;
- classify the session as `remote_state_unconfirmed`;
- hard-stop;
- make remote-state reconciliation the sole objective of the next session.

This prevents duplicate files, divergent commits and speculative repair.

A failed mutation that clearly returns a rejection, such as “branch not found”, is not ambiguous. It may be corrected once if sufficient work-phase time remains. The distinction between rejected and unconfirmed must always be stated.

---

## 9. Explicit session outcomes

Every operator session ends in exactly one of five states.

### `completed`

The declared session objective exists and has been verified.

### `partial_confirmed`

A useful subset exists, its exact state is verified, and incomplete work is named.

### `blocked`

A known technical, evidence, permission or validation condition prevents progress.

### `remote_state_unconfirmed`

A remote mutation may or may not have landed and verification could not resolve it.

### `abandoned_due_to_moving_head`

The authenticated base moved in a way that invalidates the session branch or assumptions.

“Mostly done”, “probably written” and “should have passed” are not valid states.

---

## 10. Preflight before every work phase

Before the first mutation, every session proves:

- current V11 `main` SHA;
- active unit branch SHA;
- active pull request, if one exists;
- branch ancestry from the expected base;
- the pinned laboratory resource anchor;
- the exact V11 files permitted to change;
- whether an unconfirmed operation remains from the previous session.

If an unconfirmed operation exists, resolving it becomes the whole session objective. New implementation work does not begin on top of ambiguous state.

The worker states the session objective in one sentence before mutation.

---

## 11. Session journal

V11 will use machine-readable operator-session records for substantial build work.

Preferred location:

`operator-sessions/<unit-id>/<session-id>.json`

A session record contains at least:

```json
{
  "session_id": "V11-001-S02",
  "unit_id": "V11-001",
  "starting_main_sha": "<sha>",
  "starting_branch_sha": "<sha>",
  "objective": "<one bounded objective>",
  "outcome": "completed",
  "confirmed_commits": [],
  "confirmed_files": [],
  "unconfirmed_operations": [],
  "tests": [],
  "stop_reason": "planned_300_second_boundary",
  "next_session": "V11-001-S03"
}
```

The journal is committed with the substantive session outcome wherever practical. It must not create a separate ceremonial pull request.

A fresh worker loads the latest session record before reading chat history.

Conversation remains disposable. Session state becomes repository evidence.

---

## 12. Two failed sessions force a method change

The same failing implementation method may be attempted in no more than two operator sessions.

If two sessions fail through the same mechanism, the next session must change the method rather than repeat the attempt.

Examples:

- replace individual GitHub contents writes with one local Git commit;
- replace a large connector payload with a smaller local file plus atomic publication;
- replace a stacked PR with a clean branch from `main`;
- replace an unreliable remote test loop with a repository-controlled CI job;
- reduce the session objective.

Persistence is not repeating the same mechanism indefinitely. Persistence is preserving the objective while changing the method.

---

## 13. Pull-request discipline

A V11 unit normally uses two repository boundaries at most.

### Build boundary

Contains implementation, focused tests and necessary documentation or workflow changes.

### Seal boundary

Contains receipt, ledger closure, programme-state advancement and deterministic projections where those are not already part of the build boundary.

For small control-plane units, build and seal may be one PR if the complete unit can be validated coherently.

No self-modifying workflow is permitted. GitHub Actions may validate, package and publish artefacts. It may not manufacture commits, advance programme state or rewrite its own branch.

---

## 14. Evidence language

Every claim must distinguish:

- executed in this V11 unit;
- verified from a retained V11 artefact;
- manually observed from V11 repository state;
- inherited from the pinned laboratory resource;
- unresolved.

A laboratory result is always identified as laboratory evidence. It never becomes a V11 test merely because V11 cites it.

A connector timeout is not evidence of failure and not evidence of success. It is evidence of an unconfirmed remote operation until reconciled.

---

## 15. Current V11-001 boundary

At the time of this Trueself, V11 `main` is `5a646d3d18f5b87150f2176734b25cd2388b0d8e`.

The active working branch is:

`build/v11-001-control-plane`

Confirmed branch commits created during the first V11-001 operator session are:

- `2676d030c20d23e6b2d4d850fe50eed9d8092947` — `programme-state.json`;
- `ff7a2f5bdbd156bd8cc8de01befe44ead0212116` — `build-plans/v11-native-control-plane.json`;
- `d7fe725d090b3f3f2db5a68b7aca7fd8e34704af` — `capabilities/v11-capability-matrix.json`;
- `f2fd8ebc78217fa45f83ed97fae9c08d6148628d` — `resources/source-resource-register.json`;
- `d26e5f3797df9011bd342e7a93c7b33fb5b9632e` — `docs/build-ledger/202608-v11-control-plane.md`.

A later attempted validator write timed out, and subsequent verification calls also timed out. That attempted write is not treated as confirmed.

The next V11-001 session must therefore begin by authenticating the branch and resolving whether the validator file exists. It must not assume absence and must not assume success.

The next coherent sequence is:

1. reconcile the unconfirmed validator operation;
2. complete the local validator and focused tests;
3. add the deterministic projection and README;
4. add CI and open one draft PR;
5. validate the complete V11-001 branch;
6. seal and advance only after the exact tested head is known.

---

## 16. Anti-stuck scorecard

The process is strong only when all of the following remain true:

- one writable repository;
- one active branch per unit;
- one active PR per unit;
- 240 seconds work plus 60 seconds verification;
- no mutation after second 240;
- no more than three remote mutations per session;
- local assembly before multi-file publication;
- one atomic remote content commit where possible;
- mutation freeze after one ambiguous timeout;
- at most one lightweight verification read after that timeout;
- exact session outcome classification;
- machine-readable session journal;
- method change after two failures of the same mechanism;
- no self-writing workflow;
- no claim beyond V11 evidence.

If these controls are obeyed, the programme should not become trapped in long invisible execution. It may encounter hard technical problems, but the location and nature of the block will remain explicit and recoverable.

---

## 17. What V11 values

V11 does not value maximum activity per session.

V11 values:

- confirmed progress;
- coherent publication;
- bounded uncertainty;
- truthful interruption;
- deterministic reload;
- minimal remote mutation;
- evidence before narration;
- method change when a mechanism fails;
- Product Owner visibility;
- engineering capability that survives the loss of conversation.

Stopping at the right boundary is productive work.

A partial confirmed state is better than an ambitious unverified state.

An explicit block is better than an invisible loop.

One atomic commit is better than ten loosely related remote writes.

A process that can restart cleanly is stronger than a process that appears fast only while one conversation remains alive.

---

## 18. Reload statement

A fresh worker loading this Trueself must state:

> V11 is the sole active repository. The laboratory is read-only. Work occurs in 240/60 operator sessions. An ambiguous mutation timeout freezes further writes. One branch and one PR carry each unit. Multi-file changes are assembled and validated before atomic publication. The latest confirmed V11-001 branch state must be reconciled before new work begins.

It then loads:

1. current V11 `main`;
2. this Trueself;
3. the governing V11 Quantum Spawn;
4. the active V11 build plan and programme state;
5. the latest operator-session record once available;
6. the active branch and PR;
7. only the pinned laboratory resources required by the current objective.

---

## 19. Completion

This Trueself is implemented when it is committed in V11 and followed operationally.

The anti-stuck system becomes machine-complete when V11-001 adds:

- a validator enforcing single active unit and plan/state consistency;
- operator-session records;
- a validation workflow;
- a deterministic status projection;
- a receipt proving the first V11-native control plane.

Until then, this document is the governing operating identity and the existing V11-001 branch remains partial confirmed work with one unresolved remote operation.
