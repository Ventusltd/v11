import assert from 'node:assert/strict';
import test from 'node:test';
import fs from 'node:fs';
import { fillRectangle, moveModule, assignStrings } from '../browser/layout-core.mjs';
import { deriveRouteLengths, referenceFromLayout, LayoutSimulationError } from '../browser/layout-simulation-bridge.mjs';
import { simulateComparison } from '../browser/simulation-core.mjs';

const reference = JSON.parse(fs.readFileSync('reference/lab_inverter_block_24_strings.json', 'utf8'));

function filledLayout(limit = 720) {
  return fillRectangle({
    boundary: { x_min: 0, y_min: 0, x_max: 42, y_max: 62 },
    moduleWidthM: 1.134,
    moduleHeightM: 2.384,
    gapXM: 0.03,
    gapYM: 0.05,
    limit,
  });
}

function referenceLayout() {
  return assignStrings(filledLayout(), 30, true);
}

test('720 unassigned modules derive exactly 24 complete routes', () => {
  const derived = deriveRouteLengths(filledLayout(), { modulesPerString: 30 });
  assert.equal(derived.string_count, 24);
  assert.equal(derived.route_lengths_m.length, 24);
  assert.ok(derived.strings.every((item) => item.module_count === 30));
  assert.ok(derived.strings.every((item) => item.module_ids.length === 30));
  assert.ok(derived.route_lengths_m.every((value) => value > 0));
});

test('geometry-derived reference runs the complete inverter simulation', async () => {
  const { reference: adapted, derivation } = referenceFromLayout(reference, referenceLayout());
  const result = await simulateComparison(adapted);
  assert.equal(result.sequential.strings.length, 24);
  assert.equal(result.leapfrog.strings.length, 24);
  assert.equal(result.sequential.reference_boundary.module_count, 720);
  assert.equal(adapted.provenance.layout_hash, derivation.layout_hash);
});

test('moving a module preserves topology and changes electrical results', async () => {
  const beforeLayout = referenceLayout();
  const original = beforeLayout.modules.find((module) => module.id === 'MOD-0001');
  const beforeAdapted = referenceFromLayout(reference, beforeLayout);
  const before = await simulateComparison(beforeAdapted.reference);

  const movedLayout = moveModule(beforeLayout, 'MOD-0001', 0.567, 55, 0.001);
  const moved = movedLayout.modules.find((module) => module.id === 'MOD-0001');
  assert.equal(moved.string_id, original.string_id);
  assert.equal(moved.electrical_index, original.electrical_index);

  const afterAdapted = referenceFromLayout(reference, movedLayout);
  const after = await simulateComparison(afterAdapted.reference);
  assert.notDeepEqual(afterAdapted.derivation.route_lengths_m, beforeAdapted.derivation.route_lengths_m);
  assert.notEqual(after.sequential.totals.circuit_loss_kw, before.sequential.totals.circuit_loss_kw);
  assert.notEqual(after.sequential.simulation_hash, before.sequential.simulation_hash);
});

test('partial or malformed topology is rejected', () => {
  const partial = filledLayout();
  partial.modules[0].string_id = 'STR-01';
  partial.modules[0].electrical_index = 1;
  assert.throws(() => deriveRouteLengths(partial), LayoutSimulationError);

  const malformed = referenceLayout();
  malformed.modules[1].electrical_index = 1;
  assert.throws(() => deriveRouteLengths(malformed), LayoutSimulationError);
});

test('invalid inverter coordinates are rejected', () => {
  assert.throws(() => deriveRouteLengths(referenceLayout(), { inverterPoint: { x_m: 'not-a-number', y_m: 0 } }), LayoutSimulationError);
});

test('incomplete strings cannot impersonate the 24-string reference block', () => {
  assert.throws(() => referenceFromLayout(reference, filledLayout(719)), LayoutSimulationError);
});
