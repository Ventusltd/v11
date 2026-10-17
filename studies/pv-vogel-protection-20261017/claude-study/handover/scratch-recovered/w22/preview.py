import math
from scipy.optimize import brentq
k=1.380649e-23; q=1.602176634e-19; T=298.15; Vt=k*T/q
N=1.3*22; Rs=0.02; Rsh=500.0; Voc=45.75/3; Isc=18.4
nVt=N*Vt
IS=(Isc - Voc/Rsh)/math.expm1(Voc/nVt)
print("Vt",Vt,"nVt",nVt,"IS",IS)
# bypass: N=1.1 RS=0.005, V(17A)=0.45
Nb=1.1; RSb=0.005
ISb=17/math.expm1((0.45-RSb*17)/(Nb*Vt))
print("ISb",ISb)
def vd2(i): return Nb*Vt*math.log1p(i/ISb)+RSb*i if i>0 else 0.0
def vcell(ib, iph):  # internal cell voltage giving branch current ib
    f=lambda v: iph - IS*math.expm1(v/nVt) - v/Rsh - ib
    return brentq(f,-50,40)
def vss(ib,iph): return vcell(ib,iph)-Rs*ib
# MPP of substring
import numpy as np
for G in (1000,500):
    iph=18.4*G/1000
    best=max(((vss(i,iph)*i,i) for i in np.linspace(0.01,iph-1e-6,20000)))
    print("G",G,"Pmpp_ss",best[0],"Impp",best[1],"Vmpp",vss(best[1],iph),"Voc",vss(0,iph))
# string op with node 1143.9 and Rloop
R=2*936*3.39e-3; L=936*0.713e-6
print("R",R,"L",L)
for G in (1000,500):
    iph=18.4*G/1000
    f=lambda I: 90*vss(I,iph) - R*I - 1143.9
    I0=brentq(f,0.001,iph-1e-9)
    print("G",G,"I0",I0,"Varr",90*vss(I0,iph),"Vss",vss(I0,iph))
    # incremental resistance
    d=1e-4; r=-(90*vss(I0+d,iph)-90*vss(I0-d,iph))/(2*d)
    print("  r_string",r)
    for gap in (1,3):
        for a in (12,15,20):
            K=a+0.534*gap
            g=lambda ib: vss(ib,iph)+vd2(I0-ib) - K*ib**0.12
            ib=brentq(g,1e-6,I0-1e-6)
            print(f"   gap{gap} a{a} K{K:.3f} Iarc {ib:.4f} Vgap {K*ib**0.12:.4f} P {K*ib**1.12:.3f} ID2 {I0-ib:.3f}")
        # boundary a*
        vg=vss(0.5,iph)+vd2(I0-0.5)
        astar=vg/0.5**0.12-0.534*gap
        print("   a* gap",gap,astar, "Vgap@Imin",vg)
