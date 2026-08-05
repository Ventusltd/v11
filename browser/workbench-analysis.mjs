import './sld-visual-contract.mjs';
import './sld-module-symbols.mjs';
import {
  STRING_ELECTRICAL_GRAPH_SCHEMA,
  buildStringElectricalGraph,
  validateStringElectricalGraph,
} from './connector-accounting.mjs';

export const COMPLETED_CONNECTOR_END_SCHEDULE_SCHEMA = STRING_ELECTRICAL_GRAPH_SCHEMA;

const STYLE_ID = 'v11-completed-connector-end-style';
const EVIDENCE_ID = 'v11-completed-connector-end-evidence';
const SVG_NS = 'http://www.w3.org/2000/svg';
const BLACK = 'rgb(0, 0, 0)';
const RED = 'rgb(235, 87, 87)';
const BLUE = 'rgb(47, 128, 237)';

export function buildCompletedStringConnectorEndSchedule({
  stringId,
  moduleCount,
  inputId,
  mpptId,
  strategy = 'sequential',
}) {
  return buildStringElectricalGraph({ stringId, moduleCount, inputId, mpptId, strategy });
}

export function validateCompletedStringConnectorEndSchedule(graph) {
  return validateStringElectricalGraph(graph);
}

function ensureStyle() {
  if (document.getElementById(STYLE_ID)) return;
  const style = document.createElement('style');
  style.id = STYLE_ID;
  style.textContent = `
    #detail-canvas .completed-system-connector-end { stroke:#fff!important; stroke-width:1!important; cursor:pointer; }
    #detail-canvas .completed-system-connector-positive { fill:#eb5757!important; }
    #detail-canvas .completed-system-connector-negative { fill:#2f80ed!important; }
    #detail-canvas .completed-system-string-cable { stroke:#000!important; fill:none!important; stroke-width:2.2!important; filter:drop-shadow(0 0 .7px #dbe5ed); }
    #detail-canvas .completed-system-label { fill:#f4f7fa!important; font-size:6px!important; font-weight:700!important; pointer-events:none; }
  `;
  document.head.append(style);
}

function svgElement(name, attributes = {}) {
  const element = document.createElementNS(SVG_NS, name);
  for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, String(value));
  return element;
}

function graphRecordTitle(record, strategy) {
  return `${record.connector_end_id}\n${strategy} mate: ${record.mate_connector_end_id}\nInterface: ${record.mating_interface_id} (${record.interface_class})\nEdge: ${record.electrical_edge_id}`;
}

function applyConnectorRecord(element, record, graph) {
  element.id = record.connector_end_id;
  element.classList.add(
    'completed-system-connector-end',
    record.polarity === 'positive' ? 'completed-system-connector-positive' : 'completed-system-connector-negative',
  );
  const values = {
    connectorEndId: record.connector_end_id,
    connectorSystemBoundary: record.connector_system_boundary,
    componentId: record.component_id,
    componentType: record.component_type,
    moduleId: record.module_id,
    electricalIndex: record.electrical_index,
    junctionBoxTerminalId: record.junction_box_terminal_id,
    polarity: record.polarity,
    markerColour: record.marker_colour,
    contactGender: record.contact_gender,
    mateConnectorEndId: record.mate_connector_end_id,
    matingInterfaceId: record.mating_interface_id,
    interfaceClass: record.interface_class,
    electricalEdgeId: record.electrical_edge_id,
    pathPosition: record.path_position,
    mateStatus: record.mate_status,
    topologyStrategy: graph.strategy,
    graphHash: graph.graph_hash,
  };
  for (const [key, value] of Object.entries(values)) {
    if (value === null || value === undefined) delete element.dataset[key];
    else element.dataset[key] = String(value);
  }
  element.setAttribute('aria-label', `${record.connector_end_id}; ${graph.strategy} mate ${record.mate_connector_end_id}`);
  let title = element.querySelector(':scope > title');
  if (!title) {
    title = svgElement('title');
    element.prepend(title);
  }
  title.textContent = graphRecordTitle(record, graph.strategy);
}

function appendInverterSocketProjection(group, graph, record, terminalNode) {
  if (!record) throw new Error('missing inverter socket connector record');
  const socket = svgElement('circle', {
    cx: Number(terminalNode.getAttribute('cx')),
    cy: Number(terminalNode.getAttribute('cy')),
    r: 5,
    class: 'inverter-connector-end',
  });
  applyConnectorRecord(socket, record, graph);
  group.append(socket);
}

function appendCableProjection(detailSvg, graph, polarity, y) {
  const suffix = polarity === 'positive' ? 'POS' : 'NEG';
  const moduleRecord = graph.connector_ends.find((item) => item.connector_end_id === `${graph.string_id}-${suffix}-STRING-CABLE-MODULE-END`);
  const inverterRecord = graph.connector_ends.find((item) => item.connector_end_id === `${graph.string_id}-${suffix}-STRING-CABLE-INVERTER-END`);
  if (!moduleRecord || !inverterRecord) throw new Error(`missing ${polarity} string-cable connector records`);
  const group = detailSvg.querySelector(`#${graph.string_id}-COMPLETED-CONNECTOR-ENDS`);
  const line = svgElement('line', {
    id: `${graph.string_id}-${suffix}-STRING-CABLE-BODY`,
    class: 'completed-system-string-cable',
    x1: 141, y1: y, x2: 158, y2: y,
    'data-cable-id': `${graph.string_id}-${suffix}-STRING-CABLE`,
    'data-cable-sheath-colour': 'black',
    'data-source-connector-end-id': inverterRecord.connector_end_id,
    'data-destination-connector-end-id': moduleRecord.connector_end_id,
  });
  const inverterEnd = svgElement('circle', { cx: 141, cy: y, r: 4 });
  const moduleEnd = svgElement('circle', { cx: 158, cy: y, r: 4 });
  applyConnectorRecord(inverterEnd, inverterRecord, graph);
  applyConnectorRecord(moduleEnd, moduleRecord, graph);
  group.append(line, inverterEnd, moduleEnd);
}

function selectedWiringMode() {
  const mode = window.__v11TopologyEvidence?.wiring_mode
    ?? document.querySelector('.wiring-mode[aria-pressed="true"]')?.dataset.mode
    ?? 'leapfrog';
  return ['sequential', 'leapfrog', 'compare'].includes(mode) ? mode : 'leapfrog';
}

function buildGraphBundle(args, mode) {
  const sequential = buildStringElectricalGraph({ ...args, strategy: 'sequential' });
  const leapfrog = buildStringElectricalGraph({ ...args, strategy: 'leapfrog' });
  const projection = mode === 'leapfrog' ? leapfrog : sequential;
  const sequentialIds = sequential.connector_ends.map((item) => item.connector_end_id).sort();
  const leapfrogIds = leapfrog.connector_ends.map((item) => item.connector_end_id).sort();
  const sequentialMates = sequential.connector_ends.map((item) => `${item.connector_end_id}->${item.mate_connector_end_id}`).sort();
  const leapfrogMates = leapfrog.connector_ends.map((item) => `${item.connector_end_id}->${item.mate_connector_end_id}`).sort();
  const comparison = {
    connector_identities_preserved: JSON.stringify(sequentialIds) === JSON.stringify(leapfrogIds),
    connector_end_counts_preserved: sequential.connector_ends.length === leapfrog.connector_ends.length,
    mating_interface_counts_preserved: sequential.mating_interfaces.length === leapfrog.mating_interfaces.length,
    mate_identities_differ: JSON.stringify(sequentialMates) !== JSON.stringify(leapfrogMates),
  };
  comparison.pass = Object.values(comparison).every(Boolean);
  return { sequential, leapfrog, projection, comparison };
}

async function resolveTestedSha() {
  const urlMatch = location.pathname.match(/\/([0-9a-f]{40})\/browser\/workbench\.html$/i);
  if (urlMatch) return urlMatch[1].toLowerCase();
  try {
    const head = (await fetch('../.git/HEAD', { cache: 'no-store' }).then((response) => response.ok ? response.text() : '')).trim();
    if (/^[0-9a-f]{40}$/i.test(head)) return head.toLowerCase();
    const refMatch = head.match(/^ref:\s+(.+)$/);
    if (refMatch) {
      const ref = (await fetch(`../.git/${refMatch[1]}`, { cache: 'no-store' }).then((response) => response.ok ? response.text() : '')).trim();
      if (/^[0-9a-f]{40}$/i.test(ref)) return ref.toLowerCase();
    }
  } catch {
    // Local static serving may not expose Git metadata.
  }
  return null;
}

function styleMismatches(elements, property, expected, label) {
  return elements.flatMap((element) => {
    const actual = getComputedStyle(element)[property];
    return actual === expected ? [] : [{ label, id: element.id || null, expected, actual }];
  });
}

let testedShaPromise;
let scheduled = false;
let lastEvidenceJson = '';
let lastFailureSignature = '';

async function projectAndMeasure() {
  scheduled = false;
  ensureStyle();
  const detailSvg = document.querySelector('#detail-canvas.string-strip');
  if (!detailSvg) return;
  const moduleConnectors = [...detailSvg.querySelectorAll('.module-connector-marker')];
  const expectedModules = detailSvg.querySelectorAll('.topology-cell').length;
  if (moduleConnectors.length !== expectedModules * 2) return;

  const stringId = detailSvg.dataset.stringId;
  const inputId = detailSvg.dataset.inputId;
  const mpptId = detailSvg.dataset.mpptId;
  const mode = selectedWiringMode();
  const bundle = buildGraphBundle({ stringId, moduleCount: expectedModules, inputId, mpptId }, mode);
  const graph = bundle.projection;

  const terminalNodes = [...detailSvg.querySelectorAll('circle.terminal')];
  if (terminalNodes.length !== 2) throw new Error('selected-string SLD must expose exactly two inverter terminal markers');
  const inverterNegative = graph.connector_ends.find((item) => item.connector_system_boundary === 'inverter' && item.polarity === 'negative');
  const inverterPositive = graph.connector_ends.find((item) => item.connector_system_boundary === 'inverter' && item.polarity === 'positive');
  let group = detailSvg.querySelector(`#${stringId}-COMPLETED-CONNECTOR-ENDS`);
  const needsProjection = !group
    || group.dataset.graphHash !== graph.graph_hash
    || group.dataset.displayMode !== mode
    || detailSvg.querySelectorAll('[data-connector-system-boundary="string_cable"]').length !== 4
    || group.querySelectorAll('[data-connector-system-boundary="inverter"]').length !== 2;

  if (needsProjection) {
    group?.remove();
    group = svgElement('g', {
      id: `${stringId}-COMPLETED-CONNECTOR-ENDS`,
      class: 'completed-system-connector-ends',
      'data-schedule-schema': graph.schema_version,
      'data-graph-hash': graph.graph_hash,
      'data-topology-strategy': graph.strategy,
      'data-display-mode': mode,
    });
    detailSvg.append(group);

    appendInverterSocketProjection(group, graph, inverterNegative, terminalNodes[0]);
    appendInverterSocketProjection(group, graph, inverterPositive, terminalNodes[1]);
    appendCableProjection(detailSvg, graph, 'negative', Number(terminalNodes[0].getAttribute('cy')));
    appendCableProjection(detailSvg, graph, 'positive', Number(terminalNodes[1].getAttribute('cy')));

    const label = svgElement('text', { class: 'completed-system-label', x: 137, y: 154, 'text-anchor': 'middle' });
    const displayLabel = mode === 'compare' ? 'COMPARE · sequential mate projection' : graph.strategy.toUpperCase();
    label.textContent = `${displayLabel} · ${graph.accounting.total_mated_interface_count} authoritative mates`;
    group.append(label);
  }

  for (const record of graph.connector_ends) {
    const element = document.getElementById(record.connector_end_id);
    if (element) applyConnectorRecord(element, record, graph);
  }

  const renderedByGraphId = graph.connector_ends.map((record) => document.getElementById(record.connector_end_id));
  const missingRenderedIds = graph.connector_ends
    .filter((_, index) => !renderedByGraphId[index])
    .map((record) => record.connector_end_id);
  const visibleEnds = renderedByGraphId.filter(Boolean);
  const cableEnds = visibleEnds.filter((item) => item.dataset.connectorSystemBoundary === 'string_cable');
  const inverterEnds = visibleEnds.filter((item) => item.dataset.connectorSystemBoundary === 'inverter');
  const positiveEnds = visibleEnds.filter((item) => item.dataset.polarity === 'positive');
  const negativeEnds = visibleEnds.filter((item) => item.dataset.polarity === 'negative');
  const cableBodies = [...detailSvg.querySelectorAll('.completed-system-string-cable')];
  const renderedIds = visibleEnds.map((item) => item.dataset.connectorEndId);
  const duplicateIds = renderedIds.filter((id, index) => id && renderedIds.indexOf(id) !== index);
  const graphIds = graph.connector_ends.map((item) => item.connector_end_id).sort();
  const identityPass = JSON.stringify(graphIds) === JSON.stringify([...renderedIds].sort());
  const mateMismatches = graph.connector_ends.flatMap((record) => {
    const element = document.getElementById(record.connector_end_id);
    if (!element) return [{ connector_end_id: record.connector_end_id, issue: 'not_rendered' }];
    const fields = {
      mate_connector_end_id: [element.dataset.mateConnectorEndId, record.mate_connector_end_id],
      mating_interface_id: [element.dataset.matingInterfaceId, record.mating_interface_id],
      interface_class: [element.dataset.interfaceClass, record.interface_class],
      electrical_edge_id: [element.dataset.electricalEdgeId, record.electrical_edge_id],
      path_position: [Number(element.dataset.pathPosition), record.path_position],
      topology_strategy: [element.dataset.topologyStrategy, graph.strategy],
      graph_hash: [element.dataset.graphHash, graph.graph_hash],
    };
    return Object.entries(fields).flatMap(([field, [actual, expected]]) => (
      actual === expected ? [] : [{ connector_end_id: record.connector_end_id, field, expected, actual }]
    ));
  });
  const renderedInterfaceIds = new Set(visibleEnds.map((item) => item.dataset.matingInterfaceId).filter(Boolean));
  const computedStyleMismatches = [
    ...styleMismatches(cableBodies, 'stroke', BLACK, 'black string cable body'),
    ...styleMismatches(positiveEnds, 'fill', RED, 'red positive connector end'),
    ...styleMismatches(negativeEnds, 'fill', BLUE, 'blue negative connector end'),
  ];
  const counts = {
    module_connector_ends: moduleConnectors.length,
    string_cable_connector_ends: cableEnds.length,
    inverter_connector_ends: inverterEnds.length,
    complete_system_connector_ends: visibleEnds.length,
    positive_red_connector_ends: positiveEnds.length,
    negative_blue_connector_ends: negativeEnds.length,
    black_string_cable_bodies: cableBodies.length,
    authoritative_mating_interfaces: renderedInterfaceIds.size,
  };
  const expected = graph.accounting;
  const countPass = counts.module_connector_ends === expected.module_connector_end_count
    && counts.string_cable_connector_ends === expected.string_cable_connector_end_count
    && counts.inverter_connector_ends === expected.inverter_connector_end_count
    && counts.complete_system_connector_ends === expected.complete_system_connector_end_count
    && counts.positive_red_connector_ends === expected.positive_connector_end_count
    && counts.negative_blue_connector_ends === expected.negative_connector_end_count
    && counts.black_string_cable_bodies === 2
    && counts.authoritative_mating_interfaces === expected.total_mated_interface_count;
  const matePass = mateMismatches.length === 0
    && graph.connector_ends.every((record) => record.mate_status === 'authoritative')
    && renderedInterfaceIds.size === graph.mating_interfaces.length;
  const pass = countPass
    && identityPass
    && matePass
    && bundle.comparison.pass
    && !missingRenderedIds.length
    && !duplicateIds.length
    && !computedStyleMismatches.length;
  const evidence = {
    schema_version: 'globalgrid2050.v11.graph-backed-selected-string-evidence.v2',
    tested_commit_sha: await (testedShaPromise ??= resolveTestedSha()),
    selected_string_id: stringId,
    mppt_id: mpptId,
    physical_dc_input_id: inputId,
    display_mode: mode,
    projected_strategy: graph.strategy,
    graph_hash: graph.graph_hash,
    graph_schema: graph.schema_version,
    topology_status: 'authoritative_connector_ends_mates_interfaces_and_edges',
    counts,
    expected,
    electrical_order: graph.electrical_order,
    connector_end_ids: graphIds,
    mating_interface_ids: graph.mating_interfaces.map((item) => item.mating_interface_id),
    electrical_edge_ids: graph.electrical_edges.map((item) => item.electrical_edge_id),
    path_connector_end_ids: graph.path_connector_end_ids,
    missing_rendered_ids: missingRenderedIds,
    duplicate_ids: [...new Set(duplicateIds)],
    identity_pass: identityPass,
    count_pass: countPass,
    mate_pass: matePass,
    mate_mismatches: mateMismatches,
    topology_comparison: bundle.comparison,
    computed_style_mismatches: computedStyleMismatches,
    default_30_module_acceptance: {
      applicable: expectedModules === 30,
      expected_complete_system_connector_ends: 66,
      expected_mated_interfaces: 33,
      expected_positive_red_connector_ends: 33,
      expected_negative_blue_connector_ends: 33,
      pass: expectedModules === 30 ? countPass && matePass : null,
    },
    contact_gender_inferred_from_polarity: false,
    pass,
  };

  window.__v11CompletedConnectorEndSchedule = graph;
  window.__v11StringElectricalGraphs = { sequential: bundle.sequential, leapfrog: bundle.leapfrog };
  window.__v11CompletedConnectorEndEvidence = evidence;
  const evidenceJson = JSON.stringify(evidence, null, 2);
  if (evidenceJson !== lastEvidenceJson) {
    lastEvidenceJson = evidenceJson;
    let node = document.getElementById(EVIDENCE_ID);
    if (!node) {
      node = document.createElement('script');
      node.id = EVIDENCE_ID;
      node.type = 'application/json';
      document.body.append(node);
    }
    node.textContent = evidenceJson;
    window.dispatchEvent(new CustomEvent('v11:completed-connector-end-evidence', { detail: evidence }));
  }
  detailSvg.dataset.completedConnectorEndContract = 'v2';
  detailSvg.dataset.completedConnectorEndPass = String(pass);
  detailSvg.dataset.electricalGraphHash = graph.graph_hash;
  detailSvg.dataset.electricalGraphStrategy = graph.strategy;
  document.documentElement.dataset.completedConnectorEndPass = String(pass);

  if (!pass) {
    const signature = JSON.stringify({
      counts,
      identityPass,
      matePass,
      topologyComparison: bundle.comparison,
      missingRenderedIds,
      duplicateIds,
      mateMismatches,
      computedStyleMismatches,
    });
    if (signature !== lastFailureSignature) {
      lastFailureSignature = signature;
      queueMicrotask(() => { throw new Error(`Graph-backed connector projection failed: ${signature}`); });
    }
  } else {
    lastFailureSignature = '';
  }
}

function scheduleProjection() {
  if (scheduled) return;
  scheduled = true;
  requestAnimationFrame(() => projectAndMeasure());
}

export function installCompletedStringConnectorEnds() {
  ensureStyle();
  const topologyView = document.querySelector('#topology-view');
  const observer = new MutationObserver(scheduleProjection);
  if (topologyView) observer.observe(topologyView, { childList: true, subtree: true });
  window.addEventListener('resize', scheduleProjection);
  scheduleProjection();
  return observer;
}

if (typeof document !== 'undefined') installCompletedStringConnectorEnds();

export {
  WorkbenchAnalysisError,
  analyseWorkbench,
  buildEngineeringPackage,
  workbenchCsv,
} from './workbench-analysis-core.mjs';
