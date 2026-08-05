import './sld-visual-contract.mjs';

export class WorkbenchAnalysisError extends Error {}

const finite = (name, value) => {
  const number = Number(value);
  if (!Number.isFinite(number)) throw new WorkbenchAnalysisError(`${name} must be finite`);
  return number;
};

function indexByString(items, label) {
  if (!Array.isArray(items)) throw new WorkbenchAnalysisError(`${label} must be an array`);
  const result = new Map();
  for (const item of items) {
    const id = String(item?.string_id ?? '');
    if (!id) throw new WorkbenchAnalysisError(`${label} contains a result without string_id`);
    if (result.has(id)) throw new WorkbenchAnalysisError(`${label} contains duplicate ${id}`);
    result.set(id, item);
  }
  return result;
}

function extreme(rows, value, direction = 'max') {
  if (!rows.length) throw new WorkbenchAnalysisError('at least one string result is required');
  return rows.reduce((selected, row) => {
    const candidate = finite(`diagnostic ${row.string_id}`, value(row));
    const current = finite(`diagnostic ${selected.string_id}`, value(selected));
    return direction === 'min'
      ? (candidate < current ? row : selected)
      : (candidate > current ? row : selected);
  });
}

export function analyseWorkbench(derivation, comparison) {
  if (!Array.isArray(derivation?.strings) || !derivation.strings.length) {
    throw new WorkbenchAnalysisError('route derivation contains no strings');
  }
  const sequential = comparison?.sequential;
  const leapfrog = comparison?.leapfrog;
  if (!sequential || !leapfrog) throw new WorkbenchAnalysisError('comparison requires sequential and leapfrog results');

  const sequentialById = indexByString(sequential.strings, 'sequential results');
  const leapfrogById = indexByString(leapfrog.strings, 'leapfrog results');
  const routeIds = new Set();

  const rows = derivation.strings.map((route) => {
    const stringId = String(route.string_id ?? '');
    if (!stringId) throw new WorkbenchAnalysisError('route derivation contains a result without string_id');
    if (routeIds.has(stringId)) throw new WorkbenchAnalysisError(`route derivation contains duplicate ${stringId}`);
    routeIds.add(stringId);
    const seq = sequentialById.get(stringId);
    const leap = leapfrogById.get(stringId);
    if (!seq || !leap) throw new WorkbenchAnalysisError(`electrical result missing for ${stringId}`);
    return {
      string_id: stringId,
      module_count: Number(route.module_count),
      module_ids: [...(route.module_ids ?? [])],
      centroid_x_m: finite(`${stringId} centroid x`, route.centroid?.x_m),
      centroid_y_m: finite(`${stringId} centroid y`, route.centroid?.y_m),
      home_run_m: finite(`${stringId} home run`, route.home_run_m),
      intra_string_path_m: finite(`${stringId} intra-string path`, route.intra_string_path_m),
      one_way_route_m: finite(`${stringId} route`, route.one_way_route_m),
      sequential: {
        circuit_resistance_ohm: finite(`${stringId} sequential resistance`, seq.circuit_resistance_ohm),
        voltage_drop_v: finite(`${stringId} sequential voltage drop`, seq.voltage_drop_v),
        voltage_drop_percent: finite(`${stringId} sequential voltage drop percent`, seq.voltage_drop_percent),
        loss_w: finite(`${stringId} sequential loss`, seq.loss_w),
        round_trip_delay_us: finite(`${stringId} sequential delay`, seq.round_trip_delay_us),
      },
      leapfrog: {
        circuit_resistance_ohm: finite(`${stringId} leapfrog resistance`, leap.circuit_resistance_ohm),
        voltage_drop_v: finite(`${stringId} leapfrog voltage drop`, leap.voltage_drop_v),
        voltage_drop_percent: finite(`${stringId} leapfrog voltage drop percent`, leap.voltage_drop_percent),
        loss_w: finite(`${stringId} leapfrog loss`, leap.loss_w),
        round_trip_delay_us: finite(`${stringId} leapfrog delay`, leap.round_trip_delay_us),
      },
      delta_leapfrog_minus_sequential: {
        resistance_ohm: finite(`${stringId} resistance delta`, leap.circuit_resistance_ohm - seq.circuit_resistance_ohm),
        voltage_drop_v: finite(`${stringId} voltage delta`, leap.voltage_drop_v - seq.voltage_drop_v),
        loss_w: finite(`${stringId} loss delta`, leap.loss_w - seq.loss_w),
      },
    };
  });

  if (sequentialById.size !== rows.length || leapfrogById.size !== rows.length) {
    throw new WorkbenchAnalysisError('electrical and route string sets disagree');
  }

  const longestRoute = extreme(rows, (row) => row.one_way_route_m);
  const shortestRoute = extreme(rows, (row) => row.one_way_route_m, 'min');
  const highestSequentialLoss = extreme(rows, (row) => row.sequential.loss_w);
  const highestLeapfrogLoss = extreme(rows, (row) => row.leapfrog.loss_w);
  const highestVoltageDrop = extreme(rows, (row) => row.sequential.voltage_drop_percent);
  const longestDelay = extreme(rows, (row) => row.sequential.round_trip_delay_us);

  return {
    schema_version: 'globalgrid2050.v11.workbench-analysis.v1',
    rows,
    diagnostics: {
      longest_route: { string_id: longestRoute.string_id, value_m: longestRoute.one_way_route_m },
      shortest_route: { string_id: shortestRoute.string_id, value_m: shortestRoute.one_way_route_m },
      route_spread_m: longestRoute.one_way_route_m - shortestRoute.one_way_route_m,
      highest_sequential_loss: { string_id: highestSequentialLoss.string_id, value_w: highestSequentialLoss.sequential.loss_w },
      highest_leapfrog_loss: { string_id: highestLeapfrogLoss.string_id, value_w: highestLeapfrogLoss.leapfrog.loss_w },
      highest_sequential_voltage_drop: { string_id: highestVoltageDrop.string_id, value_percent: highestVoltageDrop.sequential.voltage_drop_percent },
      longest_round_trip_delay: { string_id: longestDelay.string_id, value_us: longestDelay.sequential.round_trip_delay_us },
      field_cable_saving_m: finite('field cable saving', sequential.totals.field_cable_length_m - leapfrog.totals.field_cable_length_m),
      circuit_loss_delta_kw: finite('circuit loss delta', leapfrog.totals.circuit_loss_kw - sequential.totals.circuit_loss_kw),
    },
  };
}

export function buildEngineeringPackage({ layout, adapted, derivation, comparison }) {
  const analysis = analyseWorkbench(derivation, comparison);
  return {
    schema_version: 'globalgrid2050.v11.integrated-engineering-package.v1',
    repository: 'Ventusltd/v11',
    provisional_engineering_model: true,
    authority: {
      layout_hash: derivation.layout_hash,
      comparison_hash: comparison.comparison_hash,
      sequential_simulation_hash: comparison.sequential.simulation_hash,
      leapfrog_simulation_hash: comparison.leapfrog.simulation_hash,
      source_repository: adapted.provenance?.source_repository ?? null,
      source_commit: adapted.provenance?.source_commit ?? null,
    },
    reference_boundary: comparison.sequential.reference_boundary,
    simulation_inputs: comparison.sequential.inputs,
    diagnostics: analysis.diagnostics,
    strings: analysis.rows,
    layout,
    route_derivation: derivation,
    simulation: comparison,
  };
}

const csvCell = (value) => {
  const text = String(value ?? '');
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
};

export function workbenchCsv(analysis) {
  if (!analysis?.rows?.length) throw new WorkbenchAnalysisError('analysis contains no string rows');
  const header = [
    'string_id', 'module_count', 'one_way_route_m', 'centroid_x_m', 'centroid_y_m',
    'sequential_resistance_ohm', 'sequential_voltage_drop_v', 'sequential_voltage_drop_percent',
    'sequential_loss_w', 'leapfrog_resistance_ohm', 'leapfrog_voltage_drop_v',
    'leapfrog_voltage_drop_percent', 'leapfrog_loss_w', 'round_trip_delay_us',
  ];
  const lines = analysis.rows.map((row) => [
    row.string_id, row.module_count, row.one_way_route_m, row.centroid_x_m, row.centroid_y_m,
    row.sequential.circuit_resistance_ohm, row.sequential.voltage_drop_v,
    row.sequential.voltage_drop_percent, row.sequential.loss_w,
    row.leapfrog.circuit_resistance_ohm, row.leapfrog.voltage_drop_v,
    row.leapfrog.voltage_drop_percent, row.leapfrog.loss_w,
    row.sequential.round_trip_delay_us,
  ].map(csvCell).join(','));
  return [header.join(','), ...lines].join('\n') + '\n';
}
