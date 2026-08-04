export const SLD_VISUAL_CONTRACT = Object.freeze({
  schema_version: 'globalgrid2050.v11.sld-visual-contract.v1',
  cable_jacket: 'black',
  positive_connector_marker: 'red',
  negative_connector_marker: 'blue',
  inverter: 'orange',
  provisional_route: 'dashed-black',
  polarity_applies_to: 'connector-and-termination-markers-only',
});

const STYLE_ID = 'v11-sld-visual-contract-style';
const LEGEND_ID = 'v11-sld-visual-contract-legend';
const EVIDENCE_ID = 'v11-sld-visual-contract-evidence';
const BLACK = 'rgb(0, 0, 0)';
const RED = 'rgb(235, 87, 87)';
const BLUE = 'rgb(47, 128, 237)';
const ORANGE = 'rgb(255, 159, 67)';

function ensureStyle() {
  if (document.getElementById(STYLE_ID)) return;
  const style = document.createElement('style');
  style.id = STYLE_ID;
  style.textContent = `
    .pv-cable,
    .path-sequential,
    .path-leapfrog,
    .home-positive,
    .home-negative {
      stroke: #000 !important;
      fill: none !important;
    }
    #physical-canvas .route,
    .provisional-route {
      stroke: #000 !important;
      stroke-dasharray: 0.35 0.24 !important;
      opacity: .72 !important;
    }
    .inverter-block,
    #physical-canvas .inverter {
      fill: #ff9f43 !important;
      stroke: #ffd18a !important;
    }
    .connector-marker {
      stroke: #fff !important;
      stroke-width: 1.25 !important;
    }
    .connector-marker.connector-negative {
      fill: #2f80ed !important;
    }
    .connector-marker.connector-positive {
      fill: #eb5757 !important;
    }
    #${LEGEND_ID} {
      display: flex;
      flex-wrap: wrap;
      gap: 8px 14px;
      align-items: center;
      margin: 0 0 12px;
      padding: 8px 10px;
      border: 1px solid #303946;
      background: #0b1118;
      color: #dbe5ed;
      font-size: 12px;
    }
    #${LEGEND_ID} span { display: inline-flex; align-items: center; gap: 6px; }
    #${LEGEND_ID} i { display: inline-block; flex: 0 0 auto; }
    #${LEGEND_ID} .legend-cable { width: 26px; border-top: 3px solid #000; box-shadow: 0 0 0 1px #606b75; }
    #${LEGEND_ID} .legend-route { width: 26px; border-top: 3px dashed #000; box-shadow: 0 0 0 1px #606b75; }
    #${LEGEND_ID} .legend-positive,
    #${LEGEND_ID} .legend-negative { width: 12px; height: 12px; border-radius: 50%; border: 1px solid #fff; }
    #${LEGEND_ID} .legend-positive { background: #eb5757; }
    #${LEGEND_ID} .legend-negative { background: #2f80ed; }
    #${LEGEND_ID} .legend-inverter { width: 15px; height: 12px; background: #ff9f43; border: 1px solid #ffd18a; }
  `;
  document.head.append(style);
}

function ensureLegend() {
  if (document.getElementById(LEGEND_ID)) return;
  const topologyView = document.querySelector('#topology-view');
  const intro = topologyView?.querySelector('.topology-intro');
  if (!topologyView || !intro) return;
  const legend = document.createElement('div');
  legend.id = LEGEND_ID;
  legend.setAttribute('aria-label', 'SLD visual contract');
  legend.innerHTML = `
    <span><i class="legend-cable"></i>Black physical PV cable</span>
    <span><i class="legend-positive"></i>Red positive connector marker</span>
    <span><i class="legend-negative"></i>Blue negative connector marker</span>
    <span><i class="legend-inverter"></i>Orange inverter</span>
    <span><i class="legend-route"></i>Dashed black provisional route</span>
  `;
  intro.insertAdjacentElement('afterend', legend);
}

function markerIdentity(svg, polarity) {
  const stringId = svg.dataset.stringId || 'UNASSIGNED';
  const surface = svg.id === 'detail-canvas' ? 'DETAIL' : 'OVERVIEW';
  return `${surface}-${stringId}-INVERTER-${polarity === 'negative' ? 'NEG' : 'POS'}-CONNECTOR`;
}

function decorateStringSvg(svg) {
  svg.querySelectorAll('.path-sequential,.path-leapfrog,.home-positive,.home-negative').forEach((element) => {
    element.classList.add('pv-cable');
    element.dataset.cableJacket = 'black';
  });
  const terminals = [...svg.querySelectorAll(':scope > circle.terminal')];
  if (terminals.length < 2) return;
  const assignments = [
    [terminals[0], 'negative'],
    [terminals[1], 'positive'],
  ];
  for (const [terminal, polarity] of assignments) {
    const connectorId = markerIdentity(svg, polarity);
    terminal.id = connectorId;
    terminal.classList.add('connector-marker', `connector-${polarity}`);
    terminal.dataset.connectorId = connectorId;
    terminal.dataset.polarity = polarity;
    terminal.dataset.markerColour = polarity === 'positive' ? 'red' : 'blue';
    terminal.setAttribute('aria-label', `${polarity} connector marker`);
  }
}

function decoratePhysicalRoutes() {
  document.querySelectorAll('#physical-canvas .route').forEach((element) => {
    element.classList.add('pv-cable', 'provisional-route');
    element.dataset.cableJacket = 'black';
    element.dataset.routeAuthority = 'provisional';
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
    // Immutable public URLs are resolved above; local file use may have no Git metadata.
  }
  return null;
}

function computedMismatch(elements, property, expected, label) {
  const mismatches = [];
  elements.forEach((element, index) => {
    const actual = getComputedStyle(element)[property];
    if (actual !== expected) mismatches.push({ label, index, id: element.id || null, expected, actual });
  });
  return mismatches;
}

let testedShaPromise;
let scheduled = false;
let lastFailureSignature = '';
let lastEvidenceJson = '';

function stableWorkbenchReady() {
  return document.querySelector('#status')?.classList.contains('ok') === true;
}

async function decorateAndMeasure() {
  scheduled = false;
  ensureStyle();
  ensureLegend();
  const overviewSvgs = [...document.querySelectorAll('#topology-board .string-strip')];
  const detailSvg = document.querySelector('#detail-canvas.string-strip');
  overviewSvgs.forEach(decorateStringSvg);
  if (detailSvg) decorateStringSvg(detailSvg);
  decoratePhysicalRoutes();

  if (!overviewSvgs.length || !stableWorkbenchReady()) return;
  const overviewMarkers = [...document.querySelectorAll('#topology-board .connector-marker')];
  const detailMarkers = [...document.querySelectorAll('#detail-canvas .connector-marker')];
  const cables = [...document.querySelectorAll('.string-strip .pv-cable')];
  const routes = [...document.querySelectorAll('#physical-canvas .route')];
  const inverters = [...document.querySelectorAll('.inverter-block,#physical-canvas .inverter')];
  const positiveMarkers = [...document.querySelectorAll('.connector-marker.connector-positive')];
  const negativeMarkers = [...document.querySelectorAll('.connector-marker.connector-negative')];
  const ids = [...overviewMarkers, ...detailMarkers].map((element) => element.id);
  const missingIds = ids.filter((id) => !id);
  const duplicateIds = ids.filter((id, index) => id && ids.indexOf(id) !== index);
  const mismatches = [
    ...computedMismatch(cables, 'stroke', BLACK, 'physical PV cable stroke'),
    ...computedMismatch(routes, 'stroke', BLACK, 'provisional route stroke'),
    ...computedMismatch(positiveMarkers, 'fill', RED, 'positive connector marker'),
    ...computedMismatch(negativeMarkers, 'fill', BLUE, 'negative connector marker'),
    ...computedMismatch(inverters, 'fill', ORANGE, 'inverter fill'),
  ];
  routes.forEach((route, index) => {
    const dash = getComputedStyle(route).strokeDasharray;
    if (!dash || dash === 'none') mismatches.push({ label: 'provisional route dash', index, id: route.id || null, expected: 'dashed', actual: dash });
  });
  const expectedOverviewMarkers = overviewSvgs.length * 2;
  const expectedDetailMarkers = detailSvg ? 2 : 0;
  const markerCountPass = overviewMarkers.length === expectedOverviewMarkers
    && detailMarkers.length === expectedDetailMarkers;
  const pass = markerCountPass && !missingIds.length && !duplicateIds.length && !mismatches.length;
  const evidence = {
    schema_version: SLD_VISUAL_CONTRACT.schema_version,
    tested_commit_sha: await (testedShaPromise ??= resolveTestedSha()),
    contract: SLD_VISUAL_CONTRACT,
    counts: {
      overview_strings: overviewSvgs.length,
      overview_connector_markers: overviewMarkers.length,
      expected_overview_connector_markers: expectedOverviewMarkers,
      detail_connector_markers: detailMarkers.length,
      expected_detail_connector_markers: expectedDetailMarkers,
      black_cable_elements: cables.length,
      provisional_routes: routes.length,
      orange_inverters: inverters.length,
      positive_markers: positiveMarkers.length,
      negative_markers: negativeMarkers.length,
    },
    connector_ids: ids,
    missing_connector_ids: missingIds,
    duplicate_connector_ids: [...new Set(duplicateIds)],
    computed_style_mismatches: mismatches,
    marker_count_pass: markerCountPass,
    pass,
  };
  window.__v11SldVisualContractEvidence = evidence;
  let evidenceNode = document.getElementById(EVIDENCE_ID);
  if (!evidenceNode) {
    evidenceNode = document.createElement('script');
    evidenceNode.id = EVIDENCE_ID;
    evidenceNode.type = 'application/json';
    document.body.append(evidenceNode);
  }
  const evidenceJson = JSON.stringify(evidence, null, 2);
  if (evidenceJson !== lastEvidenceJson) {
    lastEvidenceJson = evidenceJson;
    evidenceNode.textContent = evidenceJson;
    window.dispatchEvent(new CustomEvent('v11:sld-visual-contract-evidence', { detail: evidence }));
  }
  document.documentElement.dataset.sldVisualContractPass = String(pass);

  if (!pass) {
    const signature = JSON.stringify({ markerCountPass, missingIds, duplicateIds, mismatches });
    if (signature !== lastFailureSignature) {
      lastFailureSignature = signature;
      queueMicrotask(() => { throw new Error(`SLD visual contract failed: ${signature}`); });
    }
  } else {
    lastFailureSignature = '';
  }
}

function scheduleMeasure() {
  if (scheduled) return;
  scheduled = true;
  requestAnimationFrame(() => decorateAndMeasure());
}

export function installSldVisualContract() {
  ensureStyle();
  ensureLegend();
  const observer = new MutationObserver(scheduleMeasure);
  const topologyView = document.querySelector('#topology-view');
  const physicalCanvas = document.querySelector('#physical-canvas');
  if (topologyView) observer.observe(topologyView, { childList: true, subtree: true });
  if (physicalCanvas) observer.observe(physicalCanvas, { childList: true, subtree: true });
  window.addEventListener('resize', scheduleMeasure);
  scheduleMeasure();
  return observer;
}

if (typeof document !== 'undefined') installSldVisualContract();
