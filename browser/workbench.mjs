import { fillRectangle, moveModule, footprint, assignStrings } from './layout-core.mjs';
import { referenceFromLayout } from './layout-simulation-bridge.mjs';
import { simulateComparison } from './simulation-core.mjs';
import { analyseWorkbench, buildEngineeringPackage, workbenchCsv } from './workbench-analysis.mjs';

const $ = (selector) => document.querySelector(selector);
const number = (selector) => Number($(selector).value);
const fmt = (value, digits = 2) => Number(value).toLocaleString(undefined, {
  minimumFractionDigits: digits,
  maximumFractionDigits: digits,
});

let reference;
let layout;
let selectedId = null;
let latest = null;
let calculationSerial = 0;

function resetLayout() {
  const filled = fillRectangle({
    boundary: { x_min: 0, y_min: 0, x_max: number('#bw'), y_max: number('#bh') },
    moduleWidthM: number('#mw'),
    moduleHeightM: number('#mh'),
    gapXM: number('#gx'),
    gapYM: number('#gy'),
    limit: 720,
  });
  if (filled.modules.length !== 720) {
    throw new Error(`Boundary fits only ${filled.modules.length} modules; 720 required`);
  }
  layout = assignStrings(filled, Number(reference.array.modules_per_string), true);
  selectedId = null;
  latest = null;
  calculationSerial += 1;
  renderLayout();
}

function renderLayout(derivation = null, diagnosticIds = new Set()) {
  const svg = $('#canvas');
  const width = number('#bw');
  const height = number('#bh');
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  const routes = derivation
    ? derivation.strings.map((item) => {
        const attention = diagnosticIds.has(item.string_id) ? ' attention-route' : '';
        return `<line class="route${attention}" x1="${item.centroid.x_m}" y1="${height - item.centroid.y_m}" x2="${derivation.inverter_point.x_m}" y2="${height - derivation.inverter_point.y_m}"/>`;
      }).join('')
    : '';
  const modules = layout.modules.map((module) => {
    const box = footprint(module);
    const selected = module.id === selectedId ? ' selected' : '';
    const attention = diagnosticIds.has(module.string_id) ? ' attention-module' : '';
    return `<rect class="module${selected}${attention}" data-id="${module.id}" x="${box.left}" y="${height - box.top}" width="${box.width}" height="${box.height}"/>`;
  }).join('');
  const inverter = derivation
    ? `<circle class="inverter" cx="${derivation.inverter_point.x_m}" cy="${height - derivation.inverter_point.y_m}" r="0.45"/>`
    : '';
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
  const suffix = unit ? ` ${unit}` : '';
  return `<div class="metric"><small>${label}</small><strong>${fmt(value)}${suffix}</strong></div>`;
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
  $('#status').textContent = 'Deriving routes and simulating 24 strings…';
  $('#status').className = '';
  const { reference: adapted, derivation } = referenceFromLayout(reference, sourceLayout, {
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
    metric('Modules', seq.reference_boundary.module_count, ''),
    metric('Strings', seq.reference_boundary.string_count, ''),
    metric('Sequential loss', seq.totals.circuit_loss_kw, 'kW'),
    metric('Leapfrog loss', leap.totals.circuit_loss_kw, 'kW'),
    metric('Route spread', analysis.diagnostics.route_spread_m, 'm'),
    metric('Highest ΔV', analysis.diagnostics.highest_sequential_voltage_drop.value_percent, '%'),
    metric('Sequential cable', seq.totals.field_cable_length_m, 'm'),
    metric('Leapfrog cable', leap.totals.field_cable_length_m, 'm'),
  ].join('');
  $('#diagnostics').innerHTML = diagnosticMarkup(analysis.diagnostics);
  $('#rows').innerHTML = analysis.rows.map((row) => {
    const attention = diagnosticIds.has(row.string_id) ? ' class="attention-row"' : '';
    return `<tr${attention}><td>${row.string_id}</td><td>${fmt(row.one_way_route_m, 1)}</td><td>${fmt(row.centroid_x_m, 1)}</td><td>${fmt(row.centroid_y_m, 1)}</td><td>${fmt(row.sequential.loss_w, 1)}</td><td>${fmt(row.leapfrog.loss_w, 1)}</td><td>${fmt(row.sequential.voltage_drop_v, 2)}</td><td>${fmt(row.sequential.voltage_drop_percent, 2)}</td><td>${fmt(row.sequential.round_trip_delay_us, 2)}</td></tr>`;
  }).join('');
  $('#status').textContent = `Complete · layout ${derivation.layout_hash.slice(0, 24)}…`;
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
  const payload = buildEngineeringPackage({
    layout,
    adapted: result.adapted,
    derivation: result.derivation,
    comparison: result.comparison,
  });
  download('v11-integrated-engineering-package.json', JSON.stringify(payload, null, 2) + '\n', 'application/json');
}

async function exportCsv() {
  const result = await currentResults();
  download('v11-string-results.csv', workbenchCsv(result.analysis), 'text/csv;charset=utf-8');
}

async function init() {
  reference = await fetch('../reference/lab_inverter_block_24_strings.json').then((response) => {
    if (!response.ok) throw new Error(`Reference load failed: ${response.status}`);
    return response.json();
  });
  $('#reset').addEventListener('click', async () => { resetLayout(); await calculate(); });
  $('#simulate').addEventListener('click', () => calculate().catch(showError));
  $('#export').addEventListener('click', () => exportJson().catch(showError));
  $('#export-csv').addEventListener('click', () => exportCsv().catch(showError));
  ['#current', '#temperature', '#allowance', '#intra'].forEach((selector) => {
    $(selector).addEventListener('change', () => calculate().catch(showError));
  });
  resetLayout();
  await calculate();
}

init().catch(showError);
