# CTRL-01 — Phase 1 clean-room recomputation (target: SUP-E / Track E screen)

**Controller:** CTRL-01 (Claude model, controller role) · **Cycle:** 1 · **Date:** 2026-10-17
**Target:** `review/track-E-charter-and-initial-attack.md` (prose) and `review/track_e_screen.py` (script).
**Clean-room statement:** this file was written **before** `review/track_e_screen.py` was opened. Under the task, the charter prose was read only to learn which quantities it claims. No other track's script, netlist or result file was opened. Disclosure: the mandated preamble reading included `evidence-board.md`, whose receipt R-03 quotes SUP-E headline numbers in prose. I saw those numbers but did not use them as inputs. Every value below comes from the fixture and the formulas shown.
**Inputs:** `fixture/system-fixture.json` (`V11_CYCLE1_SHARED_FIXTURE_v1`) plus the ASSUMED constants in §0. Each of those is named in the CTRL-01 task or in `assumptions.json`.
**Grade:** `algebra` for items 1–10. `illustrative_simulation` for bonus item B-7 only (lumped ODE + ngspice). **Arc numbers use the fixture's UNCALIBRATED Stokes–Oppenlander law and are ILLUSTRATIVE.**

| Producing file | sha256 | Command (from `claude-study/`) | Output |
|---|---|---|---|
| `review/controls/CTRL-01/ctrl01_cleanroom.py` | `92d7dfffa7e8821fc1f68090797826b621c93afe58c5336efc3497dba9014b77` | `python3 -I review/controls/CTRL-01/ctrl01_cleanroom.py` | `cleanroom-results.json` sha256 `bdecdf4734f8f2cd0087fbb1cd47961437511ef6ef238d4c149f3f47507e199b` (byte-identical on re-run; self-checks PASS) |
| `review/controls/CTRL-01/c2far_cin_transient.cir` + `ctrl01_ngspice_check.py` | `2833a766…c8569d` / `4b9f2f7e…9aa80` | `python3 -I review/controls/CTRL-01/ctrl01_ngspice_check.py` (ngspice 42 batch, 0.3 s) | `ngspice-check.json` sha256 `1fc76b93…40dfd`. Waveform file deleted after use (4.85 MB; sha256 `0a75641d746e8b7f24dc210bec4a45576482fa89afb11808d1b1113a1ba1050b`) |

## 0. Constants

Fixture (key path → value): `module.voc_stc_v` 45.75 V · `module.vmpp_v` 38.13 V · `module.impp_a` 17.31 A · `module.isc_a` 18.4 A · `module.voc_temp_coeff_per_c` −0.0024 /°C · `module.isc_temp_coeff_per_c` 0.0005 /°C (ASSUMED in fixture) · `module.pmpp_temp_coeff_per_c` −0.0034 /°C (ASSUMED in fixture) · 3 substrings/module · bypass diode Vf 0.45 V (fixture text `Schottky_assumed_Vf_0p45_V_at_17A`; A-032) · leads 0.35 m + 0.28 m of 4 mm², 5.09 Ω/km · field cable 6 mm², 3.39 Ω/km, α 0.00393 /K · connector 0.35 mΩ each, 33 mated interfaces/string · 24 strings × 30 modules · `vmpp_string_v` 1143.9 V · arc law `V = (20 + 0.534·gap_mm)·I^0.12`, I_min 0.5 A, V_ignite 15.0 V · S20 route 936 m, S19 route 600 m, C2-far 5 m from array end · C_in 150 µF, DC link 2 mF · loop L (0.613 + 0.1) µH/m, C 36.3 pF/m · C3: ramp 0.00035 Ω → R over 600 s, C_th 8 J/K, h 0.25 W/K, ambient 35 °C, horizon 3600 s.

ASSUMED (not fixture): 1 added outage/yr target (A-038), 8760 h/yr; 1.65 W/die, 62 K/W (A-036), 85 °C box (A-037); 20 K drift (A-033); node collapse V = 40 V (task). Used only in bonus items: E_AS 0.3 J (A-035), V_BR 120 V, I² duty 0.12, 10 ms trip, 200 °C damage (A-034), 13 V low-intercept hypothesis (A-025, NOT VERIFIED). The fixture gives **no Vmpp temperature coefficient**. Item 3 therefore carries three labelled alternatives.

Voltage–temperature convention (fixture, identical to `voc_module_cold_minus10c_v`): `Voc(T) = Voc_STC·(1 + β·(T − 25 °C))`, β = −0.0024 /°C → module Voc 49.593 / 45.750 / 40.809 V and string Voc 1487.79 / 1372.50 / 1224.27 V at −10 / 25 / 70 °C.

## 1. In-loop available voltage, C1 (arc in series with SS2 cells, inside the D2 loop)

Derivation: SS2 cells and the arc sit in series between N1 and N2. D2 (anode N1, cathode N2) is in anti-parallel across that branch. By KVL, `V_arc = V_cells(I_br) − V_N2N1`. D2 clamps `V_N2N1 ≥ −Vf`, so `V_arc ≤ V_cells(I_br) + Vf ≤ Voc_ss + Vf`, with equality only as I_br → 0. D2 cannot carry current from N2 to N1, so the branch (arc) current must return through the **string loop**.

| T_cell | Voc_ss = Voc_module/3 | **Voc_ss + Vf** |
|---|---|---|
| 25 °C | 15.250 V | **15.700 V** |
| −10 °C | 16.531 V | **16.981 V** |
| 70 °C (extra) | 13.603 V | 14.053 V |

DERIVED (Vf ASSUMED), algebra. Sensitivity: with Vf at the A-032 upper bound of 0.8 V and the cell at −40 °C, the cap is 17.629 + 0.8 = 18.43 V. That is still below the 1 mm law value in item 2.

## 2. Fixture arc-law requirement at I_min = 0.5 A

`0.5^0.12 = 0.920188`. The law increases with I (exponent > 0), so its minimum over I ≥ I_min is at I_min.

| gap | intercept (20 + 0.534·gap) | **V_req(0.5 A)** | margin over the −10 °C cap 16.981 V | margin over the STC cap 15.700 V |
|---|---|---|---|---|
| 1 mm | 20.534 V | **18.895 V** | +1.914 V | +3.195 V |
| 3 mm | 21.602 V | **19.878 V** | +2.897 V | +4.178 V |
| 5 mm | 22.670 V | **20.861 V** | +3.880 V | +5.161 V |

Under the fixture law, no operating point exists for the in-loop C1 arc at any gap. The result is ILLUSTRATIVE and rests entirely on the uncalibrated intercept. The fixture's own V_ignite of 15.0 V lies 1.981 V below the −10 °C cap and 3.895 V below the 1 mm law value, so the fixture is internally inconsistent.

## 3. Single SW-M-OUT open (rest of the string intact, I = 0)

KVL around S20 with one open switch and zero current gives no IR drops and all 30 modules at Voc. The switch is outside the bypass chain. So `V_sw = 30·Voc(T) − V_node`, where V_node is the potential the external circuit holds at the S20 array terminals: the MPPT node, reached through the current-free S20 home run. **Voc coefficient applied: fixture β = −0.0024 /°C on Voc.**

| Node convention | −10 °C | 25 °C | 70 °C | Label |
|---|---|---|---|---|
| (a) **node held at 1143.9 V** at every T (task-literal; my primary) | **343.89 V** | **228.60 V** | **80.37 V** | DERIVED, algebra |
| (b1) node = Vmpp(T), γ_V = −0.0024 (Voc coeff reused) | 247.80 V | 228.60 V | 203.91 V | γ_V ASSUMED |
| (b2) node = Vmpp(T), γ_V = −0.0034 (fixture Pmpp coeff used as proxy) | 207.77 V | 228.60 V | 255.39 V | γ_V ASSUMED |
| (b3) node = Vmpp(T), γ_V = −0.0039 (Pmpp − Isc coeff) | 187.75 V | 228.60 V | 281.12 V | γ_V ASSUMED |
| (c) node = S19 array Vmpp(T) (b2) − Impp(T)·4.1758 Ω S19 series path (4.068 Ω loop + 0.0962 Ω leads + 0.01155 Ω connectors) | 278.78 V | 300.88 V | 329.30 V | sensitivity |
| (d) **node collapsed to V_arc = 40 V** (task) | **1447.79 V** | **1332.50 V** | **1184.27 V** | DERIVED, algebra |
| (d') node at the fixture-law arc voltage at 18.4 A, 1 mm (29.124 V) | 1458.67 V | 1343.38 V | 1195.15 V | diagnostic |
| (e) node at 0 V (bolted near-end fault, or discharged C_in with S19 dark) | 1487.79 V | 1372.50 V | 1224.27 V | bound |

At 25 °C every node-at-Vmpp convention gives 228.60 V, which is above a 100 V class. The only sub-100 V single-open value in this set is (a) at 70 °C (80.37 V). Not modelled: switch leakage, turn-off transient (L·di/dt adds to V_sw during opening), irradiance dependence of Voc.

## 4. All 30 SW-M-OUT open simultaneously

KVL fixes only the **sum**, `ΣV_sw = 30·Voc(T) − V_node`. A per-device value needs an off-state leakage/capacitance sharing model, which is NOT modelled. With equal sharing as an idealisation:

| Convention | −10 °C | 25 °C | 70 °C |
|---|---|---|---|
| (a) node 1143.9 V | 11.463 V | **7.620 V** | 2.679 V |
| (b2) node Vmpp(T), −0.0034 | 6.926 V | 7.620 V | 8.513 V |
| (d) node 40 V | 48.260 V | 44.417 V | 39.476 V |

Avalanche skew window of an illustrative 100 V-class part: `t = E_AS/(V_BR·I) = 0.3 J/(120 V·17.31 A) = 144.4 µs`, at 2077 W. With I = Impp this is a lower bound on the window, because the loop current falls toward the string-IV point at V_node + V_BR.

## 5. C2-far steady arc power (20 V-intercept law, 1 mm, strings = ideal current sources at Isc = 18.4 A)

Paths: the S20 modules feed through a 10 m loop (0.0339 Ω). S19 feeds through 2 × 600 m (4.068 Ω), then the MPPT node, then 2 × 931 m of the S20 home run (6.3122 Ω), for 10.3802 Ω in total. Both strings stay in the current-source region (terminal voltages S20 32.27 V and S19 222.65 V, both ≪ Vmpp).

| State | I_arc | V_arc | **P_arc** |
|---|---|---|---|
| (a) both strings (P0, after the C_in transient) | 36.8 A | 20.534·36.8^0.12 = 31.650 V | **1164.72 W** (582.36 W from each string) |
| (b) S20 alone (P2, SW-STR-INV open) | 18.4 A | 29.124 V | **535.88 W** |

`P(b)/P(a) = 2^−1.12 = 0.4601` exactly, because P ∝ I^1.12. The steady arc power is therefore **54.0 % lower**, not 50 % lower. **Diagnostic:** the superposed value 2 × 535.88 = 1071.76 W is *not* the arc power. It evaluates V_arc at 18.4 A while the arc carries 36.8 A, an error of −7.98 %. Other results: S19 cable dissipation is 18.4²·10.3802 = 3514.3 W, and the steady MPPT node sits at 31.650 + 18.4·6.3122 = 147.79 V. That is below the 500 V window, so the V_BOOST inverter draws nothing.

## 6. 5 s energies (fixture horizon, steady power × 5 s; P2 opening at t = 0, ideal)

P0 (both): **5823.62 J**. P2 (S20 alone): **2679.41 J**. Superposition diagnostic: 5358.82 J. These figures exclude the C_in transient, which adds 5.73 J (B-7) under P0.

## 7. C3 detectability ratio against 20 K cable drift

`D = R_conn/ΔR_drift`, with `ΔR_drift = R_span·α·ΔT`, α = 0.00393 /K and ΔT = 20 K.

| Span | R_span | ΔR (20 K) | **D: 0.05 / 0.2 / 1.0 Ω** |
|---|---|---|---|
| full string path: home run 6.34608 Ω + module leads 0.096201 Ω + 33 connectors 0.01155 Ω | 6.453831 Ω | 0.507271 Ω | **0.0986 / 0.3943 / 1.9713** |
| home run + 33 connectors (module leads omitted) | 6.357630 Ω | 0.499710 Ω | 0.1001 / 0.4002 / 2.0012 |
| module-lead span (0.63 m of 4 mm² + 1 connector) | 3.5567 mΩ | 0.27956 mΩ | 178.85 / 715.42 / 3577.09 |

At 40 K every ratio halves (0.049 / 0.197 / 0.986). Using the increment R − 0.00035 Ω changes the ratios by less than 0.7 %. Applying the copper α to the connector resistance has no material effect.

## 8. Unit and die counts

Units = 24·⌈30/g⌉ → **720 / 360 / 192 / 24** for g = 1/2/4/30. The g = 4 case has 7 full groups plus one partial group of 2 modules per string. Anti-series pair dies (2 per unit): **1440 / 720 / 384 / 48**. Redundant two-stage (4 per unit): 2880 / 1440 / 768 / 96. P1b per substring: 2160 units, giving 2160 dies (unidirectional) or 4320 (anti-series).

## 9. Required unit failure rate for ≤ 1 added outage/yr (plant-wide target, ASSUMED)

`λ_req = 1 yr⁻¹/(N_units·8760 h)·1e9` FIT:

| | Units | **FIT** (8760 h) | 8766 h | per-string target instead (×24) |
|---|---|---|---|---|
| g = 1 | 720 | **158.55** | 158.44 | 3805 |
| g = 2 | 360 | **317.10** | 316.88 | 7610 |
| g = 4 | 192 | **594.56** | 594.15 | 14269 |
| g = 30 | 24 | **4756.47** | 4753.21 | 114155 |
| P1b | 2160 | 52.85 | 52.81 | 1268 |

These are required-rate targets, not reliability estimates; actual rates are UNKNOWN. They assume every unit failure causes one outage. Fail-short causes no outage, so the target constrains only outage-causing modes.

## 10. Junction-temperature screen

`P_die = 0.005·475200 W/720/2 = 1.65 W`, which matches the task value. `ΔT = 1.65 W·62 K/W = 102.3 K`, so **Tj = 85 + 102.3 = 187.3 °C**. ASSUMED R_th and box temperature; algebra. Not modelled: mutual heating of the two dies in one box, box self-heating, solar load.

## B. Other quantities the charter prints, computed before reading the script

- **B-1 Loss budgets:** R at 0.5 % of STC = 11.0134 / 22.0267 / 41.3001 / 330.4008 mΩ, and 3.6711 mΩ for P1b. W per unit at budget = 3.300 / 6.600 / **12.375** / 99.00 / 1.100 W. Plant loss 2376 W; annual 2376·8760·0.12 = 2.4977 MWh (duty factor ASSUMED).
- **B-2 Connectors:** 792 mated interfaces (1584 ends). The P1 inline retrofit adds 1440 ends, giving 3024 (×1.91).
- **B-3 C3 table (Impp held at 17.31 A):**

  | R | ΔV | P | ΔT_ss | E(0–3600 s) | t(200 °C) with thermal mass (first-order ODE, exact) | t(200 °C) quasi-static | t(ΔV = 15 V) |
  |---|---|---|---|---|---|---|---|
  | 0.05 Ω | 0.8655 V | 14.98 W | 59.93 K | 49.47 kJ | never (T_ss = 94.9 °C) | never | never |
  | 0.2 Ω | 3.462 V | 59.93 W | 239.71 K | 197.79 kJ | 444.67 s | 412.67 s | never |
  | 1.0 Ω | 17.31 V | 299.64 W | 1198.54 K | 988.83 kJ | 113.50 s | 82.42 s | 519.90 s |

  Here τ = C_th/h = 32 s. With a linear ramp, the first-order lag lands the 200 °C crossing about τ later than the quasi-static estimate.
- **B-4 C2 C_in / DC link (charge-limited estimates):** C_in stored ½CV² = 98.14 J. Share Q·V_arc = 150 µF·(1143.9 − 29.124)·29.124 = 4.870 J. R-limited peak current (1143.9 − 29.124)/6.3122 = 176.61 A. L/R = 663.80 µH/6.3122 Ω = 105.2 µs. DC link (V_DIRECTBUS): stored 1308.51 J, share 64.93 J, τ_RC = 12.62 ms.
- **B-5 Line 936 m:** L_loop 667.37 µH; ½LI² at Isc = 0.1130 J; C 33.98 nF; ½CV² at 1143.9 V = 0.02223 J.
- **B-6 C2-near C_in pulse (5 m loop):** L 3.565 µH, R 0.0339 Ω, Z0 = 0.15416 Ω. Undamped peak (1143.9 − 29.124)/Z0 = **7231 A**, or 7420 A at the full 1143.9 V. Damped by cable R only: 6152 A. Quarter period 36.32 µs.
- **B-7 C2-far lumped transient (illustrative_simulation, two independent integrals):** node C_in, S19 and S20 as 18.4 A sources, S20 home run (inverter side) as R–L, initial S20 current −17.31 A, inverter draw 0 for t > 0 (ASSUMED). E_arc(0–50 ms) is 63.963 J by scipy LSODA and 63.963 J by ngspice `meas integ` (relative difference 3.5e-7). Halving the step changes the result by 2.3e-6. The C_in transient excess over steady state is **5.727 J**. E_arc(0–10 ms) = **17.374 J**, against a steady-only 11.647 J. Peak arc current 166.5 A. V_DIRECTBUS (2.15 mF): excess 81.99 J over 0.2 s. The charge-limited share in B-4 underestimates the transient because V_arc during the pulse is 31.6–38 V, not 29.1 V. Not modelled: distributed line, S19 route L, inverter control, C_in ESR/ESL.
- **B-8 C2 observables:** array-end current step +6.30 %; inverter-end reversal 35.71 A.
- **B-9 C1loop first-order current dip:** V_arc(17.31 A, 1 mm)/Vmpp_string = 28.911/1143.9 = 2.53 % (R_dyn proxy ASSUMED).
- **B-10 Low-intercept hypothesis (13 V, NOT VERIFIED):** 13·17.31 = 225.0 W; 1125 J over 5 s; 13/1143.9 = 1.14 % of string Vmpp; substring STC output 220 W.

**NOT modelled anywhere in this file:** single-diode IV (strings are ideal current sources where stated), irradiance dependence, cable temperature in C2, arc dynamics and extinction, HF behaviour, switch internals, any probability, rate, lifetime or reliability value.
