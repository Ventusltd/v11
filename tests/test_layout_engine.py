import unittest
from v11_simulation.layout import fill_rectangle,move_module,rotate_module,assign_strings,validate_layout,LayoutError

class LayoutTests(unittest.TestCase):
 def base(self,limit=24): return fill_rectangle(boundary={'x_min':0,'y_min':0,'x_max':20,'y_max':12},module_width_m=1,module_height_m=2,gap_x_m=.1,gap_y_m=.1,obstacles=[{'id':'O1','x_min':8,'x_max':10,'y_min':4,'y_max':8}],limit=limit)
 def test_fill_is_valid(self):
  layout=self.base(); self.assertEqual(validate_layout(layout),[]); self.assertEqual(len(layout['modules']),24)
 def test_obstacle_excluded(self):
  layout=self.base(100); self.assertEqual(validate_layout(layout),[])
 def test_move_snaps(self):
  layout=self.base(1); moved=move_module(layout,'MOD-0001',2.26,2.24,snap_m=.05); self.assertEqual(moved['modules'][0]['x_m'],2.25)
 def test_invalid_move_rejected(self):
  with self.assertRaises(LayoutError): move_module(self.base(2),'MOD-0001',-1,-1)
 def test_rotation_validated(self):
  layout=self.base(1); rotated=rotate_module(layout,'MOD-0001'); self.assertEqual(rotated['modules'][0]['rotation_deg'],90)
 def test_strings_cover_all_modules(self):
  layout=assign_strings(self.base(24),modules_per_string=6); self.assertEqual(len({m['string_id'] for m in layout['modules']}),4)
 def test_deterministic_fill(self): self.assertEqual(self.base(),self.base())

if __name__=='__main__': unittest.main()
