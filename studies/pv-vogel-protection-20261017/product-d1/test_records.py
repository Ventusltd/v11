import csv
import json
import unittest
from pathlib import Path
from pv_module import module_at_current

class ProductRecordsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).resolve().parent
        cls.topology=json.loads((p/'protection-node-manifest.json').read_text(encoding='utf-8'))
        with (p/'component-selection-record.csv').open(newline='',encoding='utf-8') as f:
            cls.rows=list(csv.DictReader(f))
    def test_three_series_substrings(self):
        edges=self.topology['electrically_series_substrings']
        self.assertEqual([x[2] for x in edges],['S1','S2','S3'])
        self.assertEqual(edges[0][0],'J_MINUS')
        self.assertEqual(edges[2][1],'J_PLUS')
    def test_bypass_antiparallel_orientation(self):
        edges={x[2]:x[:2] for x in self.topology['electrically_series_substrings']}
        for d in self.topology['bypass_diodes']:
            self.assertEqual([d['anode'],d['cathode']],edges[d['parallel_to']])
    def test_candidate_switches_no_hardware_claim(self):
        self.assertEqual(len(self.topology['proposed_switch_positions']),4)
        self.assertTrue(all('HOLD' in x['status'] or 'RESEARCH' in x['status'] for x in self.topology['proposed_switch_positions']))
    def test_real_manufacturer_links(self):
        vendors=[r for r in self.rows if r['manufacturer_or_origin']!='UNSELECTED']
        self.assertGreaterEqual(len(vendors),4)
        self.assertTrue(all(r['primary_source'].startswith('https://') for r in vendors))
    def test_no_approved_parts_in_candidate_list(self):
        self.assertTrue(all(r['status_for_1500V_PV'].startswith(('HOLD','REJECT')) for r in self.rows))
    def test_dissipation_budget(self):
        self.assertAlmostEqual(0.005*660/17.31**2,.0110085,delta=1e-5)
    def test_shaded_diode_heat_is_explicit(self):
        s=module_at_current(17.31,(1000,100,1000))['substrings'][1]
        p=-s['voltage_v']*s['bypass_current_a']
        self.assertGreater(p,9)
        self.assertLess(p,10)
    def test_component_ids_unique(self):
        ids=[r['record_id'] for r in self.rows]
        self.assertEqual(len(ids),len(set(ids)))
if __name__=='__main__':unittest.main(verbosity=2)
