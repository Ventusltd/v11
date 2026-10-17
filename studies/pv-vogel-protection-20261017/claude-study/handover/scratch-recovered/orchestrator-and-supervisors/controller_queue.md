# Controller launch queue (20-concurrent cap). Launch in this order as slots free.

CTRL-01 → SUP-E charter + track_e_screen.py (clean-room recompute, diff, rerun)
CTRL-02 → SUP-C charter + review/supc-calcs/track_c_calcs.py
W31 (PRIORITY, user-directed 21:37) → design inventory of existing Ventusltd public design repos (read-only): pv-arc-protection-circuit, solar-dc-string-wiring-and-topology, solar-bess-topology-sandbox, Solar-PV-Hybrid-and-off-grid, solar-panels, solar-repowering-whitepaper, sld, 132kV, faraday, star-cable-derating-star, star-electron-star, star-solar-star, cable-trench-or-drill, substations, site-energy, ventus-grid-engine, studies, reports, solar-electrical-topology-analysis-engine-text-based (frozen lab, read-only inspection only) → claude-study/design-inventory/
CTRL-03 → SUP-D charter + review/supd-pilot/* + ledger invariants (disk coverage fractions, discrepancy pilot)
CTRL-04 → W01 topology (clean-room source-to-fault tables for C1/C2far/C2near/C3 × 7 actions; then diff switch-state-tables.json; run test_topology.py)
CTRL-05 → W02 PV model (independent 5-parameter fit from STC points; diff pv-model-fit.json; run test_pv_model.py and ngspice verification)
CTRL-06 → W03 cable/DC (independent L'/C'/Z0/delay/energies; diff cable-dc-verification.json; run tests)
CTRL-07 → W04 device register (independent web verification of 5 rows incl. IMZA65R027M1H 650 V, TPS1685, LTC4368; audit CSV; run test_switch_models.py)
CTRL-08 → W05 detection (independent C3 detectability + latency energies; run benign set; audit false-trip denominators)
CTRL-09 → W06 sampling (independent discrepancy/corner-miss for vogel2d vs Sobol at N=64/256; diff CSV; check no superiority claim)
CTRL-10 → W07 standards/arc model + W08 proofs/tools (verify 3 public scopes; run proofs; run run_all.py; check NOT EXAMINED labels)

Prompt pattern: controller preamble + target + phase-1 quantities + phase-2 files to run + output paths review/controls/CTRL-xx/.
