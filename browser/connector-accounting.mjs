export const CONNECTOR_ACCOUNTING_SCHEMA = 'globalgrid2050.v11.connector-accounting.v1';
export const STRING_ELECTRICAL_GRAPH_SCHEMA = 'globalgrid2050.v11.string-electrical-graph.v1';

export class ConnectorAccountingError extends Error {}

function moduleCount(value) {
  const number = Number(value);
  if (!Number.isInteger(number) || number < 2) {
    throw new ConnectorAccountingError('modulesPerString must be an integer >= 2');
  }
  return number;
}

function stableIdNumber(value) {
  return String(value).padStart(2, '0');
}

function stableHash(value) {
  const text = JSON.stringify(value);
  let hash = 0x811c9dc5;
  for (let index = 0; index < text.length; index += 1) {
    hash ^= text.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }
  return `fnv1a32:${(hash >>> 0).toString(16).padStart(8, '0')}`;
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

export function electricalOrder(modulesPerString, strategy) {
  const modules = moduleCount(modulesPerString);
  if (strategy === 'sequential') return Array.from({ length: modules }, (_, index) => index + 1);
  if (strategy === 'leapfrog') {
    const outward = [];
    const returning = [];
    for (let index = 1; index <= modules; index += 2) outward.push(index);
    for (let index = modules % 2 === 0 ? modules : modules - 1; index >= 2; index -= 2) returning.push(index);
    return outward.concat(returning);
  }
  throw new ConnectorAccountingError(`unsupported wiring strategy: ${strategy}`);
}

function polarityRecord(polarity) {
  return polarity === 'positive'
    ? { polarity: 'positive', marker_colour: 'red' }
    : { polarity: 'negative', marker_colour: 'blue' };
}

function moduleConnectorEnd(stringId, index, polarity) {
  const moduleId = `${stringId}-M${stableIdNumber(index)}`;
  const suffix = polarity === 'positive' ? 'POS' : 'NEG';
  return {
    connector_end_id: `${moduleId}-${suffix}-CONNECTOR`,
    connector_system_boundary: 'module',
    component_id: moduleId,
    component_type: 'pv_module',
    module_id: moduleId,
    electrical_index: index,
    junction_box_terminal_id: `${moduleId}-JBOX_${suffix}`,
    ...polarityRecord(polarity),
    connector_manufacturer: null,
    connector_model: null,
    connector_type: 'module_factory_lead_connector_end',
    contact_gender: 'unverified',
    evidence_state: 'derived_from_module_cardinality',
  };
}

function cableConnectorEnd(stringId, polarity, side) {
  const suffix = polarity === 'positive' ? 'POS' : 'NEG';
  const sideSuffix = side === 'module' ? 'MODULE-END' : 'INVERTER-END';
  const cableId = `${stringId}-${suffix}-STRING-CABLE`;
  return {
    connector_end_id: `${cableId}-${sideSuffix}`,
    connector_system_boundary: 'string_cable',
    component_id: cableId,
    component_type: 'pv_string_cable',
    module_id: null,
    electrical_index: null,
    junction_box_terminal_id: null,
    ...polarityRecord(polarity),
    connector_manufacturer: null,
    connector_model: null,
    connector_type: 'field_fitted_string_cable_connector_end',
    contact_gender: 'unverified',
    cable_id: cableId,
    cable_class: 'pv_string_cable',
    cable_sheath_colour: 'black',
    cable_side: side,
    evidence_state: 'derived_completed_string_boundary',
  };
}

function inverterConnectorEnd(stringId, inputId, mpptId, polarity) {
  const suffix = polarity === 'positive' ? 'POS' : 'NEG';
  return {
    connector_end_id: `${stringId}-${inputId}-${suffix}-INVERTER-SOCKET`,
    connector_system_boundary: 'inverter',
    component_id: inputId,
    component_type: 'inverter_dc_input',
    module_id: null,
    electrical_index: null,
    junction_box_terminal_id: null,
    ...polarityRecord(polarity),
    connector_manufacturer: null,
    connector_model: null,
    connector_type: 'inverter_dc_socket',
    contact_gender: 'unverified',
    string_id: stringId,
    mppt_id: mpptId,
    physical_dc_input_id: inputId,
    pv_terminal: null,
    pv_terminal_status: 'pending_sungrow_terminal_projection',
    evidence_state: 'derived_input_ownership',
  };
}

function connectorEnds(stringId, modules, inputId, mpptId) {
  const ends = [];
  for (let index = 1; index <= modules; index += 1) {
    ends.push(moduleConnectorEnd(stringId, index, 'negative'));
    ends.push(moduleConnectorEnd(stringId, index, 'positive'));
  }
  ends.push(cableConnectorEnd(stringId, 'negative', 'module'));
  ends.push(cableConnectorEnd(stringId, 'negative', 'inverter'));
  ends.push(cableConnectorEnd(stringId, 'positive', 'module'));
  ends.push(cableConnectorEnd(stringId, 'positive', 'inverter'));
  ends.push(inverterConnectorEnd(stringId, inputId, mpptId, 'negative'));
  ends.push(inverterConnectorEnd(stringId, inputId, mpptId, 'positive'));
  return ends;
}

function edgeRecord(stringId, sequence, edgeKind, source, destination, attributes = {}) {
  return {
    electrical_edge_id: `${stringId}-EDGE-${String(sequence).padStart(3, '0')}`,
    edge_kind: edgeKind,
    source_connector_end_id: source,
    destination_connector_end_id: destination,
    ...attributes,
  };
}

export function buildStringElectricalGraph({
  stringId = 'STR-01',
  moduleCount: modulesPerString,
  inputId = 'IN-01',
  mpptId = 'MPPT-01',
  strategy = 'sequential',
}) {
  if (!/^STR-\d{2,}$/.test(String(stringId))) throw new ConnectorAccountingError('stringId must be STR-nn');
  if (!/^IN-\d{2,}$/.test(String(inputId))) throw new ConnectorAccountingError('inputId must be IN-nn');
  if (!/^MPPT-\d{2,}$/.test(String(mpptId))) throw new ConnectorAccountingError('mpptId must be MPPT-nn');

  const modules = moduleCount(modulesPerString);
  const accounting = connectorAccounting(modules);
  const order = electricalOrder(modules, strategy);
  const ends = connectorEnds(stringId, modules, inputId, mpptId);
  const byId = new Map(ends.map((record) => [record.connector_end_id, record]));
  const negSocket = `${stringId}-${inputId}-NEG-INVERTER-SOCKET`;
  const posSocket = `${stringId}-${inputId}-POS-INVERTER-SOCKET`;
  const negCableInverter = `${stringId}-NEG-STRING-CABLE-INVERTER-END`;
  const negCableModule = `${stringId}-NEG-STRING-CABLE-MODULE-END`;
  const posCableModule = `${stringId}-POS-STRING-CABLE-MODULE-END`;
  const posCableInverter = `${stringId}-POS-STRING-CABLE-INVERTER-END`;
  const moduleEnd = (index, suffix) => `${stringId}-M${stableIdNumber(index)}-${suffix}-CONNECTOR`;

  const edges = [];
  const matingInterfaces = [];
  let sequence = 1;
  const pushMate = (source, destination, interfaceClass) => {
    const interfaceId = `${stringId}-MATE-${String(matingInterfaces.length + 1).padStart(3, '0')}`;
    const edge = edgeRecord(stringId, sequence++, 'mating_interface', source, destination, {
      mating_interface_id: interfaceId,
      interface_class: interfaceClass,
    });
    edges.push(edge);
    matingInterfaces.push({
      mating_interface_id: interfaceId,
      interface_class: interfaceClass,
      connector_end_ids: [source, destination],
      electrical_edge_id: edge.electrical_edge_id,
    });
  };
  const pushComponent = (source, destination, componentId, componentType) => {
    edges.push(edgeRecord(stringId, sequence++, 'component_internal', source, destination, {
      component_id: componentId,
      component_type: componentType,
    }));
  };

  pushMate(negSocket, negCableInverter, 'string_cable_to_inverter');
  pushComponent(negCableInverter, negCableModule, `${stringId}-NEG-STRING-CABLE`, 'pv_string_cable');
  pushMate(negCableModule, moduleEnd(order[0], 'NEG'), 'module_to_string_cable');

  for (let position = 0; position < order.length; position += 1) {
    const moduleIndex = order[position];
    const moduleId = `${stringId}-M${stableIdNumber(moduleIndex)}`;
    pushComponent(moduleEnd(moduleIndex, 'NEG'), moduleEnd(moduleIndex, 'POS'), moduleId, 'pv_module');
    if (position < order.length - 1) {
      pushMate(moduleEnd(moduleIndex, 'POS'), moduleEnd(order[position + 1], 'NEG'), 'module_to_module');
    }
  }

  pushMate(moduleEnd(order.at(-1), 'POS'), posCableModule, 'module_to_string_cable');
  pushComponent(posCableModule, posCableInverter, `${stringId}-POS-STRING-CABLE`, 'pv_string_cable');
  pushMate(posCableInverter, posSocket, 'string_cable_to_inverter');

  const mateByEnd = new Map();
  for (const record of matingInterfaces) {
    const [left, right] = record.connector_end_ids;
    mateByEnd.set(left, { mate_connector_end_id: right, ...record });
    mateByEnd.set(right, { mate_connector_end_id: left, ...record });
  }
  for (let pathPosition = 0; pathPosition < ends.length; pathPosition += 1) {
    const connectorId = pathPosition === 0
      ? edges[0].source_connector_end_id
      : edges[pathPosition - 1].destination_connector_end_id;
    const record = byId.get(connectorId);
    if (!record) throw new ConnectorAccountingError(`graph references unknown connector end ${connectorId}`);
    record.path_position = pathPosition;
    const mate = mateByEnd.get(connectorId);
    if (mate) {
      record.mate_connector_end_id = mate.mate_connector_end_id;
      record.mating_interface_id = mate.mating_interface_id;
      record.interface_class = mate.interface_class;
      record.electrical_edge_id = mate.electrical_edge_id;
      record.mate_status = 'authoritative';
    }
  }

  const graph = {
    schema_version: STRING_ELECTRICAL_GRAPH_SCHEMA,
    string_id: stringId,
    mppt_id: mpptId,
    physical_dc_input_id: inputId,
    strategy,
    modules_per_string: modules,
    electrical_order: order,
    accounting,
    connector_ends: ends,
    mating_interfaces: matingInterfaces,
    component_edges: edges.filter((edge) => edge.edge_kind === 'component_internal'),
    electrical_edges: edges,
    path_connector_end_ids: [edges[0].source_connector_end_id, ...edges.map((edge) => edge.destination_connector_end_id)],
    evidence_state: 'derived_authoritative_topology',
  };
  validateStringElectricalGraph(graph);
  graph.graph_hash = stableHash(graph);
  return graph;
}

export function validateStringElectricalGraph(graph) {
  const accounting = connectorAccounting(graph.modules_per_string);
  const ends = graph.connector_ends;
  const edges = graph.electrical_edges;
  const mates = graph.mating_interfaces;
  const ids = ends.map((record) => record.connector_end_id);
  const edgeIds = edges.map((edge) => edge.electrical_edge_id);
  const mateIds = mates.map((record) => record.mating_interface_id);
  const expectedOrder = electricalOrder(graph.modules_per_string, graph.strategy);

  if (JSON.stringify(graph.electrical_order) !== JSON.stringify(expectedOrder)) {
    throw new ConnectorAccountingError('electrical order does not match strategy');
  }
  if (ids.length !== accounting.complete_system_connector_end_count || new Set(ids).size !== ids.length) {
    throw new ConnectorAccountingError('electrical graph must contain every connector end exactly once');
  }
  if (mates.length !== accounting.total_mated_interface_count || new Set(mateIds).size !== mateIds.length) {
    throw new ConnectorAccountingError('mating-interface count or identity mismatch');
  }
  if (edges.length !== ids.length - 1 || new Set(edgeIds).size !== edgeIds.length) {
    throw new ConnectorAccountingError('electrical path must contain Nnodes-1 uniquely identified edges');
  }
  if (graph.path_connector_end_ids.length !== ids.length
      || new Set(graph.path_connector_end_ids).size !== ids.length
      || JSON.stringify([...graph.path_connector_end_ids].sort()) !== JSON.stringify([...ids].sort())) {
    throw new ConnectorAccountingError('electrical path must visit every connector end exactly once');
  }
  for (let index = 0; index < edges.length; index += 1) {
    if (edges[index].source_connector_end_id !== graph.path_connector_end_ids[index]
        || edges[index].destination_connector_end_id !== graph.path_connector_end_ids[index + 1]) {
      throw new ConnectorAccountingError('electrical edges must form one ordered continuous path');
    }
  }
  const mateUse = mates.flatMap((record) => record.connector_end_ids);
  if (mateUse.length !== ids.length || new Set(mateUse).size !== ids.length) {
    throw new ConnectorAccountingError('every connector end must participate in exactly one mating interface');
  }
  for (const record of ends) {
    const mate = ends.find((candidate) => candidate.connector_end_id === record.mate_connector_end_id);
    if (!mate || mate.mate_connector_end_id !== record.connector_end_id) {
      throw new ConnectorAccountingError(`mate identity is not symmetric for ${record.connector_end_id}`);
    }
    if (record.contact_gender !== 'unverified') {
      throw new ConnectorAccountingError('contact gender cannot be inferred from topology or polarity');
    }
  }
  const classCount = (name) => mates.filter((record) => record.interface_class === name).length;
  if (classCount('module_to_module') !== accounting.module_to_module_mate_count
      || classCount('module_to_string_cable') !== accounting.module_to_string_cable_mate_count
      || classCount('string_cable_to_inverter') !== accounting.string_cable_to_inverter_mate_count) {
    throw new ConnectorAccountingError('mating-interface class counts do not match connector authority');
  }
  if (!graph.path_connector_end_ids[0].endsWith('NEG-INVERTER-SOCKET')
      || !graph.path_connector_end_ids.at(-1).endsWith('POS-INVERTER-SOCKET')) {
    throw new ConnectorAccountingError('electrical path endpoints must be the inverter negative and positive sockets');
  }
  return graph;
}

function referenceGraphSelfCheck() {
  const cases = [30, 28, 20].map((modules) => {
    const sequential = buildStringElectricalGraph({ moduleCount: modules, strategy: 'sequential' });
    const leapfrog = buildStringElectricalGraph({ moduleCount: modules, strategy: 'leapfrog' });
    const sequentialIds = sequential.connector_ends.map((record) => record.connector_end_id).sort();
    const leapfrogIds = leapfrog.connector_ends.map((record) => record.connector_end_id).sort();
    if (JSON.stringify(sequentialIds) !== JSON.stringify(leapfrogIds)) {
      throw new ConnectorAccountingError('Sequential and Leapfrog must preserve connector-end identities');
    }
    if (sequential.graph_hash === leapfrog.graph_hash) {
      throw new ConnectorAccountingError('Sequential and Leapfrog must produce different authoritative graphs');
    }
    return {
      modules_per_string: modules,
      connector_end_count: sequential.connector_ends.length,
      mating_interface_count: sequential.mating_interfaces.length,
      electrical_edge_count: sequential.electrical_edges.length,
      sequential_graph_hash: sequential.graph_hash,
      leapfrog_graph_hash: leapfrog.graph_hash,
      connector_identity_invariant: true,
      mate_identity_difference: true,
    };
  });
  return {
    schema_version: 'globalgrid2050.v11.string-electrical-graph-self-check.v1',
    pass: true,
    cases,
  };
}

export const REFERENCE_GRAPH_SELF_CHECK = referenceGraphSelfCheck();
