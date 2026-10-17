import math
from scipy.optimize import fsolve, brentq
k=1.380649e-23; q=1.602176634e-19
def Vt(Tc): return k*(Tc+273.15)/q
Voc,Isc,Vmp,Imp=45.75,18.4,38.13,17.31
Ns=66; Rsh=1500.0
def resid4(Iph,I0,n,Rs,T=25):
    a=n*Ns*Vt(T)
    f1=Iph-I0*(math.exp(Isc*Rs/a)-1)-Isc*Rs/Rsh-Isc
    f2=Iph-I0*(math.exp(Voc/a)-1)-Voc/Rsh
    e=math.exp((Vmp+Imp*Rs)/a)
    f3=Iph-I0*(e-1)-(Vmp+Imp*Rs)/Rsh-Imp
    g=I0*e/a+1/Rsh
    f4=Imp-Vmp*g/(1+Rs*g)
    return f1,f2,f3,f4
for n in (1.0,1.1,1.2,1.3):
    def eq3(x):
        Iph,lnI0,Rs=x
        r=resid4(Iph,math.exp(lnI0),n,Rs)
        return r[:3]
    a=n*Ns*Vt(25)
    x,info,ier,msg=fsolve(eq3,[Isc,math.log(Isc/math.exp(Voc/a)),0.1],full_output=True,xtol=1e-14)
    Iph,I0,Rs=x[0],math.exp(x[1]),x[2]
    r=resid4(Iph,I0,n,Rs)
    # find actual MPP of fitted curve
    def I_of_V(V):
        return brentq(lambda I: Iph-I0*(math.exp((V+I*Rs)/a)-1)-(V+I*Rs)/Rsh-I,-50,50)
    import numpy as np
    Vs=np.linspace(30,45,3001); P=[V*I_of_V(V) for V in Vs]; i=int(np.argmax(P))
    print(f"n={n}: ier={ier} Iph={Iph:.5f} I0={I0:.4e} Rs={Rs:.5f} res3={max(abs(v) for v in r[:3]):.1e} dPdV-res={r[3]:.4f}  fitted MPP V={Vs[i]:.3f} P={P[i]:.2f} (fixture 660.0)")
