# CTRL-02 clean-room recomputation (Phase 1): Track C charter quantities

Control: CTRL-02 (Claude controller), cycle 1, 2026-10-17. Target: SUP-C `review/track-C-charter-and-initial-attack.md`
and `review/supc-calcs/track_c_calcs.py`.

**Clean-room statement.** I computed and hash-pinned every number in §1–§9 before opening any SUP-C file. At that point I
had opened neither `track_c_calcs.py` nor the charter prose. The list of quantities came only from the orchestrator's task
text. Inputs were the fixture plus the control assumptions listed in §0.

| Pinned artefact | sha256 |
|---|---|
| `fixture/system-fixture.json` (input) | `2027dd717d4eac24f96ef7106fb6df9899cec701cc08df5d19ceb7a145fea6a3` |
| `review/controls/CTRL-02/ctrl02_cleanroom.py` (producer) | `900e4e8be613e97fb8b4f2403e59fc849a4348f2a29f2e53056711a2e6615896` |
| `review/controls/CTRL-02/clean-room-results.json` (output) | `a4473c965557bc74f558c3c9526dcf837555160970b8d196d3d657f349859ce8` |

Reproduce from `claude-study/`: `python3 -I review/controls/CTRL-02/ctrl02_cleanroom.py`. The run takes 1.2 s. Two
consecutive runs gave byte-identical stdout. The script uses no random numbers and puts no wall-clock values in its output.

Every number below is graded **algebra** unless marked `illustrative_simulation`. Labels follow WORKER_PROTOCOL §3.

## 0. Inputs and control assumptions

Fixture values used: Vmpp 38.13 V, Impp 17.31 A, Voc 45.75 V, Isc 18.4 A, β_Voc −0.0024 /K, 66 cells, 3 substrings,
Vf(bypass) 0.45 V (fixture text "Schottky_assumed_Vf_0p45_V_at_17A"), 30 modules/string, Vmpp_string 1143.9 V,
Voc_string 1372.5 V (STC) and 1487.79 V (−10 °C). Field cable 3.39 Ω/km per conductor with α = 0.00393 /K. Factory leads
5.09 Ω/km, 0.35 + 0.28 m per module. 33 mates × 0.35 mΩ. Routes 78/200/300/600/936 m one-way (loop = 2 × route, A-006).
L_ext 0.613 µH/m, L_int,DC 0.1 µH/m, C' 36.3 pF/m, v = 211 985 280 m/s (= c/√2). C_in 150 µF. Fixture S-O law
V = (20 + 0.534·g)·I^0.12 with I_min 0.5 A. C3: C_th 8 J/K, h 0.25 W/K, ambient 35 °C, R ∈ {0.05, 0.2, 1.0} Ω.

Derived constants (DERIVED, algebra):

| Quantity | Value | Unit |
|---|---|---|
| R_loop S20, 936 m (2·936·3.39e-3) | 6.34608 | Ω |
| R_loop S20 node-to-arc, 931 m (C2-far) | 6.31218 | Ω |
| R_loop S19, 600 m | 4.06800 | Ω |
| L_loop S20, 936 m, (L_ext + L_int,DC)·936 | 0.667368e-3 | H |
| L_loop S20 HF (L_ext only) | 0.573768e-3 | H |
| Z0 = √(L_ext/C') | 129.95 | Ω |
| Module leads, 30 modules | 0.09620 | Ω |
| 33 mated interfaces | 0.01155 | Ω |

Control assumptions (all ASSUMED; they are listed for `assumptions.json` in the §4 report):

- Single-diode fit at 298.15 K with ideality n ∈ {1.0, 1.1, 1.2, 1.3}. No datasheet IV curve exists, so n is a free
  parameter; the band is a control choice.
- Cable drift ΔT ∈ {40 K (A-024, SUP-C), 20 K (A-033, SUP-E)}.
- C2 after the fault: the inverter draws 0 A because the node collapses below the 500 V window (V_BOOST). Both strings are
  ideal 18.4 A sources, per the task.
- Connector limit temperatures 150 °C (A-043) and 200 °C (A-034).
- V_clamp sweep 400, 600, …, 1600 V.

## 1. C1 series-arc DC current dip, node held at its pre-fault voltage

**String incremental-resistance method.** At the maximum-power point dP/dV = 0, so I + V·dI/dV = 0 and
|dV/dI| = Vmpp/Impp. This holds for *any* smooth IV curve with that MPP, so no dynamic resistance needs to be assumed:
R_dyn,module = 38.13/17.31 = 2.20277 Ω and R_dyn,string = 30 × 2.20277 = **66.083 Ω** (= 1143.9/17.31). Label DERIVED
(small-signal, exact at MPP).

- **Linear method:** ΔI = V_arc/R_dyn.
- **Large-signal cross-check:** a control-only five-parameter single-diode fit. Each fit meets Isc, Voc, Impp and
  dP/dV(Vmpp) = 0 to ≤ 4e-16 relative, inside A-020's 0.005. At n = 1.0/1.1/1.2/1.3 the fits give
  Rs = 0.1357/0.1144/0.0938/0.0738 Ω and Rsh = 134.6/183.6/287.6/657.1 Ω. The string must then deliver
  V_node + V_arc (+ I·R_series).
- **Geometry:** the arc is treated as a series element *not* limited by a bypass diode. An arc inside the SS2 bypass loop
  is capped, as §2 shows.

| V_arc (V) | Linear, no cable ΔI (A) | % of Impp | Linear, with S20 loop (6.4539 Ω total series) ΔI (A) | SDM no cable, n 1.0–1.3 (A) | SDM with S20 loop, n 1.0–1.3 (A) |
|---|---|---|---|---|---|
| 20 | **0.3026** | 1.748 | 0.2757 | 0.3597–0.3492 | 0.3172–0.3098 |
| 40 | **0.6053** | 3.497 | 0.5514 | 0.8570–0.8091 | 0.7261–0.6949 |
| 60 | **0.9079** | 5.245 | 0.8272 | 1.5300–1.4099 | 1.2376–1.1653 |

Observations:

- The IV curve bends downward above Vmpp, so the linear (current-source + R_dyn) method *underestimates* the steady dip.
  The underestimate is −15 % at 20 V, −28 % at 40 V and −39 % at 60 V (n = 1.1, no cable).
- Context (A-022, A-023): a 1 % or 2 % MPPT voltage step moves the string current by 0.173 or 0.346 A, and a 3 % module
  mismatch is 0.519 A. The 20 V dip lies inside the MPPT-step range. A 40 V or 60 V arc *outside* any bypass loop gives a
  dip larger than one MPPT step but of similar order.
- **In-loop maximum** (fixture C1 location, SS2 of M15): the worst case is that D2 conducts and the string loses one
  substring, an equivalent step of Vmpp/3 + Vf = 13.16 V. The dip is then at most **0.199 A** (linear) or **0.224 A**
  (SDM n = 1.1), 1.2–1.3 % of Impp, which is no larger than a 1–2 % MPPT step. DERIVED, algebra.

## 2. C1 in-loop voltage cap Voc_ss + Vf

The arc and the SS2 cells form a branch across D2. Once V_arc > V_ss(I) + Vf, D2 conducts, so the arc voltage cannot exceed
Voc_ss + Vf, which is reached as I_arc → 0.

| Cell T | Voc_module (V) | Voc_ss = Voc/3 (V) | Cap Voc_ss + 0.45 (V) |
|---|---|---|---|
| 25 °C | 45.750 | 15.250 | **15.700** |
| −10 °C | 49.593 | 16.531 | **16.981** |
| 70 °C (extra) | 40.809 | 13.603 | 14.053 |

At I_min = 0.5 A the fixture S-O law needs 18.895 V (1 mm), 19.878 V (3 mm) or 20.861 V (5 mm). That exceeds the
−10 °C cap of 16.98 V. Under the fixture law there is therefore **no steady in-loop arc operating point at any fixture
temperature**. This is illustrative only, because the law is uncalibrated (A-010). Literature minimum arc voltages of
12–13 V (A-025) would fall *below* the cap, so whether an in-loop arc can be sustained stays open (X-009).

## 3. HF current per volt of arc noise, 936 m loop

Lumped |Z| = √(R² + (ωL)²) with R 6.35 Ω and L 0.667 mH, as specified in the task:

| f | ωL (Ω) | \|Z\| (Ω) | A/V | mA/V |
|---|---|---|---|---|
| 10 kHz | 41.910 | 42.388 | 0.023592 | **23.59** |
| 100 kHz | 419.10 | 419.14 | 0.0023859 | **2.386** |
| 1 MHz | 4190.97 | 4190.98 | 0.00023861 | **0.2386** |

Validity check (control extension, DERIVED, algebra). The line length is 0.044 λ at 10 kHz, **0.44 λ at 100 kHz and
4.4 λ at 1 MHz**, so the lumped model is not valid at the upper two frequencies. Model used for comparison: lossless
two-wire line, inverter end shorted by C_in (X_C = 0.106 Ω at 10 kHz), zero source impedance at the array end.

| f | Array-end mA/V | Inverter-end mA/V | Lumped / distributed (array end) |
|---|---|---|---|
| 10 kHz | 27.02 | 28.10 | 0.87 (the 0.1 µH/m DC internal inductance is the main term; with L_ext only, lumped gives 27.32) |
| 100 kHz | 20.00 | 21.43 | 0.12 |
| 1 MHz | 13.09 | 15.18 | 0.018 |

With an ASSUMED round-wire skin factor (R_ac/R_dc = 1.21/3.29/9.88, proximity ignored) the array-end values become
26.4/19.6/12.3 mA/V. The lumped 100 kHz and 1 MHz figures therefore understate the HF current by about 8× and 55× at these
spot frequencies. The true response has standing-wave structure; see §4.

## 4. Lossless-line quarter-wave frequencies f = v/(4·route), v = c/√2 = 211 985 280 m/s

| Route (m) | f_λ/4 (Hz) | 3·f_λ/4 (Hz) | f_λ/2 (Hz) |
|---|---|---|---|
| 78 | **679 440** | 2 038 320 | 1 358 880 |
| 200 | **264 981.6** | 794 944.8 | 529 963.2 |
| 300 | **176 654.4** | 529 963.2 | 353 308.8 |
| 600 | **88 327.2** | 264 981.6 | 176 654.4 |
| 936 | **56 620.0** | 169 860.0 | 113 240.0 |

Interpretation, for Phase 2. With the inverter end shorted by C_in, the near-end (arc-end) input impedance is
jZ0·tan βl. It is infinite at f_λ/4, so the current at the *arc end* has a null there. The current at the *inverter end*
is V/(Z0·|sin βl|) ≥ V/Z0 = 7.7 mA/V, so it has **no null**. If the far end were open instead, the same frequency would be a
series resonance, a current maximum. Whether f_λ/4 is a "null" therefore depends on where the sensor sits and how both ends
are terminated. The array-end termination (string cell capacitance, A-027) is UNKNOWN. The 600 m and 936 m values (88 kHz
and 57 kHz) lie inside a typical 10–100 kHz AFCI band.

## 5. C2-far steady state (both strings at Isc 18.4 A, 40 V arc)

Topology: S19 (600 m) and S20 (936 m) share the MPPT node. The arc is 931 m from the inverter along S20's home-run. In
steady state the inverter draws 0 A and C_in has discharged. All of S19's current then returns through the S20 home-run
to the arc, and S20's own modules feed the arc through 5 m of cable.

| Quantity | Using R(936 m) | Using R(931 m) | Unit |
|---|---|---|---|
| V_node = 40 + 18.4·R | **156.768** | 156.144 | V |
| I_arc | 36.8 | 36.8 | A |
| I in S20 home-run (node → arc, reversed) | 18.4 | 18.4 | A |
| I from S20 modules into the arc | 18.4 | 18.4 | A |
| S19 terminal voltage (V_node + 18.4·4.068) | 231.62 | 231.00 | V |
| **Inverter-end S20 current swing** (+17.31 A toward the inverter → 18.4 A away) | **35.71** | 35.71 | A |
| Swing if referred to a pre-fault Isc | 36.8 | 36.8 | A |

S19 at 231 V is about 7.7 V per module, so it sits near Isc and the assumption is consistent.

## 6. C_in energy fraction delivered to a 40 V arc (V_arc·Q against ½CV²)

½·C_in·V0² with V0 = 1143.9 V gives **98.138 J**. Because the arc voltage is constant, the arc receives V_arc·Q of the
discharge charge. The rest goes to the home-run resistance.

| Discharge assumption | Q (C) | E_arc (J) | Fraction of ½CV0² |
|---|---|---|---|
| Full discharge, Q = C·V0 | 0.171585 | **6.863** | **6.99 %** (= 2·V_arc/V0) |
| To V_arc, Q = C(V0 − 40) | 0.165585 | 6.623 | 6.75 % |
| To the steady node 156.14 V (931 m), physically consistent | 0.148163 | 5.927 | 6.04 % |

`illustrative_simulation` cross-check: a lumped ODE (C_in + 931 m R/L + two 18.4 A sources, Radau, rtol 1e-10). It gives
E_arc(5 s) − 40·36.8·5 = 5.9265 J. That equals V_arc·C·(V0 − V_final) to 4 significant figures, because charge is
conserved. The peak arc current is 166 A at t = 0.29 ms. The C_in–home-run loop is overdamped: ζ = (R/2)·√(C/L) ≈ 1.5.
At t = 0+ the arc current is 1.09 A, above I_min. That value is an artefact of the task's set-up: the inductor carries the
pre-fault −17.31 A while the S20 source steps to Isc.

## 7. C2-far 5 s arc energies, fixture S-O law ("20 V intercept"), 1 mm gap

| Case | I_arc (A) | V_arc (V) | P (W) | E(5 s) (J) |
|---|---|---|---|---|
| Both strings feed (steady) | 36.8 | 31.6501 | 1164.72 | **5823.6** |
| S20 alone (S19 + C_in separated) | 18.4 | 29.1240 | 535.88 | **2679.4** |
| Ratio S20-alone/both | — | — | — | **0.46009** = 0.5^1.12 |

ODE with the C_in transient and the S-O law (`illustrative_simulation`): 5829.35 J, which is 5.73 J above the steady value.
In the constant-40 V version the 5 s steady energies are 7360 J and 3680 J. Not modelled: arc-length change, extinction,
the inverter's response, and the night/V_DIRECTBUS variants.

## 8. C3 hot connector (no arc), I = Impp = 17.31 A

| R (Ω) | ΔV = I·R (V) | P = I²R (W) | Steady ΔT = P/h (K) | T_steady (°C) | Ratio R/(dR/dT·40 K), 936 m | Ratio vs 20 K drift |
|---|---|---|---|---|---|---|
| 0.05 | **0.8655** | **14.982** | 59.93 | 94.9 | **0.0501** | 0.1002 |
| 0.2 | **3.462** | **59.927** | 239.71 | 274.7 | **0.2005** | 0.4010 |
| 1.0 | **17.31** | **299.64** | 1198.5 | 1233.5 (outside lumped validity) | **1.0024** | 2.0048 |

- Cable dR/dT (936 m loop) = 6.34608 × 0.00393 = **24.940 mΩ/K** (DERIVED). A 40 K drift is 0.9976 Ω, or 17.27 V at Impp.
- By route, dR/dT = 2.078 / 5.329 / 7.994 / 15.987 / 24.940 mΩ/K for 78 / 200 / 300 / 600 / 936 m. The 40 K ratios for
  0.05 Ω are 0.601 / 0.235 / 0.156 / 0.078 / 0.050.
- If the node is held, the string current falls by only 0.012 / 0.048 / 0.235 A (linear R_dyn), so the DC current channel
  is weaker still.
- **Thermal:** τ = C_th/h = 8/0.25 = **32 s**.
- **Time to limit** (control extension, initial state = steady at 0.35 mΩ, fixture 600 s linear ramp):
  - 0.2 Ω reaches 150 °C at 319 s and 200 °C at 445 s.
  - 1.0 Ω reaches them at 87 s and 113 s.
  - 0.05 Ω never reaches 150 °C.

## 9. Loop commutation time t = L·I/V_clamp, L = 0.667 mH

| V_clamp (V) | t at Impp 17.31 A (µs) | t at Isc 18.4 A (µs) | IV-aware t at Impp (µs) | IV-aware clamp energy (J) |
|---|---|---|---|---|
| 400 | **28.86** | 30.68 | 75.42 | 0.188 |
| 600 | **19.24** | 20.45 | 30.82 | 0.140 |
| 800 | **14.43** | 15.34 | 19.88 | 0.126 |
| 1000 | **11.55** | 12.27 | 14.73 | 0.120 |
| 1200 | **9.62** | 10.23 | 11.72 | 0.116 |
| 1400 | **8.25** | 8.77 | 9.73 | 0.113 |
| 1600 | **7.22** | 7.67 | 8.32 | 0.111 |

½·L·I² is 0.09998 J at Impp and 0.1130 J at Isc.

**IV-aware extension** (control, algebra plus quadrature). For SW-STR-INV opening with the node held by C_in at
1034.05 V (= Vmpp_string − Impp·R_loop), the string EMF rises toward Voc as I falls. The net decay voltage is therefore
V_clamp − (V_str(I) − R·I − V_node), and at I = 0 the string offsets the clamp by 338.45 V (STC, SDM n = 1.1).
Consequences:

- The simple formula is 2.6× optimistic at 400 V and 1.15× optimistic at 1600 V.
- The clamp absorbs more than ½LI².
- Any V_clamp below the steady off-state voltage cannot finish the commutation; the clamp would conduct continuously.
  The steady off-state voltage is 228.6 V with the node at Vmpp, 1372.5 V with the node at 0 V at STC, and 1487.79 V with
  the node at 0 V at −10 °C. Every V_clamp ≤ 1400 V in this sweep is below that last value.

Distributed-line caveat: the round trip is 8.83 µs and Z0·Impp = 2249 V. Lumped times ≤ ~12 µs (V_clamp ≥ 1000 V) are
comparable to the round trip, so the real decay is a staircase of steps of about V_clamp/Z0 per transit. The lumped
estimate is an order-of-magnitude figure only.

## 10. Not modelled (all items)

- Arc plasma dynamics. The S-O law is uncalibrated (A-010).
- HF arc source impedance and the string's HF impedance (A-027 UNKNOWN).
- Inverter control during faults and EMI filter impedance.
- Temperature dependence of the IV curve in the C1 dip (STC only).
- Cable temperature profile and proximity effect.
- Connector heat paths beyond one RC node.
- Module capacitance during commutation.
- Night, V_DIRECTBUS and irradiance variants of C2.

No probabilities are inferred anywhere.
