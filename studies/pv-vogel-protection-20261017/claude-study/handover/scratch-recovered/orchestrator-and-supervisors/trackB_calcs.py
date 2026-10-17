"""SUP-B initial-attack calculations. Deterministic, algebra grade only. Reads the shared fixture.
Run: python3 -I trackB_calcs.py   (prints labelled values used in track-B-charter-and-initial-attack.md)
"""
import json, math
FX = json.load(open('/home/claude/v11/studies/pv-vogel-protection-20261017/claude-study/fixture/system-fixture.json'))
m, p, c, inv = FX['module'], FX['plant'], FX['conductors'], FX['inverter_dc_side']
Impp, Isc, Vmpp, Voc = m['impp_a'], m['isc_a'], m['vmpp_v'], m['voc_stc_v']
aIsc = m['isc_temp_coeff_per_c']['value']
Voc_s_stc, Voc_s_cold, Voc_m_cold = p['string_derived']['voc_string_stc_v'], p['string_derived']['voc_string_cold_minus10c_v'], p['string_derived']['voc_module_cold_minus10c_v']
Vmpp_s = p['string_derived']['vmpp_string_v']
Pstr = p['string_derived']['pmpp_string_w']
tw = c['two_wire_line_defaults']
Lp = (tw['loop_external_inductance_uh_per_m_approx'] + tw['loop_internal_inductance_dc_uh_per_m_approx']) * 1e-6
Lp_ext = tw['loop_external_inductance_uh_per_m_approx'] * 1e-6
Cp = tw['line_capacitance_pf_per_m_approx'] * 1e-12
Z0 = tw['characteristic_impedance_ohm_approx']
route = 936.0
R_km = c['field_cable']['resistance_ohm_per_km_20c']
print('--- fixture-derived constants ---')
L = Lp * route; L_ext = Lp_ext * route; Cl = Cp * route
Rloop = 2 * route * R_km / 1000
print(f'L_loop_936m_h = {L:.6e} (ext+int dc)  L_ext_only = {L_ext:.6e}  C_line_f = {Cl:.4e}  R_loop_ohm_20c = {Rloop:.3f}')
print(f'Isc_hot70_a = {Isc*(1+aIsc*45):.3f}   Isc_cold-10_a = {Isc*(1+aIsc*(-35)):.3f}')
print(f'route IR drop at Impp, V = {Impp*Rloop:.1f}; route loss W = {Impp**2*Rloop:.0f}; fraction of string Pmpp = {Impp**2*Rloop/Pstr*100:.2f} %')
for I in (Impp, Isc, Isc*(1+aIsc*45)):
    print(f'half_L_I2_j at I={I:.2f} A: {0.5*L*I*I:.4f} J  (ext-only {0.5*L_ext*I*I:.4f} J)')
print(f'unclamped lumped L*di/dt for 1 us ramp of Impp: {L*Impp/1e-6:.0f} V; with 0.66 mH: {0.66e-3*Impp/1e-6:.0f} V')
print(f'distributed-line first step I*Z0 = {Impp*Z0:.0f} V; lumped LC ring f = {1/(2*math.pi*math.sqrt(L*Cl)):.0f} Hz; quarter-wave f = {1/(4*tw["one_way_delay_936m_us"]*1e-6):.0f} Hz')
print(f'line C energy at Vmpp_s: {0.5*Cl*Vmpp_s**2:.4f} J')
print('--- post-trip steady voltage bounds (forward, SW-M-OUT alone or SW-STR-*) ---')
for name, Vnode in (('node at Vmpp_s', Vmpp_s), ('node at Vmpp_s minus 936 m IR', Vmpp_s - Impp*Rloop), ('node at window min 500 V', 500.0), ('node collapsed (C2-near arc 30 V)', 30.0), ('node at 0', 0.0)):
    print(f'  {name:36s}: STC {Voc_s_stc - Vnode:7.1f} V   cold {Voc_s_cold - Vnode:7.1f} V')
print(f'reverse bound (night, string dark, node charged): V_inv_max = {inv["input_voltage_window_v"]["max"]} V (V_DIRECTBUS) / {Vmpp_s:.1f} V (pre-sunset MPPT cap)')
print(f'reverse-polarity string (SW-STR-INV opening): {2*Voc_s_cold:.0f} V cold')
print('--- clamp trade: t = L I/(Vc - Vs); E = 0.5 L I^2 Vc/(Vc - Vs); I = Impp, L = L_loop ---')
E0 = 0.5*L*Impp**2
for Vs in (228.6, 343.9, 453.8, 987.8, 1457.8):
    for Vc in (400, 600, 1000, 1600, 1700):
        if Vc > Vs:
            t = L*Impp/(Vc-Vs); E = E0*Vc/(Vc-Vs)
            print(f'  Vs={Vs:7.1f} V Vc={Vc:5d} V: t_decay={t*1e6:6.1f} us  E_clamp={E:6.3f} J  P_avg={E/t/1e3:6.1f} kW')
print('--- clamp below source: continuous clamp conduction (illustrative single-diode-ish IV) ---')
nVt66 = 1.3*66*0.02569
def I_mod(V):  # illustrative: I = Isc(1-exp((V-Voc)/(n*N*Vt)))
    return Isc*(1-math.exp((V-Voc)/nVt66))
for Vc in (100, 150, 300):
    Vm = (Vmpp_s + Vc)/30
    print(f'  Vc={Vc} V with node at Vmpp_s -> module V {Vm:.1f} V -> string I ~ {I_mod(Vm):.1f} A -> clamp P ~ {Vc*I_mod(Vm):.0f} W continuous')
print('--- conduction budgets ---')
Pmod = m['rated_wp']; Pplant = p['dc_nameplate_wp']
for frac in (0.005, 0.01):
    print(f'  {frac*100:.1f} %: module {frac*Pmod/Impp**2*1e3:.2f} mOhm; 2-mod {frac*2*Pmod/Impp**2*1e3:.2f}; 4-mod(plant/192) {frac*Pplant/192/Impp**2*1e3:.2f}; string {frac*Pstr/Impp**2*1e3:.1f} mOhm')
print('--- illustrative loss vs voltage class (ASSUMED market Rds ranges, hot, anti-series pair) ---')
for cls, r_pair_mohm in (('60-100 V Si pair', 5), ('150 V Si pair', 10), ('200 V Si pair', 20), ('650 V SJ/SiC pair', 45), ('1200 V SiC pair', 40), ('1700 V SiC pair', 120)):
    P = Impp**2*r_pair_mohm*1e-3
    print(f'  {cls:20s} {r_pair_mohm:4d} mOhm -> {P:5.1f} W/module = {P/Pmod*100:4.2f} % ; plant x720 = {P*720/1e3:5.1f} kW')
print('--- SW-SS (per-substring) numbers ---')
Voc_ss_cold = Voc_m_cold/3; Vf = 0.45
print(f'  Voc_substring cold {Voc_ss_cold:.2f} V; off-state ~ Voc_ss+Vf = {Voc_ss_cold+Vf:.2f} V; bypass diode P at Impp = {Vf*Impp:.2f} W; 3 diodes {3*Vf*Impp:.1f} W/module')
for Lss in (1e-6, 2e-6, 5e-6):
    for toff in (0.2e-6, 1e-6, 2e-6, 5e-6):
        print(f'  L_ss={Lss*1e6:.0f} uH toff={toff*1e6:.1f} us: L di/dt = {Lss*Impp/toff:.0f} V')
print('--- body diode one-switch-OFF dissipation ---')
for name, vf in (('Si SJ body diode Vf~1.0 V', 1.0), ('SiC body diode Vf~3.5 V', 3.5)):
    print(f'  {name}: {vf*Impp:.1f} W at Impp, {vf*Isc:.1f} W at Isc')
print('--- shunt (X-005) ---')
for R in (0.1, 2e-3, 1e-3, 0.5e-3):
    print(f'  R={R*1e3:.1f} mOhm: P={R*Impp**2:.3f} W at Impp, {R*Isc**2:.3f} W at Isc; signal {R*Impp*1e3:.2f} mV; x720 = {R*Impp**2*720/1e3:.2f} kW; L_par 2 nH corner f = {R/(2*math.pi*2e-9)/1e3:.0f} kHz')
print('--- thermal screen examples (ASSUMED Rth) ---')
def tj_fixed_point(Ta, Rth, I, R25, alpha, Tmax=400):
    Tj = Ta
    for _ in range(200):
        Tn = Ta + Rth*I*I*R25*(1+alpha*(Tj-25))
        if Tn > Tmax: return float('nan')
        if abs(Tn-Tj) < 1e-4: return Tn
        Tj = Tn
    return Tj
for Ta in (45, 70, 85):
    for Rth in (15, 30, 50, 60):
        for R25, alpha, lab in ((2.5e-3, 0.006, '100V Si 2.5 mOhm'), (5.0e-3, 0.008, '650V 5 mOhm?'), (22e-3, 0.0085, '650V SJ 22 mOhm'), (45e-3, 0.003, '1700V SiC 45 mOhm')):
            Tj = tj_fixed_point(Ta, Rth, Impp, R25, alpha)
            P = Impp**2*R25*(1+alpha*(Tj-25)) if Tj==Tj else float('nan')
            print(f'  Ta={Ta} C Rth={Rth} K/W {lab:18s}: Tj={Tj:6.1f} C  P/device={P:5.2f} W')
print('--- adiabatic pulse bound: dT = 2E/(A*sqrt(pi*rho*cp*k*t)) ---')
for mat, rho, cp, k in (('Si', 2330, 700, 120), ('SiC', 3210, 690, 300)):
    for E, t in ((0.1, 30e-6), (0.162, 31e-6), (0.70, 48e-6), (0.3, 100e-6), (1.9, 1e-3)):
        for A in (10e-6, 25e-6):
            dT = 2*E/(A*math.sqrt(math.pi*rho*cp*k*t))
            print(f'  {mat} E={E:.3f} J t={t*1e6:6.0f} us A={A*1e6:4.0f} mm2: dTj_adiabatic={dT:6.0f} K (x2 crowding margin {2*dT:6.0f} K)')
print('--- SW-STR-INV C2-near prospective current ---')
Lstub = Lp*5 + 0.1e-6
print(f'  5 m stub loop L = {Lstub*1e6:.2f} uH; di/dt = {Vmpp_s/Lstub/1e6:.0f} A/us; time to 200 A = {200*Lstub/Vmpp_s*1e6:.2f} us')
for Lr in (20e-6, 100e-6):
    didt = Vmpp_s/(Lr+Lstub)
    I5 = Impp + didt*5e-6; I10 = Impp + didt*10e-6
    print(f'  reactor {Lr*1e6:.0f} uH: di/dt={didt/1e6:.1f} A/us; I at 5 us={I5:.0f} A, at 10 us={I10:.0f} A; E_L at 10 us={0.5*(Lr+Lstub)*I10**2:.3f} J; E_clamp(1600 V vs 1144 V)={0.5*(Lr+Lstub)*I10**2*1600/(1600-Vmpp_s):.3f} J')
Cin = inv['mppt_input_capacitance_f']['value']; Cdc = inv['dc_link_capacitance_f']['value']
print(f'  C_in energy at Vmpp_s {0.5*Cin*Vmpp_s**2:.0f} J, at 1500 V {0.5*Cin*1500**2:.0f} J; C_dc at Vmpp_s {0.5*Cdc*Vmpp_s**2:.0f} J, at 1500 V {0.5*Cdc*1500**2:.0f} J')
print(f'  far-end DC prospective from node: {Vmpp_s/Rloop:.0f} A (20 C copper, arc V ignored); first wave V/Z0 = {Vmpp_s/Z0:.1f} A per transit')
print('--- X-003 energy argument ---')
Parc = 30*Impp
print(f'  arc power at 30 V, Impp: {Parc:.0f} W; energy saved by 1 us vs 10 us off-time: {Parc*9e-6*1e3:.2f} mJ; vs 1 ms detection: {Parc*1e-3:.3f} J')
print('--- string-wide coordination skew (first module clamp alone) ---')
for skew in (10e-6, 100e-6, 1e-3):
    print(f'  skew {skew*1e6:6.0f} us: first-clamp energy at ~1.9 kW = {1900*skew:.3f} J')
