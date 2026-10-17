import numpy as np
from scipy import optimize, constants, special
kq = constants.k/constants.e   # V/K
k_eV = constants.k/constants.e # eV/K same number
Voc, Isc, Vmp, Imp, Ns = 45.75, 18.4, 38.13, 17.31, 66
TR = 298.15
EG0, DEG = 1.121, 0.0002677
AISC = 0.0005*Isc
BV = -0.0024
def stc(n):
    a = n*Ns*kq*TR
    def sol(rs):
        A = np.array([[1-np.exp((Isc*rs-Voc)/a), 1-Isc*rs/Voc],
                      [1-np.exp((Vmp+Imp*rs-Voc)/a), (Voc-Vmp-Imp*rs)/Voc]])
        x = np.linalg.solve(A, np.array([Isc, Imp]))
        I0 = x[0]*np.exp(-Voc/a); Gsh = x[1]/Voc
        r = I0/a*np.exp((Vmp+Imp*rs)/a) + Gsh - Imp/(Vmp-Imp*rs)
        return I0, Gsh, r
    rs = optimize.brentq(lambda x: sol(x)[2], 1e-4, 0.3, xtol=1e-15, rtol=1e-15, maxiter=500)
    I0, Gsh, _ = sol(rs)
    Iph = I0*(np.exp(Voc/a)-1) + Voc*Gsh + 0  # at Voc, I=0 -> Iph = I0(exp(Voc/a)-1)+Voc/Rsh
    return dict(n=n, a=a, I0=I0, Rs=rs, Rsh=1/Gsh, Iph=Iph)
def params_at(p, G, T):
    TK = T+273.15
    a = p['a']*TK/TR
    Eg = EG0*(1-DEG*(TK-TR))
    I0 = p['I0']*(TK/TR)**3*np.exp((EG0/(k_eV*TR) - Eg/(k_eV*TK)))
    Iph = G/1000*(p['Iph'] + AISC*(TK-TR))
    return Iph, I0, a, p['Rs'], p['Rsh']
def voc(p, G, T):
    Iph, I0, a, Rs, Rsh = params_at(p, G, T)
    f = lambda V: Iph - I0*np.expm1(V/a) - V/Rsh
    return optimize.brentq(f, 0, 80, xtol=1e-13)
for n in [1.0, 1.05, 1.07, 1.08, 1.1, 1.15, 1.2]:
    p = stc(n)
    vm10, vp70 = voc(p, 1000, -10), voc(p, 1000, 70)
    slope = (voc(p,1000,26)-voc(p,1000,24))/2
    print("n %.3f Rs %.5f Rsh %.2f I0 %.3e Iph %.5f | Voc(25) %.5f Voc(-10) %.4f (fix 49.593 r %.4f) Voc(70) %.4f (fix 40.809 r %.4f) slope %.5f %%/C %.4f" % (
        n, p['Rs'], p['Rsh'], p['I0'], p['Iph'], voc(p,1000,25), vm10, vm10-49.593, vp70, vp70-40.809, slope, 100*slope/45.75))
