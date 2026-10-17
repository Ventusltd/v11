# Wave 2 plan (launch after barrier B1)

Dependencies expected from wave 1 (verify exist before launch):
- topology/s20-s19-mppt-graph.json, topology/switch-state-tables.json
- models/pv_module.lib (PVSUB/PVMOD/PVSTR), models/pv_string.py, models/pv-model-fit.json
- models/cable_line.lib (+ generator in cable_line.py), models/dc_side.lib
- models/arc_model.lib (ARC_SERIES/ARC_PARALLEL), models/arc_model.py
- electronics/switch_models.lib (SW_ANTISERIES/SW_SINGLE_BODYDIODE/SSB_SIC), electronics/switch_stress.py
- models/detection.py, detection-latency-budget.json
- tools/energy_ledger.py, tools/waveform_io.py, tools/units.py, proofs/

Workers (opus):
- W09 C1 series arc campaign (ngspice): P0 (AFCI variants), P1 SW-M-OUT(15), P1b SW-SS(15,2), P2 SW-STR-INV; G/T/gap subset; E_fault both integrators; device stress; residual voltages; time-step halving. Paths: results/C1/, experiments/c1_campaign.py
- W10 C2-far campaign: P0, P1-all, P2, P2b, P3; V_BOOST/V_DIRECTBUS; G 1000/0; gap 1/3/5. Paths: results/C2far/, experiments/c2far_campaign.py
- W11 C2-near campaign: same structure. Paths: results/C2near/, experiments/c2near_campaign.py
- W12 C3 hot connector campaign (Python thermal + electrical observables + detection): P0/P1/P1b/P2/P2b. Paths: results/C3/, experiments/c3_campaign.py
- W13 CLEAN-ROOM independent lumped SciPy model of C1 and C2 (no reading of W09–W11 files): second integral. Paths: models/independent_lumped.py, results/independent/
- W14 adversarial counterexamples ADV-* (ngspice minimal circuits), verdict per candidate. Paths: results/ADV/, experiments/adv_campaign.py
- W15 device stress + thermal + clamp coordination across wave-2 results; Tj; Pareto inputs. Paths: results/device-stress/, electronics/stress_summary.py

Wave 3 (after barrier B2):
- W16 architecture-comparison.csv + coverage/false-alarm/selectivity/loss/device-count/BOM(ASSUMED)/grades + Pareto non-dominated set. Paths: architecture-comparison.csv, results/pareto/
- W17 independent numerical verification (compare W13 vs ngspice; timestep audit; energy balance audit; recompute 3 headline energies by hand). Paths: review/independent-verification.md, proofs/test_crosscheck.py
- W18 engineering-decision.md
- W19 supervisory-review.md + contradictions.md update + README.md + manifest.json final
- W20 CI workflow (.github/workflows/pv-vogel-cycle1.yml) + run_all receipt + PR body draft
