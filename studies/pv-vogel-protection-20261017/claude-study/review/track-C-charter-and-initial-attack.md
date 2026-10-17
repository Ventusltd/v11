# Track C (SUP-C) — Detection and controls: charter and initial attack

Cycle 1, 2026-10-17. Supervisor SUP-C (model: Claude `fable`). Status: REVIEW POSITION, not a design, not a validated
detector. Fixture: `fixture/system-fixture.json` (V11_CYCLE1_SHARED_FIXTURE_v1, ILLUSTRATIVE_PROVISIONAL_NOT_OEM_VERIFIED).
All numbers below are `algebra` grade unless stated; derivations are reproducible from the equations shown and from the
scratch script `track_c_calcs.py` (sha256 `53da867041b7602c4057e694e776edc092786e22775127e69f0baae68d25aa76`, python3 -I,
reads only the fixture; orchestrator may copy it into `review/`). Labels: MEASURED / DERIVED / ASSUMED / UNKNOWN / REJECTED.

## 0. Common derived quantities (DERIVED from fixture unless labelled)

```
R_loop(route) = 2 * route_m * 3.39 ohm/km      -> 936 m: 6.346 ohm ; 931 m: 6.312 ohm ; 600 m: 4.068 ohm ; 5 m: 0.0339 ohm
dR_loop/dT (936 m) = 6.346 * 0.00393 /K        = 24.9 mohm/K   (+-25 mohm/K as in the task)
L_loop(936 m) = (0.613+0.1) uH/m * 936 m        = 667 uH ; C_line(936 m) = 36.3 pF/m * 936 = 34 nF ; Z0 ~ 130-140 ohm
one-way delay = route / 2.12e8 m/s              -> 936 m 4.415 us ; 931 m 4.392 us ; 600 m 2.83 us ; 5 m 24 ns
IR drop S20 at Impp = 17.31 A * 6.346 ohm        = 109.9 V (9.6 % of string Pmpp = 1902 W lost in the 936 m home-run)
MPPT node pre-fault (S19 600 m / S20 936 m)      ~ 1.03-1.07 kV (the two strings cannot both sit at MPP on one node)
module incremental conductance at MPP g_m        = 0.454 A/V (r_m = 2.20 ohm) ; string r_s = 30/g_m = 66.1 ohm
   (illustrative 5-parameter single-diode fit to Voc/Isc/Vmpp/Impp with Rsh fixed 2000 ohm ASSUMED, n = 1.35, Rs = 64 mohm;
    MUST be superseded by models/pv_module.py; only the order of magnitude is used here)
V_arc(S-O, fixture, ILLUSTRATIVE) at 17.31 A: 28.9 V (1 mm) / 30.4 V (3 mm) / 31.9 V (5 mm); at 0.5 A: 18.9 / 19.9 / 20.9 V
```

"Node held" approximation used throughout section 1: the inverter input capacitor (150 uF ASSUMED) and the MPPT hold the
MPPT node voltage for the first ~10 ms after a fault; the string behaves as a current source with incremental resistance
r_s + R_loop = 72.4 ohm. After one MPPT step (0.1 s, fixture) the operating point moves and the DC signature changes.

## 1. What each sensor location actually sees (initial attack)

### C1 — series arc. Two physically different cases; the fixture names only the second

C1(a) series arc IN THE STRING LOOP (module lead, mated connector, cell interconnect with a FAILED-OPEN bypass diode;
ledger ADV-2933/2934 and Phase 0 label external_connector_series_arc). V_arc = 20-60 V inserted into a 1143.9 V loop:

```
node held:  dI = -V_arc / (r_s + R_loop) = -V_arc / 72.4 ohm
   V_arc 20 V -> dI = -0.276 A (-1.6 %) ; 40 V -> -0.552 A (-3.2 %) ; 60 V -> -0.828 A (-4.8 %)
   exact illustrative IV: 20 V -> -1.8 % ; 60 V -> -6.7 %          P_arc = 341 / 670 / 989 W
after MPPT re-optimises (>= 0.1 s): I returns to ~Impp, string voltage lower by V_arc (1.7-5.2 % of 1143.9 V)
```

| Sensor location | DC current | DC voltage | HF / transient |
|---|---|---|---|
| Module JB (any module of S20, SW-M-OUT) | -1.6 to -4.8 % (same current everywhere in the loop) | module terminal: +0.6 to +1.8 V (modules move up the IV curve) | arc voltage noise appears across the module terminals only via the loop current: i_hf = v_arc_hf / |Z_loop(f)|; ZERO location information |
| Array end of string (SW-STR-ARR) | same -1.6 to -4.8 % | string voltage -V_arc if arc is between modules and sensor; else unchanged | same loop current; arc on the array side is 0.3 us away (72 m, ASSUMED 30 x 2.4 m) |
| Inverter end (SW-STR-INV) | same -1.6 to -4.8 % | node held (then -V_arc after MPPT) | loop current after 4.4 us; line loss 0.1 dB (10 kHz) to 1.0 dB (1 MHz) DERIVED skin-effect only, dielectric/proximity loss UNKNOWN |
| MPPT node (inverter AFCI) | S19+S20 sum: -0.8 to -2.4 % | node | as inverter end |

Key attack points for C1(a):
- The DC current change (0.28-0.83 A) is SMALLER than the MPPT perturb response (0.16-0.32 A per 1-2 % step, ASSUMED
  step size), module mismatch (0.52 A at 3 % ASSUMED) and cloud ramps (14 A over seconds). DC current alone cannot
  classify C1(a). DC string voltage alone cannot either: a 20-60 V drop equals a 6-18 K cell-temperature change
  (-0.3 %/K x 1143.9 V = -3.4 V/K, ASSUMED Vmpp coefficient) or one shaded module (-38 V).
- HF loop current per volt of arc noise, lumped: 1/(2*pi*f*L_loop) = 24 mA/V at 10 kHz, 2.4 mA/V at 100 kHz, 0.24 mA/V
  at 1 MHz (DERIVED, cable only). The 30 modules add an UNKNOWN series impedance (cell junction capacitance not in
  fixture; order 0.5-5 nF per string ASSUMED -> 0.3-3 kohm at 100 kHz, possibly dominant). W05 must carry this as UNKNOWN.
- Above f1 = v/(4*route) the loop is NOT lumped. With C_in a near-short at the inverter end and the array a high
  impedance, the inverter-end current transfer function from a far-end arc has nulls near odd multiples of
  f1 = 56.6 kHz (936 m), 88.3 kHz (600 m), 176.7 kHz (300 m), 265 kHz (200 m), 679 kHz (78 m) (DERIVED, lossless line,
  ideal terminations; real nulls are partial). A fixed-band HF detector (e.g. 40-100 kHz, typical AFCI practice,
  general knowledge) therefore has route-dependent blind spots. Any HF criterion must be evaluated per route length.

C1(b) series arc INSIDE the SS2 bypass loop (the fixture's actual C1 location, bypass diode healthy). Loop KVL with D2
conducting the string current: V_gap = V_SS2(I_gap) + Vf, bounded by Voc_ss + Vf = 15.25 + 0.45 = 15.70 V (STC) or
16.53 + 0.45 = 16.98 V (-10 C). Consequences:
- Under the fixture's own arc law (V_arc >= 18.9 V at 0.5 A) this arc CANNOT sustain; under a lower minimum arc voltage
  (12-13 V for Cu/Ag contacts, general knowledge, ASSUMED) it sustains at V_gap ~ 13 V, I_gap ~ 17 A, P_arc ~ 220 W
  fed by SS2's own photocurrent; upper bound (Voc_ss+Vf)*Isc = 289 W; <= 1.1-1.45 kJ over the 5 s horizon.
- String-level DC signature = -(V_SS2(Impp) + Vf) = -13.16 V and -0.18 A (node held): IDENTICAL to one shaded substring.
- HF: the arc current circulates SS2 -> arc -> D2. Fraction reaching the string loop ~ r_d / |Z_loop|, r_d ~ 1.5 mohm
  (ideal diode at 17 A) to ~20 mohm (real Schottky, ASSUMED): 1e-5 to 4e-6 at 100 kHz, i.e. -100 to -108 dB.
  Module-terminal HF voltage ~ r_d * i_arc_hf = 1.5-20 mV per ampere of arc-current fluctuation.
- Opening SW-M-OUT (P1) stops the string current; D2 then blocks the only return path of SS2, so I_gap -> 0 and the
  arc stops. P1 therefore DOES act on C1(b), but it cannot DETECT C1(b) from string current/HF. Only per-substring
  sensing (P1b) or a thermal observable sees it.
VERDICT C1: string-level or module-lead sensing has NO credible observable for C1(b). The P0/P1/P2 comparison for C1 is
degenerate unless C1(a) (ADV-2933/2934) is promoted to a priority waveform. See OBJECTION O-1.

### C2-far — parallel arc 5 m from the array end of S20 (931 m from the inverter)

Steady state (illustrative, node no longer held: the boost stage loses regulation below the 500 V input window):
```
V_node = V_arc + I_S19 * R_931 = 40 + 18.4 * 6.312 = 156 V  (20 V arc: 136 V ; 60 V arc: 176 V)
S19 modules at (156 + 18.4*4.068)/30 = 7.7 V each -> I_S19 = 18.40 A (Isc)        [+6.3 %, direction UNCHANGED]
S20 array end  = V_arc + 18.4 * 0.0339 = 40.6 V ; S20 modules at 1.35 V each -> I_S20 = 18.40 A   [+6.3 %, unchanged]
S20 INVERTER END: +17.31 A -> -18.40 A  (SIGN CHANGE, 35.7 A swing); transient up to -(1073-40)/6.312 = -164 A
I_arc = 36.8 A, V_arc(S-O 1 mm) = 31.7 V, P_arc ~ 1165 W, 5.8 kJ / 5 s ; S20 only (after SW-STR-INV opens): 536 W, 2.7 kJ / 5 s
```
Why the inverter-end sign change is strong: S19's generated current enters the node and flows OUT along the S20 positive
conductor to the fault and back on the S20 negative conductor. At the S20 inverter-end sensor the current direction
reverses relative to generation. No benign operating condition reverses the current of an illuminated string at the
inverter end while the node is below ~500 V. The reversal is fast: the fault launches a -1.0 kV step along the line;
first current step at the inverter end (C_in reflects as a short, current doubles) = 2 * (1034..1144 - 40)/140 ohm =
14-16 A at t = 4.4 us, growing by the same amount each 8.8 us round trip toward the R-limited 164 A with L/R = 106 us
(DERIVED, lossless line, ideal short). Sign reversal between 4.4 us and ~13 us after inception.
Benign reverse-current exception: a dark or fully shaded string forward-biased by its paired string at Voc (V_DIRECTBUS
or during MPPT idle). Illustrative dark-string current at 1073 V node: 0.24 A; at 1488 V (cold Voc of the partner)
the illustrative exponential explodes (117 A, Rs neglected, REJECTED as a number; physically limited near one string's
Isc = 18.4 A by the partner). Discriminator: reverse current AND node voltage < 500 V (below the inverter input window)
= parallel fault; reverse current with node >= ~1000 V = shaded string (benign for detection; module reverse-current
rating is Track A/E's problem).

| Sensor location | observable at C2-far | magnitude |
|---|---|---|
| Module JB S20 | V_mod collapse, I to Isc | 38.13 V -> +0.7..2.0 V ; +6.3 % |
| Module JB S19 (paired) | V_mod collapse too | 38.13 V -> ~7.7 V ; +6.3 % — a module-local detector cannot tell "my string" from "paired string" by voltage |
| Array end S20 | voltage collapse | 1143.9 V -> 40.6 V ; current +6.3 % |
| Inverter end S20 | current REVERSAL, node collapse | +17.31 -> -18.4 A steady, -164 A transient ; node -> 156 V, tau = R*C_in = 0.95 ms (V_BOOST) / 12.6 ms (V_DIRECTBUS, 2 mF) |
| MPPT node | undervoltage, MPPT loses regulation | 1.03-1.07 kV -> 156 V |

Capacitor energy to the far arc (V_arc 40 V, constant): E_arc = V_arc * Q = 40 V * C_in * (1073-156) V = 5.5 J of 85 J
released (C_in 150 uF); 73 J of 1127 J (DC link 2 mF, V_DIRECTBUS). The 6.3 ohm home-run absorbs the rest. For C2-near
(5 m from the inverter, R = 34 mohm, L = 3.6 uH) the same Q gives the same V_arc*Q = 6 J (C_in) / 83 J (DC link) into the
arc but the peak current is set by ESR + arc, not cable (V/sqrt(L/C) = 7 kA, REJECTED as a number: upper bound only).
Shade/cloud: a module at +6.3 % (18.4 A) is BELOW cloud-enhancement current (1200 W/m2 -> 20.8 A ASSUMED linear): the
current MAGNITUDE at the faulted string is not a C2 discriminator; the direction reversal and the voltage collapse are.
Distinguish partial shade at module level: bypassed module sits at -1.35 V (3 x Vf) with string current; shorted
illuminated module sits at +0.7..2 V with its own Isc. A 2-3 V window: W05 must state the threshold and its tolerance.

### C3 — hot connector (0.05 / 0.2 / 1.0 ohm, no arc), M12(+)-M13(-), outside any bypass loop

```
dV_conn = 17.31 A * R   = 0.87 / 3.46 / 17.3 V       P_conn = 15.0 / 59.9 / 299.6 W
dT_ss   = P / 0.25 W/K  = 60 / 240 / 1199 K (fixture thermal ASSUMED; 1.0 ohm is not a steady state: connector fails first)
tau_th  = 8 J/K / 0.25 W/K = 32 s
string current change, node held: dI = -R*Impp/(r_s+R_loop) = -0.012 / -0.048 / -0.239 A = -0.07 / -0.28 / -1.38 %
cable thermal drift: 24.9 mohm/K ; 40 K diurnal (ASSUMED) -> 1.0 ohm ; 10 K -> 0.25 ohm
detectability ratio D = R_fault / dR_cable(40 K) = 0.05 / 0.20 / 1.0
rate ratio (fixture 600 s ramp vs 40 K over 4 h ASSUMED) = 0.083/0.069 = 1.2 ; 4.8 ; 24  — real degradation is over
weeks, so rate discrimination is NOT available in the field (fixture ramp is a convenience, not physics)
```
Other masks at string level: paired-string comparison S19 vs S20 is offset by the route difference alone
(109.9 - 70.4 = 39.5 V of cable drop -> ~0.6 A current difference at a common node), module mismatch 0.52 A (3 % ASSUMED),
Vmpp temperature drift -3.4 V/K. A module-local sensor (J-/J+) sees nothing: the connector is outside both modules'
terminals. A string-end two-ended measurement R_loop = (V_array_end - V_inverter_end)/I needs an array-end voltage
sensor plus comms plus a cable-temperature model (cable temperature UNKNOWN: buried / tray / sun).
VERDICT X-008: electrical detection of 0.05 ohm is NOT CREDIBLE (D = 0.05); 0.2 ohm is NOT credible without a cable
temperature measurement and a two-ended string voltage (D = 0.2); 1.0 ohm is marginally credible (D = 1.0, 17 V) and by
then the connector is at > 300 W. A thermal sensor AT the mated connector (or an IR survey) is required for C3; a JB
thermistor 0.3 m away is not the connector. No arc-only (HF) detector can claim C3.

## 2. Latency budget per sensor location and energy to the arc

Energy to the arc during a budget of duration t: E = P_arc * t. At 300 W / 1100 W:
```
t:   1 us      10 us     100 us    1 ms     10 ms    100 ms   0.5 s    2.0 s
300 W:  0.3 mJ   3 mJ     30 mJ     0.3 J    3 J      30 J     150 J    600 J
1100 W: 1.1 mJ   11 mJ    0.11 J    1.1 J    11 J     110 J    550 J    2200 J
```

| Budget item | Module JB (SW-M-OUT) | Array end (SW-STR-ARR) | Inverter end (SW-STR-INV) | MPPT node (inverter AFCI, P0) | scale |
|---|---|---|---|---|---|
| Wave arrival from fault | 0-0.34 us (72 m array run) | 0.02-0.34 us (C2-far 24 ns) | 4.4 us (C1/C2-far), 24 ns (C2-near) | 4.4 us | us |
| Sensor bandwidth (DC I/V: 10-100 kHz; HF CT/shunt: 1 MHz; ASSUMED generic) | 5-50 us | 5-50 us | 5-50 us | 5-50 us | us |
| ADC / comparator | 1-10 us (comparator 3 us typical for a low-power part, PR5 review) | same | same | same | us |
| Classification window, HF arc (several 1 ms spectral frames with persistence; 1-100 ms, published AFCI practice, general knowledge, no clause) | 1-100 ms | 1-100 ms | 1-100 ms | 100 ms - 2 s (fixture P0 variants 0.1/0.5/2.0 s) | ms |
| Classification, C2 reversal (sign + node < 500 V, persistence 100 us-1 ms) | n/a (no sign info at module) | n/a (no reversal at array end) | 0.1-1 ms | 0.1-1 ms | us-ms |
| Communication to actuator | string detector -> SW-M-OUT: wired bus 1-10 ms; DC-line PLC 0.1-2 s; wireless 10-100 ms (all ASSUMED) | local: 0 | local: 0 | inverter internal: < 1 ms | ms-s |
| Gate drive + device turn-off | 0.1-1 us | 0.1-1 us | 0.1-1 us | n/a (inverter stops drawing) | us |
| Loop-current commutation into clamp: t = L_loop*I/(V_clamp): 667 uH*17.31 A / 100 V = 115 us; /200 V = 58 us; /500 V = 23 us; E_L = 0.5*L*I^2 = 100 mJ | 23-115 us | 23-115 us | 23-115 us | n/a | us |
| TOTAL, local decision | 1-100 ms (HF) | 1-100 ms (HF); 0.1-1 ms (C2 voltage collapse) | 0.1-1 ms (C2 reversal); 1-100 ms (HF) | 0.1-2 s | |
| TOTAL, remote command of SW-M-OUT | + 1 ms to 2 s comms | | | | |

Reading: every microsecond-scale item (wave delay, gate, turn-off, commutation) delivers < 0.2 J to a 1.1 kW arc; the
classification window (3-110 J) and any communication path (up to 2.2 kJ for PLC) set the fault energy. A sub-microsecond
switch changes nothing at the arc until the ms-scale budget is fixed (input to X-003). The only sub-ms decision available
in this fixture is the C2 reversal/collapse at the inverter or array end. For C1 the minimum credible decision time is the
HF persistence window; for C3 the time scale is tau_th = 32 s or longer, and the "detection" is thermal, not electrical.

## 3. Benign set (SYNTHETIC) that W05 must implement — every trace labelled SYNTHETIC with these parameters

| ID | event | synthetic waveform and parameters (fixture value or ASSUMED range) | what it defeats if ignored |
|---|---|---|---|
| B1 | MPPT perturb step | node voltage step +-dV every 0.1 s (fixture); dV = 1-2 % of 1143.9 V = 11-23 V (ASSUMED); string current step dI = dV/72.4 ohm = 0.16-0.32 A with 1-10 ms exponential settling (ASSUMED) | DC-current-step criteria (C1 dI is 0.28-0.83 A) |
| B2 | Boost switching ripple | 16 kHz (8-40 kHz range, fixture) triangular string-current ripple 0.05-0.5 A pk-pk (ASSUMED), harmonics to 500 kHz with 1/f^2 envelope, plus edge ringing 1-10 MHz, 0.1-1 A, 0.1-1 us (ASSUMED); frequency drift across the 8-40 kHz range during a trace | fixed-band HF energy criteria; comb falls inside 40-100 kHz |
| B3 | Partial-shade step | one substring bypassed: string voltage -13.16 V, current -0.18 A (node held), edge 10 ms-1 s (ASSUMED shadow speed); one full module: -38.13-1.35 V; module terminal goes to -1.35 V | the DC twin of C1(b); module-level "voltage collapse" criteria |
| B4 | Cloud-edge ramp | G 1000 -> 200 -> 1000 W/m2 at 50-500 W/m2/s (ASSUMED); I 17.31 -> 3.5 A; include enhancement overshoot to 1200 W/m2 (20.8 A, 13 % above Isc_STC, ASSUMED linear) | overcurrent thresholds near Isc; C2 "+6 %" |
| B5 | Inverter start / stop | start: node Voc (1372.5 V STC / 1487.8 V cold) -> ~1.05 kV over 1-10 s, I 0 -> 17.31 A; stop: I -> 0 in 1-10 ms, node -> Voc (ASSUMED); repeat 3 times (anti-islanding retries) | voltage-step and dI/dt criteria; FAIL_OPEN false diagnosis |
| B6 | 8/20 us surge | differential-mode 50-500 A peak 8/20 us double exponential on the string loop (ASSUMED 1-10 % conversion of a 1-5 kA common-mode SPD-level event, UNKNOWN physically); sensor saturation/recovery 0.1-10 ms (ASSUMED) | single-event HF triggers; spurious "reversal" during sensor recovery |
| B7 | IV-curve scan | node swept 500 -> 1372 V and back over ~1 s (ASSUMED inverter feature); current 18.4 -> 0 A | module-voltage collapse to 16.7 V/module; reverse-current logic must stay quiet |
| B8 | Night / dawn / IMD | I = 0 with node at Voc; IMD test signal 0.1-10 Hz, 10-50 V to frame (ASSUMED) producing uA-mA common-mode ripple; dark-string reverse current 0.2-18.4 A with node >= 1000 V | reverse-current criterion without the node-voltage condition; leakage channel |
Required reporting: for each criterion, the count of (trips, near-misses entering SUSPECT) over the benign set with the
denominator (number of traces and total trace-seconds), per route length (78/200/300/600/936 m), per inverter variant.

## 4. Protection-state machine requirements

States: NORMAL, SUSPECT, TRIP_LATCHED, FAIL_OPEN_DIAG, FAIL_SHORT_DIAG, CONTROL_LOST.
- NORMAL -> SUSPECT: any criterion crosses its pre-trip level; start timer; freeze a pre-trigger waveform buffer (>= 10 ms
  before, >= 100 ms after; all channels; the triggering channel and its threshold stored with the record).
- SUSPECT -> NORMAL: criterion clears before confirmation; the event is logged as a near-miss and COUNTS in the benign
  denominator. SUSPECT -> TRIP_LATCHED: persistence over N windows (N stated per criterion) AND consistency across at
  least two observables (e.g. HF plus DC step; reversal plus node < 500 V). A single-observable trip is permitted only
  for the C2 reversal-plus-collapse pair.
- TRIP_LATCHED: open command; verify within t_verify = commutation time + margin (1 ms) that the controlled current falls
  below I_min = 0.5 A (fixture minimum sustaining current, ASSUMED). Not falling -> FAIL_SHORT_DIAG. Latched in
  non-volatile memory. No automatic rejoin after a suspected arc: re-close requires an authorised reset with the stored
  record reviewed, and is inhibited while the voltage across the open device indicates the fault is still present
  (C2: array-end voltage still collapsed; C1(a): see ADV-2958 restart-into-persistent-arc). A reset that re-ignites is a
  recorded design failure, not a retry.
- FAIL_OPEN_DIAG: I = 0 while irradiance is indicated (module/string near Voc in daylight) and no trip commanded; alarm;
  nothing to open; stays until service. FAIL_SHORT_DIAG: commanded open but current persists; escalate to the next
  hierarchy level (SW-STR-INV / inverter AFCI / manual DC disconnect) and alarm; the module's own protection is absent.
- CONTROL_LOST (gate supply or watchdog failure): the switch takes its PASSIVE state; it must be a defined state
  (no floating gate), and that state must be reported by a heartbeat loss at the next level. The two options and their
  consequences, both named, neither chosen by Track C alone:
  (i) default OPEN (enhancement device, no drive): safety-conservative for isolation, but one module electronics
      failure opens the whole string loop (1/24 of plant output); 720 module units with an ASSUMED lambda of 1e-6/h give
      one string outage per ~58 days (illustrative, not a prediction) and a field visit each; the open device must
      passively withstand the solved node voltage (X-001: up to 1332 V STC / 1448 V at -10 C under C2 with 29 modules
      at Voc, or 1488 V with node at 0 V) with no active clamp control.
  (ii) default CLOSED (bypass contactor / latching relay / normally-on stage): generation preserved, but protection is
      silently absent at that module (ADV-2946 module fault + lost supply), so a heartbeat-loss alarm with a service
      deadline is mandatory and the string-level device must assume the module cannot act.
  For the string-level device (P2/P2b) default OPEN costs one string, adds no hazard at the inverter side, and leaves the
  array-end conductors live at Voc; default CLOSED leaves the string unprotected except by P0.

## 5. ACCEPTANCE CHECKLIST for W05 and wave-2 detection outputs

1. Every trip decision shows the triggering observable waveform, the threshold, the persistence count and the sensor
   location, in a file with path and sha256; a decision without its waveform is not evidence.
2. Every detection criterion is stated as an inequality on a named fixture-unit quantity (A, V, V/s, A/s, W/Hz band
   energy) with a tolerance band; "detected" means the inequality held in the trace, nothing more.
3. False-alarm count on the benign set (B1-B8) reported with denominators: traces, trace-seconds, route lengths,
   inverter variant; near-misses (SUSPECT entries) reported separately. No rate is reported without its denominator.
4. No trip criterion depends on an HF signature unless the trace carries the SYNTHETIC label with its band, amplitude and
   the route transfer function used; the lossless-line nulls at odd multiples of v/(4*route) are either modelled or
   declared out of scope per route.
5. C1(b) (in-loop arc) is NOT claimed detected by any string-level or module-lead DC/HF criterion; if claimed, the
   division ratio r_d/|Z_loop| must be shown in the trace with the assumed r_d.
6. C2 criteria state the sign convention and use a bipolar current sensor model (no rectified or single-ended channel);
   the reversal criterion is paired with the node-voltage condition (< 500 V) and tested against B8 (dark string, node
   >= 1000 V) and B7 (IV scan).
7. C3 outputs separate thermal from electrical observables; no electrical criterion claims 0.05 ohm; any claim for
   0.2/1.0 ohm shows the cable-temperature compensation used and the detectability ratio D with the drift assumption.
8. Energy to the arc is integrated from fault inception to extinction or horizon and split by source (string modules,
   paired string, C_in, DC link, line L/C), with the detection-to-open latency budget shown as a separate column; the
   same integral is produced by two independent routes (W-wave-2 requirement) and agrees within a stated tolerance.
9. Latency is reported per budget item (section 2) with us/ms scale; no "whole-array response" time is reported
   without the sensor location, the fault location and the wave arrival time.
10. The state machine of section 4 is implemented as a deterministic function of the trace with unit tests for each
    transition, including FAIL_SHORT_DIAG (current persists after open) and CONTROL_LOST default-state reporting.
11. No automatic rejoin is present in any simulated protection sequence; a reset is an explicit input event recorded
    in the result file.
12. Arc extinction is never claimed from the S-O law without the word "illustrative"; a C1(b) arc that "cannot sustain"
    under the fixture law is reported as "no sustained arc under fixture law; minimum arc voltage UNKNOWN".
13. Each result file lists what is NOT modelled (module HF impedance, dielectric line loss, sensor saturation, EMI
    coupling, temperature of cable) in a `not_modelled` field.
14. Any number not in the fixture carries its label (ASSUMED/UNKNOWN) and is listed for assumptions.json; the
    illustrative single-diode fit is replaced by models/pv_module.py output before any trace is graded above algebra.

## 6. OBJECTIONS to other tracks

O-1 (Track A, orchestrator, Track E): C1 as located (inside the SS2 bypass loop, healthy D2) is bounded to
V_gap <= Voc_ss + Vf = 15.7 V and cannot sustain under the fixture's own arc law; where it can sustain (minimum arc
voltage 12-13 V, UNKNOWN/ASSUMED) its DC and HF signatures at string level are those of a shaded substring (-13.16 V,
-100 dB HF). The P0/P1/P2 comparison on C1 is therefore degenerate for detection AND the energy is capped at
~220-290 W by the substring. Request: promote ADV-2933/2934 (series arc in the string loop) to a priority waveform with
the full 20-60 V insertion, and treat the in-loop case as a thermal/per-substring (P1b) problem. Track E should block
any "C1 detected at string level" claim.

O-2 (Track B): under C2-far the FIRST SW-M-OUT to open in S20 sees 30*Voc - V_arc = 1332 V (STC) / 1448 V (-10 C)
because the other 29 modules go to Voc while the far end sits at V_arc; if all 30 open "simultaneously" the static
sharing is set by leakage mismatch, not by count. The module device voltage class under X-001 is therefore the string
class unless a solved sharing/clamp network is shown. Also: the loop commutation time L*I/V_clamp = 23-115 us
(667 uH, 100-500 V clamp, 0.1 J per operation) is the floor for "turn-off" at string-loop level, not the device's
nanoseconds; it exceeds the 4.4 us wave delay (X-003 input).

O-3 (Track A): the fixture's 6 mm2 home-run at 936 m dissipates 1.9 kW per string (9.6 % of string Pmpp, 110 V drop)
and drifts 25 mohm/K. A real design would use larger cable or shorter routes; R_loop, dR/dT and hence the C3
detectability ratio and the C2 cable-absorbed capacitor energy (79 of 85 J) all scale with it. Request the fixture
owner confirm or revise the 6 mm2 / 936 m pairing before C3 conclusions are promoted.

O-4 (Track D): the HF classification benchmark must be run per route length (78/200/300/600/936 m) because the
inverter-end transfer function from a far-end arc is comb-filtered (nulls near (2k+1)*v/(4*route)); a Vogel/Sobol
sweep over gap and irradiance only, at one route, cannot find the blind band. Add route length as an explicit axis
with the five fixture values as corners.

O-5 (Track E): the fixture's C3 thermal parameters (8 J/K, 0.25 W/K) give 1199 K steady rise at 1.0 ohm: the 1.0 ohm
variant is not a steady state and should be re-labelled as the pre-arc end point of the 600 s ramp; and the 600 s ramp
itself is a convenience that makes rate-based electrical discrimination look 1.2-24x better than a weeks-long field
degradation would. Any electrical C3 claim must be re-tested with a ramp >= 24 h.

## 7. Contradiction register inputs (for the orchestrator to append)
- X-008 (Track C, owner): hot-connector electrical detectability D = 0.05 / 0.20 / 1.0 for 0.05 / 0.2 / 1.0 ohm against
  40 K cable drift (24.9 mohm/K); 0.05 ohm NOT CREDIBLE electrically; thermal sensor at the connector required.
  Proposed status: RESOLVED_BY_ALGEBRA pending W05 trace confirmation; blocking experiment: C3 trace with cable
  temperature as a variable and a >= 24 h ramp.
- X-002 (Track C input): after SW-STR-INV opens on C2-far, S20's own modules keep feeding the arc at 18.4 A
  (536 W illustrative); only P2b/P3 or all S20 SW-M-OUT remove that source. Inverter-end detection is excellent,
  inverter-end action alone is insufficient.
- X-003 (Track C input): the arc energy is set by the ms-scale classification and comms budgets (3 J to 2.2 kJ), not by
  the us-scale switch budget (< 0.2 J). Sub-microsecond device claims are irrelevant to E_fault at this fixture.
- NEW X-009 (Track C raises, against the fixture/Track A): C1 in-loop location cannot sustain under the fixture arc law;
  minimum arc voltage UNKNOWN; see O-1.
