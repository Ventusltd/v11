from __future__ import annotations
import argparse, json, re
from pathlib import Path

ACTIVE = "Ventusltd/v11"
LAB = "Ventusltd/solar-electrical-topology-analysis-engine-text-based"
ANCHOR = "d3b4c497144c2c9b3e8f0e82117e7e9abe4672b9"
PROGRAMME = "v11-native-control-plane-20260802"
SHA40 = re.compile(r"^[0-9a-f]{40}$")

class ControlPlaneValidationError(ValueError):
    pass

def need(value: bool, message: str) -> None:
    if not value:
        raise ControlPlaneValidationError(message)

def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    need(isinstance(value, dict), f"{path} must contain an object")
    return value

def validate_payloads(state, plan, caps, register, *, root: Path, require_projection=False):
    need(state.get("schema_version") == "globalgrid2050.v11.programme-state.v1", "wrong state schema")
    need(plan.get("schema_version") == "globalgrid2050.v11.build-plan.v1", "wrong plan schema")
    need(caps.get("schema_version") == "globalgrid2050.v11.capability-matrix.v1", "wrong capability schema")
    need(register.get("schema_version") == "globalgrid2050.v11.source-resource-register.v1", "wrong resource schema")
    need({state.get("programme_id"), plan.get("programme_id"), caps.get("programme_id"), register.get("programme_id")} == {PROGRAMME}, "programme identities disagree")
    need(state.get("active_repository") == ACTIVE, "V11 must be active")
    need(state.get("programme_status") == plan.get("programme_status") == "active", "programme must be active")
    session, protocol = state.get("operator_session", {}), plan.get("operator_protocol", {})
    need(session.get("limit_seconds") == protocol.get("session_limit_seconds") == 300, "session limit must be 300")
    need(session.get("review_required_after_session") is True and protocol.get("review_required_after_every_session") is True, "session review required")
    need(protocol.get("session_advances_programme") is False, "session may not advance programme")
    need(SHA40.fullmatch(str(session.get("started_from_commit", ""))) is not None, "invalid session SHA")
    units = plan.get("units")
    need(isinstance(units, list) and units, "units required")
    need([u.get("id") for u in units] == [f"V11-{n:03d}" for n in range(1, len(units)+1)], "unit order invalid")
    need([u.get("ordinal") for u in units] == list(range(1, len(units)+1)), "unit ordinals invalid")
    active = [u for u in units if u.get("status") == "active"]
    need(len(active) == 1, "one active unit required")
    need(active[0].get("id") == plan.get("active_unit") == state.get("current_unit"), "active unit disagrees")
    need(plan.get("next_unit") == state.get("next_unit") is None, "later unit authorised")
    planned_seen = False
    for unit in units:
        status = unit.get("status")
        need(status in {"passed", "active", "planned"}, "invalid unit status")
        planned_seen = planned_seen or status == "planned"
        need(not (planned_seen and status != "planned"), "planned suffix invalid")
        if status != "passed":
            need(unit.get("evidence") is None, "unfinished unit has evidence")
    lab_state, lab_plan, lab_caps = state["laboratory_resource"], plan["laboratory_policy"], caps["laboratory_capabilities"]
    resources = register.get("resources")
    need(isinstance(resources, list) and len(resources) == 1, "one lab resource required")
    resource = resources[0]
    need({lab_state.get("repository"), lab_plan.get("repository"), resource.get("repository")} == {LAB}, "laboratory identity disagrees")
    need({lab_state.get("anchor_commit"), lab_plan.get("anchor_commit"), lab_caps.get("anchor_commit"), resource.get("anchor_commit")} == {ANCHOR}, "laboratory anchors disagree")
    need(lab_state.get("mode") == lab_plan.get("mode") == resource.get("mode") == "read_only", "laboratory must be read-only")
    need(lab_state.get("capabilities_are_current_v11_authority") is False and lab_plan.get("laboratory_result_is_v11_authority") is False and lab_caps.get("current_v11_authority") is False, "laboratory promoted into V11 authority")
    need("claim laboratory capability as current V11 authority" in resource.get("prohibited_actions", []), "authority prohibition missing")
    items = caps.get("capabilities")
    need(isinstance(items, list) and items, "capabilities required")
    need(len({i.get("id") for i in items}) == len(items), "capability IDs duplicate")
    for item in items:
        need(item.get("authority_repository") == ACTIVE, "capability authority is not V11")
        need(item.get("state") not in {"implemented", "validated", "canonical", "available"}, "unvalidated capability claimed")
        need(item.get("evidence") is None, "unvalidated capability has evidence")
    for field in ("current_quantum_spawn", "build_plan", "execution_ledger", "capability_matrix", "source_resource_register"):
        relative = state.get(field)
        need(isinstance(relative, str) and (root / relative).is_file(), f"missing referenced file: {relative}")
    need(state["current_unit"] in (root / state["execution_ledger"]).read_text(encoding="utf-8"), "ledger omits current unit")
    missing = [p for p in state.get("generated_outputs", []) if not (root / p).is_file()]
    if require_projection:
        need(not missing, f"generated outputs missing: {missing}")
    return {"pass": True, "active_unit": state["current_unit"], "laboratory_mode": "read_only", "missing_generated_outputs": missing}

def validate_control_plane(root: Path, require_projection=False):
    state = load(root / "programme-state.json")
    return validate_payloads(state, load(root / state["build_plan"]), load(root / state["capability_matrix"]), load(root / state["source_resource_register"]), root=root, require_projection=require_projection)

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--require-projection", action="store_true")
    args = parser.parse_args(argv)
    print(json.dumps(validate_control_plane(args.root.resolve(), args.require_projection), sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
