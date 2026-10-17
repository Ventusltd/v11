import numpy as np
from scipy import optimize
KQ = 1.380649e-23/1.602176634e-19
Voc, Isc, Vmp, Imp, Ns = 45.75, 18.4, 38.13, 17.31, 66
TR = 298.15; BV=-0.0024; MU=0.0005*Isc
def stc(n):
    a = n*Ns*KQ*TR
    def sol(rs):
        A = np.array([[1-np.exp((Isc*rs-Voc)/a), 1-Isc*rs/Voc],[1-np.exp((Vmp+Imp*rs-Voc)/a), (Voc-Vmp-Imp*rs)/Voc]])
        x = np.linalg.solve(A, np.array([Isc, Imp])); I0 = x[0]*np.exp(-Voc/a); Gsh = x[1]/Voc
        return I0, Gsh, I0/a*np.exp((Vmp+Imp*rs)/a) + Gsh - Imp/(Vmp-Imp*rs)
    grid = np.linspace(0, (Voc-Vmp)/Imp, 4001)[:-1]
    r = np.array([sol(x)[2] for x in grid]); i = np.where((r[:-1] < 0) & (r[1:] >= 0))[0][0]
    rs = optimize.brentq(lambda x: sol(x)[2], grid[i], grid[i+1], xtol=1e-15, rtol=1e-15)
    I0, Gsh, _ = sol(rs); Iph = I0*np.expm1(Voc/a) + Voc*Gsh
    return dict(n=n, a=a, I0=I0, Rs=rs, Rsh=1/Gsh, Iph=Iph)
def voc_T(p, T, law):
    TK=T+273.15
    Iph=p['Iph']+MU*(T-25); I0=law(p,TK); a=p['a']*TK/TR; Rsh=p['Rsh']
    return optimize.brentq(lambda V: Iph - I0*np.expm1(V/a) - V/Rsh, 0, 100, xtol=1e-14, rtol=1e-15)
laws = {
 'desoto(Eg=1.121,dEg)': lambda p,TK: p['I0']*(TK/TR)**3*np.exp(1.121/(KQ*TR) - 1.121*(1-0.0002677*(TK-TR))/(KQ*TK)),
 'pvsyst(T3,Eg/n,Eg=1.12)': lambda p,TK: p['I0']*(TK/TR)**3*np.exp(1.12/(p['n']*KQ)*(1/TR-1/TK)),
 'spice(T^(3/n),Eg/n,Eg=1.12)': lambda p,TK: p['I0']*(TK/TR)**(3/p['n'])*np.exp(1.12/(p['n']*KQ)*(1/TR-1/TK)),
 'spice(T^(3/n),Eg/n,Eg=1.11)': lambda p,TK: p['I0']*(TK/TR)**(3/p['n'])*np.exp(1.11/(p['n']*KQ)*(1/TR-1/TK)),
 'shockley(T3,Eg=1.12)': lambda p,TK: p['I0']*(TK/TR)**3*np.exp(1.12/(KQ)*(1/TR-1/TK)),
}
fixv = lambda T: Voc*(1+BV*(T-25))
for name, law in laws.items():
    print('==', name)
    for n in [1.0, 1.1, 1.2, 1.3]:
        p = stc(n)
        rr = [voc_T(p,T,law)-fixv(T) for T in (-10,70)]
        print('  n %.2f  resid(-10)=%+.4f V resid(70)=%+.4f V  rms=%.4f' % (n, rr[0], rr[1], np.sqrt(np.mean(np.square(rr)))))
    ss = lambda n: sum((voc_T(stc(n),T,law)-fixv(T))**2 for T in (-10,70))
    r = optimize.minimize_scalar(ss, bounds=(1.0,1.33), method='bounded', options={'xatol':1e-9})
    p=stc(r.x); rr=[voc_T(p,T,law)-fixv(T) for T in (-10,0,50,70)]
    print('  best n in [1,1.33]: %.6f resid(-10,0,50,70)=%s Rs %.5f Rsh %.2f' % (r.x, np.round(rr,5), p['Rs'], p['Rsh']))
