const SVG_NS = 'http://www.w3.org/2000/svg';
const STYLE_ID = 'v11-v8-actual-connection-style';
const EVIDENCE_ID = 'v11-v8-actual-connection-evidence';
let scheduled = false;

function ensureStyle() {
  if (document.getElementById(STYLE_ID)) return;
  const style = document.createElement('style');
  style.id = STYLE_ID;
  style.textContent = `
    #selected-detail { position:relative!important; top:auto!important; z-index:auto!important; }
    #selected-detail .detail-scroll { display:block!important; overflow-x:auto!important; overflow-y:hidden!important; min-height:520px; }
    #detail-canvas.v8-actual-connection-detail { display:block!important; height:520px!important; min-width:2200px!important; width:2200px!important; background:#02070b; }
    #detail-canvas .path-sequential, #detail-canvas .path-leapfrog { display:none!important; }
    #detail-canvas .actual-mate-halo { fill:none; stroke:#7f8a94; stroke-width:5.5; opacity:.9; pointer-events:none; }
    #detail-canvas .actual-mate-path { fill:none; stroke:#000; stroke-width:2.6; cursor:pointer; filter:drop-shadow(0 0 .8px #dbe5ed); }
    #detail-canvas .actual-mate-path:focus, #detail-canvas .actual-mate-path:hover { stroke:#f2c94c; stroke-width:3.6; outline:none; }
    #detail-canvas .actual-connection-heading { fill:#56ccf2; font:800 13px ui-monospace,monospace; }
    #detail-canvas .actual-connection-subtitle { fill:#edf3f8; font:700 9px ui-monospace,monospace; }
    #selected-order { display:block!important; }
    @media(max-width:600px){
      #selected-detail { position:sticky!important; top:0!important; z-index:5!important; order:-1!important; }
      #selected-detail .detail-scroll { display:block!important; min-height:460px; }
      #detail-canvas.v8-actual-connection-detail { display:block!important; height:460px!important; min-width:2200px!important; width:2200px!important; }
      #selected-order { display:block!important; font-size:11px; }
    }
  `;
  document.head.append(style);
}

function svgElement(name, attrs = {}) {
  const node = document.createElementNS(SVG_NS, name);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, String(value));
  return node;
}

function connectorPoint(element) {
  if (!element) throw new Error('actual connection endpoint is missing');
  return {
    x: Number(element.getAttribute('cx')),
    y: Number(element.getAttribute('cy')),
  };
}

function routePath(source, destination, record, index) {
  const dx = destination.x - source.x;
  const span = Math.abs(dx);
  if (record.interface_class === 'module_to_module') {
    const moduleSpan = span > 42;
    const above = index % 2 === 0;
    const lift = moduleSpan ? Math.min(78, 28 + span * 0.18) : 24;
    const controlY = (source.y + destination.y) / 2 + (above ? -lift : lift);
    return `M ${source.x} ${source.y} C ${source.x + dx * .28} ${controlY}, ${source.x + dx * .72} ${controlY}, ${destination.x} ${destination.y}`;
  }
  const offset = record.interface_class === 'module_to_string_cable' ? 24 : 12;
  const controlY = (source.y + destination.y) / 2 + (source.y <= destination.y ? -offset : offset);
  return `M ${source.x} ${source.y} C ${source.x + dx * .35} ${controlY}, ${source.x + dx * .65} ${controlY}, ${destination.x} ${destination.y}`;
}

function wrapAndScale(svg) {
  let content = svg.querySelector(':scope > g[data-v8-actual-content="true"]');
  if (content) return content;
  content = svgElement('g', {
    'data-v8-actual-content': 'true',
    transform: 'translate(45 58) scale(1.58)',
  });
  [...svg.childNodes].forEach((node) => content.append(node));
  svg.append(content);
  const oldViewBox = svg.viewBox.baseVal;
  const originalWidth = oldViewBox?.width || 1200;
  svg.setAttribute('viewBox', `0 0 ${Math.ceil(originalWidth * 1.58 + 100)} 420`);
  svg.classList.add('v8-actual-connection-detail');
  return content;
}

function removeLogicalTraversal(content) {
  content.querySelectorAll('.path-sequential,.path-leapfrog').forEach((node) => node.remove());
}

function render() {
  scheduled = false;
  ensureStyle();
  const svg = document.querySelector('#detail-canvas.string-strip');
  const graph = window.__v11CompletedConnectorEndSchedule;
  if (!svg || !graph || graph.string_id !== svg.dataset.stringId) return;
  if (!graph.mating_interfaces?.length) return;

  const content = wrapAndScale(svg);
  removeLogicalTraversal(content);
  content.querySelector(':scope > g.actual-connection-mates')?.remove();
  content.querySelector(':scope > g.actual-connection-title')?.remove();

  const mateGroup = svgElement('g', {
    class: 'actual-connection-mates',
    'data-graph-hash': graph.graph_hash,
    'data-topology-strategy': graph.strategy,
  });
  const titleGroup = svgElement('g', { class: 'actual-connection-title' });
  const heading = svgElement('text', { x: 168, y: -18, class: 'actual-connection-heading' });
  heading.textContent = `${graph.string_id} · ${graph.strategy.toUpperCase()} · ACTUAL GRAPH CONNECTIONS`;
  const subtitle = svgElement('text', { x: 168, y: -3, class: 'actual-connection-subtitle' });
  subtitle.textContent = `${graph.mating_interfaces.length} individual mating interfaces · ${graph.connector_ends.length} connector ends`;
  titleGroup.append(heading, subtitle);

  const classCounts = {};
  graph.mating_interfaces.forEach((record, index) => {
    const [sourceId, destinationId] = record.connector_end_ids;
    const sourceElement = document.getElementById(sourceId);
    const destinationElement = document.getElementById(destinationId);
    if (!sourceElement || !destinationElement) throw new Error(`cannot render ${record.mating_interface_id}: endpoint missing`);
    const d = routePath(connectorPoint(sourceElement), connectorPoint(destinationElement), record, index);
    const halo = svgElement('path', { d, class: 'actual-mate-halo' });
    const path = svgElement('path', {
      id: `${record.mating_interface_id}-PATH`,
      d,
      class: 'actual-mate-path',
      tabindex: 0,
      role: 'button',
      'data-mating-interface-id': record.mating_interface_id,
      'data-interface-class': record.interface_class,
      'data-source-connector-end-id': sourceId,
      'data-destination-connector-end-id': destinationId,
      'data-electrical-edge-id': record.electrical_edge_id,
      'data-graph-hash': graph.graph_hash,
      'aria-label': `${record.mating_interface_id}; ${sourceId} mates with ${destinationId}`,
    });
    const openInspector = () => sourceElement.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    path.addEventListener('click', openInspector);
    path.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        openInspector();
      }
    });
    mateGroup.append(halo, path);
    classCounts[record.interface_class] = (classCounts[record.interface_class] ?? 0) + 1;
  });

  content.insertBefore(mateGroup, content.firstChild);
  content.append(titleGroup);
  const note = document.querySelector('#selected-detail-note');
  if (note) note.textContent = `${graph.string_id} · ${graph.strategy}. Every black interconnect is one graph mating interface between exact connector IDs; the former single traversal polyline is removed.`;

  const connectorTargets = graph.connector_ends.filter((record) => document.getElementById(record.connector_end_id)).length;
  const paths = [...mateGroup.querySelectorAll('.actual-mate-path')];
  const evidence = {
    schema_version: 'globalgrid2050.v11.v8-actual-connections-evidence.v1',
    string_id: graph.string_id,
    strategy: graph.strategy,
    graph_hash: graph.graph_hash,
    modules: graph.modules_per_string,
    connector_end_click_targets: connectorTargets,
    mating_paths: paths.length,
    module_to_module_paths: classCounts.module_to_module ?? 0,
    module_to_string_cable_paths: classCounts.module_to_string_cable ?? 0,
    string_cable_to_inverter_paths: classCounts.string_cable_to_inverter ?? 0,
    logical_traversal_polylines_remaining: content.querySelectorAll('.path-sequential,.path-leapfrog').length,
    path_authority: 'graph.mating_interfaces.connector_end_ids',
    panel_height_px: 520,
    mobile_detail_hidden: false,
    pass: connectorTargets === graph.connector_ends.length
      && paths.length === graph.mating_interfaces.length
      && (classCounts.module_to_module ?? 0) === graph.modules_per_string - 1
      && (classCounts.module_to_string_cable ?? 0) === 2
      && (classCounts.string_cable_to_inverter ?? 0) === 2
      && content.querySelectorAll('.path-sequential,.path-leapfrog').length === 0,
  };
  window.__v11V8ActualConnectionEvidence = evidence;
  let node = document.getElementById(EVIDENCE_ID);
  if (!node) {
    node = document.createElement('script');
    node.id = EVIDENCE_ID;
    node.type = 'application/json';
    document.body.append(node);
  }
  node.textContent = JSON.stringify(evidence, null, 2);
  document.documentElement.dataset.v8ActualConnectionsPass = String(evidence.pass);
  svg.dataset.actualConnectionProjection = 'v8-style-graph-mates-v1';
  if (!evidence.pass) queueMicrotask(() => { throw new Error(`V8 actual-connection projection failed: ${JSON.stringify(evidence)}`); });
}

function schedule() {
  if (scheduled) return;
  scheduled = true;
  requestAnimationFrame(render);
}

window.addEventListener('v11:completed-connector-end-evidence', schedule);
new MutationObserver(schedule).observe(document.querySelector('#topology-view') ?? document.body, { childList: true, subtree: true });
window.addEventListener('resize', schedule);
ensureStyle();
schedule();
