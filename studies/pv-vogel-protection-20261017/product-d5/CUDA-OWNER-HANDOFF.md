# V11 D5 — separate CUDA device handoff (NOT executed)

This is an owner-controlled, optional GPU run. The GitHub research lives in draft PR #14 on branch analysis/pv-d5-billion-furnace-kuiper-20261018, directory studies/pv-vogel-protection-20261017/product-d5/. No CUDA device, background job or 1.073-billion-case run has been activated by this research.

## Path A: direct Python without a GitHub runner

Use a pre-existing, compatible NVIDIA driver and Python environment with NumPy and a CuPy build compatible with the installed CUDA runtime. Review and check out the exact V11 branch commit first. Do not mix IEC-licensed files into the checkout or model data.

In the D5 directory, confirm CUDA works:

    python -c "import cupy as cp; assert cp.cuda.runtime.getDeviceCount()>0; a=cp.arange(8,dtype=cp.float64); assert float(cp.sum(a).get())==28"

Set V11_GPU_APPROVED=1 in the process environment, then explicitly run the small pilot:

    python cupy_furnace.py --approve-furnace --cases 65536 --output results/cuda-smoke.json

On Windows PowerShell set it using:

    $env:V11_GPU_APPROVED = "1"

Review the compact resulting JSON. It must state CUDA hardware executed, precisely 65,536 distinct synthetic evaluations, zero GPU channel mismatches, zero CPU probe differences, and successful detection of a planted mismatch. Failed or absent results are not a GPU pass.

ONLY when the owner subsequently and explicitly authorises the billion-case arithmetic run:

    python cupy_furnace.py --approve-furnace --execute-billion --cases 1073741824 --output results/cuda-billion.json

It requires the same V11_GPU_APPROVED=1 variable. The script uses bounded batches and reports actual reached cases rather than creating a billion files. The billion result remains an arithmetic screen, not a billion SPICE simulations or a certified DC-arc product.

## Path B: GitHub Actions on a separately registered device

Prepared workflow: .github/workflows/pv-d5-furnace-owner-gpu.yml.

The owner must intentionally register a trusted Linux-compatible self-hosted GitHub Actions runner carrying the pv-furnace label in addition to self-hosted. The workflow is MANUAL ONLY. approve_cuda defaults FALSE, full_billion defaults FALSE, and both inputs are operator decisions. It does not run on PRs, automatically install drivers, start a cloud GPU, or consume existing MSI GPU resources.

Because it is in an unmerged draft branch, GitHub may not offer manual dispatch until the owner approves and adds the workflow to the default branch. Do not merge research merely to expose a button. Use Path A if the CUDA machine is separate from GitHub runner hosting or is Windows-only.

## What is actually working today

The ordinary PR-triggered workflow .github/workflows/pv-d5-kuiper-furnace-cpu.yml independently verifies selected circuit-parameter arithmetic, case identity and 512 corners, Python/JavaScript Kuiper coordinate agreement, and a bounded Phase II evidence graph. It retains generated evidence files after IEC copyright checks. This GitHub CPU workflow **does not run CuPy** and cannot establish GPU device performance.

## Product-physics limits

The nine-dimensional space contains 1,073,741,824 unique INPUT tuples. Fault-class, detection latency and inverter coupling are still labels in the first-stage algebra. D5 must not claim those are simulated physics until real topology and circuit-time dependencies are connected. Verification of transistor safe-operating area, diode stress, PV cell avalanche, calibrated arcs, source-to-fault joules, frame insulation and lifetime still requires manufacturer models, SPICE/EMT and independent laboratory evidence. Maintain the IEC single-user rights boundary.

Operator security: Run only a reviewed exact commit on the private CUDA machine, never untrusted pull-request code, and publish compact receipts without machine-specific secrets or IEC text.