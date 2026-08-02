from copy import deepcopy
import importlib.util, json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validator", ROOT / "scripts" / "validate_control_plane.py")
assert SPEC and SPEC.loader
V = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V)

class ControlPlaneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.state = json.loads((ROOT / "programme-state.json").read_text())
        cls.plan = json.loads((ROOT / cls.state["build_plan"]).read_text())
        cls.caps = json.loads((ROOT / cls.state["capability_matrix"]).read_text())
        cls.register = json.loads((ROOT / cls.state["source_resource_register"]).read_text())

    def validate(self, state=None, plan=None, caps=None, register=None):
        return V.validate_payloads(
            deepcopy(state or self.state),
            deepcopy(plan or self.plan),
            deepcopy(caps or self.caps),
            deepcopy(register or self.register),
            root=ROOT,
        )

    def test_current_surfaces_validate(self):
        result = V.validate_control_plane(ROOT)
        self.assertTrue(result["pass"])
        self.assertEqual(result["active_unit"], "V11-001")
        self.assertEqual(result["laboratory_mode"], "read_only")
        self.assertEqual(result["missing_generated_outputs"], [])

    def test_programme_mismatch_rejected(self):
        plan = deepcopy(self.plan)
        plan["programme_id"] = "wrong"
        with self.assertRaisesRegex(V.ControlPlaneValidationError, "programme identities"):
            self.validate(plan=plan)

    def test_writable_laboratory_rejected(self):
        state = deepcopy(self.state)
        state["laboratory_resource"]["mode"] = "writable"
        with self.assertRaisesRegex(V.ControlPlaneValidationError, "read-only"):
            self.validate(state=state)

    def test_laboratory_promotion_rejected(self):
        caps = deepcopy(self.caps)
        caps["laboratory_capabilities"]["current_v11_authority"] = True
        with self.assertRaisesRegex(V.ControlPlaneValidationError, "promoted"):
            self.validate(caps=caps)

    def test_unvalidated_capability_claim_rejected(self):
        caps = deepcopy(self.caps)
        caps["capabilities"][0]["state"] = "validated"
        with self.assertRaisesRegex(V.ControlPlaneValidationError, "unvalidated capability"):
            self.validate(caps=caps)

    def test_active_unit_mismatch_rejected(self):
        state = deepcopy(self.state)
        state["current_unit"] = "V11-002"
        with self.assertRaisesRegex(V.ControlPlaneValidationError, "active unit"):
            self.validate(state=state)

if __name__ == "__main__":
    unittest.main()
