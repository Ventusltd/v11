import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import { canonicalJson, electricalModuleOrder, simulateBlock, simulateComparison } from "../browser/simulation-core.mjs";

const reference = JSON.parse(fs.readFileSync(new URL("../reference/lab_inverter_block_24_strings.json", import.meta.url), "utf8"));

test("reference block retains 24 strings and 720 modules", async () => {
  const result = await simulateBlock(reference, "leapfrog");
  assert.equal(result.reference_boundary.string_count, 24);
  assert.equal(result.reference_boundary.modules_per_string, 30);
  assert.equal(result.reference_boundary.module_count, 720);
  assert.equal(result.reference_boundary.dc_nameplate_power_kwp, 475.2);
});

test("leapfrog traversal retains the laboratory order law", () => {
  assert.deepEqual(electricalModuleOrder(["1", "2", "3", "4", "5", "6"], "leapfrog"), ["1", "3", "5", "6", "4", "2"]);
});

test("leapfrog reduces field cable and loop area", async () => {
  const result = await simulateComparison(reference);
  assert.ok(result.delta_leapfrog_minus_sequential.field_cable_length_m < 0);
  assert.ok(result.delta_leapfrog_minus_sequential.approximate_loop_area_m2 < 0);
  assert.ok(result.delta_leapfrog_minus_sequential.factory_lead_length_m > 0);
});

test("browser calculation is byte-stable", async () => {
  const options = { operating_current_a: 14.1, route_multiplier: 1.08 };
  assert.equal(canonicalJson(await simulateComparison(reference, options)), canonicalJson(await simulateComparison(reference, options)));
});
