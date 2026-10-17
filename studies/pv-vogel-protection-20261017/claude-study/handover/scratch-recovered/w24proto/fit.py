import math, numpy as np
from scipy.optimize import fsolve, brentq
Voc, Isc, Vmp, Imp = 45.75, 18.4, 38.13, 17.31
Ns=66; Vt=1.380649e-23*298.15/1.602176634e-19
def res(x):
    Iph, lnI0, n, Rs = x
    I0=math.exp(lnI0); a=n*Ns*Vt
    f=lambda V,I: Iph - I0*(math.exp((V+I*Rs)/a)-1) - I
    e1=f(0,Isc); e2=f(Voc,0); e3=f(Vmp,Imp)
    E=math.exp((Vmp+Imp*Rs)/a); g=I0*E/a
    dIdV=-g/(1+Rs*g)
    e4=Imp+Vmp*dIdV
    return [e1,e2,e3,e4]
best=None
for n0 in (1.0,1.2,1.4,1.6):
  for Rs0 in (0.02,0.05,0.1):
    x0=[Isc, math.log(1e-9), n0, Rs0]
    x,info,ier,msg=fsolve(res,x0,full_output=True,xtol=1e-14)
    r=max(abs(v) for v in res(x))
    print(n0,Rs0,ier,x, math.exp(x[1]), r)
