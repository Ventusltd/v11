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
const fmt = (value, digits = 2) => Number(value).toLocaleString(undefined, {
  minimumFractionDigits: digits,
  maximumFractionDigits: digits,
});

let referenceFixture;
let activeReference;
let activeDefinition;
let layout;
let selectedId = null;
let latest = null;
let calculationSerial = 0;
let arrayEditorSelfCheck = null;

function installArrayEditorUi() {
  const controls = document.querySelector('.controls');
  if (!controls) throw new Error('Workbench control panel is missing');
  controls.insertAdjacentHTML('afterbegin', `
    <label>Strings<input id="string-count" type="number" min="1" value="24" step="1"></label>
    <label>Modules / string<input id="modules-per-string" type="number" min="2" value="30" step="1"></label>
    <label>MPPTs<input id="mppt-count" type="number" min="1" value="12" step="1"></label>
    <label>Inputs / MPPT<input id="inputs-per-mppt" type="number" min="1" value="2" step="1"></label>
    <label>Strings / row<input id="strings-per-row" type="number" min="1" value="1" step="1"></label>
    <label>Row pitch m<input id="row-pitch" type="number" min="0.1" value="2.50" step="0.1"></label>
    <label>Inverter X m<input id="inverter-x" type="number" value="41" step="0.1"></label>
    <label>Inverter Y m<input id="inverter-y" type="number" value="31" step="0.1"></label>
  `);
  const reset = document.querySelector('#reset');
  if (reset) reset.textContent = 'Build / rebuild array';
  const selection = document.querySelector('#selection');
  if (selection) selection.insertAdjacentHTML('beforebegin', '<p id="active-boundary">Active array: —</p>');
  const description = document.querySelector('.head p');
  if (description) description.textContent = 'Define the array, place its inverter, move modules and recalculate every string. The committed 24 × 30 block remains the default, not a hard limit.';
  const header = document.querySelector('table thead tr');
  if (header) header.innerHTML = '<th>String</th><th>Input</th><th>MPPT</th><th>Route m</th><th>Centroid X</th><th>Centroid Y</th><th>Seq loss W</th><th>Leap loss W</th><th>ΔV seq V</th><th>ΔV seq %</th><th>RT delay µs</th>';
}

function readArrayDefinition() {
  const stringCount = positiveInt('#string-count', 'String count');
  const modulesPerString = positiveInt('#modules-per-string', 'Modules per string', 2);
  const mpptCount = positiveInt('#mppt-count', 'MPPT count');
  const inputsPerMppt = positiveInt('#inputs-per-mppt', 'Inputs per MPPT');
  const stringsPerRow = positiveInt('#strings-per-row', 'Strings per row');
  const physicalInputCount = mpptCount * inputsPerMppt;
  if (stringCount > physicalInputCount) {
    throw new Error(`${stringCount} strings exceeds ${physicalInputCount} physical inputs`);
  }
  return {
    schema_version: 'globalgrid2050.v11.array-definition.v1',
    string_count: stringCount,
    modules_per_string: modulesPerString,
    module_count: stringCount * modulesPerString,
    mppt_count: mpptCount,
    inputs_per_mppt: inputsPerMppt,
    physical_dc_input_count: physicalInputCount,
    strings_per_row: stringsPerRow,
    row_pitch_m: number('#row-pitch'),
    inverter_point: { x_m: number('#inverter-x'), y_m: number('#inverter-y') },
  };
}

function adaptedReference(definition) {
  const adapted = structuredClone(referenceFixture);
  adapted.block_id = `v11_user_array_${definition.string_count}x${definition.modules_per_string}`;
  adapted.array.string_count = definition.string_count;
  adapted.array.modules_per_string = definition.modules_per_string;
  adapted.array.module_pitch_m = number('#mw') + number('#gx');
  adapted.array.row_spacing_m = definition.row_pitch_m;
  adapted.array.leapfrog_factory_extra_m_per_string = adapted.array.module_pitch_m;
  adapted.inverter.mppt_count = definition.mppt_count;
  adapted.inverter.strings_per_mppt = definition.inputs_per_mppt;
  adapted.inverter.physical_dc_input_count = definition.physical_dc_input_count;
  adapted.conductors.connector_count_per_string = definition.modules_per_string + 1;
  adapted.routing.route_lengths_m = Array(definition.string_count).fill(0);
  adapted.provenance = {
    ...adapted.provenance,
    array_definition_schema: definition.schema_version,
    adaptation: `${adapted.provenance.adaptation} User array cardinality and deterministic input allocation applied in V11 browser without mutating the committed fixture.`,
  };
  return adapted;
}

function buildLayout(definition) {
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
    throw new Error(`Row pitch ${rowPitchM} m is smaller than module height plus Y gap ${heightM + gapYM} m`);
  }
  const xPitch = widthM + gapXM;
  const rows = Math.ceil(definition.string_count / definition.strings_per_row);
  const usedSlots = Math.min(definition.strings_per_row, definition.string_count);
  const requiredWidth = usedSlots * definition.modules_per_string * xPitch - gapXM;
  const requiredHeight = heightM + (rows - 1) * rowPitchM;
  if (requiredWidth > boundary.x_max - boundary.x_min + 1e-9 || requiredHeight > boundary.y_max - boundary.y_min + 1e-9) {
    throw new Error(`Boundary cannot fit ${definition.module_count} modules: requires ${requiredWidth.toFixed(3)} m × ${requiredHeight.toFixed(3)} m`);
  }
  const modules = [];
  for (let stringOffset = 0; stringOffset < definition.string_count; stringOffset += 1) {
    const physicalRow = Math.floor(stringOffset / definition.strings_per_row);
    const slot = stringOffset % definition.strings_per_row;
    const stringId = `STR-${String(stringOffset + 1).padStart(2, '0')}`;
    for (let electricalOffset = 0; electricalOffset < definition.modules_per_string; electricalOffset += 1) {
      const moduleOffset = modules.length;
      modules.push({
        id: `MOD-${String(moduleOffset + 1).padStart(4, '0')}`,
        x_m: +(boundary.x_min + widthM / 2 + (slot * definition.modules_per_string + electricalOffset) * xPitch).toFixed(9),
        y_m: +(boundary.y_min + heightM / 2 + physicalRow * rowPitchM).toFixed(9),
        width_m: widthM,
        height_m: heightM,
        rotation_deg: 0,
        row: physicalRow,
        column: slot * definition.modules_per_string + electricalOffset,
        string_id: stringId,
        electrical_index: electricalOffset + 1,
      });
    }
  }
  const result = {
    schema_version: 'globalgrid2050.v11.module-layout.v1',
    boundary,
    obstacles: [],
    array_definition: structuredClone(definition),
    modules,
  };
  result.layout_hash = layoutHash(result);
  return result;
}

function resetLayout() {
  const definition = readArrayDefinition();
  const candidateLayout = buildLayout(definition);
  activeDefinition = definition;
  activeReference = adaptedReference(definition);
  layout = candidateLayout;
  selectedId = null;
  latest = null;
  calculationSerial += 1;
  $('#active-boundary').textContent = `Active array: ${definition.string_count} strings × ${definition.modules_per_string} modules = ${definition.module_count} modules · ${definition.mppt_count} MPPTs × ${definition.inputs_per_mppt} inputs`;
  renderLayout();
}

function renderLayout(derivation = null, diagnosticIds = new Set()) {
  const svg = $('#canvas');
  const width = number('#bw');
  const height = number('#bh');
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  const routes = derivation ? derivation.strings.map((item) => {
    const attention = diagnosticIds.has(item.string_id) ? ' attention-route' : '';
    return `<line class="route${attention}" x1="${item.centroid.x_m}" y1="${height - item.centroid.y_m}" x2="${derivation.inverter_point.x_m}" y2="${height - derivation.inverter_point.y_m}"/>`;
  }).join('') : '';
  const modules = layout.modules.map((module) => {
    const box = footprint(module);
    const selected = module.id === selectedId ? ' selected' : '';
    const attention = diagnosticIds.has(module.string_id) ? ' attention-module' : '';
    return `<rect class="module${selected}${attention}" data-id="${module.id}" x="${box.left}" y="${height - box.top}" width="${box.width}" height="${box.height}"/>`;
  }).join('');
  const inverter = derivation ? `<circle class="inverter" cx="${derivation.inverter_point.x_m}" cy="${height - derivation.inverter_point.y_m}" r="0.45"/>` : '';
  svg.innerHTML = `${routes}${modules}${inverter}`;
  svg.querySelectorAll('.module').forEach((element) => element.addEventListener('pointerdown', beginDrag));
}

function svgPoint(event) {
  const svg = $('#canvas');
  const matrix = svg.getScreenCTM();
  if (!matrix) throw new Error('Layout canvas is not available');
  const point = svg.createSVGPoint();
  point.x = event.clientX;
  point.y = event.clientY;
  const transformed = point.matrixTransform(matrix.inverse());
  return { x_m: transformed.x, y_m: number('#bh') - transformed.y };
}

function beginDrag(event) {
  event.preventDefault();
  selectedId = event.target.dataset.id;
  $('#selection').textContent = `Selected ${selectedId}`;
  renderLayout(latest?.derivation ?? null, latest?.diagnosticIds ?? new Set());
  const move = (pointerEvent) => {
    try {
      const point = svgPoint(pointerEvent);
      layout = moveModule(layout, selectedId, point.x_m, point.y_m, 0.05);
      latest = null;
      calculationSerial += 1;
      renderLayout();
      $('#status').textContent = 'Geometry changed — electrical results are being refreshed';
      $('#status').className = '';
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

function metric(label, value, unit) {
  return `<div class="metric"><small>${label}</small><strong>${fmt(value)}${unit ? ` ${unit}` : ''}</strong></div>`;
}
function showError(error) {
  console.error(error);
  $('#status').textContent = error.message;
  $('#status').className = 'error';
}
function showDefinitionError(error) {
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
  renderLayout(derivation, diagnosticIds);
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
  $('#status').textContent = `Complete · ${activeDefinition.string_count} × ${activeDefinition.modules_per_string} · layout ${derivation.layout_hash.slice(0, 20)}…`;
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
  download('v11-integrated-engineering-package.json', JSON.stringify(payload, null, 2) + '\n', 'application/json');
}
async function exportCsv() {
  const result = await currentResults();
  download('v11-string-results.csv', workbenchCsv(result.analysis), 'text/csv;charset=utf-8');
}

async function verifyNonDefaultArray() {
  const selectors = ['#string-count','#modules-per-string','#mppt-count','#inputs-per-mppt','#strings-per-row','#row-pitch'];
  const saved = Object.fromEntries(selectors.map((selector) => [selector, $(selector).value]));
  const custom = {'#string-count':12,'#modules-per-string':20,'#mppt-count':6,'#inputs-per-mppt':2,'#strings-per-row':1,'#row-pitch':4};
  try {
    for (const [selector, value] of Object.entries(custom)) $(selector).value = String(value);
    const definition = readArrayDefinition();
    const candidateLayout = buildLayout(definition);
    const candidateReference = adaptedReference(definition);
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
      schema_version: 'globalgrid2050.v11.array-editor-self-check.v1',
      pass: true,
      strings: 12,
      modules_per_string: 20,
      modules: 240,
      mppts: 6,
      inputs_per_mppt: 2,
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
    showDefinitionError(error);
  }
}
async function init() {
  installArrayEditorUi();
  referenceFixture = await fetch('../reference/lab_inverter_block_24_strings.json').then((response) => {
    if (!response.ok) throw new Error(`Reference load failed: ${response.status}`);
    return response.json();
  });
  arrayEditorSelfCheck = await verifyNonDefaultArray();
  window.__v11ArrayEditorEvidence = structuredClone(arrayEditorSelfCheck);
  $('#reset').addEventListener('click', rebuildAndCalculate);
  $('#simulate').addEventListener('click', () => calculate().catch(showError));
  $('#export').addEventListener('click', () => exportJson().catch(showError));
  $('#export-csv').addEventListener('click', () => exportCsv().catch(showError));
  ['#current', '#temperature', '#allowance', '#intra', '#inverter-x', '#inverter-y'].forEach((selector) => {
    $(selector).addEventListener('change', () => calculate().catch(showError));
  });
  resetLayout();
  await calculate();
}
init().catch(showError);
