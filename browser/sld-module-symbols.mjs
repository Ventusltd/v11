const STYLE_ID = 'v11-module-junction-box-style';
const EVIDENCE_ID = 'v11-module-junction-box-evidence';
const SVG_NS = 'http://www.w3.org/2000/svg';
const BLACK = 'rgb(0, 0, 0)';
const RED = 'rgb(235, 87, 87)';
const BLUE = 'rgb(47, 128, 237)';

function ensureStyle() {
  if (document.getElementById(STYLE_ID)) return;
  const style = document.createElement('style');
  style.id = STYLE_ID;
  style.textContent = `
    #detail-canvas .module-body { fill:#17212b!important; stroke:#aeb9c4!important; stroke-width:1!important; }
    #detail-canvas .junction-box { fill:#0b1118!important; stroke:#dbe5ed!important; stroke-width:.8!important; }
    #detail-canvas .junction-box-terminal { fill:#dbe5ed!important; stroke:#0b1118!important; stroke-width:.6!important; }
    #detail-canvas .module-factory-lead { stroke:#000!important; fill:none!important; stroke-width:1.8!important; filter:drop-shadow(0 0 .8px #dbe5ed); }
    #detail-canvas .module-connector-marker { stroke:#fff!important; stroke-width:1!important; }
    #detail-canvas .module-connector-negative { fill:#2f80ed!important; }
    #detail-canvas .module-connector-positive { fill:#eb5757!important; }
    #detail-canvas .module-polarity-label { fill:#f4f7fa!important; font-size:7px!important; font-weight:700!important; pointer-events:none; }
  `;
  document.head.append(style);
}

function svgElement(name, attributes = {}) {
  const element = document.createElementNS(SVG_NS, name);
  for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, String(value));
  return element;
}

function moduleIdentity(stringId, electricalIndex) {
  return `${stringId}-M${String(electricalIndex).padStart(2, '0')}`;
}

function decorate(detailSvg) {
  if (!detailSvg) return;
  const stringId = detailSvg.dataset.stringId || 'UNASSIGNED';
  [...detailSvg.querySelectorAll('.topology-cell')].forEach((cell) => {
    if (cell.dataset.moduleSymbolVersion === 'v1') return;
    const electricalIndex = Number(cell.dataset.electricalIndex);
    if (!Number.isInteger(electricalIndex) || electricalIndex < 1) return;
    const moduleId = moduleIdentity(stringId, electricalIndex);
    const x = Number(cell.getAttribute('x'));
    const y = Number(cell.getAttribute('y'));
    const width = Number(cell.getAttribute('width'));
    const height = Number(cell.getAttribute('height'));
    const centreY = y + height / 2;
    const jboxY = y + 7;
    const negJboxX = x + width * 0.37;
    const posJboxX = x + width * 0.63;
    const negTerminalId = `${moduleId}-JBOX_NEG`;
    const posTerminalId = `${moduleId}-JBOX_POS`;
    const negConnectorId = `${moduleId}-NEG-CONNECTOR`;
    const posConnectorId = `${moduleId}-POS-CONNECTOR`;

    cell.id = `${moduleId}-MODULE`;
    cell.classList.add('module-body', 'sld-module-body');
    cell.dataset.moduleId = moduleId;
    cell.dataset.negativeTerminalId = negTerminalId;
    cell.dataset.positiveTerminalId = posTerminalId;
    cell.dataset.moduleSymbolVersion = 'v1';

    const group = svgElement('g', {
      id: `${moduleId}-SYMBOL`,
      class: 'module-symbol',
      'data-module-id': moduleId,
      'data-electrical-index': electricalIndex,
      'data-negative-terminal-id': negTerminalId,
      'data-positive-terminal-id': posTerminalId,
      'aria-label': `${moduleId} module junction-box symbol`,
    });
    const junctionBox = svgElement('rect', {
      id: `${moduleId}-JUNCTION-BOX`, class: 'junction-box',
      x: x + width * 0.25, y: y + 3, width: width * 0.5, height: 9, rx: 1.5,
    });
    const negNode = svgElement('circle', {
      id: negTerminalId, class: 'junction-box-terminal sld-module-terminal junction-box-negative',
      cx: negJboxX, cy: jboxY, r: 1.8,
      'data-terminal-id': negTerminalId, 'data-junction-box-node': 'JBOX_NEG',
      'data-module-id': moduleId, 'data-polarity': 'negative',
      'aria-label': `${moduleId} JBOX_NEG`,
    });
    const posNode = svgElement('circle', {
      id: posTerminalId, class: 'junction-box-terminal sld-module-terminal junction-box-positive',
      cx: posJboxX, cy: jboxY, r: 1.8,
      'data-terminal-id': posTerminalId, 'data-junction-box-node': 'JBOX_POS',
      'data-module-id': moduleId, 'data-polarity': 'positive',
      'aria-label': `${moduleId} JBOX_POS`,
    });
    const negLead = svgElement('line', {
      id: `${moduleId}-NEG-FACTORY-LEAD`, class: 'module-factory-lead',
      x1: negJboxX, y1: jboxY, x2: x, y2: centreY,
      'data-cable-jacket': 'black', 'data-source-terminal-id': negTerminalId,
      'data-destination-connector-id': negConnectorId,
    });
    const posLead = svgElement('line', {
      id: `${moduleId}-POS-FACTORY-LEAD`, class: 'module-factory-lead',
      x1: posJboxX, y1: jboxY, x2: x + width, y2: centreY,
      'data-cable-jacket': 'black', 'data-source-terminal-id': posTerminalId,
      'data-destination-connector-id': posConnectorId,
    });
    const negConnector = svgElement('circle', {
      id: negConnectorId, class: 'module-connector-marker module-connector-negative',
      cx: x, cy: centreY, r: 3,
      'data-connector-id': negConnectorId, 'data-module-id': moduleId,
      'data-terminal-id': negTerminalId, 'data-polarity': 'negative',
      'data-marker-colour': 'blue', 'aria-label': `${moduleId} negative connector marker`,
    });
    const posConnector = svgElement('circle', {
      id: posConnectorId, class: 'module-connector-marker module-connector-positive',
      cx: x + width, cy: centreY, r: 3,
      'data-connector-id': posConnectorId, 'data-module-id': moduleId,
      'data-terminal-id': posTerminalId, 'data-polarity': 'positive',
      'data-marker-colour': 'red', 'aria-label': `${moduleId} positive connector marker`,
    });
    const negLabel = svgElement('text', { class: 'module-polarity-label', x: x + 3.5, y: centreY + 2.5, 'text-anchor': 'middle' });
    negLabel.textContent = '−';
    const posLabel = svgElement('text', { class: 'module-polarity-label', x: x + width - 3.5, y: centreY + 2.5, 'text-anchor': 'middle' });
    posLabel.textContent = '+';
    group.append(junctionBox, negNode, posNode, negLead, posLead, negConnector, posConnector, negLabel, posLabel);
    cell.parentNode.insertBefore(group, cell.nextSibling);
  });
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
    // Local file use may have no Git metadata.
  }
  return null;
}

function mismatches(elements, property, expected, label) {
  return elements.flatMap((element, index) => {
    const actual = getComputedStyle(element)[property];
    return actual === expected ? [] : [{ label, index, id: element.id || null, expected, actual }];
  });
}

let testedShaPromise;
let scheduled = false;
let lastEvidenceJson = '';
let lastFailureSignature = '';

async function decorateAndMeasure() {
  scheduled = false;
  ensureStyle();
  const detailSvg = document.querySelector('#detail-canvas.string-strip');
  decorate(detailSvg);
  if (!detailSvg || !document.querySelector('#status')?.classList.contains('ok')) return;

  const modules = [...detailSvg.querySelectorAll('.module-symbol')];
  const terminals = [...detailSvg.querySelectorAll('.junction-box-terminal')];
  const connectors = [...detailSvg.querySelectorAll('.module-connector-marker')];
  const factoryLeads = [...detailSvg.querySelectorAll('.module-factory-lead')];
  const expectedModules = detailSvg.querySelectorAll('.topology-cell').length;
  const negNodes = terminals.filter((node) => node.dataset.junctionBoxNode === 'JBOX_NEG');
  const posNodes = terminals.filter((node) => node.dataset.junctionBoxNode === 'JBOX_POS');
  const allIds = [...modules, ...terminals, ...connectors, ...factoryLeads].map((element) => element.id || '');
  const missingIds = allIds.filter((id) => !id);
  const duplicateIds = allIds.filter((id, index) => id && allIds.indexOf(id) !== index);
  const styleMismatches = [
    ...mismatches(factoryLeads, 'stroke', BLACK, 'black factory lead'),
    ...mismatches(connectors.filter((item) => item.dataset.polarity === 'positive'), 'fill', RED, 'red positive connector marker'),
    ...mismatches(connectors.filter((item) => item.dataset.polarity === 'negative'), 'fill', BLUE, 'blue negative connector marker'),
  ];
  const countPass = modules.length === expectedModules
    && terminals.length === expectedModules * 2
    && connectors.length === expectedModules * 2
    && factoryLeads.length === expectedModules * 2
    && negNodes.length === expectedModules
    && posNodes.length === expectedModules;
  const pass = countPass && !missingIds.length && !duplicateIds.length && !styleMismatches.length;
  const evidence = {
    schema_version: 'globalgrid2050.v11.module-junction-box-symbol-evidence.v1',
    tested_commit_sha: await (testedShaPromise ??= resolveTestedSha()),
    selected_string_id: detailSvg.dataset.stringId || null,
    contract: {
      cable_jacket: 'black',
      negative_connector_marker: 'blue',
      positive_connector_marker: 'red',
      connector_gender_inferred_from_polarity: false,
      terminal_nodes: ['JBOX_NEG', 'JBOX_POS'],
    },
    counts: {
      module_symbols: modules.length,
      jbox_negative_nodes: negNodes.length,
      jbox_positive_nodes: posNodes.length,
      terminal_nodes: terminals.length,
      connector_markers: connectors.length,
      black_factory_leads: factoryLeads.length,
      expected_modules: expectedModules,
    },
    identities: {
      module_ids: modules.map((item) => item.dataset.moduleId),
      terminal_ids: terminals.map((item) => item.id),
      connector_ids: connectors.map((item) => item.id),
      factory_lead_ids: factoryLeads.map((item) => item.id),
    },
    measurements: modules.map((symbol) => {
      const body = document.getElementById(`${symbol.dataset.moduleId}-MODULE`);
      return {
        module_id: symbol.dataset.moduleId,
        electrical_index: Number(symbol.dataset.electricalIndex),
        x: Number(body?.getAttribute('x')),
        y: Number(body?.getAttribute('y')),
        width: Number(body?.getAttribute('width')),
        height: Number(body?.getAttribute('height')),
      };
    }),
    missing_ids: missingIds,
    duplicate_ids: [...new Set(duplicateIds)],
    computed_style_mismatches: styleMismatches,
    default_str_01_acceptance: {
      applicable: detailSvg.dataset.stringId === 'STR-01' && expectedModules === 30,
      expected_modules: 30,
      expected_terminal_nodes: 60,
      expected_connector_markers: 60,
      pass: detailSvg.dataset.stringId === 'STR-01' && expectedModules === 30
        ? modules.length === 30 && terminals.length === 60 && connectors.length === 60
        : null,
    },
    count_pass: countPass,
    pass,
  };
  window.__v11ModuleJunctionBoxEvidence = evidence;
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
    window.dispatchEvent(new CustomEvent('v11:module-junction-box-evidence', { detail: evidence }));
  }
  detailSvg.dataset.junctionBoxContract = 'v1';
  detailSvg.dataset.sldEvidencePass = String(pass);
  document.documentElement.dataset.moduleJunctionBoxPass = String(pass);
  if (!pass) {
    const signature = JSON.stringify({ countPass, missingIds, duplicateIds, styleMismatches });
    if (signature !== lastFailureSignature) {
      lastFailureSignature = signature;
      queueMicrotask(() => { throw new Error(`Module junction-box contract failed: ${signature}`); });
    }
  } else {
    lastFailureSignature = '';
  }
}

function schedule() {
  if (scheduled) return;
  scheduled = true;
  requestAnimationFrame(() => decorateAndMeasure());
}

export function installModuleJunctionBoxSymbols() {
  ensureStyle();
  const topologyView = document.querySelector('#topology-view');
  const observer = new MutationObserver(schedule);
  if (topologyView) observer.observe(topologyView, { childList: true, subtree: true });
  window.addEventListener('resize', schedule);
  schedule();
  return observer;
}

if (typeof document !== 'undefined') installModuleJunctionBoxSymbols();
