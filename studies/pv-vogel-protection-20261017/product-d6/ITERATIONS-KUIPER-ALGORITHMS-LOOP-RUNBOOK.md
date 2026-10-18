# V11 D6 — Repeatable loop: iterations, Kuiper log, algorithms, more iterations

Status: Tested as a bounded CPU research loop, with a prepared owner-approved CuPy backend. This does NOT demonstrate arc extinction, suitable electronics, or an IEC-compliant device. Main and all other repos are untouched.

## Four repeatable stages

1. ITERATIONS. Select 768 different D5 electrical screening tuples. The first iteration forces all 512 corners of the nine-axis lattice and adds source-relevant fault hypotheses, then fills remaining places through a coprime Fibonacci traversal. Each code is independently checked against a second CPU calculation.
2. KUIPER LOG. Append every unique case to a JSONL file under a LOCAL-only Kuiper namespace, with 2D live G32 coordinates, local permanent-within-run case index, screen result, reason for selection, previous SHA-256 and new chained SHA-256. Historical log entries cannot be replaced, duplicated or mutated without detection. This neither claims nor allocates keys in the user's global Kuiper registry.
3. ALGORITHMS. Inspect prior outcomes using typed screen categories (voltage, failure, heat, diode loss and unflagged controls). Generate nearby one-axis threshold candidates for the next pass while keeping at least half of its budget for new Fibonacci exploration. No machine-learning or risk probability is asserted.
4. MORE ITERATIONS. Continue from prior tip and seen-case set. Stop at the explicit iteration limit. Defaults: THREE iterations, 768 cases each, 2,304 unique synthetic screening evaluations. Hard bounds: 1–8 iterations and 512–16,384 cases per iteration. It is not a perpetual autonomous task.

A D6 physical-evidence receipt connects the loop to the twelve real ngspice simulations. Those use a provisional three-substring PV circuit and a forced 17.31 A current with a 0.2-ohm hot-connector resistor (NOT an arc). A defect outside all module bypass loops remains heated when the internal substring bypass operates. The record is a falsifiable negative result, not a new D5 model of inverter or arc physics.

The D5 initial preflight still does NOT numerically use the fault-class, inverter-coupling and response-latency axes. Therefore the 2,304 screens are 2,304 distinct parameter tuples but not 2,304 independently solved fault-transient networks. Actual D6 SPICE network count is twelve. This separation is enforced in the receipt.

## Local / GitHub ordinary CPU test

From studies/pv-vogel-protection-20261017/product-d6:

    python -m unittest -v test_d6_fault_zone.py test_adaptive_kuiper_loop.py
    python d6_fault_zone_spice.py --run --out results
    python adaptive_kuiper_loop.py --backend cpu --iterations 3 --cases-per-iteration 768 --spice-results results/observed-spice-results.json --out results/iteration_loop

The second step requires ngspice. The GitHub workflow pv-d6-physical-fault-zones.yml ran these ordinary CPU and ngspice tests successfully on 18 October 2026:

https://github.com/Ventusltd/v11/actions/runs/39139313155

The output files are:
- results/observed-spice-results.json — twelve real ngspice conditional circuit screens.
- results/iteration_loop/iteration-01.json, iteration-02.json, iteration-03.json — observed synthetic screen counts and proposed priority cases.
- results/iteration_loop/kuiper-evidence.jsonl — append-only, verifiable case log and live Kuiper position for each evaluated local case.
- results/iteration_loop/loop-receipt.json — number of distinct cases, three cycles, linked D6 source SHA, chosen algorithm, chain verification and the unproven physical requirements.

Do not rerun into an existing nonempty results directory: the script intentionally refuses overwrite. Choose a fresh versioned run directory. Source and data versions must be pinned before comparing runs.

## Future GPU CuPy operation on user's SEPARATE device

No CUDA hardware has been started or touched by this PR. V11's CPU GitHub workflow never imports CuPy, enables a self-hosted runner or burns through the full billion configurations. The separate owner machine needs a correctly installed Python/CuPy version compatible with its NVIDIA CUDA driver, and a reviewed V11 commit.

Verify the real device locally:

    nvidia-smi
    python -c "import cupy as cp; print(cp.cuda.runtime.getDeviceCount()); x=cp.arange(8); assert int(x.sum().get())==28"

For bash-compatible shells, from D6 folder, after copying the already verified SPICE receipt:

    export V11_GPU_APPROVED=1
    python adaptive_kuiper_loop.py --backend gpu --approve-gpu --iterations 3 --cases-per-iteration 768 --spice-results results/observed-spice-results.json --out results/gpu-loop

In PowerShell the environment step is: $env:V11_GPU_APPROVED = "1".

The GPU path reuses the already existing D5 Furnace source kernel. It computes selected case IDs twice using CuPy RawKernel and a separately expressed CuPy array graph, and then verifies ALL selected results against independent pure Python CPU algebra. It requires both the command approval flag and the environment approval variable. No CuPy, no physical GPU, mismatched results, or absent approval causes a hard failure. Never silently label NumPy as CUDA.

The owner can compare CPU and GPU run receipts, numeric category counts and chained Kuiper log tips after executing identical source and D6 fixture revisions. No benchmarked GPU speedup is claimed from these 2,304 cases.

## Next cycle must improve physical equations

Use Phase II results to select true SPICE circuit cases: series defects within bypass loops, hot connectors outside them, bypass diodes open/short, stuck FET, gate supply loss, cold voltage stress, MPPT coupling and inverter-capacitor reverse feed. Upgrade D6's forced-current source to a loaded full PV/inverter RLC network and obtain actual manufacturer FET/diode data and measured arc information. Export fault-site energy by source, not just switch heat.

Only after those source-resolved models agree with ngspice and trusted measurements should large CuPy Furnace evaluations of *physical* model parameters be contemplated. A billion synthetic comparisons are not a billion arc-extinction tests.

The original IEC single-user PDFs, images, normative text and licensing details remain outside V11, any GPU inputs and publicly archived CI records; only original engineering calculations and permitted bibliographic references are published. Safety/insulation certification remains a separate qualified laboratory gate.
