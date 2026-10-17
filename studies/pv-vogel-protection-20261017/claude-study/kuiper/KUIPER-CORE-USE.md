# How this study uses the Kuiper core (www.globalgrid2050.com/kuiper/)

Added 2026-10-17 21:35 BST at the product owner's direction ("use the Kuiper core on globalgrid2050.com").
Located through adjacent chats (6 and 11 October 2026) and the live site: the Kuiper is served from
`globalgrid2050.com/kuiper/` (shell release `202609192301-kuiper-shell` plus hashed cartridges, `kuiper/current.json`),
its laws and key tools live in `github.com/Ventusltd/kuiper-belt` (LAWS.md, tools/wafer_keys.py, tools/key.py,
cosmos/wafer-meta.json), and the plain-English explainer is `ventusltd.github.io/kuiper-belt/what-is-kuiper.html`.
Both repositories are READ-ONLY for this study; nothing in them was modified.

## 1. Two documented placement laws — both pinned, neither altered

| | Line Wafer (brief §4) | Kuiper core (live site, kuiper-belt) |
|---|---|---|
| Source | globalgrid2050@da7d8f6e `testcode/202609151339/lib.mjs` `place(key)` (sha256 b96c855d…) | globalgrid2050@da7d8f6e `kuiper/releases/202609192301-kuiper-shell/index.html` `keyPlace` line 566 (sha256 5b59979c…); kuiper-belt@40df5a3e `cosmos/wafer-meta.json` `law` |
| Radius | r = √key | r = √(key + 0.5) |
| Angle | θ = key · π(3 − √5) (golden angle, 2.39996 rad) | θ = 2π · ((key mod 2³²) · 2654435769 mod 2³²) / 2³² (32-bit Fibonacci hash, G = ⌊2³²/φ⌋) |
| Keys | 1 … 2⁵³−1 (parseKey) | 0 … (issued keys; 44,029,986,939 on 2026-10-17) |
| Relation | θ_LW = 2π·frac(key·0.381966…) | θ_core = 2π·frac(key·0.6180339886…) = 2π − θ_LW up to the integer approximation (Δ ≈ 1.06e-10 rad per key): the two maps are mirror images about the x-axis for small keys |

The study's ledger (`experiments/scenario-ledger.json`, version 2) now carries BOTH addresses for every scenario key:
`kuiper_xy` (Line Wafer law, unchanged from v1) and `kuiper_core_xy` (core law). Keys and scenario ids are unchanged
(append-only rule honoured; v1 entries sha256 218b25d9…, v2 9cba84ac…). `tools/ledger.py` implements the core law with
exact integer arithmetic; `kuiper/verify_core_law.py` checks it against the shell's own `keyPlace` evaluated under Node
(2967 keys including 2³²−1, 2³², 44,029,986,938 and 2⁵³−1: 0 differences after round(·,8); max 3.6e-16 relative).

Neither law carries physical, statistical or causal meaning (Kuiper README "What is not claimed"; brief §4).

## 2. Key law adopted from kuiper-belt `tools/wafer_keys.py`

- Keys are issued in time order and never moved; later material is appended further out; unissued keys are permitted
  (the belt leaves "silence" unissued at a declared frozen rate). The study's family `cycle1-physical-v1` (2561…2959) was
  appended after the frozen Phase 0 family (1…2560). Any future family is appended at the next free key; nothing is
  renumbered. New identities requested by SUP-B (P1-IN, P1-BYP, P1-FB, P1-uni, P1-shared) and by SUP-C/SUP-E (C1loop) will
  be appended as family `cycle1-physical-v2` at barrier B1, with their own changelog line.
- `tools/key.py` in kuiper-belt is the proof that a key resolves to a line; the study's analogue is `tools/ledger.py --check`
  plus `evidence_links` per entry, so that a scenario key resolves to its netlist, result file and sha256.

## 3. Laws L9 and L10 adopted as study rules

- **L9 Reproducibility**: two runs on any two machines must give identical results; every source of variation is printed
  (seed, tolerance, time step, commit range). Wave-2 harness (`experiments/harness/`) records ngspice options, step, seeds
  and sha256 for every run; `proofs/run-receipt.json` records the git HEAD.
- **L10 Reconciliation** (Portia's rule: a claim grants only what its words grant; disagreement is settled by pinned
  evidence, never by recency, seniority, plausibility or a model's judgement). Every controller report and every
  contradiction-register entry now carries one of four verdicts:
  `HONOURED` (the evaluated predicates were satisfied), `OVERREACHED` (the claim asserts more than its evidence grants —
  first concrete deviation named), `NOT EVALUATED` (listed, never merely counted), `DISCLOSED` (acknowledged gap; never
  waives a numerical contradiction). The controllers' AGREE / DISAGREE / CANNOT VERIFY map to HONOURED / OVERREACHED /
  NOT EVALUATED; DISCLOSED is added for gaps the author declared.

## 4. The V11 repository in the belt

kuiper-belt `cosmos/repos.tsv` lists `v11` as body index 48 (`cosmos/belt.tsv` row: v11, 983,673 issued line keys at the 2026-10-17 15:42 UTC run). Every line of every commit this study pushes to `Ventusltd/v11` therefore receives a belt
key at the belt's next GitHub Actions run, placed by the core law; those keys are issued by the belt, not by this study,
and are not predicted here. The study's scenario keys are a separate, small address space (research scenarios), placed by
the same law so a scenario and the code that produced it can be drawn on one wafer.

## 5. What is NOT done

- No file in globalgrid2050 or kuiper-belt was changed. No belt key was issued or predicted.
- The core law is used for addresses only; no Vogel/Kuiper geometry is used as an experiment design without W06's benchmark.
