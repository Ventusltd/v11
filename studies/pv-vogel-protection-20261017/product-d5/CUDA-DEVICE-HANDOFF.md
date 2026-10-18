# V11 D5 — separate CUDA device handoff

Date: 18 October 2026. Prepared only: NO CUDA hardware execution and NO billion-case test completed. Only V11 is writable. Existing GPU Engine/Furnace/Kuiper/Stars/Faraday sources stay read-only. IEC licensed source text and PDFs are not distributed.

## Prerequisites on the user's separate device

Use an exact, reviewed V11 branch commit (not an automatically changing main). Use a Python environment with NumPy, CuPy matching the installed CUDA/driver, and a working NVIDIA GPU. This research does not install GPU software, restart runners, use background agents or schedule compute.

    nvidia-smi
    python -c "import cupy as cp; print(cp.__version__); print(cp.cuda.runtime.getDeviceCount()); a=cp.arange(8); assert int(a.sum().get())==28"

In directory studies/pv-vogel-protection-20261017/product-d5 run CPU-only correctness first:

    python -m unittest -v test_billion_case_space.py test_projection_and_phase2.py
    python kuiper_projection.py --n 4096 --law live-kuiper-g32 --output results/kuiper-live-4096.json
    python phase2_evidence.py --projection results/kuiper-live-4096.json --output results/phase2-graph-48.json --shortlist 48

## Optional controlled CUDA pilot — 65,536 mathematical input tuples

Only on the user's device and with their deliberate approval:

    export V11_GPU_APPROVED=1
    python cupy_furnace.py --approve-furnace --cases 65536 --output results/cupy-65536.json

Verify output states: cuPy_cuda_hardware_executed is true; actually_executed_gpu_cases equals 65536; gpu_channel_mismatches and scalar_probe_differences are zero; injected_failure_detected is true. No evidence is declared if CuPy or device execution fails. The CUDA algorithm is a SYNTHETIC electrical screen, not ngspice or a qualified device.

A billion-case arithmetic run is NOT recommended until the 65k pilot is audited, and the circuit equations linked to fault, trip-time and inverter source axes.

Only after explicit approval for the full run:

    export V11_GPU_APPROVED=1
    python cupy_furnace.py --approve-furnace --execute-billion --cases 1073741824 --output results/cupy-billion.json

The script processes batches with current free GPU memory, aggregates five screen bins without exporting a billion records, checks a fused CUDA kernel against a separately expressed CuPy graph and 4096 independent CPU corner/Fibonacci witnesses, and checks a planted discrepancy. It must not silently fall back to NumPy. Report actual device, driver, CUDA, CuPy version, memory, elapsed end-to-end time, distinct tuples, mismatches, and source SHA in the owner's execution log.

## STOP gates and evidence terminology

Stop if real CUDA device is absent; kernels cannot compile; any CPU/GPU discrepancy occurs; zero work is done; input or assumptions differ; or operator approval is absent.

Distinguish indexed tuples (up to 1,073,741,824), actual evaluated arithmetic tuples, independent SPICE circuit waveforms, and physical/laboratory tests. Three early axes are inert labels in the present equation: fault class, response latency, and inverter coupling. Thus even a perfect full CUDA run is NOT one billion meaningful fault simulations and cannot establish arc extinction, device SOA, insulation coordination, 30-year reliability or manufacturing feasibility.

Local D5 case indices are not allocated permanent global Kuiper keys. Live Kuiper vs legacy Line Wafer coordinate conventions are explicitly versioned; a dot is not an electrical terminal or fault site. Phase II Stars/Faraday is an evidence-linked review engine, not an AI safety certificate.

No licensed IEC pages, figures, text tables, extracted corpora or licensee information may enter public V11 code, CI logs, artefacts or GPU dataset. Manual copyright checks remain required.
