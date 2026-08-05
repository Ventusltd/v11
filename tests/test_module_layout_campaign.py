import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("module_layout_campaign", ROOT / "scripts" / "module_layout_campaign.py")
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
import sys
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


class ModuleLayoutCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = module.load_reference(ROOT / "reference" / "lab_inverter_block_24_strings.json")
        cls.layout = module.baseline_layout(cls.reference)

    def test_baseline_has_24_strings_and_720_modules(self):
        evaluation = module.evaluate(self.layout, self.reference)
        self.assertEqual(evaluation["module_count"], 720)
        self.assertEqual(evaluation["string_count"], 24)
        self.assertEqual(evaluation["collision_count"], 0)

    def test_moving_modules_preserves_membership_and_cardinality(self):
        import random
        candidate = module.mutate(self.layout, random.Random(10), "mixed", 1.308, 4.0)
        self.assertEqual(len(candidate), 720)
        self.assertEqual({m.module_id for m in candidate}, {m.module_id for m in self.layout})
        self.assertEqual({m.string_id for m in candidate}, {m.string_id for m in self.layout})

    def test_evaluation_is_byte_stable(self):
        self.assertEqual(
            module.canonical_json(module.evaluate(self.layout, self.reference)),
            module.canonical_json(module.evaluate(self.layout, self.reference)),
        )

    def test_all_mutation_modes_are_evaluable(self):
        import random
        for index, mode in enumerate(("row-shift", "module-move", "swap", "stagger", "compact", "mixed")):
            with self.subTest(mode=mode):
                candidate = module.mutate(self.layout, random.Random(index), mode, 1.308, 4.0)
                result = module.evaluate(candidate, self.reference)
                self.assertEqual(result["module_count"], 720)
                self.assertTrue(result["evaluation_hash"].startswith("sha256:"))


if __name__ == "__main__":
    unittest.main()
