import math, json
from scipy.optimize import fsolve
FX=json.load(open('/home/claude/v11/studies/pv-vogel-protection-20261017/claude-study/fixture/system-fixture.json'))
m=FX['module']; Voc,Isc,Vmp,Imp=m['voc_stc_v'],m['isc_a'],m['vmpp_v'],m['impp_a']
Ns=66; VT=1.380649e-23*298.15/1.602176634e-19
for n in (1.0,1.1,1.2,1.3,1.4):
    a=n*Ns*VT
    def elim(Rs,Rsh):
        I0=(Isc+Isc*Rs/Rsh-Voc/Rsh)/(math.exp(Voc/a)-math.exp(Isc*Rs/a))
        Iph=I0*(math.exp(Voc/a)-1)+Voc/Rsh
        return Iph,I0
    def F(x):
        Rs,Rsh=x; Iph,I0=elim(Rs,Rsh)
        e=math.exp((Vmp+Imp*Rs)/a); g=I0*e/a+1/Rsh
        return [Iph-I0*(e-1)-(Vmp+Imp*Rs)/Rsh-Imp, -g/(1+Rs*g)+Imp/Vmp]
    best=None
    for Rs0 in (0.02,0.05,0.1,0.2,0.3):
        for Rsh0 in (50.,100.,300.,1000.,3000.):
            x,info,ier,msg=fsolve(F,[Rs0,Rsh0],xtol=1e-13,full_output=True)
            r=max(abs(v) for v in F(x))
            if ier==1 and x[0]>0 and x[1]>0 and (best is None or r<best[2]): best=(x[0],x[1],r)
    if best: 
        Iph,I0=elim(best[0],best[1]); print(n, 'Rs',best[0],'Rsh',best[1],'res',best[2],'Iph',Iph,'I0',I0)
    else: print(n,'no positive solution')
