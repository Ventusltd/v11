import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

import { connectorAccounting, resistanceAccounting } from '../browser/connector-accounting.mjs';

const reference = JSON.parse(fs.readFileSync('reference/lab_inverter_block_24_strings.json', 'utf8'));
const contract = JSON.parse(fs.readFileSync('reference/connector_accounting_contract.json', 'utf8'));

test('owner authority examples are exact', () => {
  for (const [modules, ends, interfaces] of [[30, 66, 33], [28, 62, 31], [20, 46, 23]]) {
    const accounting = connectorAccounting(modules);
    assert.equal(accounting.complete_system_connector_end_count, ends);
    assert.equal(accounting.total_mated_interface_count, interfaces);
    assert.equal(accounting.positive_connector_end_count, interfaces);
    assert.equal(accounting.negative_connector_end_count, interfaces);
    assert.equal(accounting.complete_system_connector_end_count, 2 * interfaces);
  }
});

test('30-module subsystem accounting is complete', () => {
  const accounting = connectorAccounting(30);
  assert.equal(accounting.module_connector_end_count, 60);
  assert.equal(accounting.string_cable_connector_end_count, 4);
  assert.equal(accounting.inverter_connector_end_count, 2);
  assert.equal(accounting.module_to_module_mate_count, 29);
  assert.equal(accounting.module_to_string_cable_mate_count, 2);
  assert.equal(accounting.string_cable_to_inverter_mate_count, 2);
});

test('fixture compatibility projection is corrected from 31 to 33', () => {
  const accounting = connectorAccounting(reference.array.modules_per_string);
  assert.equal(reference.conductors.connector_count_per_string, 33);
  assert.equal(reference.conductors.connector_count_per_string, accounting.total_mated_interface_count);
  assert.notEqual(reference.conductors.connector_count_per_string, 31);
  assert.equal(reference.conductors.connector_count_per_string_status, 'deprecated_compatibility_projection');
});

test('resistance policy includes all completed interface classes', () => {
  const policy = resistanceAccounting(30, contract.resistance_policy.contact_resistance_ohm_per_mated_interface);
  assert.equal(policy.mated_interface_count, 33);
  assert.equal(policy.applies_to, 'all_completed_mated_interfaces');
  assert.equal(policy.evidence_state, 'provisional_fixture');
  assert.ok(Math.abs(policy.total_connector_contact_resistance_ohm - 0.01155) < 1e-12);
});
