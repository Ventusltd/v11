import math
from scipy.optimize import brentq
K_B=1.380649e-23; Q_E=1.602176634e-19
voc,isc,vmpp,impp,ns=45.75,18.4,38.13,17.31,66
T=298.15
def params(n, rs, rsh):
    a=n*ns*K_B*T/Q_E
    i0=(isc-(voc-isc*rs)/rsh)/(math.exp(voc/a)-math.exp(isc*rs/a))
    iph=i0*(math.exp(voc/a)-1)+voc/rsh
    return a,i0,iph
def f_mpp(n,rs,rsh):
    a,i0,iph=params(n,rs,rsh)
    vd=vmpp+impp*rs
    return iph-i0*(math.exp(vd/a)-1)-vd/rsh-impp
def f_deriv(n,rs,rsh):
    a,i0,iph=params(n,rs,rsh)
    vd=vmpp+impp*rs
    G=i0/a*math.exp(vd/a)+1/rsh
    didv=-G/(1+rs*G)
    return impp+vmpp*didv
for n in [1.0,1.05,1.1,1.15,1.2,1.25,1.3,1.35,1.4]:
    # scan rs, for each find rsh solving f_mpp, then check deriv
    rows=[]
    for k in range(1,400):
        rs=k*0.001
        # f_mpp as function of rsh
        try:
            g=lambda lr: f_mpp(n,rs,math.exp(lr))
            lo,hi=math.log(1.0),math.log(1e9)
            if g(lo)*g(hi)>0:
                continue
            lr=brentq(g,lo,hi,xtol=1e-14)
            rows.append((rs,math.exp(lr),f_deriv(n,rs,math.exp(lr))))
        except (OverflowError,ZeroDivisionError,ValueError):
            pass
    sign_changes=[(rows[i],rows[i+1]) for i in range(len(rows)-1) if rows[i][2]*rows[i+1][2]<0]
    print(n, len(rows), rows[:1], rows[-1:] if rows else None, 'sign changes', [(round(a[0],3),round(a[1],1)) for a,b in sign_changes])
