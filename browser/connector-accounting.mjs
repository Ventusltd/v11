export const CONNECTOR_ACCOUNTING_SCHEMA = 'globalgrid2050.v11.connector-accounting.v1';

export class ConnectorAccountingError extends Error {}

function moduleCount(value) {
  const number = Number(value);
  if (!Number.isInteger(number) || number < 2) {
    throw new ConnectorAccountingError('modulesPerString must be an integer >= 2');
  }
  return number;
}

export function connectorAccounting(modulesPerString) {
  const modules = moduleCount(modulesPerString);
  const moduleToModule = modules - 1;
  const moduleToStringCable = 2;
  const stringCableToInverter = 2;
  const totalInterfaces = moduleToModule + moduleToStringCable + stringCableToInverter;

  const moduleEnds = 2 * modules;
  const stringCableEnds = 4;
  const inverterEnds = 2;
  const totalEnds = moduleEnds + stringCableEnds + inverterEnds;
  const positiveEnds = modules + 3;
  const negativeEnds = modules + 3;

  const result = {
    schema_version: CONNECTOR_ACCOUNTING_SCHEMA,
    modules_per_string: modules,
    module_connector_end_count: moduleEnds,
    string_cable_connector_end_count: stringCableEnds,
    inverter_connector_end_count: inverterEnds,
    complete_system_connector_end_count: totalEnds,
    module_to_module_mate_count: moduleToModule,
    module_to_string_cable_mate_count: moduleToStringCable,
    string_cable_to_inverter_mate_count: stringCableToInverter,
    total_mated_interface_count: totalInterfaces,
    loose_module_connector_end_count_before_home_runs: 2,
    positive_connector_end_count: positiveEnds,
    negative_connector_end_count: negativeEnds,
  };
  validateConnectorAccounting(result);
  return result;
}

export function validateConnectorAccounting(accounting) {
  const modules = moduleCount(accounting.modules_per_string);
  const totalEnds = Number(accounting.complete_system_connector_end_count);
  const totalInterfaces = Number(accounting.total_mated_interface_count);
  const positive = Number(accounting.positive_connector_end_count);
  const negative = Number(accounting.negative_connector_end_count);

  if (totalEnds !== 2 * modules + 6) {
    throw new ConnectorAccountingError('complete-system connector ends must equal 2N + 6');
  }
  if (totalInterfaces !== modules + 3) {
    throw new ConnectorAccountingError('mated interfaces must equal N + 3');
  }
  if (totalEnds !== 2 * totalInterfaces) {
    throw new ConnectorAccountingError('every completed interface must consume exactly two connector ends');
  }
  if (positive !== negative || positive + negative !== totalEnds) {
    throw new ConnectorAccountingError('positive and negative connector-end counts must be equal and exhaustive');
  }
}

export function resistanceAccounting(modulesPerString, contactResistanceOhmPerMatedInterface) {
  const accounting = connectorAccounting(modulesPerString);
  const resistance = Number(contactResistanceOhmPerMatedInterface);
  if (!Number.isFinite(resistance) || resistance < 0) {
    throw new ConnectorAccountingError('contact resistance must be finite and non-negative');
  }
  const count = accounting.total_mated_interface_count;
  return {
    schema_version: 'globalgrid2050.v11.connector-resistance-policy.v1',
    evidence_state: 'provisional_fixture',
    applies_to: 'all_completed_mated_interfaces',
    mated_interface_count: count,
    contact_resistance_ohm_per_mated_interface: resistance,
    total_connector_contact_resistance_ohm: count * resistance,
  };
}
