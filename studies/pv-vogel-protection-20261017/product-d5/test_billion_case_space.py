"""D5 tests: exact input accounting, Kuiper laws and falsification controls.

No actual PV hardware, SPICE, CUDA, or IEC claims are tested here.
"""
import math
import unittest
from billion_case_space import (
 TOTAL,RADICES,AXES,CODES,KINDS,FAILURES,
 FIBONACCI_44,decode_offsets,encode_offsets,case_at,case_tag,
 fibonacci_index,live_kuiper_xy,legacy_wafer_xy,explicit_corner_ids,
 review_sample,classify,case_evidence,summary
)

class BillionD5Tests(unittest.TestCase):
 def test_exact_distinct_space_not_simulations(self):
  self.assertEqual(TOTAL,1_073_741_824)
  self.assertEqual(len(RADICES),9)
  self.assertEqual(math.prod(RADICES),TOTAL)
  self.assertEqual(summary()["performed_case_evaluations"],0)
  self.assertEqual(summary()["actual_spice_waveforms"],0)
 def test_all_corner_roundtrips(self):
  corners=explicit_corner_ids()
  self.assertEqual(len(corners),512)
  self.assertEqual(len(set(corners)),512)
  for index in corners:
   self.assertEqual(encode_offsets(decode_offsets(index)),index)
 def test_coprime_fibonacci_stride(self):
  self.assertEqual(FIBONACCI_44,701408733)
  self.assertEqual(math.gcd(FIBONACCI_44,TOTAL),1)
  self.assertEqual(len(set(fibonacci_index(i) for i in range(10000))),10000)
 def test_full_stride_does_not_alias_first_large_steps(self):
  for step in (0,1,2,10,100000,TOTAL-1):
   self.assertEqual((fibonacci_index(step)+FIBONACCI_44)%TOTAL,
                    fibonacci_index((step+1)%TOTAL))
 def test_all_axis_values_exact_and_bounded(self):
  self.assertEqual(RADICES,(8,8,8,16,16,16,16,16,2))
  self.assertEqual(case_at(0)["architecture"],KINDS[0])
  self.assertEqual(case_at(TOTAL-1)["component_state"],FAILURES[-1])
 def test_illegal_index_rejected(self):
  for k in (-1,TOTAL,True,1.2,None):
   with self.assertRaises((ValueError,TypeError)):decode_offsets(k)
  with self.assertRaises(ValueError):encode_offsets((0,0))
  with self.assertRaises(ValueError):fibonacci_index(-1)
 def test_local_address_is_not_global_kuiper_key(self):
  e=case_evidence(1)
  self.assertEqual(e["case_id"],"D5:0000000001")
  self.assertIn("UNRESERVED",e["kuiper_namespace"])
  self.assertIsNone(e["physical_fault_energy_j"])
 def test_live_kuiper_hash_and_radius(self):
  x,y=live_kuiper_xy(0)
  self.assertAlmostEqual(x,math.sqrt(.5))
  self.assertAlmostEqual(y,0)
  for k in (1,2,100,2**24+1,2**32,2**32+1,TOTAL-1):
   x,y=live_kuiper_xy(k)
   self.assertAlmostEqual(math.hypot(x,y),math.sqrt(k+.5),places=6)
  a=live_kuiper_xy(1)
  b=live_kuiper_xy(2**32+1)
  self.assertNotEqual(a,b) # angle wraps; radial location does not
 def test_legacy_is_not_live(self):
  a=legacy_wafer_xy(25)
  b=live_kuiper_xy(25)
  self.assertNotAlmostEqual(a[0],b[0],places=3)
 def test_fault_all_cases_are_labels_not_efuse_efficacy(self):
  e=case_evidence(7)
  self.assertIn("NOT_EVALUATED",e["actual_insulation_status"])
  self.assertTrue(all("SAFE" not in x or "NOT_SAFE" in x for x in CODES.values()))
 def test_healthy_device_stress_hard_flag(self):
  # architecture=single_shunt, failure=healthy; at voltage=1500 > local 80V
  vals=[0]*9
  vals[0]=3;vals[6]=15
  idx=encode_offsets(vals)
  self.assertEqual(classify(idx),1)
 def test_device_failure_flag(self):
  z=[0]*9
  z[0]=3;z[2]=3
  self.assertEqual(classify(encode_offsets(z)),3)
 def test_no_unconditional_success(self):
  vals=[0]*9
  vals[0]=3;vals[3]=13;vals[5]=0
  code=classify(encode_offsets(vals))
  self.assertIn(code,CODES)
  self.assertEqual(case_evidence(0)["evidence_grade"],"synthetic_algebra_preflight_only")
 def test_sample_combines_all_corners_and_fibonacci(self):
  s=review_sample(4096)
  self.assertEqual(len(s),4096)
  self.assertEqual(len(set(s)),4096)
  self.assertEqual(set(explicit_corner_ids())-set(s),set())
 def test_strict_equality_voltage_boundary(self):
  z=[0]*9;z[0]=3;z[6]=10 # imposed 80V = hypothetical local rating 80V
  self.assertEqual(classify(encode_offsets(z)),1)
 def test_no_guessed_iec_creepage(self):
  s=str(summary()).lower()
  self.assertNotIn("clearance_mm':",s)
  self.assertNotIn("certified",s)
if __name__=="__main__":unittest.main(verbosity=2)
