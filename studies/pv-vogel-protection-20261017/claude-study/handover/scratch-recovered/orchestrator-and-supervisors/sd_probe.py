import math
from scipy.optimize import fsolve
K_B=1.380649e-23; Q_E=1.602176634e-19
voc,isc,vmpp,impp,ns=45.75,18.4,38.13,17.31,66
for n in [0.9,1.0,1.1,1.2,1.3,1.4,1.5]:
    a=n*ns*K_B*298.15/Q_E
    def eqs(x):
        iph,li0,rs,lrsh=x; i0=math.exp(li0); rsh=math.exp(lrsh)
        esc=math.exp(isc*rs/a); eoc=math.exp(voc/a); emp=math.exp((vmpp+impp*rs)/a)
        G=i0/a*emp+1/rsh
        return [iph-i0*(esc-1)-isc*rs/rsh-isc, iph-i0*(eoc-1)-voc/rsh,
                iph-i0*(emp-1)-(vmpp+impp*rs)/rsh-impp, impp-vmpp*G/(1+rs*G)]
    x0=[isc, math.log(isc)-voc/a, 0.2, math.log(500.)]
    sol,info,ier,msg=fsolve(eqs,x0,full_output=True,xtol=1e-14)
    print(n, ier, [round(v,6) for v in sol], 'Rsh', round(math.exp(sol[3]),2), 'res', max(abs(r) for r in eqs(sol)))
