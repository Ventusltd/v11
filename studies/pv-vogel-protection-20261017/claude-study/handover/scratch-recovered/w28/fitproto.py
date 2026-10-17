import math, json
import numpy as np
from scipy.optimize import fsolve, brentq
k=1.380649e-23; q=1.602176634e-19
T=298.15; Vt=k*T/q
Voc,Isc,Vmp,Imp=45.75,18.4,38.13,17.31
Ns=66; Rsh=1500.0
def eqs(x):
    Iph,lnI0,n,Rs=x
    I0=math.exp(lnI0); a=n*Ns*Vt
    f1=Iph-I0*(math.exp(Isc*Rs/a)-1)-Isc*Rs/Rsh-Isc
    f2=Iph-I0*(math.exp(Voc/a)-1)-Voc/Rsh
    e=math.exp((Vmp+Imp*Rs)/a)
    f3=Iph-I0*(e-1)-(Vmp+Imp*Rs)/Rsh-Imp
    g=I0*e/a+1/Rsh
    f4=Imp-Vmp*g/(1+Rs*g)
    return [f1,f2,f3,f4]
best=None
for n0 in (0.9,1.0,1.1,1.2,1.3,1.5):
  for Rs0 in (0.05,0.1,0.2,0.3):
    a=n0*Ns*Vt
    I00=Isc/math.exp(Voc/a)
    x,info,ier,msg=fsolve(eqs,[Isc,math.log(I00),n0,Rs0],full_output=True,xtol=1e-14)
    r=max(abs(v) for v in eqs(x))
    print(n0,Rs0,ier,x,math.exp(x[1]),r)
    if ier==1 and x[3]>0 and (best is None or r<best[1]): best=(x,r)
print("BEST",best, math.exp(best[0][1]))
