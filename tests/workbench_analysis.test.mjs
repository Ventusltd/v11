import assert from 'node:assert/strict';
import test from 'node:test';
import { analyseWorkbench, buildEngineeringPackage, workbenchCsv, WorkbenchAnalysisError } from '../browser/workbench-analysis.mjs';

const route = (id, value) => ({
  string_id: id,
  module_count: 30,
  module_ids: Array.from({ length: 30 }, (_, index) => `${id}-M${index + 1}`),
  centroid: { x_m: value, y_m: value + 1 },
  home_run_m: value + 10,
  intra_string_path_m: value + 20,
  one_way_route_m: value + 30,
});

const electrical = (id, value) => ({
  string_id: id,
  circuit_resistance_ohm: value / 100,
  voltage_drop_v: value / 10,
  voltage_drop_percent: value / 20,
  loss_w: value,
  round_trip_delay_us: value / 2,
});

function fixture() {
  const derivation = {
    layout_hash: 'sha256:layout',
    strings: [route('STR-01', 10), route('STR-02', 20)],
  };
  const sequential = [electrical('STR-01', 100), electrical('STR-02', 200)];
  const leapfrog = [electrical('STR-02', 180), electrical('STR-01', 90)];
  const comparison = {
    comparison_hash: 'sha256:comparison',
    sequential: {
      simulation_hash: 'sha256:sequential',
      reference_boundary: { module_count: 60, string_count: 2 },
      inputs: { operating_current_a: 17.31 },
      totals: { field_cable_length_m: 1000, circuit_loss_kw: 0.3 },
      strings: sequential,
    },
    leapfrog: {
      simulation_hash: 'sha256:leapfrog',
      totals: { field_cable_length_m: 900, circuit_loss_kw: 0.27 },
      strings: leapfrog,
    },
  };
  return { derivation, comparison };
}

test('joins geometry and electrical results by string identity', () => {
  const { derivation, comparison } = fixture();
  const analysis = analyseWorkbench(derivation, comparison);
  assert.equal(analysis.rows[0].string_id, 'STR-01');
  assert.equal(analysis.rows[0].sequential.loss_w, 100);
  assert.equal(analysis.rows[0].leapfrog.loss_w, 90);
  assert.equal(analysis.rows[1].leapfrog.loss_w, 180);
});

test('reports deterministic diagnostic extremes', () => {
  const { derivation, comparison } = fixture();
  const diagnostics = analyseWorkbench(derivation, comparison).diagnostics;
  assert.equal(diagnostics.longest_route.string_id, 'STR-02');
  assert.equal(diagnostics.highest_sequential_loss.string_id, 'STR-02');
  assert.equal(diagnostics.field_cable_saving_m, 100);
  assert.equal(diagnostics.circuit_loss_delta_kw, -0.03);
});

test('rejects missing and duplicate string identities', () => {
  const { derivation, comparison } = fixture();
  comparison.leapfrog.strings = [comparison.leapfrog.strings[0]];
  assert.throws(() => analyseWorkbench(derivation, comparison), WorkbenchAnalysisError);

  const duplicate = fixture();
  duplicate.comparison.sequential.strings[1].string_id = 'STR-01';
  assert.throws(() => analyseWorkbench(duplicate.derivation, duplicate.comparison), WorkbenchAnalysisError);
});

test('engineering package has no runtime timestamp and is byte-stable', () => {
  const { derivation, comparison } = fixture();
  const input = {
    layout: { layout_hash: derivation.layout_hash, modules: [] },
    adapted: { provenance: { source_repository: 'lab', source_commit: 'abc' } },
    derivation,
    comparison,
  };
  const first = buildEngineeringPackage(input);
  const second = buildEngineeringPackage(input);
  assert.deepEqual(first, second);
  assert.equal(Object.hasOwn(first, 'generated_at'), false);
  assert.equal(first.authority.layout_hash, 'sha256:layout');
});

test('CSV contains one header and one row per string', () => {
  const { derivation, comparison } = fixture();
  const csv = workbenchCsv(analyseWorkbench(derivation, comparison));
  const lines = csv.trimEnd().split('\n');
  assert.equal(lines.length, 3);
  assert.match(lines[0], /^string_id,module_count,one_way_route_m/);
  assert.match(lines[1], /^STR-01,/);
  assert.match(lines[2], /^STR-02,/);
});
