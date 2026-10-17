# Review track A (power systems) — charter and initial attack

**Supervisor:** SUP-A (Claude, model `fable`), persistent across barriers B1–B3. **Date:** 2026-10-17, cycle 1.
**Scope (brief §3 track A):** PV I-V and bypass substrings, conductor/fault zones, actual parallel connections (only the
paired string shares an MPPT node), transmission-line R/L/C, inverter DC input/DC link, MPPT, earthing, transient energy
and alternate feeds. I do not build the models (W01 topology, W02 PV module/string, W03 cable + DC side). I attack, set
acceptance criteria, and run small independent calculations.
**Fixture:** `fixture/system-fixture.json` (V11_CYCLE1_SHARED_FIXTURE_v1, ILLUSTRATIVE, not OEM verified). Every number
below is DERIVED from it unless labelled ASSUMED/UNKNOWN. **Grade of everything here: algebra** (closed-form or scalar
root-finding; no circuit simulation ran). Reproducer: `review/track-A-check.py` (run from `claude-study/`:
`python3 review/track-A-check.py`; sha256 `e8840777e373c5816883a3f4b22968019d7e5b1046adfe2760fd8d852a095d84`).
Its single-diode fit uses FIXED ideality n in {1.0, 1.2, 1.4} as a reviewer's cross-check; the study fit must come from
W02 with residuals. Cross-check fit at n = 1.2: Iph 18.406 A, I0 3.14e-9 A, Rs 0.0938 ohm, Rsh 288 ohm, residual 4e-16.

Notation: Voc_m 45.75 V (STC), 49.593 V (-10 C); Voc_s = 30*Voc_m = 1372.5 V (STC), 1487.79 V (-10 C); Vmpp_s 1143.9 V;
Isc 18.4 A; Impp 17.31 A; substring Voc_ss = Voc_m/3 = 15.25 V (STC), 16.53 V (-10 C), 13.60 V (70 C); bypass Vf 0.45 V
(fixture ASSUMED); C_in 150 uF; C_dc 2 mF; arc law V_arc = (20 + 0.534*gap_mm)*I^0.12 (fixture, UNCALIBRATED).

---

## 1. Independent source-to-fault analysis of the three priority cases

### 1.0 Two topology facts that drive everything below (algebra)

F1. **A substring's own photocurrent cannot circulate through its own bypass diode.** D2 (anode at tap N1, cathode at
N2) is reverse-biased by SS2's own voltage; it conducts only the *string* current when the SS2 branch voltage falls below
-Vf. Consequence: a series arc inside the SS2 loop carries current only while string current flows, and D2 clamps the arc
voltage at V_arc(I_ss) = V_cells_SS2(I_ss) + Vf <= Voc_ss + Vf = **15.70 V (STC) / 16.98 V (-10 C) / 14.05 V (70 C)**.
The fixture law needs >= V_arc(I_min = 0.5 A, 1 mm) = **18.90 V** to sustain, and 15 V (ASSUMED) to ignite. So, under the
fixture law, the C1 arc as specified **cannot be sustained at any temperature** and cannot ignite at 70 C; at STC/cold
it can ignite (15.0 V <= 15.7 V) and must then extinguish: a sputtering ignite/extinguish cycle whose per-cycle energy is
bounded by (Voc_ss+Vf)*Isc*t_cycle (289 W upper envelope; actual UNKNOWN). Arc power bound with any arc law:
P_arc <= max_I [V_cells_SS2(I)+Vf]*I ~= P_mpp_ss + Vf*Impp = **220 + 7.8 = 228 W** (STC). This is ILLUSTRATIVE and hinges
entirely on the arc law's minimum voltage; it is also why C1-as-framed will not discriminate between P0/P1/P2 (see §6).

F2. **A series loop is de-energised by any series opening; a parallel fault is not.** The string S20 is one series loop
(30 modules, 33 mated interfaces, row return, 936 m home-run pair, MPPT node). Opening it anywhere (SW-M-OUT at any
module, SW-STR-ARR, SW-STR-INV) stops the loop current to zero; this clears C1 and C3 but only removes S20's *own*
contribution to a C2 arc on the home run. The paired string S19, C_in and (V_DIRECTBUS) C_dc stay connected to the home
run through the MPPT node unless the opening is between the node and the fault.

### 1.1 C1 — module-internal series arc, SS2 of M15/S20 (inside the D2 loop)

| Source | Path to the arc | Magnitude (algebra) | SW-M-OUT (M15) | SW-SS (SS2) | SW-STR-INV | SW-STR-ARR |
|---|---|---|---|---|---|---|
| SS2's own 22-cell x2-branch illuminated cells | in the same branch as the arc; needs string current as the return | <= 228 W STC, extinguished by fixture law (F1) | removes (loop current 0) | removes (branch open; string current via D2) | removes | removes |
| Other 29 modules + SS1/SS3 of M15 | string loop; feed the arc only until D2 conducts (V_arc > V_cells+Vf); the loop current does not change, it commutates to D2 in ~us | ~13 V x 17.31 A x ~1 us ~= 0.2 mJ per ignition; thereafter 7.8 W in D2, 0 to the arc | removes | removes (D2 carries string current; arc branch open) | removes | removes |
| Paired string S19 via MPPT node | reverse current into S20 only if V_node > EMF(S20); reverse current must cross the arc (D2 blocks it) | Inverter running: 0 (node 1143.9 V < EMF 1357 V). P0 AFCI action (inverter stops drawing, node floats): equal conditions 15 V drive < 18.9 V -> 0; S20 dark, S19 STC: **4.4–6.3 A at 24.6–25.6 V = 109–163 W** (n 1.0–1.4) | removes | removes as arc source, but SW-SS then holds V_node - EMF(S20 less SS2): full node voltage for a dark S20 (§1.5) | removes | removes |
| C_in (150 uF, 98 J at Vmpp) | only via reverse current (as S19 above) | 0 with inverter running; transient <= C*dV*V_arc ~= 150e-6*13*25 ~= 0.05 J if node floats | removes | as S19 | removes | removes |
| C_dc (2 mF, 1309 J) | V_BOOST: blocked by boost diode (0 J). V_DIRECTBUS: as C_in x13 | 0 J / <= 0.65 J transient | removes | as S19 | removes | removes |
| Loop inductance 0.777 mH at 17.31 A | 0.116 J; stays circulating through D2, NOT delivered to the arc | 0 to arc; but it IS the clamp energy of any switch that opens the loop (§3) | n/a | n/a | n/a | n/a |
| Frame capacitance (floating IT array) | CM only; dV at the arc ~13 V | negligible (< 1 mJ) | – | – | – | – |

Variant that matters (not C1 as framed): **D2 open** (ADV-open-bypass-diode) or the arc **outside** the loop (J-box
ribbon, connector = external_connector_series_arc). Then V_arc is set by the string's I-V, not clamped: ~28.9 V at
17.31 A, **~500 W** fed by the other 29 modules, indefinitely, until any series opening. P1/P1b/P2/P2b all clear it;
P1b (SW-SS) cannot clear the outside-loop variant at all.

### 1.2 C2-far — parallel arc 5 m from the array end of S20's home run (931 m from inverter)

Pre-trip operating point (STC, gap 1 mm, both strings at the arc through their cable resistances; n = 1.2 fit):
I20 = 18.40 A (via 5 m: 0.034 ohm + 0.108 ohm string internal), I19 = 18.37 A (via 600 m + 931 m: 10.38 ohm),
I_arc = 36.77 A, V_arc = 31.6 V, **P_arc = 1164 W**; MPPT node collapses to V_arc + 6.31 ohm*18.37 A ~= **148 V**
(below the 500 V window: the inverter will stop; that does not reduce the arc current).

| Source | Path | Magnitude | SW-M-OUT (any S20 module) | SW-STR-INV (S20) | SW-STR-ARR (S20) |
|---|---|---|---|---|---|
| S20's 30 modules | array end -> 5 m -> arc | **18.40 A = 99.98 % of Isc**, 29.1 V, **536 W** (gap 1) – 592 W (gap 5); 246 W at 500 W/m2, 88 W at 200 W/m2; extinction by the law only below ~27 W/m2 | removes | **does NOT remove** | removes |
| S19 via MPPT node + 931 m | node -> 931 m -> arc | 18.37 A, **535 W**; 3.5 kW dissipated in 1531 m of cable | does NOT remove | removes | **does NOT remove** |
| C_in 150 uF | node -> 931 m (R 6.31 ohm, L 0.664 mH, zeta 1.5 overdamped, tau_LR 105 us, RC 0.95 ms) | releases 96.5 J; charge 0.149 C; **~4.5 J to the arc** at ~30 V, ~92 J in the cable; I_pk ~158 A | does NOT remove | removes | does NOT remove |
| C_dc 2 mF | V_BOOST: 0 J. V_DIRECTBUS: same path x13: ~60 J to arc; if the bus is 24-string (see objection D-3), steady fault current is cable-limited to (1144-30)/6.31 = **177 A**, 198 kW in the home run | – | removes | – |
| Home-run L 0.664 mH | 0.11 J at 18.4 A; not delivered to arc; sets SW-STR-INV clamp energy | – | – | – |
| Line C 34 nF | 0.022 J at Vmpp; first wave reaches inverter at **4.39 us**, current step (Vmpp-V_arc)/Z0 = 8.6 A per transit | – | – | – |
| Frame C (ASSUMED 5–150 nF/module) | CM-to-DM conversion through the arc | 0.6–18 J, UNKNOWN | – | – | – |

**Residual after P2 (SW-STR-INV only): 536 W indefinitely from S20's own modules. Residual after P2b (SW-STR-ARR
only): 535 W from S19 plus C_in. Only P3 (both ends) removes all current sources; the fault must lie between them.**

### 1.3 C2-near — parallel arc 5 m from the inverter end

Same sources, mirrored: S20 feeds via 931 m (18.38 A, 535 W, 2.1 kW in its own cable); S19 via node + 5 m (18.4 A);
C_in via 5 m only: Z_surge = sqrt(3.57 uH/150 uF) = 0.154 ohm, undamped peak bound (1144-30)/0.154 = **7.2 kA**,
LC period 145 us, zeta(cable only) 0.11 -> most of the **98 J reaches the arc within ~0.2 ms**; the fixture arc law is
not valid at kA (it gives V_arc ~59 V at 7 kA); label the near-end capacitor contribution "order 10^2 J, waveform
UNKNOWN". V_DIRECTBUS adds C_dc: 1309 J, peak bound 26 kA — an arc-flash class event, UNKNOWN beyond "order 10^3 J in
< 1 ms". Switch matrix identical to C2-far (fault is on the array side of SW-STR-INV): P2 alone leaves S20's 535 W; P2b
alone leaves S19 + C_in (+ C_dc); P3 needed.
Night (G = 0): S19 dark cannot source current (no photocurrent); C_in ASSUMED discharged (0 J) unless the inverter holds
it; **V_DIRECTBUS at night: UNKNOWN whether the grid-side bridge holds C_dc at ~1.1 kV** (fixture note says "only
capacitors"; a grid-held link is an unlimited source until AC protection acts) — W03 must declare this.

### 1.4 C3 — hot connector M12(+)/M13(-), no arc

Single source: the series string current, set by S20's own 30 modules and the MPPT voltage. S19, C_in, C_dc do not add
current to a series element. P = Impp^2*R = **15.0 / 59.9 / 299.6 W** at 0.05 / 0.2 / 1.0 ohm; **54 / 216 / 1079 kJ per
3600 s** horizon; voltage drop 0.87 / 3.46 / 17.3 V = 0.08 / 0.30 / 1.51 % of Vmpp_s. Lumped thermal (fixture ASSUMED
8 J/K, 0.25 W/K, 35 C): tau = 32 s; steady dT = 60 / 240 / 1199 K -> 95 / 275 / 1234 C. With an ASSUMED 150 C housing
limit (R = 0.096 ohm), the 0.2 and 1.0 ohm ramps cross it at ~287 s and ~57 s of the 600 s ramp; the 0.05 ohm case
plateaus at 95 C. Constant-conductance thermal is unphysical above ~200 K rise (radiation, melting, housing failure ->
series arc, i.e. the C1-outside-loop variant); state so. Removal: any series opening (SW-M-OUT anywhere in S20,
SW-STR-INV, SW-STR-ARR) stops the heating; **SW-SS does nothing** (connector is outside all bypass loops; string current
continues through the bypass diodes). The MPPT cannot throttle S20 alone (shared node). Detectability: 0.87–3.5 V is
below the 936 m route's thermal drift, 0.748 ohm x 17.31 A = **13.0 V per 30 K**; see objection C-3.

### 1.5 X-001 — steady post-trip voltage across an opened SW-M-OUT (and SW-SS)

KVL round the open string loop with zero current: every illuminated module sits at its Voc, so
**V_sw = 30*Voc_m(T) - V_node** (the switch's own module is part of the sum; no sharing exists with a single switch).

| Node condition | V_node | V_sw STC (Voc_s 1372.5) | V_sw, S20 at -10 C (1487.79) |
|---|---|---|---|
| (a) inverter at MPP on S19 | 1143.9 V | **228.6 V** | 343.9 V (both cold, node at 1240.0 V ASSUMED-scaled Vmpp: 247.8 V) |
| (a') MPPT global scan at window minimum | 500 V | 872.5 V | 987.8 V |
| (a'') inverter off, S19 at Voc (node floats) | Voc_s19 | 0 V equal conditions; 98 V if S19 at 200 W/m2; 115.3 V if S20 -10 C vs S19 25 C | – |
| (b) node 0 V (DC side discharged/shorted, S20 lit) | 0 V | **1372.5 V** | **1487.8 V** |
| (c) parallel arc on home run (node ~V_arc) | 30 V | **1342.5 V** | **1457.8 V** |
| (c') bolted parallel fault | 0 V | 1372.5 V | 1487.8 V |

Case (c) is precisely the event a module switch is asked to act on, so the standing voltage of a lone SW-M-OUT is
string class: **>= 1487.8 V plus transient margin (fixture cold Voc), i.e. a 1500 V-class element is insufficient; a
>= 1700 V device or a different architecture is required.** A clamp below the standing voltage conducts continuously
(600 V clamp in case (c): 11 kW; 1200 V: 22 kW). The only way a module switch sees ~Voc_m is the P3 variant where all 30
switches of S20 open on a string-wide signal and share: equal share = Voc_m - V_node/30 = 7.6 V (case a) to 49.6 V
(cold, node 0). Sharing is set by off-state leakage/clamps, not guaranteed; the first device to open holds the full
1342–1458 V until the others do (18.4 A x 1.34 kV = 24.7 kW into its clamp; 2.5 J per 100 us of skew) — Track B item.
**SW-SS (inside the D2 loop), forward string current, D2 healthy: V_sw = Voc_ss + Vf = 15.70 V (STC) / 16.98 V
(-10 C) / 14.05 V (70 C), independent of V_node — genuinely module-local in that regime only.** It reverts to string
class when (i) D2 is open (string current has no bypass), or (ii) the module is dark while the node is live: the
reverse (node-into-string) path runs through SS2's cells and SW-SS, D2 blocks it, so an open SW-SS holds **V_node =
1143.9 V (inverter running on S19) up to 1487.8 V**; with SW-SS closed the same regime passes 0.48–0.73 A reverse
through the dark string (n 1.0–1.4; no string fuse in P0). (iii) Module lit, inverter off, S19 at higher Voc: 15–130 V.
An SW-SS left latched open on a module that later goes dark (snow, row shading) while S19 runs is a string-voltage event.

## 2. Position on X-002 (far-end parallel arc vs inverter-end breaker)

**The claim is false under the fixture topology (grade algebra).** After SW-STR-INV opens, S20's 30 modules still
close a loop through 5 m of cable (0.034 ohm) and the string's 0.108 ohm internal resistance into the arc. Treating the
string as a current source limited by Isc at low voltage is accurate to 0.02 % here (module at 1.1 V delivers
0.99979*Isc from the n = 1.2 fit): residual arc current **18.40 A at 1000 W/m2 (18.81 A at 70 C; 18.08 A at -10 C),
9.20 A at 500 W/m2, 3.68 A at 200 W/m2**; arc voltage 29.1 / 26.8 / 24.0 V (gap 1 mm), 32.2 V at Isc for 5 mm; residual
power **536 (gap 1) – 592 (gap 5) W at STC, 246 W at 500 W/m2, 88 W at 200 W/m2**. The fixture law extinguishes only
when I < 0.5 A, i.e. below ~27 W/m2 (ILLUSTRATIVE). Over the 5 s horizon P2 delivers ~2.7–3.0 kJ vs ~5.8 kJ for P0: a
"54 % reduction" that is a horizon artefact, since 536 W continues until sunset or until the string loop is opened at the
array side (SW-STR-ARR or any SW-M-OUT of S20). SW-STR-INV does remove S19 (535 W), C_in (~4.5 J far / ~98 J near) and
C_dc, which is worthwhile, but it is not "clearing". Required action for C2 = open the string loop on the array side AND
isolate the node side (P3), or the module-level units of S20 must all open; a lone inverter-end action must be labelled
"source reduction, arc persists". Note for X-003: the detection signature of C2-far reaches the inverter 4.39 us after
inception; the string current itself settles with tau = L/R ~ 0.8 ms (S20 side) and the C_in discharge with RC 0.95 ms.

## 3. Energy magnitudes (algebra; sanity bounds for wave-2 workers)

Cable line parameters from fixture geometry (6 mm2, r 1.382 mm, D 6.4 mm, eps_r 2): L_ext = mu0/pi*ln(D/r) = 0.613 uH/m
(acosh form 0.593 uH/m, 3.4 % lower — W03 must pick one); L_int(dc) 0.1 uH/m (fixture); C = 36.3 pF/m; Z0 = 130 ohm;
v = 2.120e8 m/s; 936 m one-way 4.415 us (matches fixture); R 3.39 ohm/km -> loop 6.346 ohm (936 m), 6.312 ohm (931 m),
4.068 ohm (600 m), 0.0339 ohm (5 m); string internal (30 x 0.63 m of 4 mm2 lead + 33 x 0.35 mohm) 0.108 ohm.
Row-return loop (fixture 1 m separation; **row length 40 m ASSUMED**): 2.73 uH/m x 40 m = 0.109 mH. L_loop(S20) = 0.667 +
0.109 = **0.777 mH**.

| Store | Value | Note |
|---|---|---|
| 1/2 L I^2, 936 m home-run pair at 18.4 A | **0.113 J** (0.097 J external-only) | must be absorbed by whichever switch opens that loop |
| 1/2 L I^2, full S20 loop, 17.31 A / 18.4 A | 0.116 J / 0.132 J | SW-M-OUT clamp duty (plus source energy during t_off) |
| 1/2 C V^2, C_in 150 uF at Vmpp_s / Voc_s / Voc_s cold | **98.1 J** (32.7–327 J for 50–500 uF) / 141 J / 166 J | C2 only; far: ~4.5 J to arc; near: most of it |
| 1/2 C V^2, C_dc 2 mF at Vmpp_s | **1309 J** (654–2617 J for 1–4 mF) | V_BOOST: 0 J reaches PV side; V_DIRECTBUS: all |
| Line C 936 m (34 nF) at Vmpp_s | 0.022 J | travelling-wave only |
| Frame C, 5–150 nF/module ASSUMED, +/-572 V CM | 0.6–18 J | UNKNOWN; CM path |
| Arc power envelope, V_arc 20–60 V x 17–18.4 A | **340–1104 W** (fixture law: 500 W at Impp/1 mm, 592 W at Isc/5 mm; two strings 1164 W) | 1.7–5.5 kJ per 5 s horizon |
| Hot connector | 15 / 60 / 300 W | 54 / 216 / 1079 kJ per hour |

Unclamped L*dI/dt for a 1 us interruption of 17.31 A in L_loop: **13.4 kV** — sub-microsecond opening of the string
loop is a flashover, not a design point. Clamped turn-off of the loop is set by the loop, t_off = L*I/(V_clamp - V_src),
E_clamp = 1/2 L I^2 * V_clamp/(V_clamp - V_src): SW-M-OUT with V_clamp 1500 V: case (c) STC 85 us, 1.11 J; cold 319 us,
4.14 J. SW-STR-INV (931 m loop, 18.4 A, 1500 V clamp): node at Vmpp 32 us, 0.44 J; node at Voc STC 78 us, 1.07 J; cold
289 us, 3.99 J. These are per event and at the Type 2 SPD's working-voltage level (coordination item for Track B).

## 4. Acceptance checklist for W01 / W02 / W03 at barrier B1

1. Topology JSON marks each MPPT node as shared by exactly two strings (S19+S20 on one node); 12 nodes; no PV-side edge
   between MPPT nodes in V_BOOST; V_DIRECTBUS flagged ADVERSARIAL with its bus membership (2 or 24 strings) declared.
2. Each module has nodes J-, N1, N2, J+ and edges SS1–SS3 (22 cells, 2 parallel branches) with D1–D3 orientation explicit
   (anode at the lower tap); an automated test asserts F1 (a substring's own current cannot flow through its own diode).
3. Fault sites are graph elements: C1 an edge inside SS2 of M15 (state whether one or both half-cell branches are opened);
   C2-far/near nodes at 5 m / 931 m on the S20 home run; C3 the mated-interface edge M12(+)–M13(-), one of 33 per string,
   each carrying 0.35 mohm.
4. Source enumeration per fault is computed by closed-loop reachability through the fault element (illuminated modules,
   S19, C_in, C_dc, line C, frame C), not hand-listed; the switch-state table enumerates SW-M-OUT(M15 / all 30), SW-SS,
   SW-STR-INV(S19, S20), SW-STR-ARR, bypass diodes (healthy/open/short) and the P0 AFCI state "inverter current = 0,
   node floating with S19 and S20 still paralleled".
5. Post-trip node voltages are SOLVED by a nonlinear DC solve of the module I-V network with switches open, not asserted;
   must reproduce §1.5: 228.6 / 1372.5 / 1342.5 V (STC) and 1487.8 V (-10 C) for SW-M-OUT, 15.70 V for SW-SS forward,
   and the dark-module/live-node SW-SS case (1143.9 V).
6. W02 fit: five-parameter single-diode, residuals at Voc, Isc, Vmpp, Impp and dP/dV = 0 at Vmpp reported (< 1e-6
   relative), fitted n stated (my fixed-n cross-check brackets: n 1.0 -> Rs 0.136 / Rsh 135 ohm; n 1.2 -> 0.094 / 288 ohm;
   n 1.4 degenerates Rsh); irradiance scaling of Iph; Voc -0.24 %/K and Isc +0.05 %/K (ASSUMED) applied.
7. W02 exposes substring terminals and provides (i) the dark forward characteristic (Iph = 0) for backfeed, (ii) the
   reverse-bias branch or an explicit bypass clamp at -Vf with stated validity, (iii) a test that the C1 loop cannot
   satisfy V_arc >= 18.9 V (arc current -> 0) with D2 healthy, and the D2-open variant where the string feeds the arc.
8. W03 cable: lumped vs distributed stated with validity; lambda/10 for 936 m is f < 22.6 kHz (11.3 kHz at lambda/20),
   round trip 8.8 us; any edge faster than ~50 us on the 936 m route uses the distributed (ngspice LTRA/TXL or >= 10
   sections) model; Z0 130 ohm, v 2.12e8 m/s, 4.415 us reproduced; ln vs acosh inductance form chosen and stated; skin
   effect (delta 0.21 mm at 100 kHz, Rac/Rdc ~3.3) stated as modelled or not.
9. W03 declares the row-return geometry (length and separation) as ASSUMED and reports E_clamp sensitivity to it.
10. DC side: C_in per MPPT node; boost diode orientation makes C_dc -> PV flow impossible in V_BOOST (test); V_DIRECTBUS
    C_dc at the node; inverter draw as a controllable source with MPPT at 0.1 s steps, "ceases to draw" state, and the
    500–1500 V window; night initial voltages of C_in and C_dc declared (ASSUMED values, grid-held link UNKNOWN).
11. Energy bookkeeping: per case, sum of source energies = E_arc + E_cable_R + E_switch + E_clamp + dE_L + dE_C within
    1 %; two independent integrals (solver .meas and trapezoid on the full-rate export) agree within 1 %; decimated CSVs
    are not used for integrals (C_in near-fault LC period 145 us).
12. Every file states NOT MODELLED (arc plasma, HF signature, skin effect, frame C, earth faults, thermal) and carries the
    producing script's sha256; fixture unit suffixes only; no extinction claim without "illustrative".
13. The 24 route lengths and the per-metre R/L/C are substitutable inputs (one function of length), so S19 (600 m) and
    S20 (936 m) share code paths; a corner test runs 78 m and 936 m.
14. Common-mode: module M1 and M30 sit at about -/+572 V to frame at Vmpp (floating IT); after a first earth fault the far
    module sits at up to 1487.8 V to frame; W01 records the CM potential of every protection device location.

## 5. Objections to other tracks (to be entered in contradictions.md by the orchestrator)

B-1 (X-001, Track B): a lone SW-M-OUT is a string-class device (>= 1487.8 V standing in case (c)); any clamp below that
conducts continuously (11–22 kW). Either specify >= 1700 V class, or a 30-switch synchronous scheme with verified
voltage sharing, a per-device clamp rated for 24.7 kW x skew, and a fail-short clamp failure mode.
B-2 (X-003, Track B): with a 1500 V clamp the loop-limited t_off is 32–320 us and E_clamp 0.44–4.1 J per event; device
off-time below ~10 us buys nothing and an unclamped 1 us opening implies 13.4 kV. Coordinate the SW-STR-INV clamp with
the Type 2 SPD working voltage or the SPD absorbs the repetitive DC interruption energy it is not rated for.
B-3 (Track B): the anti-series pair's body diodes must block node-into-string current: a dark S20 on a live node passes
0.48–0.73 A reverse with the switch closed; with the switch open the full node voltage appears across it.
C-1 (X-002, Track C): after SW-STR-INV opens, the inverter-end sensor is disconnected from the arc that continues at
536 W; "cleared" cannot be inferred from signal loss at the inverter. Extinction confirmation needs an array-side or
module-local measurement. Positive note: a home-run parallel fault collapses every S20 module terminal from 38.1 V to
~1 V at ~Isc (settling tau ~0.8 ms), a local DC signature needing no HF channel.
C-2 (Track C): the P0 AFCI action "cease drawing" leaves S19 and S20 paralleled on a floating node; with S20 weaker
(dark/snow/shade), S19 backfeeds through the series arc in reverse (109–163 W illustrative). "Stop drawing" is not
"isolate"; the baseline must be modelled with the node floating, not open.
C-3 (X-008, Track C): C3 at 0.05 / 0.2 ohm drops 0.87 / 3.5 V, below the 13 V per 30 K thermal drift of the 936 m
route; string-level V/I cannot see it. The M12 module-local unit has no electrical access to the M12–M13 connector drop
unless it measures across the mated pair; only local temperature or differential sensing is plausible — quantify or say
"undetectable".
D-1 (Track D): the arc-law gaps 1/3/5 mm all give V_min 18.9–20.9 V > 15.7 V loop maximum, so every C1 healthy-D2 case
"extinguishes" and every 70 C case "cannot ignite" by construction; the campaign must add arc-law variants with
V_min <= 14 V (ASSUMED alternative) or the 162 C1 identities measure nothing.
D-2 (Track D): tag each case with lumped/distributed model and time step (<= 0.44 us for distributed 936 m); MPPT ripple
at 16–40 kHz on 936 m is l/lambda = 0.07–0.18, beyond lumped validity — the benign-noise corpus for S20 must be distributed.
D-3 (Track D, X-007): V_DIRECTBUS as written ("common DC bus") implies 24 strings on one bus, contradicting the 2-string
rule; declare membership per scenario or every DIRECTBUS result is ambiguous (177 A cable-limited far fault vs 36.8 A).
E-1 (Track E): the fixture arc form is attributed to Stokes & Oppenlander, J. Phys. D 24 (1991) 26–35; I could not access
the original (publisher blocks fetch) and the one secondary source I examined cites it only for Lowke's low-current
limitation, not for this formula: provenance NOT VERIFIED; I_min 0.5 A and ignition 15 V are ASSUMED. Track E should
block any C1 extinction statement until calibrated against published PV series-arc V-I data.
E-2 (Track E): block "P1 protects against C1": C1 with healthy D2 is self-limited regardless of P1 (F1). The
discriminating series-arc cases are D2-open and the J-box/connector arc; require both in the comparison set.
E-3 (Track E): energy at the 5 s horizon hides persistence; require power-at-horizon and time-to-extinction alongside
E_fault_j, and mark "not extinguished" explicitly (C2 under P2 or P2b).

## 6. Summary verdicts (algebra grade, fixture-dependent)
- X-001: SW-M-OUT standing voltage = 30*Voc(T) - V_node; worst 1487.8 V (-10 C, node at 0–30 V). Module-local voltage
  holds only for SW-SS in forward conduction with D2 healthy (15.7–17.0 V) and fails for a dark module on a live node.
- X-002: inverter-end breaker leaves 18.4 A x 29–32 V = 536–592 W at the far arc; not a clearing action; P3 required.
- C1 as framed is self-limited to <= 228 W and extinguished under the fixture law; redirect effort to D2-open and
  outside-loop series arcs. C3 is a thermal detection problem; any series opening clears it, SW-SS does not.
