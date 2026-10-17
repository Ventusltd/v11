# SUP-D pilot checks (supervisor-authored, 2026-10-17)

Small reproducible scripts behind the numbers in `../track-D-charter-and-initial-attack.md`.
They are pilots, not the study's benchmark (W06) or campaigns (wave 2).

```
# from this directory
KUIPER_LIB=/path/to/globalgrid2050/testcode/202609151339/lib.mjs node place_node.mjs > place_node.json
python3 -I verify_address_law.py place_node.json     # ledger.py kuiper_xy == lib.mjs place(key), keys 1..2959
python3 -I pilot_bench.py                            # one-seed equal-budget sampling pilot (not W06's result)
python3 -I spice_pilot/run_pilot.py                  # ngspice 42 RLC energy pilot, h and h/2, SciPy trapezoid
```
Kuiper source: Ventusltd/globalgrid2050 commit da7d8f6e6a7806ad5039701f5c86637d84be0704, lib.mjs sha256
b96c855de1f5477e0bbd46ff3a2aed6811ba074ba5da76975984fef505c06b0d (read-only; not vendored here).
