import { resistanceAccounting } from './connector-accounting.mjs';

const MU0 = 4e-7 * Math.PI;
const EPS0 = 8.8541878128e-12;

export class SimulationInputError extends Error {}

function finite(name, value, minimum = null) {
  const result = Number(value);
  if (!Number.isFinite(result)) throw new SimulationInputError(`${name} must be finite`);
  if (minimum !== null && result < minimum) throw new SimulationInputError(`${name} must be >= ${minimum}`);
  return result;
}

function positiveInt(name, value) {
  const result = Number(value);
  if (!Number.isInteger(result) || result <= 0) throw new SimulationInputError(`${name} must be a positive integer`);
  return result;
}

export function canonicalJson(value) {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  const keys = Object.keys(value).sort();
  return `{${keys.map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(",")}}`;
}

async function sha256Hex(text) {
  if (globalThis.crypto?.subtle) {
    const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
    return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
  }
  const { createHash } = await import("node:crypto");
  return createHash("sha256").update(text).digest("hex");
}

export async function canonicalHash(value) {
  return `sha256:${await sha256Hex(canonicalJson(value))}`;
}

export function validateReferenceBlock(payload) {
  if (payload.schema_version !== "globalgrid2050.v11.inverter-block-input.v1") {
    throw new SimulationInputError("unsupported inverter-block schema");
  }
  const strings = positiveInt("string_count", payload.array?.string_count);
  const modules = positiveInt("modules_per_string", payload.array?.modules_per_string);
  const inputs = positiveInt("physical_dc_input_count", payload.inverter?.physical_dc_input_count);
  if (strings > inputs) throw new SimulationInputError("string count exceeds physical DC input count");
  if (modules < 2) throw new SimulationInputError("at least two modules are required per string");
  if (!Array.isArray(payload.routing?.route_lengths_m) || payload.routing.route_lengths_m.length !== strings) {
    throw new SimulationInputError("one route length is required for every string");
  }
  payload.routing.route_lengths_m.forEach((value, index) => finite(`route_lengths_m[${index + 1}]`, value, 0));
  finite("module_pitch_m", payload.array.module_pitch_m, 0.001);
  finite("junction_box_separation_m", payload.array.junction_box_separation_m, 0);
}

export function electricalModuleOrder(moduleIds, strategy) {
  const ids = [...moduleIds];
  if (!ids.length) throw new SimulationInputError("at least one module is required");
  if (new Set(ids).size !== ids.length) throw new SimulationInputError("module identifiers must be unique");
  if (strategy === "sequential") return ids;
  if (strategy === "leapfrog") {
    const odd = ids.filter((_, index) => index % 2 === 0);
    const even = ids.filter((_, index) => index % 2 === 1).reverse();
    return [...odd, ...even];
  }
  throw new SimulationInputError(`unsupported wiring strategy: ${strategy}`);
}

function temperatureResistance(r20, temperatureC, alpha) {
  const factor = 1 + alpha * (temperatureC - 20);
  if (factor <= 0) throw new SimulationInputError("conductor temperature correction is non-positive");
  return r20 * factor;
}

function acosh(value) {
  return Math.log(value + Math.sqrt(value * value - 1));
}

export function twoWireParameters(areaMm2, centreSpacingM, relativePermittivity) {
  const areaM2 = finite("area_mm2", areaMm2, 0.001) * 1e-6;
  const diameterM = Math.sqrt((4 * areaM2) / Math.PI);
  const spacing = finite("centre_spacing_m", centreSpacingM, 0.000001);
  const epsR = finite("relative_permittivity", relativePermittivity, 1);
  if (spacing <= diameterM) throw new SimulationInputError("pair centre spacing must exceed equivalent conductor diameter");
  const geometry = acosh(spacing / diameterM);
  const inductance = (MU0 / Math.PI) * geometry;
  const capacitance = (Math.PI * EPS0 * epsR) / geometry;
  return {
    equivalent_conductor_diameter_m: diameterM,
    external_inductance_h_per_m: inductance,
    differential_capacitance_f_per_m: capacitance,
    characteristic_impedance_ohm: Math.sqrt(inductance / capacitance),
    propagation_velocity_m_per_s: 1 / Math.sqrt(inductance * capacitance),
  };
}

export async function simulateBlock(reference, strategy, overrides = {}) {
  validateReferenceBlock(reference);
  const allowed = new Set([
    "operating_current_a", "conductor_temperature_c", "minimum_cell_temperature_c",
    "home_pair_separation_m", "effective_relative_permittivity",
    "sequential_row_return_separation_m", "route_multiplier", "module_pitch_m",
    "connector_resistance_ohm_each",
  ]);
  const unknown = Object.keys(overrides).filter((key) => !allowed.has(key));
  if (unknown.length) throw new SimulationInputError(`unknown simulation override(s): ${unknown.join(", ")}`);

  const module = reference.module;
  const array = reference.array;
  const inverter = reference.inverter;
  const conductors = reference.conductors;
  const routing = reference.routing;
  const strings = Number(array.string_count);
  const modulesPerString = Number(array.modules_per_string);
  const modulePitchM = finite("module_pitch_m", overrides.module_pitch_m ?? array.module_pitch_m, 0.001);
  const rowSpanM = modulePitchM * (modulesPerString - 1);
  const routeMultiplier = finite("route_multiplier", overrides.route_multiplier ?? 1, 0.001);
  const currentA = finite("operating_current_a", overrides.operating_current_a ?? module.imp_a, 0);
  const conductorTemperatureC = finite("conductor_temperature_c", overrides.conductor_temperature_c ?? 70);
  const minimumCellTemperatureC = finite("minimum_cell_temperature_c", overrides.minimum_cell_temperature_c ?? -10);
  const pairSpacingM = finite("home_pair_separation_m", overrides.home_pair_separation_m ?? routing.home_pair_separation_m, 0.000001);
  const epsR = finite("effective_relative_permittivity", overrides.effective_relative_permittivity ?? routing.effective_relative_permittivity, 1);
  const rowReturnSeparationM = finite("sequential_row_return_separation_m", overrides.sequential_row_return_separation_m ?? routing.sequential_row_return_separation_m, 0);
  const connectorResistance = finite("connector_resistance_ohm_each", overrides.connector_resistance_ohm_each ?? conductors.connector_resistance_ohm_each, 0);
  const connectorResistancePolicy = resistanceAccounting(modulesPerString, connectorResistance);
  const field = conductors.field_cable;
  const factory = conductors.factory_lead;
  const fieldR = temperatureResistance(field.resistance_ohm_per_km_20c, conductorTemperatureC, field.temperature_coefficient_per_c);
  const factoryR = temperatureResistance(factory.resistance_ohm_per_km_20c, conductorTemperatureC, factory.temperature_coefficient_per_c);
  const line = twoWireParameters(field.area_mm2, pairSpacingM, epsR);
  const moduleIds = Array.from({ length: modulesPerString }, (_, index) => `M${String(index + 1).padStart(2, "0")}`);
  const order = electricalModuleOrder(moduleIds, strategy);
  const factoryBaseM = modulesPerString * (Number(module.positive_lead_m) + Number(module.negative_lead_m));
  let factoryTotalM;
  let rowReturnM;
  if (strategy === "leapfrog") {
    factoryTotalM = factoryBaseM + Number(array.leapfrog_factory_extra_m_per_string);
    rowReturnM = 0;
  } else if (strategy === "sequential") {
    factoryTotalM = factoryBaseM;
    rowReturnM = rowSpanM;
  } else {
    throw new SimulationInputError(`unsupported wiring strategy: ${strategy}`);
  }

  const results = [];
  let totalLossW = 0;
  let totalFieldLengthM = 0;
  let totalFactoryLengthM = 0;
  let totalLoopAreaM2 = 0;
  let totalMagneticEnergyJ = 0;

  routing.route_lengths_m.forEach((rawRoute, offset) => {
    const oneWayRouteM = finite("route length", rawRoute, 0) * routeMultiplier;
    const positiveFieldM = oneWayRouteM;
    const negativeFieldM = oneWayRouteM + rowReturnM;
    const fieldLoopM = positiveFieldM + negativeFieldM;
    const fieldResistanceOhm = (fieldR * fieldLoopM) / 1000;
    const factoryResistanceOhm = (factoryR * factoryTotalM) / 1000;
    const connectorTotalOhm = connectorResistancePolicy.total_connector_contact_resistance_ohm;
    const circuitResistanceOhm = fieldResistanceOhm + factoryResistanceOhm + connectorTotalOhm;
    const voltageDropV = currentA * circuitResistanceOhm;
    const lossW = currentA * voltageDropV;
    const stringVmpV = modulesPerString * Number(module.vmp_v);
    const stringOperatingPowerW = stringVmpV * currentA;
    const deliveredPowerW = Math.max(0, stringOperatingPowerW - lossW);
    let loopAreaM2 = oneWayRouteM * pairSpacingM;
    if (strategy === "sequential") loopAreaM2 += rowSpanM * rowReturnSeparationM;
    const oneWayDelayS = oneWayRouteM / line.propagation_velocity_m_per_s;
    const magneticEnergyJ = 0.5 * line.external_inductance_h_per_m * oneWayRouteM * currentA ** 2;
    const index = offset + 1;
    const item = {
      string_id: `STR-${String(index).padStart(2, "0")}`,
      input_id: `IN-${String(index).padStart(2, "0")}`,
      mppt_id: `MPPT-${String(Math.floor(offset / Number(inverter.strings_per_mppt)) + 1).padStart(2, "0")}`,
      one_way_route_m: oneWayRouteM,
      positive_field_length_m: positiveFieldM,
      negative_field_length_m: negativeFieldM,
      field_loop_length_m: fieldLoopM,
      factory_lead_length_m: factoryTotalM,
      circuit_resistance_ohm: circuitResistanceOhm,
      voltage_drop_v: voltageDropV,
      loss_w: lossW,
      delivered_power_w: deliveredPowerW,
      voltage_drop_percent: stringVmpV ? (100 * voltageDropV) / stringVmpV : 0,
      approximate_loop_area_m2: loopAreaM2,
      one_way_delay_us: oneWayDelayS * 1e6,
      round_trip_delay_us: 2 * oneWayDelayS * 1e6,
      interruption_envelope_v: currentA * line.characteristic_impedance_ohm,
      external_magnetic_energy_j: magneticEnergyJ,
    };
    results.push(item);
    totalLossW += lossW;
    totalFieldLengthM += fieldLoopM;
    totalFactoryLengthM += factoryTotalM;
    totalLoopAreaM2 += loopAreaM2;
    totalMagneticEnergyJ += magneticEnergyJ;
  });

  const ratedDcKwp = (strings * modulesPerString * Number(module.rated_power_wp)) / 1000;
  const inverterKva = Number(inverter.apparent_power_kva);
  const coldVocModuleV = Number(module.voc_v) * (1 + Number(module.voc_temperature_coefficient_per_c) * (minimumCellTemperatureC - 25));
  const blockOperatingPowerW = results.reduce((sum, item) => sum + item.delivered_power_w + item.loss_w, 0);
  const output = {
    schema_version: "globalgrid2050.v11.inverter-block-simulation.v1",
    block_id: reference.block_id,
    strategy,
    provenance: reference.provenance,
    reference_boundary: {
      string_count: strings,
      modules_per_string: modulesPerString,
      module_count: strings * modulesPerString,
      module_rated_power_wp: module.rated_power_wp,
      dc_nameplate_power_kwp: ratedDcKwp,
      inverter_apparent_power_kva: inverterKva,
      dc_ac_nameplate_ratio: ratedDcKwp / inverterKva,
      physical_dc_input_count: inverter.physical_dc_input_count,
      mppt_count: inverter.mppt_count,
      equipment_evidence_state: "incomplete_evidence",
    },
    inputs: {
      operating_current_a: currentA,
      conductor_temperature_c: conductorTemperatureC,
      minimum_cell_temperature_c: minimumCellTemperatureC,
      module_pitch_m: modulePitchM,
      row_span_m: rowSpanM,
      home_pair_separation_m: pairSpacingM,
      effective_relative_permittivity: epsR,
      route_multiplier: routeMultiplier,
    },
    electrical_traversal: order,
    transmission_line: line,
    totals: {
      field_cable_length_m: totalFieldLengthM,
      factory_lead_length_m: totalFactoryLengthM,
      circuit_loss_kw: totalLossW / 1000,
      block_operating_power_kw: blockOperatingPowerW / 1000,
      delivered_power_kw: (blockOperatingPowerW - totalLossW) / 1000,
      loss_percent_of_operating_power: blockOperatingPowerW ? (100 * totalLossW) / blockOperatingPowerW : 0,
      approximate_loop_area_m2: totalLoopAreaM2,
      external_magnetic_energy_j: totalMagneticEnergyJ,
      cold_string_voc_v: coldVocModuleV * modulesPerString,
    },
    strings: results,
  };
  output.simulation_hash = await canonicalHash(output);
  return output;
}

export async function simulateComparison(reference, overrides = {}) {
  const sequential = await simulateBlock(reference, "sequential", overrides);
  const leapfrog = await simulateBlock(reference, "leapfrog", overrides);
  const result = {
    schema_version: "globalgrid2050.v11.inverter-block-comparison.v1",
    reference_block_id: reference.block_id,
    sequential,
    leapfrog,
    delta_leapfrog_minus_sequential: {
      field_cable_length_m: leapfrog.totals.field_cable_length_m - sequential.totals.field_cable_length_m,
      factory_lead_length_m: leapfrog.totals.factory_lead_length_m - sequential.totals.factory_lead_length_m,
      circuit_loss_kw: leapfrog.totals.circuit_loss_kw - sequential.totals.circuit_loss_kw,
      approximate_loop_area_m2: leapfrog.totals.approximate_loop_area_m2 - sequential.totals.approximate_loop_area_m2,
    },
  };
  result.comparison_hash = await canonicalHash(result);
  return result;
}
