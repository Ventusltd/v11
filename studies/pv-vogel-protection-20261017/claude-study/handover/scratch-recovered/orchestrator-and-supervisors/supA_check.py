"""SUP-A independent cross-check (scratchpad, NOT the study model). Deterministic, no seeds needed.
Reads only the shared fixture. Single-diode fit here is a supervisor's sanity fit with FIXED n (1.0/1.2/1.4);
the study fit must come from claude-study/models/pv_module.py (W02)."""
import json, math, hashlib, sys
from scipy.optimize import fsolve, brentq

FXP = '/home/claude/v11/studies/pv-vogel-protection-20261017/claude-study/fixture/system-fixture.json'
FX = json.load(open(FXP))
m, p, c, inv, arc = FX['module'], FX['plant'], FX['conductors'], FX['inverter_dc_side'], FX['arc_model']
Voc, Isc, Vmp, Imp = m['voc_stc_v'], m['isc_a'], m['vmpp_v'], m['impp_a']
Ns = m['single_diode_fit']['cells_in_series_total']; NSS = m['internal_structure']['substrings_per_module']
Vf = 0.45  # fixture: Schottky_assumed_Vf_0p45_V_at_17A
kVoc, kIsc = m['voc_temp_coeff_per_c'], m['isc_temp_coeff_per_c']['value']
N = p['modules_per_string']; Vmp_s, Voc_s, Voc_s_cold = p['string_derived']['vmpp_string_v'], p['string_derived']['voc_string_stc_v'], p['string_derived']['voc_string_cold_minus10c_v']
Vt = 1.380649e-23 * 298.15 / 1.602176634e-19
out = {}

# ---- 1. single-diode fit with fixed n (supervisor cross-check) ----
def fit(n):
    """Fixed-n five-parameter fit: Iph and I0 eliminated by the Voc and Isc equations; (Rs, Rsh) from the
    MPP current equation and dP/dV = 0 at Vmp. Supervisor cross-check only."""
    a = n * Ns * Vt
    def elim(Rs, Rsh):
        I0 = (Isc + Isc * Rs / Rsh - Voc / Rsh) / (math.exp(Voc / a) - math.exp(Isc * Rs / a))
        Iph = I0 * (math.exp(Voc / a) - 1) + Voc / Rsh
        return Iph, I0
    def F(x):
        Rs, Rsh = x
        Iph, I0 = elim(Rs, Rsh)
        e_mp = math.exp((Vmp + Imp * Rs) / a)
        g = I0 * e_mp / a + 1 / Rsh            # dI/dV magnitude at MPP (before Rs feedback)
        return [Iph - I0 * (e_mp - 1) - (Vmp + Imp * Rs) / Rsh - Imp,
                -g / (1 + Rs * g) + Imp / Vmp]   # dP/dV = I + V dI/dV = 0
    best = None
    for Rs0 in (0.05, 0.1, 0.2, 0.3):
        for Rsh0 in (100.0, 300.0, 1000.0):
            x, info, ier, msg = fsolve(F, [Rs0, Rsh0], xtol=1e-13, full_output=True)
            res = max(abs(v) for v in F(x))
            if x[0] > 0 and x[1] > 0 and (best is None or res < best['residual']):
                Iph, I0 = elim(*x)
                best = dict(n=n, Iph=Iph, I0=I0, Rs=x[0], Rsh=x[1], residual=res)
    return best

def I_of_V(V, prm, G=1.0, Iph_scale=1.0):
    a = prm['n'] * Ns * Vt; Iph = prm['Iph'] * G * Iph_scale
    f = lambda I: Iph - prm['I0'] * (math.exp((V + I * prm['Rs']) / a) - 1) - (V + I * prm['Rs']) / prm['Rsh'] - I
    return brentq(f, -200, 200)

def V_of_I(I, prm, G=1.0):
    """Terminal voltage of one illuminated module at current I (I <= Iph). Allows negative V (reverse bias when
    I exceeds the module's photocurrent) down to -60 V, i.e. the bypass-diode-free reverse branch; callers
    that have bypass diodes must clamp at -Vf themselves."""
    a = prm['n'] * Ns * Vt; Iph = prm['Iph'] * G
    # explicit inverse: V = a*ln((Iph - I - (V+I Rs)/Rsh)/I0 + 1) - I Rs  -> solve scalar in V
    f = lambda V: Iph - prm['I0'] * (math.exp((V + I * prm['Rs']) / a) - 1) - (V + I * prm['Rs']) / prm['Rsh'] - I
    return brentq(f, -60.0, Voc + 5)

def V_module_bypassed(I, prm, G=1.0):
    """Module with ideal 3-substring bypass: terminal V cannot go below -3*Vf (all three diodes conducting).
    If the demanded current exceeds what the cells deliver at -3*Vf, the diodes carry the excess."""
    if I >= I_of_V(-NSS * Vf, prm, G):
        return -NSS * Vf
    return V_of_I(I, prm, G)

fits = {n: fit(n) for n in (1.0, 1.2, 1.4)}
out['fits'] = fits
# ---- 2. arc law ----
def Varc(I, gap): return (20 + 0.534 * gap) * I ** 0.12
out['Varc_17p31_gap1_3_5_v'] = [Varc(Imp, g) for g in (1, 3, 5)]
out['Varc_18p4_gap1_3_5_v'] = [Varc(Isc, g) for g in (1, 3, 5)]
out['Varc_Imin_0p5A_gap1_v'] = Varc(0.5, 1.0)
out['Parc_env_w'] = dict(min_20v_17a=20 * 17, max_60v_18p4a=60 * 18.4, fixture_gap1_imp=Varc(Imp, 1) * Imp, fixture_gap5_isc=Varc(Isc, 5) * Isc)

# ---- 3. C1 substring numbers ----
Voc_ss = Voc / NSS; Vmp_ss = Vmp / NSS
out['C1'] = dict(Voc_ss_stc_v=Voc_ss, Voc_ss_m10c_v=Voc_ss * (1 + kVoc * (-10 - 25)), Voc_ss_70c_v=Voc_ss * (1 + kVoc * (70 - 25)),
                 gap_v_during_commutation_stc=Vmp_ss + Vf, gap_v_during_commutation_m10c=Vmp_ss * (1 + kVoc * (-35)) + Vf,
                 loop_v_max_stc=Voc_ss + Vf, loop_v_max_m10c=Voc_ss * (1 + kVoc * (-35)) + Vf,
                 Pss_mpp_w=m['rated_wp'] / NSS, Parc_bound_w=m['rated_wp'] / NSS + Vf * Imp)

# ---- 4. X-001 SW-M-OUT and SW-SS voltages ----
Vmp_s_cold = Vmp_s * (1 + kVoc * (-35))  # ASSUMED: Vmpp scales with the Voc coefficient
out['X001'] = dict(a_vmpp_stc=Voc_s - Vmp_s, a_cold_voc_stc_vmpp=Voc_s_cold - Vmp_s, a_cold_both=Voc_s_cold - Vmp_s_cold,
                   b_node0_stc=Voc_s, b_node0_cold=Voc_s_cold, c_par_arc30_stc=Voc_s - 30, c_par_arc30_cold=Voc_s_cold - 30,
                   sw_ss_stc=Voc_ss + Vf, sw_ss_cold=Voc_ss * (1 + kVoc * (-35)) + Vf, share_if_30_open_cold=Voc_s_cold / N)

# ---- 5. cable / loop ----
r = c['two_wire_line_defaults']['conductor_radius_6mm2_m']; D = c['home_pair_separation_m']; mu0 = 4e-7 * math.pi; eps0 = 8.8541878128e-12
L_ext_ln = mu0 / math.pi * math.log(D / r); L_ext_acosh = mu0 / math.pi * math.acosh(D / (2 * r)); L_int = 0.1e-6
C_line = math.pi * eps0 * c['effective_relative_permittivity'] / math.log(D / r)
L_row_per_m = mu0 / math.pi * math.log(c['sequential_row_return_separation_m'] / r) + L_int
row_len_m = 40.0  # ASSUMED (30 modules x ~1.3 m pitch)
L_hr = (L_ext_ln + L_int) * 936; L_row = L_row_per_m * row_len_m; L_loop = L_hr + L_row
R_km = c['field_cable']['resistance_ohm_per_km_20c']; R_hr_loop_936 = 2 * 936 * R_km / 1000; R_hr_loop_931 = 2 * 931 * R_km / 1000; R_hr_loop_600 = 2 * 600 * R_km / 1000
R_5m_loop = 2 * 5 * R_km / 1000
R_str_int = N * (m['internal_structure']['positive_lead_m'] + m['internal_structure']['negative_lead_m']) * c['factory_lead']['resistance_ohm_per_km_20c'] / 1000 + c['mated_interfaces_per_string']['total'] * c['connector_resistance_ohm_each']
out['cable'] = dict(L_ext_ln_uH_per_m=L_ext_ln * 1e6, L_ext_acosh_uH_per_m=L_ext_acosh * 1e6, pct_diff=100 * (L_ext_ln - L_ext_acosh) / L_ext_acosh,
                    C_pF_per_m=C_line * 1e12, Z0=math.sqrt(L_ext_ln / C_line), v=1 / math.sqrt(L_ext_ln * C_line), delay_936_us=936 * math.sqrt(L_ext_ln * C_line) * 1e6,
                    L_hr_936_mH=L_hr * 1e3, L_row_per_m_uH=L_row_per_m * 1e6, L_row_40m_mH=L_row * 1e3, L_loop_mH=L_loop * 1e3,
                    R_hr_loop_936=R_hr_loop_936, R_hr_loop_931=R_hr_loop_931, R_hr_loop_600=R_hr_loop_600, R_5m_loop=R_5m_loop, R_string_internal=R_str_int,
                    R_drift_30K_936=R_hr_loop_936 * c['field_cable']['temp_coeff_per_c'] * 30, lumped_limit_hz=(1 / math.sqrt(L_ext_ln * C_line)) / (4 * 936))
# ---- 6. energies ----
Cin = inv['mppt_input_capacitance_f']['value']; Cin_r = inv['mppt_input_capacitance_f']['range']; Cdc = inv['dc_link_capacitance_f']['value']; Cdc_r = inv['dc_link_capacitance_f']['range']
out['energy'] = dict(LI2_936_full=0.5 * L_hr * Isc ** 2, LI2_936_ext_only=0.5 * L_ext_ln * 936 * Isc ** 2, LI2_loop_17p31=0.5 * L_loop * Imp ** 2,
                     CV2_Cin_vmpp=0.5 * Cin * Vmp_s ** 2, CV2_Cin_range=[0.5 * x * Vmp_s ** 2 for x in Cin_r], CV2_Cin_voc=0.5 * Cin * Voc_s ** 2,
                     CV2_dc_vmpp=0.5 * Cdc * Vmp_s ** 2, CV2_dc_range=[0.5 * x * Vmp_s ** 2 for x in Cdc_r], CV2_line_936=0.5 * C_line * 936 * Vmp_s ** 2)
# ---- 7. C2 operating points (STC, gap 1 mm), using fit n=1.2 ----
prm = fits[1.2]
def c2_point(R20, R19, gap=1.0):
    """Two illuminated strings feeding one parallel arc at a common node; each string is a current-limited source
    V_str(I) = 30*V_mod(I) - R*I; the node voltage equals V_arc(I20+I19). Solved by nesting: for a trial node
    voltage Vn, each string current is I_k = argI{30 V_mod(I) - R_k I = Vn} (unique, monotone), then
    Varc(I20+I19) = Vn is a scalar root in Vn."""
    Imax = prm['Iph']
    def I_str(Vn, R):
        g = lambda I: N * V_module_bypassed(I, prm) - R * I - Vn
        return brentq(g, 0.0, Imax * 1.5)
    def h(Vn): return Varc(max(I_str(Vn, R20) + I_str(Vn, R19), 0.5), gap) - Vn
    Vn = brentq(h, 1.0, Voc_s - 0.01)
    I20, I19 = I_str(Vn, R20), I_str(Vn, R19); Va = Varc(I20 + I19, gap)
    return dict(I20=I20, I19=I19, Iarc=I20 + I19, Varc=Va, Parc=Va * (I20 + I19))
def c2_single(R, gap=1.0):
    I = brentq(lambda I: N * V_module_bypassed(I, prm) - Varc(I, gap) - R * I, 0.6, prm['Iph'] * 1.5)
    return dict(I=I, Varc=Varc(I, gap), Parc=Varc(I, gap) * I, Vstring=N * V_of_I(I, prm), P_cable=I * I * R)
far_pre = c2_point(R_5m_loop + R_str_int, R_hr_loop_931 + R_hr_loop_600 + R_str_int)
far_pre['Vnode'] = far_pre['Varc'] + R_hr_loop_931 * far_pre['I19']
near_pre = c2_point(R_hr_loop_931 + R_str_int, R_5m_loop + R_hr_loop_600 + R_str_int)
near_pre['Vnode'] = near_pre['Varc'] + R_5m_loop * near_pre['I19']
out['C2'] = dict(far_pre=far_pre, near_pre=near_pre,
                 far_after_SWSTRINV=c2_single(R_5m_loop + R_str_int), near_after_SWSTRINV=c2_single(R_hr_loop_931 + R_str_int),
                 far_after_SWSTRARR_S19_only=c2_single(R_hr_loop_931 + R_hr_loop_600 + R_str_int),
                 residual_isc_by_G_T={'G1000_25C': Isc, 'G500_25C': Isc * 0.5, 'G1000_70C': Isc * (1 + kIsc * 45), 'G1000_m10C': Isc * (1 + kIsc * -35)},
                 residual_P_gap1_5_at_isc=[Varc(Isc, 1) * Isc, Varc(Isc, 5) * Isc],
                 I_module_at_1p1V_over_Isc=I_of_V(1.1, prm) / Isc, I_module_at_4p9V_over_Isc=I_of_V(4.9, prm) / Isc)
# C_in discharge split (far): charge moved x arc voltage vs total
dQ_far = Cin * (Vmp_s - far_pre['Vnode']); E_Cin_total_far = 0.5 * Cin * (Vmp_s ** 2 - far_pre['Vnode'] ** 2)
L931 = (L_ext_ln + L_int) * 931
out['C2']['Cin_far'] = dict(dQ_C=dQ_far, E_total_released=E_Cin_total_far, E_arc_at_30V=30 * dQ_far, zeta=(R_hr_loop_931 / 2) * math.sqrt(Cin / L931), tau_LR_us=L931 / R_hr_loop_931 * 1e6, RC_ms=R_hr_loop_931 * Cin * 1e3)
L5 = (L_ext_ln + L_int) * 5
out['C2']['Cin_near'] = dict(E_total=0.5 * Cin * Vmp_s ** 2, Z_surge=math.sqrt(L5 / Cin), Ipk_undamped_bound=(Vmp_s - 30) / math.sqrt(L5 / Cin), zeta_cable_only=(R_5m_loop / 2) * math.sqrt(Cin / L5), E_arc_floor_30V=30 * Cin * (Vmp_s - 31))
out['C2']['dclink_near_directbus'] = dict(E_total=0.5 * Cdc * Vmp_s ** 2, Z_surge=math.sqrt(L5 / Cdc), Ipk_undamped_bound=(Vmp_s - 30) / math.sqrt(L5 / Cdc))
# ---- 8. SW-M-OUT clamp / off-time ----
def clamp(Vc, Vsrc, I=Imp, L=L_loop):
    if Vc <= Vsrc: return dict(Vc=Vc, Vsrc=Vsrc, result='clamp conducts indefinitely', P_w=Vc * Isc)
    return dict(Vc=Vc, Vsrc=Vsrc, t_off_us=L * I / (Vc - Vsrc) * 1e6, E_clamp_j=0.5 * L * I * I * Vc / (Vc - Vsrc), di_dt_A_per_us=(Vc - Vsrc) / L * 1e-6)
out['clamp'] = [clamp(600, Voc_s - Vmp_s), clamp(1200, Voc_s - Vmp_s), clamp(600, Voc_s - 30), clamp(1200, Voc_s - 30), clamp(1500, Voc_s - 30), clamp(1500, Voc_s_cold - 30)]
out['unclamped_LdIdt_1us_kV'] = L_loop * Imp / 1e-6 / 1e3
# ---- 9. backfeed (reverse) checks ----
def dark_V_of_I(I, prm):  # forward-biased dark module (Iph=0) at current I flowing in the diode-forward direction
    a = prm['n'] * Ns * Vt
    return brentq(lambda V: prm['I0'] * (math.exp((V - I * prm['Rs']) / a) - 1) + (V - I * prm['Rs']) / prm['Rsh'] - I, 0, 80)
bf = {}
for n, pr in fits.items():
    # V_DIRECTBUS night: DC link at Vmpp_string pushes into a dark 30-module string
    I_night = brentq(lambda I: N * dark_V_of_I(I, pr) - Vmp_s, 1e-6, 40)
    # S19 illuminated (STC), S20 fully dark with a series arc (gap 1 mm): V_S19(I) = V_arc(I) + 30 * V_dark(I)
    try:
        I_bf = brentq(lambda I: N * V_of_I(I, pr) - Varc(I, 1.0) - N * dark_V_of_I(I, pr), 0.5, 18.0)
    except ValueError:
        I_bf = 0.0
    # same-irradiance paired strings, S20 hotter by dT: illuminated reverse feed requires Voc19 - V_rev_stack20(I) > Varc
    bf[n] = dict(night_directbus_backfeed_A=I_night, S19_into_dark_S20_arc_A=I_bf, Varc_at_that_I=Varc(max(I_bf, 0.5), 1))
out['backfeed'] = bf
# ---- 10. C3 thermal ----
th = FX['priority_cases']['C3']['thermal']; Cth = th['connector_thermal_mass_j_per_k']['value']; G = th['connector_to_ambient_w_per_k']['value']
out['C3'] = {f'R{R}': dict(P_w=Imp ** 2 * R, dT_ss_K=Imp ** 2 * R / G, T_ss_C=th['ambient_c'] + Imp ** 2 * R / G, V_drop_v=Imp * R, E_3600s_kJ=Imp ** 2 * R * 3.6) for R in FX['priority_cases']['C3']['resistance_variants_ohm']}
out['C3']['tau_s'] = Cth / G

json.dump(out, sys.stdout, indent=1, default=float)
print('\nSCRIPT_SHA256', hashlib.sha256(open(__file__, 'rb').read()).hexdigest())
