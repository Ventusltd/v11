import './sld-visual-contract.mjs';
import './sld-module-symbols.mjs';
import { connectorAccounting } from './connector-accounting.mjs';

export const COMPLETED_CONNECTOR_END_SCHEDULE_SCHEMA = 'globalgrid2050.v11.completed-string-connector-end-schedule.v1';

const STYLE_ID = 'v11-completed-connector-end-style';
const EVIDENCE_ID = 'v11-completed-connector-end-evidence';
const SVG_NS = 'http://www.w3.org/2000/svg';
const BLACK = 'rgb(0, 0, 0)';
const RED = 'rgb(235, 87, 87)';
const BLUE = 'rgb(47, 128, 237)';

function stableHash(value) {
  const text = JSON.stringify(value);
  let hash = 0x811c9dc5;
  for (let index = 0; index < text.length; index += 1) {
    hash ^= text.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }
  return `fnv1a32:${(hash >>> 0).toString(16).padStart(8, '0')}`;
}

function polarityRecord(polarity) {
  return polarity === 'positive'
    ? { polarity: 'positive', marker_colour: 'red' }
    : { polarity: 'negative', marker_colour: 'blue' };
}

function moduleConnectorEnd(stringId, electricalIndex, polarity) {
  const moduleId = `${stringId}-M${String(electricalIndex).padStart(2, '0')}`;
  const suffix = polarity === 'positive' ? 'POS' : 'NEG';
  return {
    connector_end_id: `${moduleId}-${suffix}-CONNECTOR`,
    connector_system_boundary: 'module',
    component_id: moduleId,
    component_type: 'pv_module',
    module_id: moduleId,
    electrical_index: electricalIndex,
    junction_box_terminal_id: `${moduleId}-JBOX_${suffix}`,
    ...polarityRecord(polarity),
    connector_type: 'module_factory_lead_connector_end',
    connector_manufacturer: null,
    connector_model: null,
    contact_gender: 'unverified',
    mate_connector_end_id: null,
    mating_interface_id: null,
    interface_class: null,
    mate_status: 'pending_electrical_graph',
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
    connector_type: 'field_fitted_string_cable_connector_end',
    connector_manufacturer: null,
    connector_model: null,
    contact_gender: 'unverified',
    cable_id: cableId,
    cable_class: 'pv_string_cable',
    cable_sheath_colour: 'black',
    cable_side: side,
    mate_connector_end_id: null,
    mating_interface_id: null,
    interface_class: side === 'module' ? 'module_to_string_cable' : 'string_cable_to_inverter',
    mate_status: 'pending_electrical_graph',
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
    connector_type: 'inverter_dc_socket',
    connector_manufacturer: null,
    connector_model: null,
    contact_gender: 'unverified',
    string_id: stringId,
    mppt_id: mpptId,
    physical_dc_input_id: inputId,
    pv_terminal: null,
    pv_terminal_status: 'pending_sungrow_terminal_projection',
    mate_connector_end_id: null,
    mating_interface_id: null,
    interface_class: 'string_cable_to_inverter',
    mate_status: 'pending_electrical_graph',
    evidence_state: 'derived_input_ownership',
  };
}

export function buildCompletedStringConnectorEndSchedule({ stringId, moduleCount, inputId, mpptId }) {
  if (!/^STR-\d{2,}$/.test(String(stringId))) throw new Error('stringId must be a stable STR-nn identity');
  if (!/^IN-\d{2,}$/.test(String(inputId))) throw new Error('inputId must be a stable IN-nn identity');
  if (!/^MPPT-\d{2,}$/.test(String(mpptId))) throw new Error('mpptId must be a stable MPPT-nn identity');

  const accounting = connectorAccounting(moduleCount);
  const connectorEnds = [];
  for (let index = 1; index <= accounting.modules_per_string; index += 1) {
    connectorEnds.push(moduleConnectorEnd(stringId, index, 'negative'));
    connectorEnds.push(moduleConnectorEnd(stringId, index, 'positive'));
  }
  connectorEnds.push(cableConnectorEnd(stringId, 'negative', 'module'));
  connectorEnds.push(cableConnectorEnd(stringId, 'negative', 'inverter'));
  connectorEnds.push(cableConnectorEnd(stringId, 'positive', 'module'));
  connectorEnds.push(cableConnectorEnd(stringId, 'positive', 'inverter'));
  connectorEnds.push(inverterConnectorEnd(stringId, inputId, mpptId, 'negative'));
  connectorEnds.push(inverterConnectorEnd(stringId, inputId, mpptId, 'positive'));

  const schedule = {
    schema_version: COMPLETED_CONNECTOR_END_SCHEDULE_SCHEMA,
    string_id: stringId,
    mppt_id: mpptId,
    physical_dc_input_id: inputId,
    modules_per_string: accounting.modules_per_string,
    accounting,
    connector_ends: connectorEnds,
    topology_status: 'connector_ends_authoritative_mates_pending_electrical_graph',
  };
  schedule.graph_hash = stableHash(schedule);
  validateCompletedStringConnectorEndSchedule(schedule);
  return schedule;
}

export function validateCompletedStringConnectorEndSchedule(schedule) {
  const accounting = connectorAccounting(schedule.modules_per_string);
  const ends = schedule.connector_ends;
  const ids = ends.map((item) => item.connector_end_id);
  const boundaries = (name) => ends.filter((item) => item.connector_system_boundary === name);
  const positive = ends.filter((item) => item.polarity === 'positive');
  const negative = ends.filter((item) => item.polarity === 'negative');

  if (ids.some((id) => !id) || new Set(ids).size !== ids.length) throw new Error('connector-end IDs must be present and unique');
  if (boundaries('module').length !== accounting.module_connector_end_count) throw new Error('module connector-end count mismatch');
  if (boundaries('string_cable').length !== accounting.string_cable_connector_end_count) throw new Error('string-cable connector-end count mismatch');
  if (boundaries('inverter').length !== accounting.inverter_connector_end_count) throw new Error('inverter connector-end count mismatch');
  if (ends.length !== accounting.complete_system_connector_end_count) throw new Error('complete-system connector-end count mismatch');
  if (positive.length !== accounting.positive_connector_end_count || negative.length !== accounting.negative_connector_end_count) {
    throw new Error('polarity connector-end count mismatch');
  }
  if (positive.some((item) => item.marker_colour !== 'red') || negative.some((item) => item.marker_colour !== 'blue')) {
    throw new Error('connector marker colours must follow polarity');
  }
  if (ends.some((item) => item.contact_gender !== 'unverified')) throw new Error('contact gender must remain unverified without manufacturer evidence');
  return schedule;
}

function ensureStyle() {
  if (document.getElementById(STYLE_ID)) return;
  const style = document.createElement('style');
  style.id = STYLE_ID;
  style.textContent = `
    #detail-canvas .completed-system-connector-end { stroke:#fff!important; stroke-width:1!important; }
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

function applyConnectorRecord(element, record) {
  element.id = record.connector_end_id;
  element.classList.add(
    'completed-system-connector-end',
    record.polarity === 'positive' ? 'completed-system-connector-positive' : 'completed-system-connector-negative',
  );
  element.dataset.connectorEndId = record.connector_end_id;
  element.dataset.connectorSystemBoundary = record.connector_system_boundary;
  element.dataset.componentId = record.component_id;
  element.dataset.componentType = record.component_type;
  element.dataset.polarity = record.polarity;
  element.dataset.markerColour = record.marker_colour;
  element.dataset.contactGender = record.contact_gender;
  element.dataset.mateStatus = record.mate_status;
  element.setAttribute('aria-label', `${record.connector_end_id} ${record.polarity} connector end`);
}

function appendCableProjection(detailSvg, schedule, polarity, y) {
  const suffix = polarity === 'positive' ? 'POS' : 'NEG';
  const moduleRecord = schedule.connector_ends.find((item) => item.connector_end_id === `${schedule.string_id}-${suffix}-STRING-CABLE-MODULE-END`);
  const inverterRecord = schedule.connector_ends.find((item) => item.connector_end_id === `${schedule.string_id}-${suffix}-STRING-CABLE-INVERTER-END`);
  const group = detailSvg.querySelector(`#${schedule.string_id}-COMPLETED-CONNECTOR-ENDS`);
  const line = svgElement('line', {
    id: `${schedule.string_id}-${suffix}-STRING-CABLE-BODY`,
    class: 'completed-system-string-cable',
    x1: 141, y1: y, x2: 158, y2: y,
    'data-cable-id': `${schedule.string_id}-${suffix}-STRING-CABLE`,
    'data-cable-sheath-colour': 'black',
    'data-source-connector-end-id': inverterRecord.connector_end_id,
    'data-destination-connector-end-id': moduleRecord.connector_end_id,
  });
  const inverterEnd = svgElement('circle', { cx: 141, cy: y, r: 4 });
  const moduleEnd = svgElement('circle', { cx: 158, cy: y, r: 4 });
  applyConnectorRecord(inverterEnd, inverterRecord);
  applyConnectorRecord(moduleEnd, moduleRecord);
  group.append(line, inverterEnd, moduleEnd);
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
  const schedule = buildCompletedStringConnectorEndSchedule({ stringId, moduleCount: expectedModules, inputId, mpptId });

  const terminalNodes = [...detailSvg.querySelectorAll('circle.terminal')];
  if (terminalNodes.length !== 2) throw new Error('selected-string SLD must expose exactly two inverter terminal markers');
  const inverterNegative = schedule.connector_ends.find((item) => item.connector_system_boundary === 'inverter' && item.polarity === 'negative');
  const inverterPositive = schedule.connector_ends.find((item) => item.connector_system_boundary === 'inverter' && item.polarity === 'positive');
  let group = detailSvg.querySelector(`#${stringId}-COMPLETED-CONNECTOR-ENDS`);
  const needsProjection = !group
    || group.dataset.graphHash !== schedule.graph_hash
    || detailSvg.querySelectorAll('[data-connector-system-boundary="string_cable"]').length !== 4
    || terminalNodes[0].dataset.connectorEndId !== inverterNegative.connector_end_id
    || terminalNodes[1].dataset.connectorEndId !== inverterPositive.connector_end_id;

  if (needsProjection) {
    group?.remove();
    group = svgElement('g', {
      id: `${stringId}-COMPLETED-CONNECTOR-ENDS`,
      class: 'completed-system-connector-ends',
      'data-schedule-schema': schedule.schema_version,
      'data-graph-hash': schedule.graph_hash,
    });
    detailSvg.append(group);

    applyConnectorRecord(terminalNodes[0], inverterNegative);
    applyConnectorRecord(terminalNodes[1], inverterPositive);
    terminalNodes[0].classList.add('inverter-connector-end');
    terminalNodes[1].classList.add('inverter-connector-end');

    appendCableProjection(detailSvg, schedule, 'negative', Number(terminalNodes[0].getAttribute('cy')));
    appendCableProjection(detailSvg, schedule, 'positive', Number(terminalNodes[1].getAttribute('cy')));

    const label = svgElement('text', { class: 'completed-system-label', x: 137, y: 154, 'text-anchor': 'middle' });
    label.textContent = `${schedule.accounting.complete_system_connector_end_count} ends · ${schedule.accounting.total_mated_interface_count} interfaces`;
    group.append(label);
  }

  const visibleEnds = [
    ...detailSvg.querySelectorAll('.module-connector-marker'),
    ...detailSvg.querySelectorAll('.completed-system-connector-end'),
  ];
  const cableEnds = [...detailSvg.querySelectorAll('.string-cable-connector-end, [data-connector-system-boundary="string_cable"]')];
  const inverterEnds = [...detailSvg.querySelectorAll('.inverter-connector-end')];
  const positiveEnds = visibleEnds.filter((item) => item.dataset.polarity === 'positive');
  const negativeEnds = visibleEnds.filter((item) => item.dataset.polarity === 'negative');
  const cableBodies = [...detailSvg.querySelectorAll('.completed-system-string-cable')];
  const ids = visibleEnds.map((item) => item.dataset.connectorEndId || item.dataset.connectorId || item.id);
  const missingIds = ids.filter((id) => !id);
  const duplicateIds = ids.filter((id, index) => id && ids.indexOf(id) !== index);
  const scheduleIds = schedule.connector_ends.map((item) => item.connector_end_id).sort();
  const renderedIds = [...ids].sort();
  const identityPass = JSON.stringify(scheduleIds) === JSON.stringify(renderedIds);
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
  };
  const countPass = counts.module_connector_ends === schedule.accounting.module_connector_end_count
    && counts.string_cable_connector_ends === schedule.accounting.string_cable_connector_end_count
    && counts.inverter_connector_ends === schedule.accounting.inverter_connector_end_count
    && counts.complete_system_connector_ends === schedule.accounting.complete_system_connector_end_count
    && counts.positive_red_connector_ends === schedule.accounting.positive_connector_end_count
    && counts.negative_blue_connector_ends === schedule.accounting.negative_connector_end_count
    && counts.black_string_cable_bodies === 2;
  const pass = countPass && identityPass && !missingIds.length && !duplicateIds.length && !computedStyleMismatches.length;
  const evidence = {
    schema_version: 'globalgrid2050.v11.completed-string-connector-end-evidence.v1',
    tested_commit_sha: await (testedShaPromise ??= resolveTestedSha()),
    selected_string_id: stringId,
    mppt_id: mpptId,
    physical_dc_input_id: inputId,
    graph_hash: schedule.graph_hash,
    schedule_schema: schedule.schema_version,
    topology_status: schedule.topology_status,
    counts,
    expected: schedule.accounting,
    connector_end_ids: scheduleIds,
    missing_ids: missingIds,
    duplicate_ids: [...new Set(duplicateIds)],
    identity_pass: identityPass,
    count_pass: countPass,
    computed_style_mismatches: computedStyleMismatches,
    default_30_module_acceptance: {
      applicable: expectedModules === 30,
      expected_complete_system_connector_ends: 66,
      expected_mated_interfaces: 33,
      expected_positive_red_connector_ends: 33,
      expected_negative_blue_connector_ends: 33,
      pass: expectedModules === 30 ? countPass : null,
    },
    contact_gender_inferred_from_polarity: false,
    mate_identities_status: 'pending_electrical_graph',
    pass,
  };

  window.__v11CompletedConnectorEndSchedule = schedule;
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
  detailSvg.dataset.completedConnectorEndContract = 'v1';
  detailSvg.dataset.completedConnectorEndPass = String(pass);
  document.documentElement.dataset.completedConnectorEndPass = String(pass);

  if (!pass) {
    const signature = JSON.stringify({ counts, identityPass, missingIds, duplicateIds, computedStyleMismatches });
    if (signature !== lastFailureSignature) {
      lastFailureSignature = signature;
      queueMicrotask(() => { throw new Error(`Completed connector-end contract failed: ${signature}`); });
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
