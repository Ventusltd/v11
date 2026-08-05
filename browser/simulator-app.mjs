import { simulateComparison, electricalModuleOrder } from "./simulation-core.mjs";

const $ = (selector) => document.querySelector(selector);
const fmt = (value, digits = 2) => Number(value).toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: digits });

let reference;

function inputNumber(id) {
  return Number($(id).value);
}

function overrides() {
  return {
    operating_current_a: inputNumber("#operating-current"),
    conductor_temperature_c: inputNumber("#conductor-temperature"),
    minimum_cell_temperature_c: inputNumber("#minimum-temperature"),
    home_pair_separation_m: inputNumber("#pair-spacing-mm") / 1000,
    effective_relative_permittivity: inputNumber("#relative-permittivity"),
    sequential_row_return_separation_m: inputNumber("#row-return-separation"),
    route_multiplier: inputNumber("#route-multiplier"),
    module_pitch_m: inputNumber("#module-pitch"),
  };
}

function card(label, sequential, leapfrog, unit, smallerIsBetter = true) {
  const delta = leapfrog - sequential;
  const winner = Math.abs(delta) < 1e-12 ? "equal" : ((delta < 0) === smallerIsBetter ? "leapfrog" : "sequential");
  return `<article class="metric"><span>${label}</span><strong>${fmt(sequential)} <small>${unit}</small></strong><strong>${fmt(leapfrog)} <small>${unit}</small></strong><em class="${winner}">${delta >= 0 ? "+" : ""}${fmt(delta)} ${unit}</em></article>`;
}

function drawTopology(strategy) {
  const svg = $(strategy === "sequential" ? "#sequential-svg" : "#leapfrog-svg");
  const ids = Array.from({ length: 30 }, (_, i) => `M${String(i + 1).padStart(2, "0")}`);
  const order = electricalModuleOrder(ids, strategy);
  const points = new Map(ids.map((id, i) => [id, { x: 24 + i * 30, y: 58 }]));
  let path = "";
  order.forEach((id, index) => {
    const point = points.get(id);
    path += `${index ? " L" : "M"}${point.x},${point.y}`;
  });
  const modules = ids.map((id, i) => `<rect x="${16 + i * 30}" y="42" width="16" height="32" rx="2"/><text x="${24 + i * 30}" y="92">${i + 1}</text>`).join("");
  svg.innerHTML = `<g class="modules">${modules}</g><path class="route ${strategy}" d="${path}"/><text x="20" y="20">${strategy.toUpperCase()} electrical traversal</text>`;
}

function tableRows(result) {
  return result.strings.map((item) => `<tr>
    <td>${item.string_id}</td><td>${item.mppt_id}</td><td>${fmt(item.one_way_route_m, 0)}</td>
    <td>${fmt(item.circuit_resistance_ohm, 3)}</td><td>${fmt(item.voltage_drop_v, 2)}</td>
    <td>${fmt(item.loss_w, 1)}</td><td>${fmt(item.round_trip_delay_us, 2)}</td>
    <td>${fmt(item.interruption_envelope_v, 0)}</td>
  </tr>`).join("");
}

async function run() {
  try {
    $("#status").textContent = "Calculating 24 strings…";
    const comparison = await simulateComparison(reference, overrides());
    const seq = comparison.sequential;
    const leap = comparison.leapfrog;
    $("#reference-summary").innerHTML = `
      <strong>${seq.reference_boundary.module_count} modules</strong>
      <span>${seq.reference_boundary.string_count} strings × ${seq.reference_boundary.modules_per_string} modules</span>
      <span>${fmt(seq.reference_boundary.dc_nameplate_power_kwp, 1)} kWp / ${fmt(seq.reference_boundary.inverter_apparent_power_kva, 0)} kVA</span>
      <span>DC/AC ${fmt(seq.reference_boundary.dc_ac_nameplate_ratio, 2)}</span>`;
    $("#metrics").innerHTML = [
      card("Field cable", seq.totals.field_cable_length_m, leap.totals.field_cable_length_m, "m"),
      card("Factory lead", seq.totals.factory_lead_length_m, leap.totals.factory_lead_length_m, "m"),
      card("Circuit loss", seq.totals.circuit_loss_kw, leap.totals.circuit_loss_kw, "kW"),
      card("Approx. loop area", seq.totals.approximate_loop_area_m2, leap.totals.approximate_loop_area_m2, "m²"),
      card("Delivered block power", seq.totals.delivered_power_kw, leap.totals.delivered_power_kw, "kW", false),
      card("Magnetic energy", seq.totals.external_magnetic_energy_j, leap.totals.external_magnetic_energy_j, "J"),
    ].join("");
    $("#line-metrics").innerHTML = `
      <strong>Z₀ ${fmt(leap.transmission_line.characteristic_impedance_ohm, 1)} Ω</strong>
      <span>Velocity ${fmt(leap.transmission_line.propagation_velocity_m_per_s / 1e8, 2)} ×10⁸ m/s</span>
      <span>Cold string Voc ${fmt(leap.totals.cold_string_voc_v, 1)} V</span>
      <span>Evidence: ${leap.reference_boundary.equipment_evidence_state}</span>`;
    $("#sequential-table tbody").innerHTML = tableRows(seq);
    $("#leapfrog-table tbody").innerHTML = tableRows(leap);
    $("#hashes").textContent = `Comparison ${comparison.comparison_hash} · Sequential ${seq.simulation_hash} · Leapfrog ${leap.simulation_hash}`;
    $("#status").textContent = "Simulation complete";
  } catch (error) {
    console.error(error);
    $("#status").textContent = `Error: ${error.message}`;
  }
}

async function init() {
  reference = await fetch("../reference/lab_inverter_block_24_strings.json").then((response) => {
    if (!response.ok) throw new Error(`Unable to load reference block: ${response.status}`);
    return response.json();
  });
  drawTopology("sequential");
  drawTopology("leapfrog");
  $("#simulate").addEventListener("click", run);
  document.querySelectorAll("input").forEach((input) => input.addEventListener("change", run));
  await run();
}

init();
