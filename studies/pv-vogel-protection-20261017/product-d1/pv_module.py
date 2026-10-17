"""Research PV module with 3 bypass-protected substrings, SI units.

NOT a device-verified solar model, certified circuit, or an arc physics model.
STC 5-parameter substring fit with n=1.3 prescribed and Iph/I0/Rs/Rsh
fitted to a provisional 660 W module's Isc, Voc, Imp, Vmp and dP/dV=0.
Bypass is a simplified Schottky Vf + rd branch, NOT a measured diode curve.
"""
from dataclasses import dataclass
import math

K_B = 1.380649e-23
Q_E = 1.602176634e-19
REF_K = 298.15
EG_J = 1.121 * Q_E

@dataclass(frozen=True)
class Substring:
    cells_in_series: int = 22
    ideality: float = 1.3
    iph_stc_a: float = 18.402067
    i0_stc_a: float = 1.778242293090851e-8
    rs_ohm: float = .0246039952
    rsh_ohm: float = 219.017492
    isc_temp_coefficient_per_k: float = .0005  # unverified fixture assumption
    bypass_vf_v: float = .45               # unverified diode approximation
    bypass_rd_ohm: float = .01             # unverified diode approximation

    def at_conditions(self, irradiance_w_m2=1000.0, cell_c=25.0):
        if not 0 <= irradiance_w_m2 <= 1500 or not -40 <= cell_c <= 100:
            raise ValueError('outside initial screened G,T interval')
        T = 273.15 + cell_c
        a = self.cells_in_series * self.ideality * K_B * T / Q_E
        iph = self.iph_stc_a * irradiance_w_m2/1000 * (1+self.isc_temp_coefficient_per_k*(cell_c-25))
        i0 = self.i0_stc_a * (T/REF_K)**3 * math.exp(EG_J/(self.ideality*K_B)*(1/REF_K - 1/T))
        return a, iph, i0

    def cell_branch_current(self, voltage_v, irradiance_w_m2=1000.0, cell_c=25.0):
        """Five-parameter single-diode I(V), bisection on implicit Rs current."""
        a,iph,i0 = self.at_conditions(irradiance_w_m2,cell_c)
        def residual(i):
            vj=voltage_v + i*self.rs_ohm
            z=min(90,max(-90,vj/a))
            return iph - i0*math.expm1(z) - vj/self.rsh_ohm - i
        low,high=-100.,100.
        for _ in range(20):
            if residual(low)>0: break
            low*=2
        if residual(low)*residual(high)>0:
            raise ValueError('current not bracketed; model outside validated range')
        for _ in range(64):
            mid=(low+high)/2
            if residual(mid)>0:
                low=mid
            else:
                high=mid
        return (low+high)/2

    def current_at_voltage(self, voltage_v, irradiance_w_m2=1000.0, cell_c=25.0):
        ipv=self.cell_branch_current(voltage_v,irradiance_w_m2,cell_c)
        ibyp=max(0.0,(-voltage_v-self.bypass_vf_v)/self.bypass_rd_ohm)
        return ipv+ibyp

    def at_current(self, current_a, irradiance_w_m2=1000.0, cell_c=25.0):
        """Return v, bypass-current, cell-current for a chosen series current."""
        if current_a < 0 or current_a > 50:
            raise ValueError('current outside first-quadrant screening domain')
        low,high=-5.0,35.0
        if self.current_at_voltage(low,irradiance_w_m2,cell_c) < current_a:
            raise ValueError('current beyond bypass branch bracket')
        if self.current_at_voltage(high,irradiance_w_m2,cell_c) > current_a:
            raise ValueError('voltage beyond bracket')
        for _ in range(55):
            v=(low+high)/2
            if self.current_at_voltage(v,irradiance_w_m2,cell_c)>current_a:
                low=v
            else:
                high=v
        v=(low+high)/2
        return {'voltage_v':v,
                'cell_current_a':self.cell_branch_current(v,irradiance_w_m2,cell_c),
                'bypass_current_a':max(0.0,(-v-self.bypass_vf_v)/self.bypass_rd_ohm)}


def module_at_current(current_a, irradiances=(1000.,1000.,1000.), cell_c=25.0):
    if len(irradiances) != 3: raise ValueError('exactly three substrings')
    model=Substring()
    subst=[model.at_current(current_a,g,cell_c) for g in irradiances]
    v=sum(x['voltage_v'] for x in subst)
    return {'module_voltage_v':v,'module_power_w':v*current_a,
            'current_a':current_a,'substrings':subst}


def module_open_circuit(irradiances=(1000.,1000.,1000.),cell_c=25.):
    return module_at_current(0,irradiances,cell_c)['module_voltage_v']


def module_maximum_power(irradiances=(1000.,1000.,1000.), cell_c=25.):
    # Golden-section optimisation of P(I), uses objective only, no magic Vogel search.
    lo,hi=0.,20.0
    gr=(math.sqrt(5)-1)/2
    c=hi-gr*(hi-lo);d=lo+gr*(hi-lo)
    for _ in range(60):
        pc=module_at_current(c,irradiances,cell_c)['module_power_w']
        pd=module_at_current(d,irradiances,cell_c)['module_power_w']
        if pc>pd:
            hi=d;d=c;c=hi-gr*(hi-lo)
        else:
            lo=c;c=d;d=lo+gr*(hi-lo)
    return module_at_current((hi+lo)/2,irradiances,cell_c)

if __name__=='__main__':
    import json
    out={'stc_at_imp':module_at_current(17.31),
         'stc_voc':module_open_circuit(),
         'stc_maximum_power':module_maximum_power(),
         'shaded_10pct_at_17_31a':module_at_current(17.31,(1000,100,1000)),
         'shaded_10pct_mpp':module_maximum_power((1000,100,1000)),
         'cold_voc_minus10c':module_open_circuit(cell_c=-10),
         'hot_voc_70c':module_open_circuit(cell_c=70),
         'explicit_limitations':['module internal structure assumed', 'no avalanche or breakdown model',
           'bypass diode is piecewise approximation','no transient capacitance',
           'no hotspot/thermal model','no actual OEM IV or bypass diode trace']}
    print(json.dumps(out,indent=2))
