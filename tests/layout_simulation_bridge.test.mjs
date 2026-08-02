import assert from 'node:assert/strict';
import test from 'node:test';
import fs from 'node:fs';
import { fillRectangle, moveModule } from '../browser/layout-core.mjs';
import { deriveRouteLengths, referenceFromLayout, LayoutSimulationError } from '../browser/layout-simulation-bridge.mjs';
import { simulateComparison } from '../browser/simulation-core.mjs';

const reference = JSON.parse(fs.readFileSync('reference/lab_inverter_block_24_strings.json', 'utf8'));

function referenceLayout() {
  return fillRectangle({
    boundary: { x_min: 0, y_min: 0, x_max: 42, y_max: 62 },
    moduleWidthM: 1.134,
    moduleHeightM: 2.384,
    gapXM: 0.03,
    gapYM: 0.05,
    limit: 720,
  });
}

test('720 modules derive exactly 24 complete routes', () => {
  const derived = deriveRouteLengths(referenceLayout(), { modulesPerString: 30 });
  assert.equal(derived.string_count, 24);
  assert.equal(derived.route_lengths_m.length, 24);
  assert.ok(derived.strings.every((item) => item.module_count === 30));
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

test('moving a module changes the deterministic route vector', () => {
  const sparse = fillRectangle({
    boundary: { x_min: 0, y_min: 0, x_max: 80, y_max: 80 },
    moduleWidthM: 1,
    moduleHeightM: 1,
    gapXM: 1,
    gapYM: 1,
    limit: 60,
  });
  const before = deriveRouteLengths(sparse, { modulesPerString: 30 });
  const moved = moveModule(sparse, 'MOD-0001', 0.5, 60.5, 0.5);
  const after = deriveRouteLengths(moved, { modulesPerString: 30 });
  assert.notDeepEqual(after.route_lengths_m, before.route_lengths_m);
  assert.notEqual(after.layout_hash, before.layout_hash);
  assert.equal(after.string_count, before.string_count);
});

test('incomplete strings cannot impersonate the 24-string reference block', () => {
  const incomplete = fillRectangle({
    boundary: { x_min: 0, y_min: 0, x_max: 20, y_max: 20 },
    moduleWidthM: 1,
    moduleHeightM: 1,
    gapXM: 0.1,
    gapYM: 0.1,
    limit: 719,
  });
  assert.throws(() => referenceFromLayout(reference, incomplete), LayoutSimulationError);
});
