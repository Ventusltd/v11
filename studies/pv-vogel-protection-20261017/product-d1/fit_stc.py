"""Optional independently reproducible STC parameter fit (requires SciPy).

The data points are provisional module fixture numbers, NOT OEM measured IV curves.
Three 22-cell substrings with parallel half-cell branches are assumed.
Ideality 1.3 is fixed to make four constraints determine four unknowns.
"""
import math
import json
from scipy.optimize import least_squares
from pv_module import K_B, Q_E

def fit():
    v_oc=45.75/3
    v_mp=38.13/3
    i_sc=18.4
    i_mp=17.31
    a=22*1.3*K_B*298.15/Q_E
    def residual(x):
        iph,rs,rsh,logi0=x
        i0=math.exp(logi0)
        def mismatch(v,i):
            z=math.exp(min(70,(v+i*rs)/a))
            return iph-i0*(z-1)-(v+i*rs)/rsh-i
        vj=v_mp+i_mp*rs
        g=i0*math.exp(min(70,vj/a))/a+1/rsh
        dp_dv=i_mp-v_mp*g/(1+g*rs)
        return [mismatch(0,i_sc),mismatch(v_oc,0),mismatch(v_mp,i_mp),dp_dv]
    x0=[18.41,.024,220,math.log(1.8e-8)]
    lo=[18.0,0,20,-45];hi=[25,.4,1e8,-5]
    s=least_squares(residual,x0,bounds=(lo,hi),
                    xtol=1e-13,ftol=1e-13,gtol=1e-13,max_nfev=2000)
    p=s.x
    return {
         'status':'FOUR_POINT_STC_FIT_TO_PROVISIONAL_FIXTURE_NOT_DEVICE_VALIDATION',
         'fit_fixed_parameters':{'substrings':3,'cells_per_substring':22,'ideality':1.3},
         'iph_stc_a':float(p[0]),'rs_ohm':float(p[1]),
         'rsh_ohm':float(p[2]),'i0_stc_a':float(math.exp(p[3])),
         'max_abs_constraint_error':float(max(abs(v) for v in s.fun)),
         'assumed_module_points':{'voc_stc_v':45.75,'isc_a':18.4,
                                  'vmpp_v':38.13,'impp_a':17.31}}
if __name__=='__main__':
    print(json.dumps(fit(),indent=2))
