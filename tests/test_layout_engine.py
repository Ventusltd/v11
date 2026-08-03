import time
import unittest
from v11_simulation.layout import fill_rectangle, move_module, rotate_module, assign_strings, validate_layout, LayoutError

class LayoutTests(unittest.TestCase):
    def base(self, limit=24):
        return fill_rectangle(boundary={'x_min':0,'y_min':0,'x_max':20,'y_max':12}, module_width_m=1, module_height_m=2, gap_x_m=.1, gap_y_m=.1, obstacles=[{'id':'O1','x_min':8,'x_max':10,'y_min':4,'y_max':8}], limit=limit)

    def isolated(self):
        return {'schema_version':'globalgrid2050.v11.module-layout.v1','boundary':{'x_min':0,'y_min':0,'x_max':10,'y_max':10},'obstacles':[],'modules':[{'id':'MOD-0001','x_m':5.0,'y_m':5.0,'width_m':1.0,'height_m':2.0,'rotation_deg':0,'row':0,'column':0,'string_id':None}]}

    def test_fill_is_valid(self):
        layout=self.base(); self.assertEqual(validate_layout(layout),[]); self.assertEqual(len(layout['modules']),24)

    def test_obstacle_excluded(self):
        layout=self.base(100); self.assertEqual(validate_layout(layout),[])

    def test_move_snaps(self):
        moved=move_module(self.isolated(),'MOD-0001',5.26,5.24,snap_m=.05); self.assertEqual(moved['modules'][0]['x_m'],5.25); self.assertEqual(moved['modules'][0]['y_m'],5.25)

    def test_boundary_flush_noop_survives_snap(self):
        layout=fill_rectangle(boundary={'x_min':0,'y_min':0,'x_max':10,'y_max':10},module_width_m=1.134,module_height_m=2.384,limit=1)
        original=layout['modules'][0]
        moved=move_module(layout,original['id'],original['x_m'],original['y_m'],snap_m=.05)
        self.assertEqual(moved['modules'][0]['x_m'],original['x_m'])
        self.assertEqual(moved['modules'][0]['y_m'],original['y_m'])
        self.assertEqual(validate_layout(moved),[])

    def test_colliding_move_rejected(self):
        with self.assertRaises(LayoutError): move_module(self.base(2),'MOD-0001',1.6,1.0)

    def test_outside_move_rejected(self):
        with self.assertRaises(LayoutError): move_module(self.base(2),'MOD-0001',-1,-1)

    def test_rotation_validated(self):
        rotated=rotate_module(self.isolated(),'MOD-0001'); self.assertEqual(rotated['modules'][0]['rotation_deg'],90); self.assertEqual(validate_layout(rotated),[])

    def test_invalid_boundary_rotation_rejected(self):
        with self.assertRaises(LayoutError): rotate_module(self.base(1),'MOD-0001')

    def test_strings_cover_all_modules(self):
        layout=assign_strings(self.base(24),modules_per_string=6); self.assertEqual(len({m['string_id'] for m in layout['modules']}),4)

    def test_deterministic_fill(self):
        self.assertEqual(self.base(),self.base())

    def test_720_module_fill_is_bounded(self):
        start=time.perf_counter(); layout=fill_rectangle(boundary={'x_min':0,'y_min':0,'x_max':90,'y_max':60},module_width_m=1.134,module_height_m=2.384,gap_x_m=.03,gap_y_m=.05,limit=720); elapsed=time.perf_counter()-start
        self.assertEqual(len(layout['modules']),720); self.assertEqual(validate_layout(layout),[]); self.assertLess(elapsed,5.0)

if __name__=='__main__': unittest.main()
