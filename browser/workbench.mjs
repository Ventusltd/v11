import { fillRectangle, moveModule, footprint } from './layout-core.mjs';
import { referenceFromLayout } from './layout-simulation-bridge.mjs';
import { simulateComparison } from './simulation-core.mjs';

const $ = (selector) => document.querySelector(selector);
const number = (selector) => Number($(selector).value);
const fmt = (value, digits = 2) => Number(value).toLocaleString(undefined, {minimumFractionDigits: digits, maximumFractionDigits: digits});
let reference;
let layout;
let selectedId = null;
let latest = null;

function resetLayout() {
  layout = fillRectangle({
    boundary: {x_min: 0, y_min: 0, x_max: number('#bw'), y_max: number('#bh')},
    moduleWidthM: number('#mw'), moduleHeightM: number('#mh'), gapXM: number('#gx'), gapYM: number('#gy'), limit: 720,
  });
  if (layout.modules.length !== 720) throw new Error(`Boundary fits only ${layout.modules.length} modules; 720 required`);
  selectedId = null;
  renderLayout();
}

function renderLayout(derivation = null) {
  const svg = $('#canvas');
  const width = number('#bw'), height = number('#bh');
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  const routes = derivation ? derivation.strings.map((item) => `<line class="route" x1="${item.centroid.x_m}" y1="${height - item.centroid.y_m}" x2="${derivation.inverter_point.x_m}" y2="${height - derivation.inverter_point.y_m}"/>`).join('') : '';
  const modules = layout.modules.map((module) => {
    const box = footprint(module);
    return `<rect class="module${module.id === selectedId ? ' selected' : ''}" data-id="${module.id}" x="${box.left}" y="${height - box.top}" width="${box.width}" height="${box.height}"/>`;
  }).join('');
  const inverter = derivation ? `<circle class="inverter" cx="${derivation.inverter_point.x_m}" cy="${height - derivation.inverter_point.y_m}" r="0.45"/>` : '';
  svg.innerHTML = `${routes}${modules}${inverter}`;
  svg.querySelectorAll('.module').forEach((element) => element.addEventListener('pointerdown', beginDrag));
}

function svgPoint(event) {
  const svg = $('#canvas');
  const point = svg.createSVGPoint(); point.x = event.clientX; point.y = event.clientY;
  const transformed = point.matrixTransform(svg.getScreenCTM().inverse());
  return {x_m: transformed.x, y_m: number('#bh') - transformed.y};
}

function beginDrag(event) {
  selectedId = event.target.dataset.id;
  $('#selection').textContent = `Selected ${selectedId}`;
  renderLayout(latest?.derivation);
  const move = (pointerEvent) => {
    try {
      const point = svgPoint(pointerEvent);
      layout = moveModule(layout, selectedId, point.x_m, point.y_m, 0.05);
      renderLayout(latest?.derivation);
      $('#status').textContent = 'Geometry changed — recalculate to update electrical results';
      $('#status').className = '';
    } catch (error) {
      $('#status').textContent = error.message;
      $('#status').className = 'error';
    }
  };
  const finish = () => { window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', finish); };
  window.addEventListener('pointermove', move); window.addEventListener('pointerup', finish, {once: true});
}

function metric(label, value, unit) { return `<div class="metric"><small>${label}</small><strong>${fmt(value)} ${unit}</strong></div>`; }

async function calculate() {
  $('#status').textContent = 'Deriving routes and simulating 24 strings…';
  $('#status').className = '';
  const {reference: adapted, derivation} = referenceFromLayout(reference, layout, {
    geometryAllowance: number('#allowance'), intraStringContribution: number('#intra'),
  });
  const comparison = await simulateComparison(adapted, {
    operating_current_a: number('#current'), conductor_temperature_c: number('#temperature'),
  });
  latest = {adapted, derivation, comparison};
  renderLayout(derivation);
  const seq = comparison.sequential, leap = comparison.leapfrog;
  $('#metrics').innerHTML = [
    metric('Modules', seq.reference_boundary.module_count, ''), metric('Strings', seq.reference_boundary.string_count, ''),
    metric('Sequential loss', seq.totals.circuit_loss_kw, 'kW'), metric('Leapfrog loss', leap.totals.circuit_loss_kw, 'kW'),
    metric('Worst route', Math.max(...derivation.route_lengths_m), 'm'), metric('Shortest route', Math.min(...derivation.route_lengths_m), 'm'),
    metric('Sequential cable', seq.totals.field_cable_length_m, 'm'), metric('Leapfrog cable', leap.totals.field_cable_length_m, 'm'),
  ].join('');
  $('#rows').innerHTML = derivation.strings.map((item, index) => `<tr><td>${item.string_id}</td><td>${fmt(item.one_way_route_m,1)}</td><td>${fmt(item.centroid.x_m,1)}</td><td>${fmt(item.centroid.y_m,1)}</td><td>${fmt(seq.strings[index].loss_w,1)}</td><td>${fmt(leap.strings[index].loss_w,1)}</td><td>${fmt(seq.strings[index].voltage_drop_v,2)}</td><td>${fmt(seq.strings[index].round_trip_delay_us,2)}</td></tr>`).join('');
  $('#status').textContent = `Complete · layout ${derivation.layout_hash.slice(0,24)}…`;
  $('#status').className = 'ok';
}

function exportJson() {
  if (!latest) return;
  const blob = new Blob([JSON.stringify({layout, ...latest}, null, 2)], {type:'application/json'});
  const anchor = document.createElement('a'); anchor.href = URL.createObjectURL(blob); anchor.download = 'v11-integrated-workbench.json'; anchor.click(); URL.revokeObjectURL(anchor.href);
}

async function init() {
  reference = await fetch('../reference/lab_inverter_block_24_strings.json').then((response) => { if (!response.ok) throw new Error(`Reference load failed: ${response.status}`); return response.json(); });
  $('#reset').addEventListener('click', async () => { try { resetLayout(); await calculate(); } catch (error) { $('#status').textContent = error.message; $('#status').className='error'; } });
  $('#simulate').addEventListener('click', () => calculate().catch((error) => { $('#status').textContent = error.message; $('#status').className='error'; }));
  $('#export').addEventListener('click', exportJson);
  resetLayout(); await calculate();
}
init().catch((error) => { $('#status').textContent = error.message; $('#status').className='error'; });
