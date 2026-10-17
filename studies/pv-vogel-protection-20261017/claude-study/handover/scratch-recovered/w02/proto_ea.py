import numpy as np
from scipy import optimize, constants, special
KQ = constants.k/constants.e
Voc, Isc, Vmp, Imp, Ns = 45.75, 18.4, 38.13, 17.31, 66
TR = 298.15; BV=-0.0024; AISC=0.0005*Isc
def stc(n):
    a = n*Ns*KQ*TR
    def sol(rs):
        A = np.array([[1-np.exp((Isc*rs-Voc)/a), 1-Isc*rs/Voc],[1-np.exp((Vmp+Imp*rs-Voc)/a), (Voc-Vmp-Imp*rs)/Voc]])
        x = np.linalg.solve(A, np.array([Isc, Imp])); I0 = x[0]*np.exp(-Voc/a); Gsh = x[1]/Voc
        return I0, Gsh, I0/a*np.exp((Vmp+Imp*rs)/a) + Gsh - Imp/(Vmp-Imp*rs)
    grid = np.linspace(0, 0.999*(Voc-Vmp)/Imp, 4001)
    r = np.array([sol(x)[2] for x in grid]); i = np.where((r[:-1] < 0) & (r[1:] >= 0))[0][0]
    rs = optimize.brentq(lambda x: sol(x)[2], grid[i], grid[i+1], xtol=1e-15, rtol=1e-15)
    I0, Gsh, _ = sol(rs); Iph = I0*np.expm1(Voc/a) + Voc*Gsh
    return dict(n=n, a=a, I0=I0, Rs=rs, Rsh=1/Gsh, Iph=Iph)
def voc_of(Iph, I0, a, Rs, Rsh):
    return optimize.brentq(lambda V: Iph - I0*np.expm1(V/a) - V/Rsh, 0, 100, xtol=1e-14, rtol=1e-15)
def i0_desoto(p, T):
    TK=T+273.15; Eg=1.121*(1-0.0002677*(TK-TR))
    return p['I0']*(TK/TR)**3*np.exp(1.121/(KQ*TR) - Eg/(KQ*TK))
def i0_ea(p, T, EA):
    TK=T+273.15
    return p['I0']*(TK/TR)**3*np.exp(EA/KQ*(1/TR-1/TK))
def voc_T(p, T, law):
    TK=T+273.15
    return voc_of(p['Iph']+AISC*(T-25), law(p,T), p['a']*TK/TR, p['Rs'], p['Rsh'])
fixv = lambda T: Voc*(1+BV*(T-25))
# De Soto n* (LS at -10,70)
def ss_desoto(n):
    p=stc(n); return sum((voc_T(p,T,i0_desoto)-fixv(T))**2 for T in (-10,70))
for n in [0.85,0.9,0.92,0.93,0.94,0.95,1.0]:
    print('n',n,'SS desoto',ss_desoto(n))
res = optimize.minimize_scalar(ss_desoto, bounds=(0.7,1.5), method='bounded', options={'xatol':1e-10})
print('De Soto n* =', res.x, 'SS', res.fun)
p=stc(res.x); print(p, [voc_T(p,T,i0_desoto)-fixv(T) for T in (-10,70)])
for n in [1.0,1.1,1.2,1.3]:
    p = stc(n)
    f = lambda EA: sum((voc_T(p,T,lambda pp,TT: i0_ea(pp,TT,EA))-fixv(T))**2 for T in (-10,70))
    r = optimize.minimize_scalar(f, bounds=(0.6,1.6), method='bounded', options={'xatol':1e-12})
    EA=r.x; law=lambda pp,TT: i0_ea(pp,TT,EA)
    rr=[voc_T(p,T,law)-fixv(T) for T in (-10,0,25,50,70)]
    sl=(voc_T(p,25.5,law)-voc_T(p,24.5,law))/45.75*100
    # pmpp coefficient
    def pmp(T):
        TK=T+273.15; Iph=p['Iph']+AISC*(T-25); I0=law(p,T); a=p['a']*TK/TR
        def I_of_V(V):
            return optimize.brentq(lambda I: Iph - I0*np.expm1((V+I*p['Rs'])/a) - (V+I*p['Rs'])/p['Rsh'] - I, -5, 25, xtol=1e-14)
        r=optimize.minimize_scalar(lambda V:-V*I_of_V(V), bounds=(30,46), method='bounded', options={'xatol':1e-10})
        return -r.fun
    g=(pmp(26)-pmp(24))/2/pmp(25)*100
    print('n %.2f Rs %.6f Rsh %.3f EA %.6f eV resid(-10,0,25,50,70)=%s slope25 %.5f %%/C  gammaPmp %.4f %%/C Pmp %.4f'%(n,p['Rs'],p['Rsh'],EA,np.round(rr,5),sl,g,pmp(25)))
