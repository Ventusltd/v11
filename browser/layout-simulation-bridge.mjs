import { assignStrings, validateLayout, layoutHash } from './layout-core.mjs';

export class LayoutSimulationError extends Error {}

const finite = (name, value) => {
  const number = Number(value);
  if (!Number.isFinite(number)) throw new LayoutSimulationError(`${name} must be finite`);
  return number;
};

function distance(a, b) {
  return Math.hypot(a.x_m - b.x_m, a.y_m - b.y_m);
}

function groupedModules(layout) {
  const groups = new Map();
  for (const module of layout.modules) {
    if (!module.string_id) throw new LayoutSimulationError(`${module.id} is not assigned to a string`);
    if (!groups.has(module.string_id)) groups.set(module.string_id, []);
    groups.get(module.string_id).push(module);
  }
  return groups;
}

function centroid(modules) {
  return {
    x_m: modules.reduce((sum, module) => sum + finite('x_m', module.x_m), 0) / modules.length,
    y_m: modules.reduce((sum, module) => sum + finite('y_m', module.y_m), 0) / modules.length,
  };
}

function orderedPathLength(modules) {
  const ordered = [...modules].sort((a, b) => Number(a.electrical_index) - Number(b.electrical_index));
  return ordered.slice(1).reduce((sum, module, index) => sum + distance(ordered[index], module), 0);
}

export function deriveRouteLengths(layout, {
  inverterPoint = null,
  modulesPerString = 30,
  snake = true,
  geometryAllowance = 1.0,
  intraStringContribution = 0.5,
} = {}) {
  const errors = validateLayout(layout);
  if (errors.length) throw new LayoutSimulationError(errors.join('; '));
  if (!layout.modules?.length) throw new LayoutSimulationError('layout contains no modules');
  const allowance = finite('geometryAllowance', geometryAllowance);
  const intraContribution = finite('intraStringContribution', intraStringContribution);
  if (allowance <= 0 || intraContribution < 0) throw new LayoutSimulationError('route factors are outside their allowed range');
  const assigned = assignStrings(layout, modulesPerString, snake);
  const groups = groupedModules(assigned);
  const boundary = assigned.boundary;
  const inverter = inverterPoint ?? {
    x_m: finite('boundary.x_max', boundary.x_max),
    y_m: (finite('boundary.y_min', boundary.y_min) + finite('boundary.y_max', boundary.y_max)) / 2,
  };
  const strings = [...groups.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([stringId, modules]) => {
    const centre = centroid(modules);
    const homeRunM = distance(centre, inverter);
    const intraStringPathM = orderedPathLength(modules);
    const oneWayRouteM = allowance * (homeRunM + intraContribution * intraStringPathM);
    return {
      string_id: stringId,
      module_count: modules.length,
      centroid: centre,
      home_run_m: homeRunM,
      intra_string_path_m: intraStringPathM,
      one_way_route_m: oneWayRouteM,
    };
  });
  return {
    schema_version: 'globalgrid2050.v11.layout-route-derivation.v1',
    layout_hash: assigned.layout_hash ?? layoutHash(assigned),
    inverter_point: inverter,
    modules_per_string: modulesPerString,
    string_count: strings.length,
    strings,
    route_lengths_m: strings.map((item) => Number(item.one_way_route_m.toFixed(9))),
  };
}

export function referenceFromLayout(reference, layout, options = {}) {
  const derivation = deriveRouteLengths(layout, {
    modulesPerString: Number(reference.array.modules_per_string),
    ...options,
  });
  if (derivation.string_count !== Number(reference.array.string_count)) {
    throw new LayoutSimulationError(`layout produces ${derivation.string_count} strings; reference requires ${reference.array.string_count}`);
  }
  if (derivation.strings.some((item) => item.module_count !== Number(reference.array.modules_per_string))) {
    throw new LayoutSimulationError('every string must contain the reference modules-per-string count');
  }
  const adapted = structuredClone(reference);
  adapted.routing.route_lengths_m = derivation.route_lengths_m;
  adapted.provenance = {
    ...adapted.provenance,
    layout_hash: derivation.layout_hash,
    route_derivation_schema: derivation.schema_version,
  };
  return { reference: adapted, derivation };
}
