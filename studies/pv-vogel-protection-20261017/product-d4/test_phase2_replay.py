"""Phase II evidence shortlist is reproducible and NEVER a safety verdict."""
import json
import tempfile
import unittest
from pathlib import Path
from phase2_replay import (
    STAR_SCHEMA,GRAPH_SCHEMA,FARADAY_SCHEMA,PRIORITY,research_priority,
    select_witnesses,graph_and_experiments,write,star_id
)
from billion_case_contract import simple_arithmetic_screen,scheme_sha256

class Phase2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=graph_and_experiments(pilot_n=192,limit=24)
    def test_nonempty_bounded_priorities(self):
        q=select_witnesses(pilot_n=192,limit=24)
        self.assertEqual(len(q),24)
        self.assertEqual(len({x['case_index'] for x in q}),24)
        self.assertGreater(max(research_priority(x) for x in q),0)
    def test_stars_are_stable(self):
        self.assertEqual(star_id(0),star_id(0))
        self.assertNotEqual(star_id(0),star_id(1))
        self.assertEqual(len(star_id(42).split(":")[1]),20)
    def test_graph_edges_do_not_dangle(self):
        g=self.data['graph']
        ids={n['id'] for n in g['nodes']}
        self.assertEqual(len(ids),len(g['nodes']))
        self.assertEqual(g['schema'],GRAPH_SCHEMA)
        for e in g['edges']:
            self.assertIn(e['from'],ids)
            self.assertIn(e['to'],ids)
    def test_no_green_or_validated_arc_conclusion(self):
        s=self.data['stars']
        self.assertEqual(len(s),24)
        self.assertTrue(all(x['schema']==STAR_SCHEMA for x in s))
        self.assertTrue(all(x['status'] in ('INPUT_CONTRADICTION','NUMERIC_ONLY') for x in s))
        self.assertTrue(all('arc quenching' in x['not_claimed'] for x in s))
        self.assertTrue(all(x['source']=='billion_case_contract.py' for x in s))
        self.assertNotIn('green',{n['rag'] for n in self.data['graph']['nodes']})
    def test_faraday_records_are_proposals_not_laboratory(self):
        a=self.data['faraday_proposals']
        self.assertEqual(len(a),24)
        self.assertTrue(all(x['schema']==FARADAY_SCHEMA for x in a))
        self.assertTrue(all(x['laboratory_test_performed'] is False for x in a))
        self.assertTrue(all(x['verdict']=='UNRESOLVED__NEEDS_PHYSICAL_SIMULATION' for x in a))
        self.assertEqual(len({x['experiment_id'] for x in a}),24)
    def test_phase2_declared_grid_versus_executed(self):
        r=self.data['receipt']
        self.assertEqual(r['actually_pilot_screened'],192)
        self.assertEqual(r['virtual_lattice_size_not_executed'],1_000_000_000)
        self.assertFalse(r['real_cuda_executed'])
        self.assertFalse(r['actual_spice_in_this_workflow'])
        self.assertTrue(r['no_risk_probabilities'])
        self.assertEqual(r['lattice_sha256'],scheme_sha256())
    def test_priority_is_followup_only(self):
        x=simple_arithmetic_screen(0)
        self.assertIn('ARC_PLASMA_AND_REAL_SOURCE_TO_FAULT_UNMODELLED',x['model_rejection_flags'])
        self.assertIn('ARC_PLASMA_AND_REAL_SOURCE_TO_FAULT_UNMODELLED',PRIORITY)
    def test_writer_outputs_bounded_json(self):
        with tempfile.TemporaryDirectory() as d:
            a=write(d,pilot_n=128,limit=12)
            p=Path(d)
            self.assertEqual(len(list(p.glob('*.json'))),4)
            self.assertEqual(json.loads((p/'phase2-receipt.json').read_text())['replay_candidates'],12)
            self.assertEqual(a['receipt']['actually_pilot_screened'],128)
if __name__=="__main__":
    unittest.main(verbosity=2)
