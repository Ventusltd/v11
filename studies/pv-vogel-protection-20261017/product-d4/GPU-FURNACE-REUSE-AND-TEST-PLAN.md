# V11 D4 — CuPy readiness and module-level fault-electronics test plan

Research only · 18 October 2026 · V11 is the only writable repository · stacked on D3 draft PR #12. No product safety claims, no real CUDA execution asserted, and no licensed IEC material republished.

## Resources actually read — provenance and decisions

1. Ventusltd/gpu-drivers-for-global-grid, commit bfdc344289c0f03093e0c65979487e9916ea1ef4:
   - engine/ventus_engine.py: existing reusable Engine/Space, NumPy/CuPy backends, independent checks, compact reductions, runtime-free-memory batch selection. **V11 uses this file via PINNED READ-ONLY checkout, NOT by copying or reinventing it.**
   - engine/fused.py and engine/selftest.py: fused GPU arithmetic, CPU witness and measured runs. Small D4 grid is NOT a rate benchmark.
   - docs/GPU-TESTING-LESSONS-20260924.md and docs/GPU-REUSE-RESTART-LESSON-20260925.md: do not restart paused workflows, confuse repeated evaluations with independent cases, or compare GPU kernel time to end-to-end CPU time.
   - .cvaa/contracts/cuda-furnace.json: a separate scoped GPU evidence contract, not validation of PV protection.
2. Ventusltd/worlds-:
   - src/furnace.py and night-results/furnace.json: historical 1,000,000,000-case three-channel comparison (fused NVRTC kernel, independent CuPy operator graph, alternative algebra). Furnace is a **module in worlds-**, not a repository called Furnace. The published receipt covers 49.355293% of its own synthetic lattice and reports zero disagreements, not proof its assumptions are true. V11 must not present that receipt as current PV evidence.
   - src/annihilate.py: strict-versus-inclusive boundary probes detect threshold equality, not every arithmetic/physics mistake.
3. Ventusltd/globalgrid2050:
   - docs/GPU-REUSE-INVENTORY.md, compute/enumeration/sweep_hot_cold.py and .github/workflows/gpu-engine-check.yml. Historical Windows MSI runner uses PowerShell, not Bash; historical September report had twelve GPU-domain runners offline, but **CURRENT runner availability has NOT been checked or established**. No existing runner was started and no workflow was resumed here.
4. Ventusltd/trillion-loop: README.md and mathematical residency/provenance design; reuse bounded receipts, avoid shipping full per-case buffers.
5. Ventusltd/ventus-grid-engine, kuiper-drawing-engine and kuiper-ship: geometrical and indexing architecture; no reason to copy these unrelated engines. Kuiper address keys must remain append-only, and Vogel placement is not electrical fault physics.
6. Ventusltd/star-maker: independently executed browser-composition GPU tests, not PV module transient physics.
7. Ventusltd/data-gpu-holy-mother: only a README file appeared at main root in inspection; do not claim an implementation was discovered there.
8. Ventusltd/v11, source D3 draft PR #12 and D2 standards licence policy: nine verified generic-MOSFET ngspice cases and IEC copyright restrictions; preserve both.

## Actual D4 new test

The independent scalar circuit screen contains **17,640 unique synthetic cases**, the Cartesian product of:

- active substring shunt current: 0, 1, 10, 15.46965, 17.31, 20, 25 A;
- hypothetical hot two-MOSFET path resistance: 2, 5, 10, 20, 50 milliohms;
- active duty: 0, 0.1, 0.5, 1;
- hypothetical differential stress: 0, 12.8, 15.25, 20, 45, 80, 1500 V;
- hypothetical nominal device voltage rating: 30, 40, 60, 80, 1200, 1700 V;
- assumed passive diode forward drop: 0.4, 0.6, 0.8 V.

First closed form: D3 measured-simulator value 15.46965 A through a hypothesised 5 milliohm shunt implies I squared R approximately 1.19655 W, consistent within rounding with D3 ngspice 1.196517 W. 17.31 A and 660 Wp yield a research-only added-series-loss target 3.3 W, R approximately 11.013 milliohms. These are source traceability checks; neither is a real semiconductor selection or IEC limit.

Screens classify imposed nominal device differential voltage and simple shunt I squared R versus that research target, with a comparison to passive diode current times forward voltage. A voltage at the nominal part rating is considered a screen failure **before** any transient margin. No code labels are certified, safe, probability, or effective arc interruption. In particular 1500V on a *local substring differential* is an adversarial hypothetical input, not a claim that a correctly insulated low-voltage substring is normally at 1500V differential. Frame/common-mode insulation is a separate problem.

## CPU first, GPU later: executable gates

D4 code: product-d4/gpu_parameter_sweep.py. Original scalar oracle explicitly enumerates all 17,640 stable integer case IDs and computes four-category totals independently. Existing Ventus Engine consumes the same mixed-radix lattice using NumPy and checks closed forms, all-case parity, non-empty reduction and total counts. A compact JSON receipt includes source pins, assumptions, distinct cases, counts and a SHA-256 digest; speed is excluded from that digest.

CPU workflow: .github/workflows/pv-d4-cpu-engine.yml, triggered on relevant PR changes, uses original pinned read-only engine checkout and installed NumPy, executes tests and CPU enumeration, runs IEC release guard, archives only a compact receipt. **CPU success must never be reported as CUDA success.**

Future CUDA workflow: .github/workflows/pv-d4-cupy-manual.yml. Workflow-dispatch only; explicit approval defaults to FALSE. It targets existing [self-hosted, msi, gpu] labels, requires owner-set Actions repository variable V11_GPU_PYTHON pointing to an already configured real CuPy Python interpreter, proves nvidia-smi and device kernel execution, and executes CPU-versus-CuPy parity. It neither installs CuPy nor provisions a runner nor launches a job without explicit operator approval. No historical running status is treated as current.

NOTE: GitHub manual workflow dispatch generally appears after the reviewed workflow exists on the default branch. This remains an unmerged DRAFT PR; it is not a promise that an unmerged workflow can be dispatched now. Do NOT merge simply to launch hardware.

## Reproduction

Set V11_GPU_ENGINE_DIR to a read-only local checkout of the pinned GPU engine /engine folder. Install NumPy. From product-d4:

    python -m unittest -v test_gpu_parameter_sweep.py
    python gpu_parameter_sweep.py --backend cpu --receipt results/cpu-parameter-receipt.json

In future, only on an actual CUDA/CuPy machine and with explicit owner approval:

    V11_D4_REQUIRE_GPU=1 python -m unittest -v test_gpu_parameter_sweep.py
    python gpu_parameter_sweep.py --backend gpu --receipt results/gpu-parameter-receipt.json

GPU request on a missing device must **fail** rather than falling back to CPU.

## Boundary of this work

CuPy **cannot** automatically accelerate ngspice's electrical solver and 17,640 simple cases will normally be too small to justify a GPU speed claim. The reason for GPU readiness is future large, verified module-parameter and worst-corner sweeps, with the existing Furnace fused-kernel pattern if physically warranted.

The physically decisive next work is real MOSFET manufacturer models, calibrated PV bypass-diode characteristics, floating gate supply and Vgs/Vds transients, loss-of-power/bypass diode failure simulations, RLC inverter backfeed, actual measured arc current and fault-site energy, hot-spot thermal behaviour, and independently reviewed dielectric/insulation validation. A CUDA arithmetic receipt is not any of those.

IEC 62548-1:2023 and IEC TS 62738:2018 are restricted single-user references. Neither PDFs, standard pages, proprietary tables, normative language, watermarks nor licence metadata may be uploaded to V11, model inputs or public CI artifacts. V11 D2 copyright guard remains mandatory, without replacing manual permission review.

**Decision:** re-use the existing GPU Engine read-only, run independent CPU tests now, prepare a manual CuPy lane without activating it, and retain all product safety/laboratory gates at HOLD.
