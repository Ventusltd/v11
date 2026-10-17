import numpy as np
from scipy.integrate import simpson as sp_simpson, trapezoid as sp_trap
def trap(t,f):
    t=np.asarray(t,float); f=np.asarray(f,float)
    return float(np.sum(0.5*(f[1:]+f[:-1])*np.diff(t)))
def simpson_nonuniform(t,f):
    t=np.asarray(t,float); f=np.asarray(f,float)
    n=len(t)-1  # intervals
    h=np.diff(t)
    tot=0.0
    m = n if n%2==0 else n-1
    for i in range(0,m,2):
        h0,h1=h[i],h[i+1]
        s=h0+h1
        tot += s/6.0*((2.0-h1/h0)*f[i] + s*s/(h0*h1)*f[i+1] + (2.0-h0/h1)*f[i+2])
    if n%2==1:
        # last interval: quadratic through last three points, integrate over last interval only
        h0,h1=h[-2],h[-1]
        a=(2*h1**2+3*h0*h1)/(6*(h0+h1)); b=(h1**2+3*h0*h1)/(6*h0); c=h1**3/(6*h0*(h0+h1))
        tot += a*f[-1]+b*f[-2]-c*f[-3]
    return tot
d=np.loadtxt('out.dat',skiprows=1)
t=d[:,0]; ia=d[:,1]; vg=d[:,2]; em=d[:,8]
P=vg*ia
print("trap",trap(t,P),"scipy trap",sp_trap(P,x=t))
print("simp",simpson_nonuniform(t,P),"scipy simp",sp_simpson(P,x=t))
print("solver",em[-1]*1e-3)
# max weight magnitude
h=np.diff(t); r=h[1::2][:len(h[0::2])]/h[0::2][:len(h[1::2])]
print("pair ratio range", r.min(), r.max())
