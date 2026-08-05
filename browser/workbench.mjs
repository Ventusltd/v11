import { moveModule, footprint, layoutHash } from './layout-core.mjs';
import { referenceFromLayout } from './layout-simulation-bridge.mjs';
import { simulateComparison } from './simulation-core.mjs';
import { analyseWorkbench, buildEngineeringPackage, workbenchCsv } from './workbench-analysis.mjs';

const $ = (selector) => document.querySelector(selector);
const number = (selector) => Number($(selector).value);
const positiveInt = (selector, label, minimum = 1) => {
  const value = number(selector);
  if (!Number.isInteger(value) || value < minimum) throw new Error(`${label} must be an integer >= ${minimum}`);
  return value;
};
const pad = (value, width = 2) => String(value).padStart(width, '0');
const fmt = (value, digits = 2) => Number(value).toLocaleString(undefined, {
  minimumFractionDigits: digits,
  maximumFractionDigits: digits,
});

let referenceFixture;
let activeReference;
let activeDefinition;
let layout;
let selectedStringId = 'STR-01';
let selectedModuleId = null;
let latest = null;
let calculationSerial = 0;
let wiringMode = 'leapfrog';
let activeView = 'topology';
let physicalEditEnabled = false;
let arrayEditorSelfCheck = null;

function electricalOrder(count, strategy) {
  if (strategy === 'sequential') return Array.from({ length: count }, (_, index) => index + 1);
  if (strategy === 'leapfrog') {
    const outward = [];
    const returning = [];
    for (let index = 1; index <= count; index += 2) outward.push(index);
    for (let index = count % 2 === 0 ? count : count - 1; index >= 2; index -= 2) returning.push(index);
    return outward.concat(returning);
  }
  throw new Error(`Unsupported wiring strategy: ${strategy}`);
}

function readArrayDefinition() {
  const stringCount = positiveInt('#string-count', 'String count');
  const modulesPerString = positiveInt('#modules-per-string', 'Modules per string', 2);
  const mpptCount = positiveInt('#mppt-count', 'MPPT count');
  const inputsPerMppt = positiveInt('#inputs-per-mppt', 'Inputs per MPPT');
  const eastStringCount = positiveInt('#east-string-count', 'East-face string count', 0);
  const stringsPerBand = positiveInt('#strings-per-band', 'Strings per face band');
  const physicalInputCount = mpptCount * inputsPerMppt;
  if (stringCount > physicalInputCount) throw new Error(`${stringCount} strings exceeds ${physicalInputCount} physical inputs`);
  if (eastStringCount > stringCount) throw new Error('East-face string count cannot exceed total string count');
  const rowPitchM = number('#row-pitch');
  const inverterPoint = { x_m: number('#inverter-x'), y_m: number('#inverter-y') };
  return {
    schema_version: 'globalgrid2050.v11.array-definition.v2',
    string_count: stringCount,
    modules_per_string: modulesPerString,
    module_count: stringCount * modulesPerString,
    mppt_count: mpptCount,
    inputs_per_mppt: inputsPerMppt,
    physical_dc_input_count: physicalInputCount,
    east_string_count: eastStringCount,
    west_string_count: stringCount - eastStringCount,
    strings_per_face_band: stringsPerBand,
    row_pitch_m: rowPitchM,
    inverter_point: inverterPoint,
  };
}

function adaptedReference(definition) {
  const adapted = structuredClone(referenceFixture);
  const moduleToModuleMates = definition.modules_per_string - 1;
  const moduleToStringCableMates = 2;
  const stringCableToInverterMates = 2;
  const totalMatedInterfaces = definition.modules_per_string + 3;
  adapted.block_id = `v11_user_array_${definition.string_count}x${definition.modules_per_string}`;
  adapted.array.string_count = definition.string_count;
  adapted.array.modules_per_string = definition.modules_per_string;
  adapted.array.module_pitch_m = number('#mw') + number('#gx');
  adapted.array.row_spacing_m = definition.row_pitch_m;
  adapted.array.leapfrog_factory_extra_m_per_string = adapted.array.module_pitch_m;
  adapted.inverter.mppt_count = definition.mppt_count;
  adapted.inverter.strings_per_mppt = definition.inputs_per_mppt;
  adapted.inverter.physical_dc_input_count = definition.physical_dc_input_count;
  delete adapted.conductors.connector_count_per_string;
  delete adapted.conductors.connector_count_per_string_status;
  adapted.conductors.connector_resistance_policy = {
    ...adapted.conductors.connector_resistance_policy,
    schema_version: 'globalgrid2050.v11.connector-resistance-policy.v1',
    evidence_state: 'provisional_fixture',
    applies_to: 'all_completed_mated_interfaces',
    included_interface_classes: [
      'module_to_module',
      'module_to_string_cable',
      'string_cable_to_inverter',
    ],
    module_to_module_mate_count: moduleToModuleMates,
    module_to_string_cable_mate_count: moduleToStringCableMates,
    string_cable_to_inverter_mate_count: stringCableToInverterMates,
    total_mated_interface_count: totalMatedInterfaces,
    note: 'Derived from adapted array cardinality: N - 1 module mates plus two module-to-string-cable and two string-cable-to-inverter interfaces.',
  };
  if (adapted.conductors.connector_resistance_policy.total_mated_interface_count !== definition.modules_per_string + 3) {
    throw new Error('Adapted connector resistance policy must equal N + 3 completed interfaces');
  }
  adapted.routing.route_lengths_m = Array(definition.string_count).fill(0);
  adapted.provenance = {
    ...adapted.provenance,
    array_definition_schema: definition.schema_version,
    topology_view_schema: 'globalgrid2050.v11.full-array-string-strips.v1',
    adaptation: `${adapted.provenance.adaptation} User array cardinality, east/west grouping and deterministic input allocation applied in V11 without mutating the committed fixture.`,
  };
  return adapted;
}

function validateGeometry(definition) {
  const boundary = { x_min: 0, y_min: 0, x_max: number('#bw'), y_max: number('#bh') };
  const widthM = number('#mw');
  const heightM = number('#mh');
  const gapXM = number('#gx');
  const gapYM = number('#gy');
  const rowPitchM = definition.row_pitch_m;
  for (const [label, value, minimum] of [
    ['Boundary width', boundary.x_max, 0.001], ['Boundary height', boundary.y_max, 0.001],
    ['Module width', widthM, 0.001], ['Module height', heightM, 0.001],
    ['Gap X', gapXM, 0], ['Gap Y', gapYM, 0], ['Row pitch', rowPitchM, 0.001],
    ['Inverter X', definition.inverter_point.x_m, -Infinity], ['Inverter Y', definition.inverter_point.y_m, -Infinity],
  ]) {
    if (!Number.isFinite(value) || value < minimum) throw new Error(`${label} is outside its allowed range`);
  }
  if (rowPitchM + 1e-12 < heightM + gapYM) {
    throw new Error(`Physical row pitch ${rowPitchM} m is smaller than module height plus Y gap ${heightM + gapYM} m`);
  }
  const xPitch = widthM + gapXM;
  const requiredWidth = definition.modules_per_string * xPitch - gapXM;
  const requiredHeight = heightM + (definition.string_count - 1) * rowPitchM;
  if (requiredWidth > boundary.x_max - boundary.x_min + 1e-9 || requiredHeight > boundary.y_max - boundary.y_min + 1e-9) {
    throw new Error(`Physical boundary cannot fit ${definition.module_count} modules: requires ${requiredWidth.toFixed(3)} m × ${requiredHeight.toFixed(3)} m`);
  }
  return { boundary, widthM, heightM, gapXM, xPitch, rowPitchM };
}

function buildLayout(definition) {
  const geometry = validateGeometry(definition);
  const modules = [];
  for (let stringOffset = 0; stringOffset < definition.string_count; stringOffset += 1) {
    const stringId = `STR-${pad(stringOffset + 1)}`;
    for (let electricalOffset = 0; electricalOffset < definition.modules_per_string; electricalOffset += 1) {
      const moduleOffset = modules.length;
      modules.push({
        id: `MOD-${pad(moduleOffset + 1, 4)}`,
        x_m: +(geometry.boundary.x_min + geometry.widthM / 2 + electricalOffset * geometry.xPitch).toFixed(9),
        y_m: +(geometry.boundary.y_min + geometry.heightM / 2 + stringOffset * geometry.rowPitchM).toFixed(9),
        width_m: geometry.widthM,
        height_m: geometry.heightM,
        rotation_deg: 0,
        row: stringOffset,
        column: electricalOffset,
        string_id: stringId,
        electrical_index: electricalOffset + 1,
      });
    }
  }
  const result = {
    schema_version: 'globalgrid2050.v11.module-layout.v1',
    boundary: geometry.boundary,
    obstacles: [],
    array_definition: structuredClone(definition),
    modules,
  };
  result.layout_hash = layoutHash(result);
  return result;
}

function faceBandForString(stringNumber) {
  const east = stringNumber <= activeDefinition.east_string_count;
  const faceIndex = east ? stringNumber - 1 : stringNumber - activeDefinition.east_string_count - 1;
  return {
    face: east ? 'EAST' : 'WEST',
    band: Math.floor(faceIndex / activeDefinition.strings_per_face_band) + 1,
  };
}

function resetLayout() {
  const definition = readArrayDefinition();
  activeDefinition = definition;
  activeReference = adaptedReference(definition);
  layout = buildLayout(definition);
  selectedStringId = 'STR-01';
  selectedModuleId = null;
  latest = null;
  calculationSerial += 1;
  $('#active-boundary').textContent = `Active array: ${definition.string_count} strings × ${definition.modules_per_string} modules = ${definition.module_count} modules · ${definition.mppt_count} MPPTs × ${definition.inputs_per_mppt} inputs · east ${definition.east_string_count} / west ${definition.west_string_count}`;
  $('#selection').textContent = `Selected string: ${selectedStringId}`;
  renderTopology();
  renderPhysical();
}

function moduleCentreX(index, detail = false) {
  const cellWidth = detail ? 27 : 20;
  const gap = detail ? 6 : 4;
  const startX = detail ? 170 : 150;
  return startX + (index - 1) * (cellWidth + gap) + cellWidth / 2;
}

function traversalPoints(count, strategy, detail = false) {
  const inputX = detail ? 132 : 116;
  const outwardY = detail ? 46 : 25;
  const returnY = detail ? 126 : 66;
  if (strategy === 'sequential') {
    const points = [[inputX, outwardY]];
    for (let index = 1; index <= count; index += 1) points.push([moduleCentreX(index, detail), outwardY]);
    points.push([moduleCentreX(count, detail), returnY], [inputX, returnY]);
    return points;
  }
  const points = [[inputX, outwardY]];
  for (let index = 1; index <= count; index += 2) points.push([moduleCentreX(index, detail), outwardY]);
  const highestEven = count % 2 === 0 ? count : count - 1;
  if (highestEven >= 2) {
    points.push([moduleCentreX(highestEven, detail), returnY]);
    for (let index = highestEven - 2; index >= 2; index -= 2) points.push([moduleCentreX(index, detail), returnY]);
  }
  points.push([inputX, returnY]);
  return points;
}

function pointsAttribute(points) {
  return points.map(([x, y]) => `${x},${y}`).join(' ');
}

function pathMarkup(count, mode, detail, face) {
  const faceClass = face === 'WEST' ? ' face-west-path' : '';
  const sequential = `<polyline class="path-sequential${faceClass}" points="${pointsAttribute(traversalPoints(count, 'sequential', detail))}"/>`;
  const leapfrog = `<polyline class="path-leapfrog${faceClass}" points="${pointsAttribute(traversalPoints(count, 'leapfrog', detail))}"/>`;
  if (mode === 'sequential') return sequential;
  if (mode === 'leapfrog') return leapfrog;
  return `${sequential}${leapfrog}`;
}

function stripSvg(stringNumber, detail = false) {
  const count = activeDefinition.modules_per_string;
  const stringId = `STR-${pad(stringNumber)}`;
  const inputId = `IN-${pad(stringNumber)}`;
  const mpptNumber = Math.floor((stringNumber - 1) / activeDefinition.inputs_per_mppt) + 1;
  const mpptId = `MPPT-${pad(mpptNumber)}`;
  const { face, band } = faceBandForString(stringNumber);
  const cellWidth = detail ? 27 : 20;
  const cellHeight = detail ? 48 : 32;
  const cellY = detail ? 62 : 29;
  const startX = detail ? 170 : 150;
  const gap = detail ? 6 : 4;
  const width = startX + count * (cellWidth + gap) + 28;
  const height = detail ? 165 : 88;
  const labels = [];
  const cells = [];
  for (let index = 1; index <= count; index += 1) {
    const x = startX + (index - 1) * (cellWidth + gap);
    const selected = detail && stringId === selectedStringId ? ' selected-cell' : '';
    cells.push(`<rect class="topology-cell${selected}" data-string-id="${stringId}" data-electrical-index="${index}" x="${x}" y="${cellY}" width="${cellWidth}" height="${cellHeight}" rx="2"/>`);
    const showLabel = detail || index <= 3 || index > count - 3 || index % 5 === 0;
    if (showLabel) labels.push(`<text class="module-label" x="${x + cellWidth / 2}" y="${cellY + cellHeight + (detail ? 18 : 13)}" text-anchor="middle">M${index}</text>`);
  }
  const yTop = detail ? 46 : 25;
  const yBottom = detail ? 126 : 66;
  const modeLabel = wiringMode === 'compare' ? 'SEQUENTIAL + LEAPFROG' : wiringMode.toUpperCase();
  return `
  <svg class="string-strip${stringId === selectedStringId ? ' selected-strip' : ''}" data-string-id="${stringId}" data-mppt-id="${mpptId}" data-input-id="${inputId}" viewBox="0 0 ${width} ${height}" role="button" tabindex="0" aria-label="${stringId} ${mpptId} ${inputId} ${modeLabel}">
    <rect class="inverter-block" x="8" y="${detail ? 34 : 15}" width="${detail ? 105 : 92}" height="${detail ? 105 : 62}" rx="5"/>
    <text class="input-label" x="${detail ? 60 : 54}" y="${detail ? 53 : 34}" text-anchor="middle">INVERTER</text>
    <text class="input-label" x="${detail ? 60 : 54}" y="${detail ? 70 : 49}" text-anchor="middle">${inputId}</text>
    <text class="input-label" x="${detail ? 60 : 54}" y="${detail ? 87 : 64}" text-anchor="middle">${mpptId}</text>
    <circle class="terminal" cx="${detail ? 132 : 116}" cy="${yTop}" r="${detail ? 6 : 4}"/><circle class="terminal" cx="${detail ? 132 : 116}" cy="${yBottom}" r="${detail ? 6 : 4}"/>
    <text class="strip-label" x="${startX}" y="${detail ? 21 : 12}">${stringId} · ${face} B${pad(band)} · ${mpptId} · ${inputId}</text>
    <text class="path-label" x="${detail ? 120 : 106}" y="${yTop - 8}" text-anchor="end">− OUT →</text>
    <text class="path-label" x="${detail ? 120 : 106}" y="${yBottom + 13}" text-anchor="end">← + RETURN</text>
    ${cells.join('')}
    ${pathMarkup(count, wiringMode, detail, face)}
    ${labels.join('')}
  </svg>`;
}

function renderSelectedDetail() {
  const selectedNumber = Number(selectedStringId.split('-')[1]);
  $('#detail-canvas').outerHTML = stripSvg(selectedNumber, true).replace('class="string-strip', 'id="detail-canvas" class="string-strip');
  const order = wiringMode === 'compare'
    ? `Sequential: ${electricalOrder(activeDefinition.modules_per_string, 'sequential').join(' → ')}\nLeapfrog: ${electricalOrder(activeDefinition.modules_per_string, 'leapfrog').join(' → ')}`
    : `${wiringMode[0].toUpperCase()}${wiringMode.slice(1)}: ${electricalOrder(activeDefinition.modules_per_string, wiringMode).join(' → ')}`;
  $('#selected-order').textContent = order;
  const stringNumber = selectedNumber;
  const { face, band } = faceBandForString(stringNumber);
  const mpptId = `MPPT-${pad(Math.floor((stringNumber - 1) / activeDefinition.inputs_per_mppt) + 1)}`;
  $('#selected-detail-note').textContent = `${selectedStringId} · ${face} face band ${band} · ${mpptId} · IN-${pad(stringNumber)}. Module positions stay fixed left-to-right; the line shows the selected electrical traversal.`;
}

function renderTopology() {
  if (!activeDefinition) return;
  const board = $('#topology-board');
  const groups = [];
  for (let mppt = 1; mppt <= activeDefinition.mppt_count; mppt += 1) {
    const start = (mppt - 1) * activeDefinition.inputs_per_mppt + 1;
    const end = Math.min(start + activeDefinition.inputs_per_mppt - 1, activeDefinition.string_count);
    if (start > activeDefinition.string_count) break;
    const strings = [];
    for (let stringNumber = start; stringNumber <= end; stringNumber += 1) {
      strings.push(`<div class="strip-scroll">${stripSvg(stringNumber)}</div>`);
    }
    const faces = new Set(Array.from({ length: end - start + 1 }, (_, offset) => faceBandForString(start + offset).face));
    const faceClass = faces.size === 1 && faces.has('WEST') ? 'face-west' : 'face-east';
    groups.push(`<section class="mppt-group ${faceClass}" data-mppt-id="MPPT-${pad(mppt)}"><div class="mppt-header"><span>MPPT-${pad(mppt)}</span><span>${[...faces].join(' / ')} · inputs ${pad(start)}–${pad(end)}</span></div>${strings.join('')}</section>`);
  }
  board.innerHTML = groups.join('');
  board.querySelectorAll('.string-strip').forEach((strip) => {
    const choose = () => {
      selectedStringId = strip.dataset.stringId;
      $('#selection').textContent = `Selected string: ${selectedStringId}`;
      renderTopology();
    };
    strip.addEventListener('click', choose);
    strip.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        choose();
      }
    });
  });
  renderSelectedDetail();
  window.__v11TopologyEvidence = {
    schema_version: 'globalgrid2050.v11.full-array-string-strips-evidence.v1',
    wiring_mode: wiringMode,
    selected_string_id: selectedStringId,
    string_strip_count: board.querySelectorAll('.string-strip').length,
    topology_cell_count: board.querySelectorAll('.topology-cell').length,
    mppt_group_count: board.querySelectorAll('.mppt-group').length,
    sequential_order: electricalOrder(activeDefinition.modules_per_string, 'sequential'),
    leapfrog_order: electricalOrder(activeDefinition.modules_per_string, 'leapfrog'),
    layout_hash: layout?.layout_hash ?? null,
  };
}

function renderPhysical(derivation = latest?.derivation ?? null, diagnosticIds = latest?.diagnosticIds ?? new Set()) {
  if (!layout) return;
  const svg = $('#physical-canvas');
  const width = number('#bw');
  const height = number('#bh');
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  const routes = derivation ? derivation.strings.map((item) => {
    const attention = diagnosticIds.has(item.string_id) ? ' attention-route' : '';
    return `<line class="route${attention}" x1="${item.centroid.x_m}" y1="${height - item.centroid.y_m}" x2="${derivation.inverter_point.x_m}" y2="${height - derivation.inverter_point.y_m}"/>`;
  }).join('') : '';
  const modules = layout.modules.map((module) => {
    const box = footprint(module);
    const selected = module.id === selectedModuleId ? ' selected' : '';
    const attention = diagnosticIds.has(module.string_id) ? ' attention-module' : '';
    return `<rect class="module${selected}${attention}" data-id="${module.id}" x="${box.left}" y="${height - box.top}" width="${box.width}" height="${box.height}"/>`;
  }).join('');
  const inverter = derivation ? `<circle class="inverter" cx="${derivation.inverter_point.x_m}" cy="${height - derivation.inverter_point.y_m}" r="0.45"/>` : '';
  svg.innerHTML = `${routes}${modules}${inverter}`;
  $('#physical-shell').classList.toggle('physical-editing', physicalEditEnabled);
  if (physicalEditEnabled) svg.querySelectorAll('.module').forEach((element) => element.addEventListener('pointerdown', beginDrag));
}

function svgPoint(event) {
  const svg = $('#physical-canvas');
  const matrix = svg.getScreenCTM();
  if (!matrix) throw new Error('Physical layout canvas is not available');
  const point = svg.createSVGPoint();
  point.x = event.clientX;
  point.y = event.clientY;
  const transformed = point.matrixTransform(matrix.inverse());
  return { x_m: transformed.x, y_m: number('#bh') - transformed.y };
}

function beginDrag(event) {
  if (!physicalEditEnabled) return;
  event.preventDefault();
  selectedModuleId = event.target.dataset.id;
  const module = layout.modules.find((item) => item.id === selectedModuleId);
  if (module?.string_id) {
    selectedStringId = module.string_id;
    $('#selection').textContent = `Selected string: ${selectedStringId} · physical module ${selectedModuleId}`;
  }
  renderPhysical();
  const move = (pointerEvent) => {
    try {
      const point = svgPoint(pointerEvent);
      layout = moveModule(layout, selectedModuleId, point.x_m, point.y_m, 0.05);
      latest = null;
      calculationSerial += 1;
      renderPhysical(null, new Set());
      $('#status').textContent = 'Physical geometry changed — electrical results are being refreshed';
      $('#status').className = 'warning';
    } catch (error) {
      $('#status').textContent = error.message;
      $('#status').className = 'error';
    }
  };
  const finish = () => {
    window.removeEventListener('pointermove', move);
    window.removeEventListener('pointerup', finish);
    window.removeEventListener('pointercancel', finish);
    calculate().catch(showError);
  };
  window.addEventListener('pointermove', move);
  window.addEventListener('pointerup', finish, { once: true });
  window.addEventListener('pointercancel', finish, { once: true });
}

function switchView(view) {
  activeView = view;
  $('#topology-view').hidden = view !== 'topology';
  $('#physical-view').hidden = view !== 'physical';
  $('#show-topology').setAttribute('aria-pressed', String(view === 'topology'));
  $('#show-physical').setAttribute('aria-pressed', String(view === 'physical'));
  if (view === 'topology') renderTopology();
  else renderPhysical();
}

function setWiringMode(mode) {
  wiringMode = mode;
  document.querySelectorAll('.wiring-mode').forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.mode === mode)));
  renderTopology();
}

function metric(label, value, unit) {
  return `<div class="metric"><small>${label}</small><strong>${fmt(value)}${unit ? ` ${unit}` : ''}</strong></div>`;
}
function showError(error) {
  console.error(error);
  $('#status').textContent = error.message;
  $('#status').className = 'error';
}
function diagnosticMarkup(diagnostics) {
  return [
    `<strong>Longest route:</strong> ${diagnostics.longest_route.string_id} · ${fmt(diagnostics.longest_route.value_m, 1)} m`,
    `<strong>Highest sequential loss:</strong> ${diagnostics.highest_sequential_loss.string_id} · ${fmt(diagnostics.highest_sequential_loss.value_w, 1)} W`,
    `<strong>Highest voltage drop:</strong> ${diagnostics.highest_sequential_voltage_drop.string_id} · ${fmt(diagnostics.highest_sequential_voltage_drop.value_percent, 2)}%`,
    `<strong>Longest round trip:</strong> ${diagnostics.longest_round_trip_delay.string_id} · ${fmt(diagnostics.longest_round_trip_delay.value_us, 2)} µs`,
    `<strong>Field-cable difference:</strong> ${fmt(diagnostics.field_cable_saving_m, 1)} m less in leapfrog`,
  ].map((line) => `<span>${line}</span>`).join('');
}

async function calculate() {
  const serial = ++calculationSerial;
  const sourceLayout = structuredClone(layout);
  $('#status').textContent = `Deriving routes and simulating ${activeDefinition.string_count} strings…`;
  $('#status').className = '';
  const { reference: adapted, derivation } = referenceFromLayout(activeReference, sourceLayout, {
    inverterPoint: activeDefinition.inverter_point,
    geometryAllowance: number('#allowance'),
    intraStringContribution: number('#intra'),
  });
  const comparison = await simulateComparison(adapted, {
    operating_current_a: number('#current'),
    conductor_temperature_c: number('#temperature'),
  });
  if (serial !== calculationSerial || layout.layout_hash !== sourceLayout.layout_hash) return null;
  const analysis = analyseWorkbench(derivation, comparison);
  const diagnosticIds = new Set([
    analysis.diagnostics.longest_route.string_id,
    analysis.diagnostics.highest_sequential_loss.string_id,
    analysis.diagnostics.highest_sequential_voltage_drop.string_id,
    analysis.diagnostics.longest_round_trip_delay.string_id,
  ]);
  latest = { adapted, derivation, comparison, analysis, diagnosticIds };
  renderTopology();
  renderPhysical(derivation, diagnosticIds);
  const seq = comparison.sequential;
  const leap = comparison.leapfrog;
  $('#metrics').innerHTML = [
    metric('Modules', seq.reference_boundary.module_count, ''), metric('Strings', seq.reference_boundary.string_count, ''),
    metric('MPPTs', seq.reference_boundary.mppt_count, ''), metric('Physical inputs', seq.reference_boundary.physical_dc_input_count, ''),
    metric('Sequential loss', seq.totals.circuit_loss_kw, 'kW'), metric('Leapfrog loss', leap.totals.circuit_loss_kw, 'kW'),
    metric('Route spread', analysis.diagnostics.route_spread_m, 'm'), metric('Highest ΔV', analysis.diagnostics.highest_sequential_voltage_drop.value_percent, '%'),
  ].join('');
  $('#diagnostics').innerHTML = diagnosticMarkup(analysis.diagnostics);
  const electricalById = new Map(seq.strings.map((item) => [item.string_id, item]));
  $('#rows').innerHTML = analysis.rows.map((row) => {
    const electrical = electricalById.get(row.string_id);
    const attention = diagnosticIds.has(row.string_id) ? ' class="attention-row"' : '';
    return `<tr${attention}><td>${row.string_id}</td><td>${electrical.input_id}</td><td>${electrical.mppt_id}</td><td>${fmt(row.one_way_route_m, 1)}</td><td>${fmt(row.centroid_x_m, 1)}</td><td>${fmt(row.centroid_y_m, 1)}</td><td>${fmt(row.sequential.loss_w, 1)}</td><td>${fmt(row.leapfrog.loss_w, 1)}</td><td>${fmt(row.sequential.voltage_drop_v, 2)}</td><td>${fmt(row.sequential.voltage_drop_percent, 2)}</td><td>${fmt(row.sequential.round_trip_delay_us, 2)}</td></tr>`;
  }).join('');
  $('#status').textContent = `Complete · ${activeDefinition.string_count} × ${activeDefinition.modules_per_string} · ${wiringMode} view · layout ${derivation.layout_hash.slice(0, 20)}…`;
  $('#status').className = 'ok';
  return latest;
}

function download(filename, content, type) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}
async function currentResults() {
  if (!latest || latest.derivation.layout_hash !== layout.layout_hash) await calculate();
  if (!latest) throw new Error('Electrical results are not current');
  return latest;
}
async function exportJson() {
  const result = await currentResults();
  const payload = buildEngineeringPackage({ layout, adapted: result.adapted, derivation: result.derivation, comparison: result.comparison });
  payload.array_definition = structuredClone(activeDefinition);
  payload.array_editor_self_check = structuredClone(arrayEditorSelfCheck);
  payload.view_contract = {
    schema_version: 'globalgrid2050.v11.full-array-string-strips.v1',
    primary_view: 'v8-style-full-array-string-strips',
    active_view: activeView,
    wiring_mode: wiringMode,
    selected_string_id: selectedStringId,
    string_strip_count: activeDefinition.string_count,
    topology_cell_count: activeDefinition.module_count,
    mppt_group_count: Math.ceil(activeDefinition.string_count / activeDefinition.inputs_per_mppt),
    physical_edit_enabled: physicalEditEnabled,
    sequential_order: electricalOrder(activeDefinition.modules_per_string, 'sequential'),
    leapfrog_order: electricalOrder(activeDefinition.modules_per_string, 'leapfrog'),
  };
  download('v11-integrated-engineering-package.json', JSON.stringify(payload, null, 2) + '\n', 'application/json');
}
async function exportCsv() {
  const result = await currentResults();
  download('v11-string-results.csv', workbenchCsv(result.analysis), 'text/csv;charset=utf-8');
}

async function verifyNonDefaultArray() {
  const selectors = ['#string-count','#modules-per-string','#mppt-count','#inputs-per-mppt','#east-string-count','#strings-per-band','#row-pitch'];
  const saved = Object.fromEntries(selectors.map((selector) => [selector, $(selector).value]));
  const custom = {'#string-count':12,'#modules-per-string':20,'#mppt-count':6,'#inputs-per-mppt':2,'#east-string-count':6,'#strings-per-band':2,'#row-pitch':4};
  try {
    for (const [selector, value] of Object.entries(custom)) $(selector).value = String(value);
    const definition = readArrayDefinition();
    const candidateLayout = buildLayout(definition);
    const candidateReference = adaptedReference(definition);
    const connectorPolicy = candidateReference.conductors.connector_resistance_policy;
    if ('connector_count_per_string' in candidateReference.conductors
        || 'connector_count_per_string_status' in candidateReference.conductors) {
      throw new Error('Non-default array reintroduced deprecated connector compatibility fields');
    }
    if (connectorPolicy.module_to_module_mate_count !== 19
        || connectorPolicy.module_to_string_cable_mate_count !== 2
        || connectorPolicy.string_cable_to_inverter_mate_count !== 2
        || connectorPolicy.total_mated_interface_count !== 23) {
      throw new Error('Non-default array connector policy must contain 19 + 2 + 2 = 23 mated interfaces');
    }
    const { reference: adapted, derivation } = referenceFromLayout(candidateReference, candidateLayout, {
      inverterPoint: definition.inverter_point,
      geometryAllowance: 1.1,
      intraStringContribution: 0.5,
    });
    const comparison = await simulateComparison(adapted, { operating_current_a: 17.31, conductor_temperature_c: 70 });
    if (candidateLayout.modules.length !== 240 || derivation.string_count !== 12 || comparison.sequential.strings.length !== 12) {
      throw new Error('Non-default 12 × 20 array self-check returned inconsistent counts');
    }
    const finalString = comparison.sequential.strings.at(-1);
    if (finalString.input_id !== 'IN-12' || finalString.mppt_id !== 'MPPT-06') {
      throw new Error('Non-default array self-check returned inconsistent input allocation');
    }
    return {
      schema_version: 'globalgrid2050.v11.array-editor-self-check.v3',
      pass: true,
      strings: 12,
      modules_per_string: 20,
      modules: 240,
      mppts: 6,
      inputs_per_mppt: 2,
      string_strips: 12,
      topology_cells: 240,
      connector_accounting: {
        module_connector_ends: 40,
        string_cable_connector_ends: 4,
        inverter_connector_ends: 2,
        complete_system_connector_ends: 46,
        module_to_module_mates: connectorPolicy.module_to_module_mate_count,
        module_to_string_cable_mates: connectorPolicy.module_to_string_cable_mate_count,
        string_cable_to_inverter_mates: connectorPolicy.string_cable_to_inverter_mate_count,
        total_mated_interfaces: connectorPolicy.total_mated_interface_count,
        deprecated_compatibility_fields_absent: true,
      },
      final_input_id: finalString.input_id,
      final_mppt_id: finalString.mppt_id,
      layout_hash: candidateLayout.layout_hash,
      comparison_hash: comparison.comparison_hash,
    };
  } finally {
    for (const [selector, value] of Object.entries(saved)) $(selector).value = value;
  }
}

async function rebuildAndCalculate() {
  try {
    resetLayout();
    await calculate();
  } catch (error) {
    showError(error);
  }
}

async function init() {
  referenceFixture = await fetch('../reference/lab_inverter_block_24_strings.json').then((response) => {
    if (!response.ok) throw new Error(`Reference load failed: ${response.status}`);
    return response.json();
  });
  arrayEditorSelfCheck = await verifyNonDefaultArray();
  window.__v11ArrayEditorEvidence = structuredClone(arrayEditorSelfCheck);
  $('#reset').addEventListener('click', rebuildAndCalculate);
  $('#simulate').addEventListener('click', () => calculate().catch(showError));
  $('#reset-view').addEventListener('click', () => {
    selectedStringId = 'STR-01';
    setWiringMode('leapfrog');
    switchView('topology');
  });
  $('#export').addEventListener('click', () => exportJson().catch(showError));
  $('#export-csv').addEventListener('click', () => exportCsv().catch(showError));
  $('#show-topology').addEventListener('click', () => switchView('topology'));
  $('#show-physical').addEventListener('click', () => switchView('physical'));
  $('#edit-physical').addEventListener('change', (event) => {
    physicalEditEnabled = event.target.checked;
    $('#status').textContent = physicalEditEnabled
      ? 'Physical editing enabled — drag carefully'
      : 'Physical editing locked — scrolling is safe';
    $('#status').className = physicalEditEnabled ? 'warning' : 'ok';
    renderPhysical();
  });
  document.querySelectorAll('.wiring-mode').forEach((button) => button.addEventListener('click', () => setWiringMode(button.dataset.mode)));
  ['#current', '#temperature', '#allowance', '#intra', '#inverter-x', '#inverter-y'].forEach((selector) => {
    $(selector).addEventListener('change', () => calculate().catch(showError));
  });
  resetLayout();
  await calculate();
}
init().catch(showError);
