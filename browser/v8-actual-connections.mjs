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
    #detail-canvas .actual-mate-path[data-v8-lane="outward"] { stroke-width:2.8; }
    #detail-canvas .actual-mate-path[data-v8-lane="return"] { stroke-width:2.8; }
    #detail-canvas .actual-mate-path[data-v8-turnaround="true"] { stroke-width:3.2; }
    #detail-canvas .actual-connection-heading { fill:#56ccf2; font:800 13px ui-monospace,monospace; }
    #detail-canvas .actual-connection-subtitle { fill:#edf3f8; font:700 9px ui-monospace,monospace; }
    #detail-canvas .actual-turnaround-label { fill:#f2c94c; font:800 9px ui-monospace,monospace; pointer-events:none; }
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

function connectorRecord(graph, connectorEndId) {
  const record = graph.connector_ends.find((item) => item.connector_end_id === connectorEndId);
  if (!record) throw new Error(`actual connection graph record is missing for ${connectorEndId}`);
  return record;
}

function v8MateGeometry(graph, record, source, destination, index) {
  const [sourceId, destinationId] = record.connector_end_ids;
  const sourceRecord = connectorRecord(graph, sourceId);
  const destinationRecord = connectorRecord(graph, destinationId);
  const dx = destination.x - source.x;
  const span = Math.abs(dx);

  if (record.interface_class !== 'module_to_module') {
    const offset = record.interface_class === 'module_to_string_cable' ? 24 : 12;
    const controlY = (source.y + destination.y) / 2 + (source.y <= destination.y ? -offset : offset);
    return {
      d: `M ${source.x} ${source.y} C ${source.x + dx * .35} ${controlY}, ${source.x + dx * .65} ${controlY}, ${destination.x} ${destination.y}`,
      lane: record.interface_class,
      isTurnaround: false,
      sourceIndex: null,
      destinationIndex: null,
      labelPoint: null,
    };
  }

  const sourceIndex = Number(sourceRecord.electrical_index);
  const destinationIndex = Number(destinationRecord.electrical_index);
  const leapfrog = graph.strategy === 'leapfrog';
  const isOutward = leapfrog && sourceIndex % 2 === 1 && destinationIndex % 2 === 1;
  const isReturn = leapfrog && sourceIndex % 2 === 0 && destinationIndex % 2 === 0;
  const isTurnaround = leapfrog
    && Math.abs(sourceIndex - destinationIndex) === 1
    && Math.max(sourceIndex, destinationIndex) === graph.modules_per_string;
  const lane = leapfrog
    ? isOutward ? 'outward' : isReturn ? 'return' : isTurnaround ? 'turnaround' : 'transition'
    : 'sequential';
  const above = lane === 'outward' || lane === 'sequential';
  const direction = above ? -1 : 1;
  const lift = Math.min(78, 22 + span * .12 + (index % 2) * 3);
  const controlY = (source.y + destination.y) / 2 + direction * lift;

  return {
    d: `M ${source.x} ${source.y} C ${source.x} ${controlY}, ${destination.x} ${controlY}, ${destination.x} ${destination.y}`,
    lane,
    isTurnaround,
    sourceIndex,
    destinationIndex,
    labelPoint: isTurnaround
      ? { x: (source.x + destination.x) / 2 - 56, y: Math.min(source.y, destination.y) - 42 }
      : null,
  };
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
  content.querySelector(':scope > g.actual-connection-annotations')?.remove();

  const mateGroup = svgElement('g', {
    class: 'actual-connection-mates',
    'data-graph-hash': graph.graph_hash,
    'data-topology-strategy': graph.strategy,
  });
  const annotationGroup = svgElement('g', { class: 'actual-connection-annotations' });
  const titleGroup = svgElement('g', { class: 'actual-connection-title' });
  const heading = svgElement('text', { x: 168, y: -18, class: 'actual-connection-heading' });
  heading.textContent = `${graph.string_id} · ${graph.strategy.toUpperCase()} · ACTUAL GRAPH CONNECTIONS`;
  const subtitle = svgElement('text', { x: 168, y: -3, class: 'actual-connection-subtitle' });
  subtitle.textContent = `${graph.mating_interfaces.length} individual mating interfaces · ${graph.connector_ends.length} connector ends`;
  titleGroup.append(heading, subtitle);

  const classCounts = {};
  const laneCounts = {};
  const endpointPairs = [];
  let turnaround = null;

  graph.mating_interfaces.forEach((record, index) => {
    const [sourceId, destinationId] = record.connector_end_ids;
    const sourceElement = document.getElementById(sourceId);
    const destinationElement = document.getElementById(destinationId);
    if (!sourceElement || !destinationElement) throw new Error(`cannot render ${record.mating_interface_id}: endpoint missing`);
    const geometry = v8MateGeometry(
      graph,
      record,
      connectorPoint(sourceElement),
      connectorPoint(destinationElement),
      index,
    );
    const halo = svgElement('path', { d: geometry.d, class: 'actual-mate-halo' });
    const path = svgElement('path', {
      id: `${record.mating_interface_id}-PATH`,
      d: geometry.d,
      class: 'actual-mate-path',
      tabindex: 0,
      role: 'button',
      'data-mating-interface-id': record.mating_interface_id,
      'data-interface-class': record.interface_class,
      'data-source-connector-end-id': sourceId,
      'data-destination-connector-end-id': destinationId,
      'data-electrical-edge-id': record.electrical_edge_id,
      'data-graph-hash': graph.graph_hash,
      'data-v8-lane': geometry.lane,
      'data-v8-turnaround': geometry.isTurnaround,
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
    laneCounts[geometry.lane] = (laneCounts[geometry.lane] ?? 0) + 1;
    endpointPairs.push(`${sourceId}->${destinationId}`);

    if (geometry.isTurnaround && geometry.labelPoint) {
      turnaround = {
        mating_interface_id: record.mating_interface_id,
        source_connector_end_id: sourceId,
        destination_connector_end_id: destinationId,
        source_module_index: geometry.sourceIndex,
        destination_module_index: geometry.destinationIndex,
      };
      const label = svgElement('text', {
        x: geometry.labelPoint.x,
        y: geometry.labelPoint.y,
        class: 'actual-turnaround-label',
      });
      label.textContent = `TURNAROUND M${geometry.sourceIndex}+ → M${geometry.destinationIndex}−`;
      annotationGroup.append(label);
    }
  });

  content.insertBefore(mateGroup, content.firstChild);
  content.append(annotationGroup, titleGroup);
  const note = document.querySelector('#selected-detail-note');
  if (note) {
    note.textContent = graph.strategy === 'leapfrog'
      ? `${graph.string_id} · Leapfrog. Odd-module outward hops are above, even-module return hops are below, and the far-end turnaround is explicit. Every path comes from exact graph connector IDs.`
      : `${graph.string_id} · Sequential. Adjacent module matings are individually drawn above the fixed M1–M30 row; every path comes from exact graph connector IDs.`;
  }

  const connectorTargets = graph.connector_ends.filter((record) => document.getElementById(record.connector_end_id)).length;
  const paths = [...mateGroup.querySelectorAll('.actual-mate-path')];
  const expectedLeapfrogOutward = graph.strategy === 'leapfrog' ? Math.ceil(graph.modules_per_string / 2) - 1 : 0;
  const expectedLeapfrogReturn = graph.strategy === 'leapfrog' ? Math.floor(graph.modules_per_string / 2) - 1 : 0;
  const topologyGeometryPass = graph.strategy === 'leapfrog'
    ? (laneCounts.outward ?? 0) === expectedLeapfrogOutward
      && (laneCounts.return ?? 0) === expectedLeapfrogReturn
      && (laneCounts.turnaround ?? 0) === 1
      && turnaround !== null
    : (laneCounts.sequential ?? 0) === graph.modules_per_string - 1;
  const evidence = {
    schema_version: 'globalgrid2050.v11.v8-actual-connections-evidence.v2',
    string_id: graph.string_id,
    strategy: graph.strategy,
    graph_hash: graph.graph_hash,
    modules: graph.modules_per_string,
    connector_end_click_targets: connectorTargets,
    mating_paths: paths.length,
    module_to_module_paths: classCounts.module_to_module ?? 0,
    module_to_string_cable_paths: classCounts.module_to_string_cable ?? 0,
    string_cable_to_inverter_paths: classCounts.string_cable_to_inverter ?? 0,
    v8_lane_counts: laneCounts,
    expected_leapfrog_outward_hops: expectedLeapfrogOutward,
    expected_leapfrog_return_hops: expectedLeapfrogReturn,
    turnaround,
    mating_endpoint_pairs: endpointPairs,
    topology_geometry_pass: topologyGeometryPass,
    logical_traversal_polylines_remaining: content.querySelectorAll('.path-sequential,.path-leapfrog').length,
    path_authority: 'graph.mating_interfaces.connector_end_ids',
    lane_authority: 'graph strategy plus connector-end electrical_index',
    panel_height_px: 520,
    mobile_detail_hidden: false,
    pass: connectorTargets === graph.connector_ends.length
      && paths.length === graph.mating_interfaces.length
      && (classCounts.module_to_module ?? 0) === graph.modules_per_string - 1
      && (classCounts.module_to_string_cable ?? 0) === 2
      && (classCounts.string_cable_to_inverter ?? 0) === 2
      && topologyGeometryPass
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
  svg.dataset.actualConnectionProjection = 'v8-style-graph-mates-v2';
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
