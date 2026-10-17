import unittest
from pv_module import Substring, module_at_current, module_open_circuit, module_maximum_power

class PVModuleD1Tests(unittest.TestCase):
    def test_stc_voltage_at_max_current(self):
        q = module_at_current(17.31)
        self.assertAlmostEqual(q['module_voltage_v'], 38.13, delta=0.005)
        self.assertAlmostEqual(q['module_power_w'],660.03,delta=0.1)
    def test_stc_open_circuit(self):
        self.assertAlmostEqual(module_open_circuit(),45.75,delta=0.01)
    def test_stc_isc(self):
        q = module_at_current(18.4)
        self.assertAlmostEqual(q['module_voltage_v'],0,delta=0.01)
    def test_stc_mpp_solution(self):
        q = module_maximum_power()
        self.assertAlmostEqual(q['current_a'],17.31,delta=0.01)
        self.assertAlmostEqual(q['module_power_w'],660.03,delta=0.1)
    def test_bypass_stays_off_in_unshaded_module(self):
        q=module_at_current(17.31)
        self.assertTrue(all(s['bypass_current_a']==0 for s in q['substrings']))
    def test_shaded_substring_bypasses(self):
        q=module_at_current(17.31,(1000,100,1000))
        x=q['substrings'][1]
        self.assertLess(x['voltage_v'],-.45)
        self.assertGreater(x['bypass_current_a'],15)
        self.assertLess(x['bypass_current_a'],17.31)
        self.assertAlmostEqual(x['cell_current_a']+x['bypass_current_a'],17.31,delta=1e-5)
    def test_partial_shade_decreases_power(self):
        self.assertLess(module_maximum_power((1000,100,1000))['module_power_w'],module_maximum_power()['module_power_w'])
    def test_no_irradiance(self):
        q=module_at_current(17.31,(0,0,0))
        self.assertTrue(all(s['bypass_current_a']>17 for s in q['substrings']))
        self.assertLess(q['module_voltage_v'],0)
    def test_temperature_voc(self):
        self.assertGreater(module_open_circuit(cell_c=-10), module_open_circuit())
        self.assertLess(module_open_circuit(cell_c=70), module_open_circuit())
    def test_voltage_monotonic_with_current_at_stc(self):
        pts=[module_at_current(i)['module_voltage_v'] for i in [0,3,8,13,17.31,18.4,22]]
        self.assertTrue(all(a>b for a,b in zip(pts,pts[1:])))
    def test_bypass_current_positive_only(self):
        s=Substring()
        self.assertGreater(s.current_at_voltage(-1),s.cell_branch_current(-1))
        self.assertAlmostEqual(s.current_at_voltage(0),s.cell_branch_current(0))
    def test_irradiance_zero_with_high_voltage(self):
        q=module_at_current(0,(0,0,0))
        self.assertLess(q['module_voltage_v'],1)
    def test_bad_irradiance_fails(self):
        with self.assertRaises(ValueError):module_at_current(10,(1000,-1,1000))
        with self.assertRaises(ValueError):module_at_current(10,(1000,1000))
    def test_bad_temperature_fails(self):
        with self.assertRaises(ValueError):module_open_circuit(cell_c=125)
    def test_negative_current_out_of_scope(self):
        with self.assertRaises(ValueError):module_at_current(-1)
    def test_shorttime_bypass_diode_watts(self):
        z=module_at_current(17.31,(1000,100,1000))['substrings'][1]
        p=(-z['voltage_v'])*z['bypass_current_a']
        self.assertGreater(p,8)
        self.assertLess(p,12)
if __name__=='__main__':unittest.main(verbosity=2)
