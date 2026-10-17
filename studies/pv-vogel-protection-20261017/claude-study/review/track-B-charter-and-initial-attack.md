# Track B (power electronics) — charter and initial attack, cycle 1
Supervisor SUP-B (Claude, model fable). Date 2026-10-17. Status: REVIEW POSITION, grade = algebra unless stated.
Fixture: claude-study/fixture/system-fixture.json (V11_CYCLE1_SHARED_FIXTURE_v1). All numbers below are DERIVED from it
by claude-study/review/track-B-initial-attack-calcs.py (sha256 3bce2722741267a40889ac49b450f4db33c64a784707add56065e942dcee2982,
run: `python3 -I review/track-B-initial-attack-calcs.py`, exit 0, self-checks OK) unless tagged ASSUMED or UNKNOWN.
Plain-text units: V, A, W, J, mOhm, uH, mH, us, K/W. Nothing here is a design approval or a part selection.

## 0. Track B charter
Scope (brief section 3 track B, section 7): for every candidate placement, derive the device REQUIREMENTS from the circuit nodes
(off-state voltage both directions, continuous current, interruption/clamp energy, gate reference, common mode, SOA, thermal),
then let W04 (archetype/datasheet register) and wave-2 (device-stress simulation) test named parts against them.
Standing rules I will enforce: (1) no voltage class assigned by assumption, only by the Track A node solution plus the bounding
cases in section 1; (2) no part without a verified datasheet URL; (3) the MOSFET is never the clamp; (4) the loss screen (0.5 %
STC) is a screen, the sealed-box thermal budget is the binding constraint; (5) the effective off-time is the clamp decay time.

## 1. Requirements by placement, derived from circuit nodes (not from parts)

### 1.0 Shared loop constants (936 m home run, fixture two-wire defaults; DERIVED)
  L_loop = (0.613 + 0.1) uH/m x 936 m = 0.667 mH   (external + dc internal)      C_line = 36.3 pF/m x 936 m = 34 nF
  R_loop = 2 x 936 m x 3.39 mOhm/m = 6.35 Ohm (20 C)   Z0 = 130 Ohm   T_one_way = 4.415 us
  Row loop (string snakes along a row, 1.0 m return separation, 6 mm2 radius 1.382 mm): L' = (mu0/pi) ln(1.0/0.001382) = 2.63 uH/m
    -> +103..190 uH for a 39..72 m row (row length ASSUMED from 30 modules in portrait/landscape; Track A to derive).
  Stored energy 0.5 L I^2 in the home run alone: 0.100 J at 17.31 A (Impp), 0.113 J at 18.4 A (Isc STC),
    0.118 J at 18.81 A (Isc at 70 C cell, using the fixture's ASSUMED +0.05 %/K). Whole-loop (home run + row): 0.115..0.129 J.
  Unclamped 1 us linear interruption of 17.31 A: V = L dI/dt = 0.667 mH x 17.31 A / 1 us = 11.6 kV (11.4 kV at 0.66 mH).
    Distributed-line view of an ideal open: first step I x Z0 = 17.31 A x 130 Ohm = 2.25 kV, repeating every 8.8 us round trip.
    Either view exceeds every candidate device class -> a clamp (external) is mandatory at every series interrupter in this loop.
  Interruption loop by placement and case (the current that is interrupted and the inductance it flows in):
    SW-M-OUT, any series case (C1/C3)        : whole loop, 0.77..0.86 mH (home run + row)       I = 17.31..18.81 A
    SW-STR-INV, series case (C1/C3)           : whole loop, 0.77..0.86 mH                        I = 17.31..18.81 A
    SW-STR-ARR, series case (C1/C3)           : whole loop, 0.77..0.86 mH                        I = 17.31..18.81 A
    SW-STR-INV, C2-near (arc 5 m from inv.)   : C_in + 5 m stub + arc, 3.7 uH (ASSUMED stub)     I = I_paired + C_in discharge (kA prospective)
    SW-STR-INV, C2-far  (arc 5 m from array)  : C_in + 931 m + arc, 0.664 mH                     I = I_paired + line-limited C_in current
    SW-STR-ARR, C2-far                        : modules + row + 5 m + arc, 0.10..0.19 mH         I = 17.31..18.81 A (string's own)
    SW-STR-ARR, C2-near                       : modules + row + 931 m + arc, 0.76..0.85 mH       I = 17.31..18.81 A (string's own)
    SW-SS, C1                                 : substring ribbon loop, 1..5 uH (ASSUMED)         I = 17.31..18.81 A
  In every C2 variant the switch interrupts only ONE of the two feeds (see objection A3): the other keeps feeding the arc.

### 1.1 Clamp trade (applies to every series interrupter in the whole loop; DERIVED, algebra)
  Model: switch opens, loop current commutates into a clamp at Vc; the loop EMF opposing the clamp is Vs = V_string_EMF - V_node.
    t_decay = L I / (Vc - Vs)        E_clamp = 0.5 L I^2 x Vc / (Vc - Vs)        (Vc > Vs required, else the clamp conducts forever)
  Vs rises along the PV IV curve from ~0 V (at the instant of opening, string at Vmpp_s = node) to Voc_s - V_node at zero current;
  using the end value is conservative. L = 0.667 mH, I = 17.31 A (home run only; add 15..28 % for the row):
    Vs = 228.6 V (STC, node held at Vmpp_s 1143.9 V by the paired string):  Vc 400 V: 67 us, 0.233 J | 600 V: 31 us, 0.162 J | 1000 V: 15 us, 0.130 J | 1600 V: 8.4 us, 0.117 J
    Vs = 343.9 V (cold -10 C, same node):                                   Vc 400 V: 206 us, 0.713 J | 600 V: 45 us, 0.234 J | 1000 V: 18 us, 0.152 J | 1600 V: 9.2 us, 0.127 J
    Vs = 987.8 V (cold, node at window minimum 500 V):                      Vc 1000 V: 946 us, 8.19 J | 1600 V: 19 us, 0.261 J | 1700 V: 16 us, 0.239 J
    Vs = 1457.8 V (cold, node collapsed to a 30 V arc, V_ARC ASSUMED):      Vc 1600 V: 81 us, 1.13 J | 1700 V: 48 us, 0.70 J | 2500 V: 11 us, 0.24 J
  Reading: the clamp energy is ~0.12..0.26 J whenever Vc exceeds Vs by a few hundred volts, and blows up as Vc -> Vs.
  A clamp BELOW Voc_s - V_node is not a clamp: the string is a current source at any voltage below Voc_s, so a 100..150 V clamp with
  the node at Vmpp_s carries 12.8..15.8 A continuously (illustrative single-diode IV) = 1.6..1.9 kW until it fails.
  RCD/capacitive alternative: C_snub absorbs 0.5 L I^2 with overshoot dV = I sqrt(L/C): 10 uF -> 141 V, 40 uF -> 71 V at 17.31 A;
  but a 1458 V-rated 10 uF capacitor stores 10.6 J and is a large part (iteration-3 review 4: a 2.2 uF 1600 V MKP is ~35x50x57 mm).
  Position: MOV/TVS clamp sized by E_clamp above, external to the MOSFET; MOSFET avalanche is NOT an acceptable energy sink (section 2).

### 1.2 SW-M-OUT: anti-series pair in the module positive lead, OUTSIDE the bypass-diode chain (P1)
  Node picture: with SW-M-OUT(k) open, the 30 modules (all still illuminated, I = 0) sit in series with the open switch between the
  two home-run conductors, which the MPPT node ties together through C_in and the paired string. Hence
    V_switch(forward, generation direction) = V_string_EMF(I=0) - V_node = Voc_s - V_node.
  Bounding cases (STC Voc_s 1372.5 V / cold Voc_s 1487.79 V; DERIVED; the node value is Track A's X-001 deliverable):
    a) node held by the paired string at Vmpp_s 1143.9 V (inverter running)    : 228.6 V STC / 343.9 V cold  (cold node also rises; conservative)
    b) node at the MPPT window minimum 500 V                                   : 872.5 V / 987.8 V
    c) parallel fault anywhere on the string loop (C2-near/far, bolted or arc) : 1342.5 V / 1457.8 V (arc 30 V ASSUMED) up to 1372.5 / 1487.8 V (bolted)
    d) node at ~0 V: paired string dark or snow-covered while this string is lit, V_DIRECTBUS bus discharged/precharging
       (tau = 6.35 Ohm x 2 mF = 12.7 ms), inverter input crowbarred (UNKNOWN whether this inverter does)   : 1372.5 V / 1487.8 V
    e) dawn, "last switch to close": with 29 module switches closed and one still open, NO current flows, C_in stays where it was;
       if the node is low (case d) the last switch sees the full Voc_s before it closes. Daily event, not a fault.
  => The forward class is NOT the module Voc (49.6 V). Even the benign case (a) puts 229 V (STC) / up to 344 V (cold, conservative)
     on it -> a 300..450 V class after 80 % derating (ASSUMED practice): the 60..200 V silicon classes are excluded by case (a) alone.
     Cases (c)/(d)/(e) put 1343..1488 V on it. Only an ARCHITECTURAL exclusion of (c)-(e) (never open under them, or fold-back
     re-close at Vds > V_limit, section 1.6) permits a device below 1500 V class. Track B does not accept that exclusion by
     assumption; Track A must prove or deny each case.
  Reverse (night, string dark, node charged): a dark string drops ~0 V at zero current, so the reverse-blocking device sees the whole
  node: 1143.9 V (V_BOOST, C_in at the last MPP; decay UNKNOWN) .. 1500 V (V_DIRECTBUS). With a unidirectional module switch the
  body diode conducts the backfeed; the backfeed current is set by the 30 dark modules' forward IV at V_node/30 (Track A's n = 1.2
  cross-check fit, 25 C cells, ASSUMED): 0.42 A at 1143.9 V (0.4 W heater per switch), 4.5 A at 1300 V, 32.7 A at 1500 V (49 kW
  into the dark string: a module-destroying case in V_DIRECTBUS if anything holds the bus at 1500 V at night — UNKNOWN).
  Reverse blocking is a STRING-level function (one 1500 V-class element per string, section 1.4) rather than 30 module-level ones.
  Track B preference: single-direction blocking at module level ("P1-uni", halves Rds), IF Track A finds no module-level reverse
  requirement in V_BOOST. Fixture P1 is anti-series; both to be compared.
  Body-diode state table (common-source pair, D1-Q1-S-Q2-D2, module + at D1):
    Q1 OFF, Q2 ON : generation blocked; reverse flows via Q2 channel + Q1 body diode (Vsd).
    Q1 ON,  Q2 OFF: generation CONTINUES via Q1 channel + Q2 body diode = continuous heater 17.3 W (Si, Vsd 1.0 V ASSUMED) or
                    60..92 W (SiC, Vsd 3.5..5 V ASSUMED) at 17.31..18.4 A, not interruptible by Q1 (ADV-body-diode-feed-one-switch-off).
                    This is what a single lost gate drive on Q2 looks like: the string keeps running, the J-box cooks.
    both OFF      : both directions blocked (control_supply_lost -> string open -> ADV-switch-failed-open-nuisance; fail-safe for
                    isolation, fail-open for yield).
    Q1 failed short: generation can never be blocked again -> module reverts to baseline, silently unless Vds is monitored.
  Continuous current: 17.31 A (Impp STC) .. 18.4 A (Isc STC) .. 18.81 A (Isc, 70 C cell); design to 18.81 A continuous.
  Interruption: whole loop, 0.77..0.86 mH, 0.115..0.129 J; clamp per 1.1 across the module switch (local), Vc > Voc_s,cold - V_node.
  Gate reference: common source floats at the module's own potential; driver supply from the module (38..49.6 V) via a local
  regulator; no isolation inside the module; everything floats with the module relative to frame (section 1.7).
  Conduction budget (section 1.8): 11.01 mOhm (0.5 %) / 22.03 mOhm (1 %) for the ENTIRE added path (pair + shunt + PCB + joints).
  Thermal: a sealed J-box at Ta 70 C with Rth_ja 30 K/W (ASSUMED) allows 6.1 mOhm per device hot (section 2), ie a 12.2 mOhm pair.
  Verdict (Track B prior, to be tested): a pair meeting 12 mOhm hot exists only in the 60..200 V silicon classes; those classes die
  under cases (c)-(e). A 1500 V-class pair (2 x 1700 V SiC, ~126 mOhm hot, ASSUMED market figure) dissipates 37.8 W = 5.7 % of the
  module, and runs away thermally at Rth_ja >= 15 K/W (section 2). P1 as defined in the fixture therefore fails EITHER the voltage
  requirement OR the loss/thermal screen; it cannot pass both. Unless Track A removes cases (c)-(e), Track B will mark P1 REJECT.

### 1.3 SW-SS: one low-voltage switch per substring, INSIDE its own bypass loop (P1b)
  Node picture: S2 (22 cells) in series with SW-SS2, D2 anti-parallel across both. Open SW-SS2: string current commutates into D2
  (node at -Vf); the open switch sees V_S2(I=0) + Vf = Voc_ss + Vf = 49.593/3 + 0.45 = 16.98 V cold (15.70 V STC). That is the ONLY
  off-state case while D2 is intact, because D2 is the alternate path and sits inside the module. The 30-module string EMF never
  appears across SW-SS. Reverse: night backfeed enters the cells in their forward-diode direction and passes SW-SS through its body
  diode (if OFF, unpowered at night): ~0.7..1 V x backfeed current (V_DIRECTBUS only; 98 J transient in V_BOOST). No reverse
  blocking needed -> UNIDIRECTIONAL single device is correct here.
  Failure: D2 failed OPEN (ADV-open-bypass-diode) and SW-SS2 opened -> the switch now stands between the string EMF and the node
  like SW-M-OUT: 1343..1488 V -> a 60..100 V device avalanches at 17.31..18.4 A (~1.4 kW) and fails short within ms, reverting to
  baseline (arc continues) after a 1..10 J event in the J-box. Mitigation: monitor Vds after opening; if Vds > ~25 V the diode is
  open -> re-close immediately and alarm (safe here because the alternative is device destruction; the arc is baseline either way).
  Interruption: substring ribbon loop L_ss 1..5 uH (ASSUMED, wave-2 to derive from ribbon geometry): L dI/dt = 17..87 V at 1 us,
  3..17 V at 5 us; stored 0.15..0.75 mJ -> a 30..40 V TVS or the device's own E_AS (typically tens of mJ, W04 to verify) absorbs it;
  gate ramp >= 5 us removes the problem entirely.
  Continuous: 17.31..18.81 A through the switch when ON; when OFF the bypass diode carries it: 0.45 V x 17.31 A = 7.8 W continuous
  (3 diodes 23.4 W if all three substrings open) in a sealed box designed for intermittent shade duty -> thermal case for wave-2
  and Track E; an active (synchronous) bypass MOSFET across the diode (0.6 W at 2 mOhm) is the mitigation to evaluate.
  Loss: 3 switches x 17.31^2 x ~2 mOhm hot (60..100 V Si, ASSUMED) = 1.8 W per module = 0.27 % (budget 11.01 mOhm total -> 3.67
  mOhm per switch incl. shunt). Device count 2160 switches + 2160 drivers for the plant.
  Zone: ONLY faults inside the substring loop (C1). It does nothing for a tap/J-box/connector arc, C3 or C2.
  Construction: inserting a series element in one substring requires that substring's end ribbon and the next substring's start
  ribbon to be separate (split taps / split three-box J-box); fixture lists J-, J+, N1, N2 only -> UNKNOWN; W04 to check the
  datasheet/J-box drawing before P1b is costed.
  Verdict: the only module-level placement whose stand-off (17 V) is independent of the string; passes the loss and thermal
  screens by a wide margin; narrow zone. Track B keeps P1b.

### 1.4 SW-STR-INV: 1500 V-class SiC breaker at the inverter end of the home run (P2)
  Off-state forward: string side at Voc_s (1372.5 / 1487.8 V), node side at V_node (0..1500 V): up to 1487.8 V (node at 0).
  Off-state reverse: node charged, string dark: -1143.9 V (V_BOOST) .. -1500 V (V_DIRECTBUS). Reverse blocking IS a string-level
  function (replaces the absent string fuse/blocking diode for night backfeed) -> bidirectional: anti-series 1700 V pair, or one
  1700 V MOSFET + series 1700 V SiC Schottky (Vf ~1.5 V -> 26 W, ASSUMED) -> compare in W04's register.
  Common mode to the inverter chassis/earth: +Vmpp_s/2 = +572 V nominal (floating IT, symmetric leakage ASSUMED), up to +1488 V
  under a first earth fault on the negative pole. Isolated gate driver and isolated sensing, 1500 V working class.
  Continuous: 17.31..18.81 A. Loss budget 330.4 mOhm (0.5 %) / 660.8 mOhm (1 %) of the string's 19.8 kW; a 126 mOhm hot pair = 37.8 W
  = 0.19 %. Easy; use the margin for a reactor and a second (redundant/galvanic) stage.
  Interruption, series cases: whole loop 0.77..0.86 mH, 0.115..0.129 J; clamp Vc ~1600..1700 V, E_clamp 0.12..0.26 J, 8..19 us.
  Interruption, C2-near (the case that sizes this device): C_in (150 uF, 98 J at 1143.9 V) discharges through 5 m of cable
  (3.7 uH ASSUMED) into the arc: dI/dt = 312 A/us, undamped peak 7.3 kA at 37 us (zeta 0.11); V_DIRECTBUS C_dc (2 mF, 1309 J):
  26.7 kA peak. No MOSFET interrupts that. Hence a series reactor + fast local trip (dI/dt or desaturation) is part of the device:
    reactor 20 uH (ASSUMED):  trip at 1 / 5 / 10 us -> let-through 66 / 259 / 501 A; E_L 0.05 / 0.79 / 2.97 J; E_clamp (1600 V) 0.18 / 2.78 / 10.4 J
    reactor 100 uH (ASSUMED): trip at 1 / 5 / 10 us -> let-through 28 / 72 / 128 A;  E_L 0.04 / 0.27 / 0.85 J; E_clamp 0.15 / 0.96 / 2.96 J
  SOA: the short-circuit withstand time t_SC of the chosen SiC device at 1143.9..1500 V must exceed the trip delay (W04 to record).
  What it does NOT do: it removes the node sources (paired string, capacitors) from a C2 arc but the faulted string's own
  17.31..18.81 A keeps flowing through 931 m into the arc (C2-near) or 5 m (C2-far). X-002: SW-STR-INV alone does not clear C2.

### 1.5 SW-STR-ARR: disconnect at the array end of the home run (P2b)
  Off-state: identical bounds to 1.4 (+1487.8 V forward with node at 0; -1143.9..-1500 V reverse). Common mode: the string + end
  at up to +1488 V vs frame (first earth fault); + and - string ends are both at this box (snake return) so the string voltage is
  available locally for an auxiliary supply (500..1488 V input, 0 V at night -> normally-OFF device sits open until dawn; at dawn
  the supply must boot from the ARRAY side of the open switch, else it never closes).
  Interruption, series cases: whole loop 0.77..0.86 mH (the home run is in the loop regardless of where the loop is cut).
  C2-far: interrupts the string's own current in the row loop + 5 m (0.10..0.19 mH, 17..32 mJ at 18.4 A); Vs = 1343..1458 V (node
  collapsed) -> Vc 1600 V: 14..25 us, 0.19..0.36 J. But the paired string (17.31..18.81 A) + C_in continue to feed the arc through
  the 936 m home run via the MPPT node. SW-STR-ARR alone does not clear C2 either. Only both ends open (P3) leave the home-run arc
  with just the line's own 34 nF x 1143.9 V = 22 mJ (plus whatever the inverter/paired string do), illustrative.
  No local capacitor -> no kA duty; simpler SOA than SW-STR-INV; harsher environment; control power at night = none.

### 1.6 Variants Track B asks the orchestrator to add to the ledger (new keys; do not alter P1/P1b definitions)
  P1-IN : series switch INSIDE the module's D1-D2-D3 chain (between the cell string and the J+ node). Stand-off = Voc_m + 3 Vf =
          49.6 + 1.35 = 51 V cold; one 80..100 V device, ~2.5 mOhm hot -> 0.75 W = 0.11 %; string current continues through the
          three diodes = 23.4 W continuous (too hot: see P1-BYP). Zone: inside the module only (an external connector in series
          with the module still carries 17.31 A through the bypass path -> does NOT interrupt C3).
  P1-BYP: P1-IN plus a synchronous bypass MOSFET across the module (0.6 W at 2 mOhm) instead of the diodes carrying 23.4 W. Two
          80..100 V devices per module; the module "shades itself out". Stand-off 51 V. Same zone limit as P1-IN.
  P1-FB : fixture P1 with a 400..650 V pair (case (a) needs 229..344 V) and fold-back re-close when Vds > ~400 V. Holds open only
          while the node holds (case (a)); under cases (c)-(e) it re-closes (reverts to baseline), and its 60..80 us clamp interval
          then re-energises the fault -> likely re-ignition. Track B does NOT recommend it; listed so Track C/E can reject it with
          reasons rather than silence. Loss: 2 x ~30 mOhm hot (ASSUMED) = 18 W = 2.7 %, so it also fails the loss/thermal screens.
  P1-uni: fixture P1 with one blocking direction only (reverse via body diode). Same voltage problem as P1 for cases (c)-(e).
  The architectural rule these expose: a series element INSIDE a bypass loop sees only that loop's Voc but protects only that
  loop; a series element OUTSIDE every bypass loop protects the whole string loop but must stand the whole string loop.

### 1.7 Common-mode insulation to frame (all placements)
  Floating IT array, symmetric leakage (ASSUMED): module k of 30 sits at (k/30 - 1/2) x Vmpp_s = -572..+572 V vs frame at MPP,
  -744..+744 V at cold Voc. First earth fault on one pole shifts the whole string: 0..+1487.8 V (fault on -) or 0..-1487.8 V (fault
  on +). Module-level electronics therefore need the module's own 1500 V-system insulation to frame (module safety class per
  IEC 61730: NOT EXAMINED); any wired communication off the module needs 1500 V-class isolation; string-end and inverter-end units
  need 1500 V-class isolated gate drive and sensing. Impulse levels: NOT EXAMINED (licensed text unavailable).

### 1.8 Conduction-loss budgets (0.5 % and 1 % of STC nameplate at Impp 17.31 A; DERIVED)
  Unit            devices   0.5 % budget    1 % budget     note
  1 module        720       11.01 mOhm      22.03 mOhm     whole added path: pair + shunt + PCB + joints + driver self-consumption/I^2
  2 modules       360       22.03 mOhm      44.05 mOhm
  4 modules       192       41.30 mOhm      82.60 mOhm     includes the partial (2-module) group per string
  string          24        330.4 mOhm      660.8 mOhm     0.5 % of 19.8 kW = 99 W per string
  Illustrative hot anti-series pair by class (ASSUMED market ranges, W04 to replace with datasheet values at 125 C / 175 C):
    60..100 V Si 5 mOhm -> 1.5 W = 0.23 %   | 150 V Si 10 mOhm -> 3.0 W = 0.45 %   | 200 V Si 20 mOhm -> 6.0 W = 0.91 %
    650 V SiC 2x27 mOhm typ x1.4 = 76 mOhm -> 22.8 W = 3.45 % (16.4 kW plant) | 1200 V SiC 40 mOhm -> 12.0 W = 1.82 %
    1700 V SiC 2x45x1.4 = 126 mOhm -> 37.8 W = 5.72 % as a module unit (27.2 kW plant), 0.19 % as a string unit.
  Self-consumption: 50..200 mW per module unit (ASSUMED) = 36..144 W plant = 0.008..0.03 % — count it.
  The 936 m home run itself drops 17.31 A x 6.35 Ohm = 110 V and 1.9 kW = 9.6 % of that string's Pmpp (20 C copper): any
  device loss claim must be stated against the string's actual delivered power, not only nameplate.

## 2. Junction-temperature screening method (wave-2 MUST use; grade algebra; screens are ASSUMED engineering limits)
  Steady state, per device, per operating point I in {17.31, 18.4, 18.81} A:
    P_cond(Tj) = I^2 x Rds25 x (1 + alpha x (Tj - 25))        alpha from the datasheet Rds(Tj) curve fitted between 25 C and
                                                              125 C AND checked at 150/175 C (SiC curves are non-linear: use the curve)
    Tj = Ta_box + Rth_ja x (P_cond(Tj) + P_local_aux)         iterate, or closed form for linear alpha:
    Tj = (Ta + Rth I^2 Rds25 (1 - 25 alpha)) / (1 - g),   g = Rth x I^2 x Rds25 x alpha  (report g; g >= 1 is thermal runaway)
  Rth_ja ASSUMED range for a sealed junction box (to be replaced by a measured value, first lab item): 15 K/W (device clipped or
    potted to a baseplate against the backsheet, like bypass diodes) / 30 K/W (D2PAK-class on 2 oz copper pour in a potted box) /
    60 K/W (free-standing TO-247 in still air; iteration-3 review cites ~62 K/W). Each device its own path unless co-mounted; if
    co-mounted use a coupled two-source model. String-level units: assume a heatsink, Rth_ja 2..5 K/W (ASSUMED), state it.
  Ta_box ASSUMED 70 C nominal (cell ~65..70 C at 1000 W/m2, 35 C ambient), 85 C worst; range 55..85 C.
  Screen: Tj_steady <= 125 C (ASSUMED Track B field-life screen, not a qualification limit). Equivalent hot-resistance budget:
    Rds_hot <= (125 - Ta) / (Rth_ja x I^2)  -> at Ta 70 C, I 17.31 A: 12.2 mOhm (15 K/W), 6.1 mOhm (30 K/W), 3.1 mOhm (60 K/W) per device.
  Worked rows (Ta 70 C, Impp): 100 V Si 2.5 mOhm a 0.6 %/K: Tj 85 / 103 / 148 C at 15 / 30 / 60 K/W (fails only at 60);
    650 V SJ 22 mOhm a 0.85 %/K: 927 C at 15 K/W (g 0.84), runaway at 30 K/W (g 1.68); 650 V SiC 27 mOhm a 0.4 %/K: 348 C at
    15 K/W; 1700 V SiC 45 mOhm: 1320 C at 15 K/W, ok only with a heatsink (106 C at 2 K/W). The thermal screen, not the 0.5 % screen,
    is what excludes every >= 650 V class from a sealed module box.
  Pulse (interruption event), per device: E_dev = switching energy only = I x Vc x t_fall (17.31 A x 1600 V x 100 ns = 2.8 mJ) when an
    external clamp carries E_clamp; E_dev = E_clamp if the device avalanches (NOT acceptable, shown why):
    dTj = P_avg x Zth_jc(t_pulse) with P_avg = E_dev / t_pulse, Zth from the datasheet single-pulse curve; if no Zth at that t, use
    the semi-infinite-solid bound dTj = 2 E / (A sqrt(pi rho cp k t)) with A = active die area (datasheet or ASSUMED 10..25 mm2),
    Si: rho 2330 kg/m3, cp 700 J/kg/K, k 120 W/m/K; SiC: 3210, 690, 300; multiply by 2 for avalanche current crowding (ASSUMED).
    Examples: E 0.162 J in 31 us, 10 mm2: Si +235 K, SiC +127 K; E 0.702 J in 48 us: Si +817 K, SiC +444 K (x2 for crowding).
    Tj_peak = Tj_steady + dTj <= 175 C screen (ASSUMED). Repetitive events (nuisance trips, re-close attempts): report count-to-fail
    as UNKNOWN unless a repetitive avalanche/pulse rating is in the datasheet.
  Output fields per device per scenario: I_a, Rds_hot_mohm, P_cond_w, g, Ta_c, Rth_ja_k_per_w(label), Tj_steady_c, E_dev_j, E_clamp_j
    (separately), t_pulse_s, method(Zth|adiabatic), A_die_mm2(label), dTj_k, Tj_peak_c, pass/fail per screen, file id + sha256.

## 3. Positions on X-003, X-004, X-005
  X-003 (sub-us off-time): REJECT as a whole-circuit claim; ACCEPT only as local self-protection at SW-STR-INV.
    (i) Remote faults: information reaches the inverter end after 4.415 us (936 m), and a far-end parallel fault shows up there as
        current steps of (1143.9 - 30) / 130 = 8.6 A every 8.8 us round trip, with the DC limit ~180 A reached only after ~5 L/R =
        0.5 ms; a HF-band arc classifier needs >= ms. (ii) Energy: a 30 V arc at 17.31 A is 519 W; 1 us vs 10 us of off-time is 4.7 mJ,
        versus >= 0.100 J that the interruption itself must dump into a clamp and 0.52 J per millisecond of detection latency.
    (iii) The effective off-time is the clamp decay: 8..80 us (section 1.1) however fast the gate; a 1 us gate ramp merely reaches
        the clamp voltage sooner (unclamped would be 11.6 kV lumped / 2.25 kV first line step). (iv) Where speed is real: C2-near at
        SW-STR-INV, 312 A/us from C_in (7.3 kA prospective; 26.7 kA in V_DIRECTBUS) -> a reactor plus a trip in <= 1..5 us is needed
        for the breaker's own survival, with E_clamp 0.15..2.8 J. Any sub-us claim must show the sensor that sees the fault at t < 1 us,
        the reactor, and the clamp energy; otherwise it is marketing.
  X-004 (650 V reuse): REJECT for every placement in this fixture. The web search returned distributor listings for IMZA65R027M1H
    as "650 V, 59 A, 4-pin TO-247 CoolSiC" (RS Online, accessed 2026-10-17; the manufacturer page fetch was blocked). At 80 % derating
    (ASSUMED practice) a 650 V device may see <= 520 V: SW-M-OUT exceeds that in cases (b)-(e) of 1.2 (873..1488 V) and in reverse at
    night (1144..1500 V); SW-STR-INV/ARR exceed it in both directions; SW-SS needs 17 V and would waste 27 mOhm where 1..3 mOhm is
    available. At 2 x 27 mOhm x 1.4 hot it costs 22.8 W per module = 3.45 % and runs to 348 C at 15 K/W. Wrong class in both directions.
  X-005 (0.1 Ohm shunt): REJECT (carried), numbers: 29.96 W at 17.31 A, 33.9 W at 18.4 A, 21.6 kW plant, 908 % of the 11.01 mOhm budget.
    DC channel: <= 1 mOhm four-terminal shunt (0.30 W, 17.3 mV full scale, 9 % of budget, needs a chopper/zero-drift front end and a
    2 nH parasitic gives an 80 kHz zero) or a magnetic (Hall/fluxgate) sensor (no series loss, 10..30 mA self-consumption ASSUMED,
    offset drift too large for leakage but fine for 17 A). HF arc channel: a separate HF current transformer or capacitive pick-off,
    not the DC shunt. Two channels, two front ends, documented separately (brief section 7).

## 4. Acceptance checklist for W04 (register) and wave-2 (device stress)
  1. Every named part: manufacturer datasheet URL (not a distributor page alone), access date, revision, lifecycle status (NRND flag).
  2. Per part: V_DS class, Rds at 25 C AND at 125 C AND 150/175 C (or the curve), I_D continuous at a stated case temperature,
     I_D pulsed, E_AS / avalanche conditions (L, I, Tj_start), t_SC short-circuit withstand (SiC), body-diode Vsd at I, Qrr, Coss,
     Rth_jc, Zth_jc single-pulse curve, package, orderability (one distributor stock line with date).
  3. Placement-to-class matrix: each part assigned ONLY to placements whose node-derived stand-off (section 1, both directions) is
     <= 80 % of V_DS (derating ASSUMED; state it). No 650 V part carries a >= 520 V duty; no part below 1500 V class carries a
     SW-STR-INV / SW-STR-ARR duty; no SW-M-OUT part is justified by "module Voc" without the Track A node table attached.
  4. Direction table per placement: forward/reverse blocked by which device; body-diode path and its Vsd x I heater power when one
     device is OFF or failed short; both-OFF state; gate-supply-lost state; fail-short detectability (what signal reveals it).
  5. Interruption loop declared per scenario (section 1.0 table or Track A's replacement): L (H), I0 (A), Vs (V), Vc (V); computed
     t_decay and E_clamp; clamp part named with its rated single-pulse energy at that pulse width and its repetitive rating or UNKNOWN.
  6. Vds waveform exported (decimated CSV + sha256) showing the clamp plateau; the integral of v_clamp x i_clamp equals E_clamp
     within 5 %; MOSFET avalanche energy = 0 in every accepted case (or the case is marked REJECTED with the dTj from section 2).
  7. Energy balance per case: sources - (fault + semiconductor + clamp + conduction + stored) residual < 1 % of the largest term.
  8. Steady Tj per device per operating point with g, Ta_box and Rth_ja labelled ASSUMED with the range; no device above 125 C screen
     unless the entry is marked FAIL; Tj_peak after the pulse with the method stated.
  9. Total added-path resistance per unit (switches + shunt + PCB + connector) against 11.01 / 22.03 / 41.30 / 330.4 mOhm; include
     self-consumption as equivalent resistance P_aux / I^2.
 10. SW-STR-INV: reactor value, dI/dt trip threshold and delay, let-through current, and t_SC margin for C2-near in BOTH inverter
     variants; prospective current without the reactor stated (7.3 / 26.7 kA) so the reader sees why it exists.
 11. SW-SS: ribbon-loop L derivation, bypass-diode continuous power (7.8 W) and its Tj at the assumed J-box Rth, the D-open
     re-close logic, and whether the module's taps are physically separable (datasheet/J-box drawing cited or UNKNOWN).
 12. Common-mode: for each unit, the potential to frame in normal, first-earth-fault(+) and first-earth-fault(-) states, and the
     isolation element that spans it (part, working voltage, UNKNOWN impulse).
 13. Night/dawn states: switch state with no control power; the "last switch to close" voltage; the backfeed path and power.
 14. Reverse-polarity and failed-short MOSFET cases from the ADV list have an entry each (even if "no effect, reason: ...").
 15. Every result row: scenario_id from the ledger, producing script path + sha256, label, grade; "NOT modelled" list present.
 16. No vendor SPICE model files; behavioural models only (switch with Rds(Tj), body diode Vsd, clamp = source + diode), marked
     illustrative_simulation; no standards clause cited unless the licensed text was examined (else NOT EXAMINED).

## 5. Objections to other tracks (for the contradiction register)
  A1 (Track A, X-001): the post-trip node table must include, not only daytime MPP with the paired string lit, but: paired string
     dark/snow-covered with this string lit; V_DIRECTBUS precharge (tau 12.7 ms); inverter input crowbar (UNKNOWN); the dawn
     last-switch-to-close state; and the dark-string reverse case where a 30-module string drops ~0 V at zero current so the whole
     node (1144..1500 V) lands on one open switch. Omitting any of these understates the SW-M-OUT class by up to 1259 V.
  A2 (Track A, M3): one loop inductance is not enough. Provide L per interruption loop per scenario (section 1.0 table), including
     the row loop (2.63 uH/m at 1.0 m return separation -> 103..190 uH, ASSUMED row length) and the 5 m stubs; the home run alone
     under-predicts the clamp energy by 15..28 % for series cases and is simply the wrong loop for C2 variants.
  A3 (Track A/C, X-002): no single switch clears C2. SW-STR-INV leaves the faulted string's own 17.31..18.81 A (through 931 m or
     5 m); SW-STR-ARR leaves the paired string's 17.31..18.81 A plus C_in through the node and 936 m. Only P3 (both ends) or an
     inverter-side action on the MPPT pair removes the DC sources; the residual is then the line's 22 mJ. Please confirm or refute
     with the source graph before any P2/P2b row is credited with C2 containment.
  A4 (Track A, M1): enumerate the two parallel half-cell branches per substring as their own loop. After SW-M-OUT or SW-SS opens,
     a C1 arc sitting in ONE branch still has the sibling branch as a source: loop EMF <= Voc_ss (16.5 V cold) and circulating
     current ~0.9 A at 20 % shade mismatch (illustrative, equal-branch IV). The fixture arc law gives ~25 V at 5 A, 1 mm, above
     that EMF, so the arc should not persist — but that rests on the ASSUMED 15 V ignition / 0.5 A sustaining values; flag it and
     report the branch-loop energy separately. Opening the series switch does not make the branch loop inert.
  C1 (Track C): write the latency budget as t_detect + t_decide + t_gate + t_clamp_decay with t_clamp_decay = 8..80 us from the loop
     and clamp; a classifier that needs >= 1 ms of HF evidence makes any gate faster than ~10 us irrelevant to E_fault (0.52 J/ms vs
     4.7 mJ for 1 vs 10 us). Do not spend the budget on a fast comparator.
  C2 (Track C): the SW-M-OUT trip command must be INHIBITED (or the device rated for it) whenever the string state implies cases
     (c)-(e): a correctly detected parallel arc that opens a module switch puts 1343..1488 V across it. Conversely, SW-SS may always
     open (17 V), subject to the D-open re-close rule.
  C3 (Track C): per-module sensing/driver self-consumption (ASSUMED 50..200 mW) is 36..144 W plant-wide; put it in the loss column.
  D1 (Track D): simulate the home run as a distributed line or >= 10 lumped LC sections; a single lumped L gives an 11.6 kV spike and
     33 kHz ringing where the line gives 2.25 kV steps at 8.8 us — the clamp energy and dV/dt differ. Time step <= 50 ns during the
     clamp interval; finite gate ramp (not an ideal switch) for ngspice convergence; print the energy-balance residual per run.
  E1 (Track E): the binding module-unit constraint is the sealed-box thermal budget (6.1 mOhm per device hot at 30 K/W; 3.1 at
     60 K/W), not the 0.5 % screen; a measured Rth_ja of a potted J-box with a representative device is the first laboratory item,
     before any arc test.
  E2 (Track E): datasheet E_AS is a single-pulse, 25 C-start figure; nuisance trips and re-close attempts are repetitive. Do not
     accept E_AS as evidence of clamp capability; require an external clamp with a repetitive rating or report UNKNOWN.
  E3 (Track E): an anti-series pair with one device failed short silently loses one blocking direction; a unit that cannot detect
     its own fail-short (periodic Vds test when OFF, or a Vsd signature when ON) cannot claim redundancy. Make it an FMEDA line.

## 5b. Replies to objections already filed against Track B (A: B-1/B-2/B-3; C: O-2; D: OBJ-D3) — section M of the script
  A B-1 / C O-2 (lone SW-M-OUT is string class; first-to-open holds 1332..1458 V): AGREED, independently derived in 1.2. On the
     30-switch "P1-shared" variant: a per-module clamp below the standing voltage carries ~Isc until the others open: 200 V clamp
     3.7 kW, 400 V clamp 7.4 kW; 0.37..0.74 J per 100 us of skew, 37..74 J per 10 ms. Only a wired, sub-100 us string-wide trip makes
     this survivable, and P1-shared then needs 30 clamps rated for that pulse plus a fail-short analysis per clamp. Track B's
     position: P1-shared is a P3 sub-variant and inherits P3's cost; it does not rescue P1.
  A B-2 (SPD coordination): with a 1600 V clamp at SW-STR-INV and the node at Vmpp_s, the array-side line-to-line voltage during the
     clamp interval is V_node + Vc = 2744 V (node at 0: 1600 V). A Type 2 PV SPD with Up ~2.5 kV (ASSUMED class, NOT EXAMINED) would
     conduct for the 8..80 us decay on every trip; Up ~4 kV would not. Therefore: SPD Up >= 1.5 x (V_node,max + Vc) or the breaker's
     clamp must sit across the breaker only and the SPD across line-to-line at the array side of the reactor — a W04/wave-2 item.
  A B-3 (body diodes must block node-into-string current): quantified in 1.2 (0.42 A / 4.5 A / 32.7 A at 1144 / 1300 / 1500 V node,
     25 C dark fit). Below ~1300 V the unidirectional module switch's body-diode heater is < 5 W; above it the dark string itself is
     destroyed before the switch matters. Reverse blocking belongs at string level; a module-level reverse requirement in V_BOOST
     needs Track A to show a node above ~1250 V at night, which C_in at the last MPP (1143.9 V) does not give.
  D OBJ-D3 (1.0 m separation variant 2.559 mH; report denied energy per source): the 1.0 m-separation loop gives 0.383 J stored,
     44.3 kV unclamped at 1 us, and 0.49 J / 35 us (Vc 1600 V, Vs 344 V) or 4.3 J / 312 us (Vs 1458 V) clamp duty — 3.8 x the fixture
     loop. The energy the switch DENIES the fault is, per source: the string's own 519 W x (t_horizon - t_trip) and nothing from
     C_in/C_dc/paired string unless the opening is between them and the fault (1.4/1.5); the off-time's own share is 0.52 J per ms
     of latency, 4.7 mJ for 1 vs 10 us. Track B will report E_denied per source in every device-stress row (checklist 7).
  C (clamp at 100..500 V, 23..115 us): a 100..500 V clamp is below Vs in every case except (a) at STC; it conducts continuously
     in cases (b)-(e) (section 1.1). Track C's latency table should use Vc >= 1600 V (8..80 us) for SW-STR-* and should strike the
     SW-M-OUT row until the X-001 class is settled.

## 6. What Track B did NOT do
  No simulation was run (algebra only); no datasheet was read in full (one blocked fetch, one distributor listing); no standards
  text examined; no probabilities; no part is selected or approved; row length, J-box Rth, Ta_box, clamp voltages, stub inductance,
  reactor values, market Rds ranges and arc voltage are ASSUMED and listed in the section-4 report for assumptions.json.
