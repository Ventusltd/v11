const NS = 'http://www.w3.org/2000/svg';
const svg = document.querySelector('#sld');
const viewport = document.querySelector('#viewport');

const MODULES = 30;
const STRINGS = 24;
const INPUTS_PER_MPPT = 2;
const MPPTS = STRINGS / INPUTS_PER_MPPT;

const modulePhysical = Object.freeze({
  model: 'Trina TSM-DEG21C.20',
  height_mm: 2384,
  width_mm: 1303,
  depth_mm: 33,
  jbox_axis_from_bottom_mm: 1192,
  jbox_axis_basis: 'derived geometric centre of the manufacturer back-view drawing',
  cable_positive_mm: 350,
  cable_negative_mm: 280,
  cable_length_status: 'manufacturer standard; custom length available',
  connector_family: 'MC4 EVO2 / TS4; regional datasheet governs',
  connector_gender: 'unverified',
  polarity_root_side: 'unverified',
  evidence: 'Trina TSM-DEG21C.20 datasheet TSM_EN_2024_A',
});

const connectorReference = Object.freeze({
  negative_x_mm: modulePhysical.width_mm / 2 - modulePhysical.cable_negative_mm,
  positive_x_mm: modulePhysical.width_mm / 2 + modulePhysical.cable_positive_mm,
});

const drawing = Object.freeze({
  canvasWidth: 3740,
  left: 310,
  top: 60,
  rowHeight: 318,
  mpptGap: 52,
  moduleWidth: 88,
  moduleHeight: 88 * modulePhysical.height_mm / modulePhysical.width_mm,
  moduleGap: 20,
  inverterX: 34,
  inverterWidth: 132,
  inverterHeight: 170,
  inverterCableOffset: 24,
  moduleCableOffset: 20,
});

let mode = 'leapfrog';

const element = (name, attributes = {}, text = '') => {
  const node = document.createElementNS(NS, name);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, String(value));
  if (text) node.textContent = text;
  return node;
};

const pad2 = (value) => String(value).padStart(2, '0');
const stringId = (stringNumber) => `STR-${pad2(stringNumber)}`;
const moduleId = (stringNumber, moduleNumber) => `${stringId(stringNumber)}-M${pad2(moduleNumber)}`;
const moduleConnectorId = (stringNumber, moduleNumber, polarity) =>
  `${moduleId(stringNumber, moduleNumber)}-${polarity === 'positive' ? 'POS' : 'NEG'}-CONNECTOR`;
const cableConnectorId = (stringNumber, polarity, side) =>
  `${stringId(stringNumber)}-${polarity === 'positive' ? 'POS' : 'NEG'}-STRING-CABLE-${side === 'module' ? 'MODULE-END' : 'INVERTER-END'}`;
const inverterSocketId = (stringNumber, polarity) =>
  `${stringId(stringNumber)}-IN-${pad2(stringNumber)}-${polarity === 'positive' ? 'POS' : 'NEG'}-INVERTER-SOCKET`;
const interfaceId = (stringNumber, interfaceNumber) =>
  `${stringId(stringNumber)}-MATE-${String(interfaceNumber).padStart(3, '0')}`;

function electricalOrder(count, strategy) {
  if (strategy === 'sequential') return Array.from({ length: count }, (_, index) => index + 1);
  if (strategy !== 'leapfrog') throw new Error(`Unsupported wiring mode ${strategy}`);
  const outward = [];
  const returning = [];
  for (let module = 1; module <= count; module += 2) outward.push(module);
  for (let module = count % 2 === 0 ? count : count - 1; module >= 2; module -= 2) returning.push(module);
  return outward.concat(returning);
}

function moduleX(moduleNumber) {
  return drawing.left + (moduleNumber - 1) * (drawing.moduleWidth + drawing.moduleGap);
}

function rowCentreY(rowIndex) {
  return drawing.top
    + rowIndex * drawing.rowHeight
    + Math.floor(rowIndex / INPUTS_PER_MPPT) * drawing.mpptGap
    + drawing.rowHeight / 2;
}

function pathFromPoints(start, end, side, laneIndex = 0) {
  const distance = Math.abs(end.x - start.x);
  const direction = side === 'above' ? -1 : 1;
  const lane = Math.min(76, 42 + distance * 0.16 + (laneIndex % 2) * 4);
  const controlY = (start.y + end.y) / 2 + direction * lane;
  return `M ${start.x} ${start.y} C ${start.x} ${controlY}, ${end.x} ${controlY}, ${end.x} ${end.y}`;
}

function orthogonalCablePath(start, end, laneY) {
  return `M ${start.x} ${start.y} L ${start.x} ${laneY} L ${end.x} ${laneY} L ${end.x} ${end.y}`;
}

function addConnector(layer, connectorPoints, id, x, y, polarity, attributes = {}) {
  if (connectorPoints.has(id)) throw new Error(`Duplicate connector point ${id}`);
  const connector = element('circle', {
    id,
    cx: x,
    cy: y,
    r: 4.7,
    class: `connector ${polarity}`,
    tabindex: 0,
    role: 'button',
    'data-connector-id': id,
    'data-polarity': polarity,
    'data-contact-gender': modulePhysical.connector_gender,
    ...attributes,
  });
  layer.append(connector);
  connectorPoints.set(id, { x, y, polarity });
  return connector;
}

function connectorPoint(connectorPoints, id) {
  const point = connectorPoints.get(id);
  if (!point) throw new Error(`Unknown connector endpoint ${id}`);
  return point;
}

function appendCable(layer, d, className, attributes = {}) {
  layer.append(element('path', { d, class: 'cable-halo', 'aria-hidden': 'true' }));
  const path = element('path', { d, class: className, ...attributes });
  layer.append(path);
  return path;
}

function addMatePath(layer, connectorPoints, {
  id,
  sourceId,
  destinationId,
  interfaceClass,
  side = 'above',
  laneIndex = 0,
  path = null,
  v8Lane = interfaceClass,
  isTurnaround = false,
}) {
  const source = connectorPoint(connectorPoints, sourceId);
  const destination = connectorPoint(connectorPoints, destinationId);
  const d = path ?? pathFromPoints(source, destination, side, laneIndex);
  return appendCable(layer, d, 'mate-path', {
    id,
    tabindex: 0,
    role: 'button',
    'data-mating-interface-id': id,
    'data-source-connector-id': sourceId,
    'data-destination-connector-id': destinationId,
    'data-interface-class': interfaceClass,
    'data-v8-lane': v8Lane,
    'data-v8-turnaround': isTurnaround,
  });
}

function addCableBody(layer, connectorPoints, {
  id,
  sourceId,
  destinationId,
  laneY,
  polarity,
}) {
  const source = connectorPoint(connectorPoints, sourceId);
  const destination = connectorPoint(connectorPoints, destinationId);
  appendCable(layer, orthogonalCablePath(source, destination, laneY), 'string-cable', {
    id,
    'data-cable-id': id,
    'data-source-connector-id': sourceId,
    'data-destination-connector-id': destinationId,
    'data-polarity': polarity,
    'data-cable-sheath-colour': 'black',
  });
}

function drawModule(bodyLayer, connectorLayer, annotationLayer, connectorPoints, stringNumber, moduleNumber, rowY) {
  const x = moduleX(moduleNumber);
  const top = rowY - drawing.moduleHeight / 2;
  const centreX = x + drawing.moduleWidth / 2;
  const scaleX = drawing.moduleWidth / modulePhysical.width_mm;
  const scaleY = drawing.moduleHeight / modulePhysical.height_mm;
  const axisFromTopMm = modulePhysical.height_mm - modulePhysical.jbox_axis_from_bottom_mm;
  const axisY = top + axisFromTopMm * scaleY;
  const rootSeparationPx = 14;
  const negativeRoot = { x: centreX - rootSeparationPx / 2, y: axisY };
  const positiveRoot = { x: centreX + rootSeparationPx / 2, y: axisY };
  const negativeConnector = { x: x + connectorReference.negative_x_mm * scaleX, y: axisY };
  const positiveConnector = { x: x + connectorReference.positive_x_mm * scaleX, y: axisY };
  const id = moduleId(stringNumber, moduleNumber);

  bodyLayer.append(element('rect', {
    id: `${id}-MODULE`,
    x,
    y: top,
    width: drawing.moduleWidth,
    height: drawing.moduleHeight,
    rx: 3,
    class: 'module-body',
    'data-module-id': id,
    'data-actual-width-mm': modulePhysical.width_mm,
    'data-actual-height-mm': modulePhysical.height_mm,
    'data-actual-depth-mm': modulePhysical.depth_mm,
    'data-svg-px-per-mm': scaleX,
  }));
  bodyLayer.append(element('line', {
    x1: centreX,
    y1: top + 6,
    x2: centreX,
    y2: top + drawing.moduleHeight - 6,
    class: 'module-backline vertical',
  }));
  bodyLayer.append(element('line', {
    x1: x + 6,
    y1: axisY,
    x2: x + drawing.moduleWidth - 6,
    y2: axisY,
    class: 'module-backline axis',
    'data-jbox-axis-from-bottom-mm': modulePhysical.jbox_axis_from_bottom_mm,
  }));
  bodyLayer.append(element('rect', {
    id: `${id}-JUNCTION-BOX`,
    x: centreX - 18,
    y: axisY - 8,
    width: 36,
    height: 16,
    rx: 2.5,
    class: 'jbox',
    'data-axis-basis': modulePhysical.jbox_axis_basis,
    'data-polarity-root-side': modulePhysical.polarity_root_side,
  }));
  bodyLayer.append(element('circle', {
    id: `${id}-JBOX_NEG`,
    cx: negativeRoot.x,
    cy: negativeRoot.y,
    r: 2,
    class: 'jbox-terminal',
    'data-terminal-id': `${id}-JBOX_NEG`,
  }));
  bodyLayer.append(element('circle', {
    id: `${id}-JBOX_POS`,
    cx: positiveRoot.x,
    cy: positiveRoot.y,
    r: 2,
    class: 'jbox-terminal',
    'data-terminal-id': `${id}-JBOX_POS`,
  }));
  bodyLayer.append(element('path', {
    id: `${id}-NEG-FACTORY-LEAD`,
    d: `M ${negativeRoot.x} ${negativeRoot.y} L ${negativeConnector.x} ${negativeConnector.y}`,
    class: 'factory-lead',
    'data-actual-length-mm': modulePhysical.cable_negative_mm,
    'data-cable-sheath-colour': 'black',
  }));
  bodyLayer.append(element('path', {
    id: `${id}-POS-FACTORY-LEAD`,
    d: `M ${positiveRoot.x} ${positiveRoot.y} L ${positiveConnector.x} ${positiveConnector.y}`,
    class: 'factory-lead',
    'data-actual-length-mm': modulePhysical.cable_positive_mm,
    'data-cable-sheath-colour': 'black',
  }));

  connectorLayer.append(element('rect', {
    x: negativeConnector.x - 10,
    y: axisY - 12,
    width: 20,
    height: 24,
    rx: 3,
    class: 'connector-housing negative-housing',
    'data-module-connector-housing': `${id}-NEG`,
  }));
  connectorLayer.append(element('rect', {
    x: positiveConnector.x - 10,
    y: axisY - 12,
    width: 20,
    height: 24,
    rx: 3,
    class: 'connector-housing positive-housing',
    'data-module-connector-housing': `${id}-POS`,
  }));

  addConnector(
    connectorLayer,
    connectorPoints,
    moduleConnectorId(stringNumber, moduleNumber, 'negative'),
    negativeConnector.x,
    negativeConnector.y,
    'negative',
    {
      'data-component-id': id,
      'data-component-type': 'pv_module',
      'data-module': moduleNumber,
      'data-junction-box-terminal-id': `${id}-JBOX_NEG`,
      'data-actual-factory-lead-mm': modulePhysical.cable_negative_mm,
      'data-connector-location': 'central_jbox_axis',
    },
  );
  addConnector(
    connectorLayer,
    connectorPoints,
    moduleConnectorId(stringNumber, moduleNumber, 'positive'),
    positiveConnector.x,
    positiveConnector.y,
    'positive',
    {
      'data-component-id': id,
      'data-component-type': 'pv_module',
      'data-module': moduleNumber,
      'data-junction-box-terminal-id': `${id}-JBOX_POS`,
      'data-actual-factory-lead-mm': modulePhysical.cable_positive_mm,
      'data-connector-location': 'central_jbox_axis',
    },
  );

  annotationLayer.append(element('text', {
    x: negativeConnector.x,
    y: axisY + 22,
    'text-anchor': 'middle',
    class: 'polarity-glyph negative-glyph',
  }, '−'));
  annotationLayer.append(element('text', {
    x: positiveConnector.x,
    y: axisY + 22,
    'text-anchor': 'middle',
    class: 'polarity-glyph positive-glyph',
  }, '+'));
  annotationLayer.append(element('text', {
    x: centreX,
    y: top + drawing.moduleHeight + 18,
    'text-anchor': 'middle',
    class: 'module-label',
  }, `M${moduleNumber}`));
}

function drawString(stringNumber, rowIndex) {
  const id = stringId(stringNumber);
  const mpptNumber = Math.floor((stringNumber - 1) / INPUTS_PER_MPPT) + 1;
  const input = `PV${stringNumber}`;
  const rowY = rowCentreY(rowIndex);
  const group = element('g', {
    id: `${id}-DRAWING`,
    'data-string-id': id,
    'data-mppt-id': `MPPT-${pad2(mpptNumber)}`,
    'data-physical-dc-input-id': `IN-${pad2(stringNumber)}`,
    'data-topology-strategy': mode,
  });
  const baseLayer = element('g', { class: 'base-layer' });
  const bodyLayer = element('g', { class: 'component-body-layer' });
  const cableLayer = element('g', { class: 'cable-layer' });
  const connectorLayer = element('g', { class: 'connector-layer' });
  const annotationLayer = element('g', { class: 'annotation-layer' });
  const connectorPoints = new Map();
  const bandTop = rowY - drawing.rowHeight / 2 + 8;
  const bandHeight = drawing.rowHeight - 16;

  baseLayer.append(element('rect', {
    x: 10,
    y: bandTop,
    width: drawing.canvasWidth - 20,
    height: bandHeight,
    class: 'mppt-band',
  }));
  annotationLayer.append(element('text', {
    x: 22,
    y: bandTop + 22,
    class: 'string-title',
  }, `${id} · MPPT-${pad2(mpptNumber)} · ${input}+ / ${input}− · ${mode.toUpperCase()}`));

  const inverterY = rowY - drawing.inverterHeight / 2;
  bodyLayer.append(element('rect', {
    id: `${id}-INVERTER-INPUT-BLOCK`,
    x: drawing.inverterX,
    y: inverterY,
    width: drawing.inverterWidth,
    height: drawing.inverterHeight,
    rx: 7,
    class: 'inverter',
  }));
  annotationLayer.append(element('text', {
    x: drawing.inverterX + drawing.inverterWidth / 2,
    y: inverterY + 34,
    'text-anchor': 'middle',
    class: 'inverter-label inverter-title',
  }, 'INVERTER'));
  annotationLayer.append(element('text', {
    x: drawing.inverterX + drawing.inverterWidth / 2,
    y: inverterY + 58,
    'text-anchor': 'middle',
    class: 'inverter-label',
  }, `IN-${pad2(stringNumber)}`));
  annotationLayer.append(element('text', {
    x: drawing.inverterX + drawing.inverterWidth / 2,
    y: inverterY + 80,
    'text-anchor': 'middle',
    class: 'inverter-label',
  }, `MPPT-${pad2(mpptNumber)}`));

  const inverterNegative = { x: drawing.inverterX + drawing.inverterWidth, y: rowY - 32 };
  const inverterPositive = { x: drawing.inverterX + drawing.inverterWidth, y: rowY + 32 };
  addConnector(
    connectorLayer,
    connectorPoints,
    inverterSocketId(stringNumber, 'negative'),
    inverterNegative.x,
    inverterNegative.y,
    'negative',
    {
      'data-component-id': `IN-${pad2(stringNumber)}`,
      'data-component-type': 'inverter_dc_input',
      'data-pv-terminal': `${input}-`,
      'data-mppt-id': `MPPT-${pad2(mpptNumber)}`,
    },
  );
  addConnector(
    connectorLayer,
    connectorPoints,
    inverterSocketId(stringNumber, 'positive'),
    inverterPositive.x,
    inverterPositive.y,
    'positive',
    {
      'data-component-id': `IN-${pad2(stringNumber)}`,
      'data-component-type': 'inverter_dc_input',
      'data-pv-terminal': `${input}+`,
      'data-mppt-id': `MPPT-${pad2(mpptNumber)}`,
    },
  );
  annotationLayer.append(element('text', {
    x: drawing.inverterX + drawing.inverterWidth - 30,
    y: inverterNegative.y + 5,
    class: 'terminal-label',
  }, '−'));
  annotationLayer.append(element('text', {
    x: drawing.inverterX + drawing.inverterWidth - 30,
    y: inverterPositive.y + 5,
    class: 'terminal-label',
  }, '+'));

  for (let moduleNumber = 1; moduleNumber <= MODULES; moduleNumber += 1) {
    drawModule(
      bodyLayer,
      connectorLayer,
      annotationLayer,
      connectorPoints,
      stringNumber,
      moduleNumber,
      rowY,
    );
  }

  const order = electricalOrder(MODULES, mode);
  const firstModule = order[0];
  const lastModule = order.at(-1);
  const freeNegativeId = moduleConnectorId(stringNumber, firstModule, 'negative');
  const freePositiveId = moduleConnectorId(stringNumber, lastModule, 'positive');
  const freeNegative = connectorPoint(connectorPoints, freeNegativeId);
  const freePositive = connectorPoint(connectorPoints, freePositiveId);

  const negativeCableInverterId = cableConnectorId(stringNumber, 'negative', 'inverter');
  const negativeCableModuleId = cableConnectorId(stringNumber, 'negative', 'module');
  const positiveCableInverterId = cableConnectorId(stringNumber, 'positive', 'inverter');
  const positiveCableModuleId = cableConnectorId(stringNumber, 'positive', 'module');

  addConnector(
    connectorLayer,
    connectorPoints,
    negativeCableInverterId,
    inverterNegative.x + drawing.inverterCableOffset,
    inverterNegative.y,
    'negative',
    {
      'data-component-id': `${id}-NEG-STRING-CABLE`,
      'data-component-type': 'pv_string_cable',
      'data-cable-side': 'inverter',
      'data-cable-sheath-colour': 'black',
    },
  );
  addConnector(
    connectorLayer,
    connectorPoints,
    negativeCableModuleId,
    freeNegative.x - drawing.moduleCableOffset,
    freeNegative.y,
    'negative',
    {
      'data-component-id': `${id}-NEG-STRING-CABLE`,
      'data-component-type': 'pv_string_cable',
      'data-cable-side': 'module',
      'data-cable-sheath-colour': 'black',
    },
  );
  addConnector(
    connectorLayer,
    connectorPoints,
    positiveCableInverterId,
    inverterPositive.x + drawing.inverterCableOffset,
    inverterPositive.y,
    'positive',
    {
      'data-component-id': `${id}-POS-STRING-CABLE`,
      'data-component-type': 'pv_string_cable',
      'data-cable-side': 'inverter',
      'data-cable-sheath-colour': 'black',
    },
  );
  addConnector(
    connectorLayer,
    connectorPoints,
    positiveCableModuleId,
    freePositive.x + (mode === 'sequential' ? drawing.moduleCableOffset : -drawing.moduleCableOffset),
    freePositive.y,
    'positive',
    {
      'data-component-id': `${id}-POS-STRING-CABLE`,
      'data-component-type': 'pv_string_cable',
      'data-cable-side': 'module',
      'data-cable-sheath-colour': 'black',
    },
  );

  addMatePath(cableLayer, connectorPoints, {
    id: interfaceId(stringNumber, 1),
    sourceId: inverterSocketId(stringNumber, 'negative'),
    destinationId: negativeCableInverterId,
    interfaceClass: 'string_cable_to_inverter',
    path: `M ${inverterNegative.x} ${inverterNegative.y} L ${inverterNegative.x + drawing.inverterCableOffset} ${inverterNegative.y}`,
  });
  addCableBody(cableLayer, connectorPoints, {
    id: `${id}-NEG-STRING-CABLE-BODY`,
    sourceId: negativeCableInverterId,
    destinationId: negativeCableModuleId,
    laneY: rowY - drawing.moduleHeight / 2 - 28,
    polarity: 'negative',
  });
  addMatePath(cableLayer, connectorPoints, {
    id: interfaceId(stringNumber, 2),
    sourceId: negativeCableModuleId,
    destinationId: freeNegativeId,
    interfaceClass: 'module_to_string_cable',
    path: `M ${freeNegative.x - drawing.moduleCableOffset} ${freeNegative.y} L ${freeNegative.x} ${freeNegative.y}`,
  });

  order.slice(0, -1).forEach((fromModule, position) => {
    const toModule = order[position + 1];
    const sourceId = moduleConnectorId(stringNumber, fromModule, 'positive');
    const destinationId = moduleConnectorId(stringNumber, toModule, 'negative');
    const isOutward = mode === 'leapfrog' && fromModule % 2 === 1 && toModule % 2 === 1;
    const isTurnaround = mode === 'leapfrog'
      && Math.abs(fromModule - toModule) === 1
      && Math.max(fromModule, toModule) === MODULES;
    const v8Lane = mode === 'sequential'
      ? 'sequential'
      : isTurnaround
        ? 'turnaround'
        : isOutward
          ? 'outward'
          : 'return';
    const side = v8Lane === 'sequential' || v8Lane === 'outward' ? 'above' : 'below';
    addMatePath(cableLayer, connectorPoints, {
      id: interfaceId(stringNumber, position + 3),
      sourceId,
      destinationId,
      interfaceClass: 'module_to_module',
      side,
      laneIndex: position,
      v8Lane,
      isTurnaround,
    });
  });

  addMatePath(cableLayer, connectorPoints, {
    id: interfaceId(stringNumber, 32),
    sourceId: freePositiveId,
    destinationId: positiveCableModuleId,
    interfaceClass: 'module_to_string_cable',
    path: `M ${freePositive.x} ${freePositive.y} L ${connectorPoint(connectorPoints, positiveCableModuleId).x} ${connectorPoint(connectorPoints, positiveCableModuleId).y}`,
  });
  addCableBody(cableLayer, connectorPoints, {
    id: `${id}-POS-STRING-CABLE-BODY`,
    sourceId: positiveCableModuleId,
    destinationId: positiveCableInverterId,
    laneY: rowY + drawing.moduleHeight / 2 + 30,
    polarity: 'positive',
  });
  addMatePath(cableLayer, connectorPoints, {
    id: interfaceId(stringNumber, 33),
    sourceId: positiveCableInverterId,
    destinationId: inverterSocketId(stringNumber, 'positive'),
    interfaceClass: 'string_cable_to_inverter',
    path: `M ${inverterPositive.x + drawing.inverterCableOffset} ${inverterPositive.y} L ${inverterPositive.x} ${inverterPositive.y}`,
  });

  annotationLayer.append(element('text', {
    x: freeNegative.x - 8,
    y: rowY - drawing.moduleHeight / 2 - 12,
    class: 'input-label',
  }, 'FREE − M1−'));
  annotationLayer.append(element('text', {
    x: freePositive.x - 16,
    y: rowY + drawing.moduleHeight / 2 + 24,
    class: 'input-label',
  }, mode === 'sequential' ? `FREE + M${MODULES}+` : 'FREE + M2+'));
  if (mode === 'sequential') {
    annotationLayer.append(element('text', {
      x: moduleX(19),
      y: rowY + drawing.moduleHeight / 2 + 52,
      class: 'route-label',
    }, 'ADDITIONAL FAR-END POSITIVE RETURN'));
  } else {
    annotationLayer.append(element('text', {
      x: moduleX(MODULES - 2),
      y: rowY - drawing.moduleHeight / 2 - 16,
      class: 'route-label turnaround-label',
    }, 'TURNAROUND M29+ → M30−'));
  }

  group.append(baseLayer, bodyLayer, cableLayer, connectorLayer, annotationLayer);
  group.dataset.connectorEnds = connectorPoints.size;
  group.dataset.matedInterfaces = group.querySelectorAll('.mate-path').length;
  group.dataset.electricalOrder = order.join(',');
  return group;
}

function validateDrawing() {
  const groups = [...svg.querySelectorAll('g[data-string-id]')];
  const modules = [...svg.querySelectorAll('.module-body')];
  const connectors = [...svg.querySelectorAll('.connector')];
  const mates = [...svg.querySelectorAll('.mate-path')];
  const housings = [...svg.querySelectorAll('.connector-housing')];
  const cableHalos = [...svg.querySelectorAll('.cable-halo')];
  const stringCables = [...svg.querySelectorAll('.string-cable')];
  const allIds = [...svg.querySelectorAll('[id]')].map((node) => node.id);
  const duplicateIds = allIds.filter((id, index) => allIds.indexOf(id) !== index);
  const unresolvedEndpoints = mates.flatMap((mate) => {
    const sourceId = mate.dataset.sourceConnectorId;
    const destinationId = mate.dataset.destinationConnectorId;
    return [sourceId, destinationId].filter((id) => !id || !document.getElementById(id));
  });
  const perStringPass = groups.every((group) => {
    const laneCounts = [...group.querySelectorAll('.mate-path[data-interface-class="module_to_module"]')]
      .reduce((result, mate) => {
        result[mate.dataset.v8Lane] = (result[mate.dataset.v8Lane] ?? 0) + 1;
        return result;
      }, {});
    const v8LanePass = mode === 'sequential'
      ? laneCounts.sequential === 29
      : laneCounts.outward === 14 && laneCounts.return === 14 && laneCounts.turnaround === 1;
    return Number(group.dataset.connectorEnds) === 66
      && Number(group.dataset.matedInterfaces) === 33
      && group.querySelectorAll('.module-body').length === 30
      && group.querySelectorAll('.connector').length === 66
      && group.querySelectorAll('.mate-path').length === 33
      && group.querySelectorAll('.connector-housing').length === 60
      && v8LanePass;
  });
  const v8VisualPass = housings.length === 1440
    && stringCables.length === 48
    && cableHalos.length === 840;
  const pass = groups.length === STRINGS
    && modules.length === STRINGS * MODULES
    && connectors.length === 1584
    && mates.length === 792
    && duplicateIds.length === 0
    && unresolvedEndpoints.length === 0
    && perStringPass
    && v8VisualPass;

  const result = {
    schema_version: 'globalgrid2050.v11.2.full-array-sld-evidence.v2',
    mode,
    strings: groups.length,
    modules: modules.length,
    complete_system_connector_ends: connectors.length,
    mated_interfaces: mates.length,
    module_connector_housings: housings.length,
    cable_halos: cableHalos.length,
    string_cable_bodies: stringCables.length,
    duplicate_ids: [...new Set(duplicateIds)],
    unresolved_endpoint_ids: [...new Set(unresolvedEndpoints)],
    per_string_66_33_pass: perStringPass,
    v8_visual_language_pass: v8VisualPass,
    module_geometry_mm: modulePhysical,
    path_endpoint_authority: 'connector_id_map',
    lane_authority: 'electrical_order_and_explicit_connector_ids',
    screen_order_inference_used: false,
    pass,
  };
  window.__V11_2_SLD_EVIDENCE__ = result;
  svg.dataset.validationPass = String(pass);
  if (!pass) throw new Error(`V11.2 drawing validation failed: ${JSON.stringify(result)}`);
}

function render() {
  svg.replaceChildren();
  const height = drawing.top
    + STRINGS * drawing.rowHeight
    + MPPTS * drawing.mpptGap
    + 40;
  svg.setAttribute('viewBox', `0 0 ${drawing.canvasWidth} ${height}`);
  svg.setAttribute('width', drawing.canvasWidth);
  svg.setAttribute('height', height);
  svg.style.width = `${drawing.canvasWidth}px`;
  svg.style.height = `${height}px`;

  for (let mppt = 1; mppt <= MPPTS; mppt += 1) {
    const firstRow = (mppt - 1) * INPUTS_PER_MPPT;
    const titleY = rowCentreY(firstRow) - drawing.rowHeight / 2 - 8;
    svg.append(element('text', {
      x: 12,
      y: titleY,
      class: 'mppt-title',
    }, `MPPT-${pad2(mppt)} · INPUTS ${pad2(firstRow + 1)}–${pad2(firstRow + 2)}`));
    svg.append(drawString(firstRow + 1, firstRow));
    svg.append(drawString(firstRow + 2, firstRow + 1));
  }

  svg.dataset.mode = mode;
  svg.dataset.strings = STRINGS;
  svg.dataset.modulesPerString = MODULES;
  svg.dataset.completeSystemConnectorEnds = 1584;
  svg.dataset.matedInterfaces = 792;
  svg.dataset.moduleWidthMm = modulePhysical.width_mm;
  svg.dataset.moduleHeightMm = modulePhysical.height_mm;
  svg.dataset.jboxAxisFromBottomMm = modulePhysical.jbox_axis_from_bottom_mm;
  svg.dataset.visualAuthority = 'v8-leapfrog-explicit-physical-connections';
  validateDrawing();
  window.dispatchEvent(new CustomEvent('v11-2-rendered', { detail: { mode } }));
}

function fitWidth() {
  const unscaledHeight = Number(svg.getAttribute('height'));
  const scale = Math.max(0.18, viewport.clientWidth / drawing.canvasWidth);
  svg.style.width = `${drawing.canvasWidth * scale}px`;
  svg.style.height = `${unscaledHeight * scale}px`;
  viewport.scrollTo({ left: 0, top: 0, behavior: 'auto' });
}

document.querySelectorAll('[data-mode]').forEach((button) => {
  button.addEventListener('click', () => {
    mode = button.dataset.mode;
    document.querySelectorAll('[data-mode]').forEach((candidate) =>
      candidate.classList.toggle('active', candidate === button));
    render();
  });
});

document.querySelector('#fit').addEventListener('click', fitWidth);
svg.addEventListener('click', (event) => {
  const target = event.target.closest?.('.connector,.mate-path');
  if (!target) return;
  svg.querySelectorAll('.selected').forEach((node) => node.classList.remove('selected'));
  target.classList.add('selected');
});

render();
