import numpy as np
from scipy import optimize, constants
kq = constants.k/constants.e
Voc, Isc, Vmp, Imp, Ns = 45.75, 18.4, 38.13, 17.31, 66
TR = 298.15
def stc_given_n_rs(n, rs):
    a = n*Ns*kq*TR
    # unknowns x1=I0*exp(Voc/a), x2 = Gsh*Voc
    A = np.array([[1-np.exp((Isc*rs-Voc)/a), 1-Isc*rs/Voc],
                  [1-np.exp((Vmp+Imp*rs-Voc)/a), (Voc-Vmp-Imp*rs)/Voc]])
    b = np.array([Isc, Imp])
    x = np.linalg.solve(A, b)
    I0 = x[0]*np.exp(-Voc/a); Gsh = x[1]/Voc
    r = I0/a*np.exp((Vmp+Imp*rs)/a) + Gsh - Imp/(Vmp-Imp*rs)
    return I0, Gsh, r, a
for n in [1.0, 1.1, 1.2, 1.3, 1.4, 1.5]:
    rs_grid = np.linspace(0, 0.5, 2001)
    rr = np.array([stc_given_n_rs(n, rs)[2] for rs in rs_grid])
    idx = np.where(np.sign(rr[:-1]) != np.sign(rr[1:]))[0]
    print("n", n, "r(0)", rr[0], "sign changes at", rs_grid[idx][:5])
    for i in idx[:2]:
        rs = optimize.brentq(lambda x: stc_given_n_rs(n, x)[2], rs_grid[i], rs_grid[i+1], xtol=1e-15, rtol=1e-15)
        I0, Gsh, r, a = stc_given_n_rs(n, rs)
        Iph = I0*(np.exp(Voc/a)-1) + Voc*Gsh
        print("   Rs %.6f Rsh %.3f I0 %.4e Iph %.6f" % (rs, 1/Gsh if Gsh>0 else -1, I0, Iph))
