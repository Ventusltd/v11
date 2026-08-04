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

// Browser-only selected-string connector SLD. It augments only the selected detail, not all 720 overview modules.
const SLD_SCHEMA='globalgrid2050.v11.selected-string-connector-sld.v1';
const CABLE='#000000',HALO='#77828c',RED='#eb5757',BLUE='#2f80ed';
const p=(n,w=2)=>String(n).padStart(w,'0');
const order=(n,s)=>s==='sequential'?[...Array(n)].map((_,i)=>i+1):[...Array(Math.ceil(n/2))].map((_,i)=>i*2+1).concat([...Array(Math.floor(n/2))].map((_,i)=>n-(n%2)-i*2));
const ident=(sid,i)=>{const m=`${sid}-M${p(i)}`;return{m,nt:`${m}-JBOX-NEG-T`,pt:`${m}-JBOX-POS-T`,nc:`${m}-NEG-CON`,pc:`${m}-POS-CON`}};
const inv=sid=>({nt:`${sid}-INVERTER-NEG-T`,pt:`${sid}-INVERTER-POS-T`,nc:`${sid}-INVERTER-NEG-CON`,pc:`${sid}-INVERTER-POS-CON`});
function model(sid,n,s){const o=order(n,s),iv=inv(sid),e=[];e.push({id:`${sid}-${s}-PAIR-${p(1,3)}`,k:'free-negative',a:iv.nc,b:ident(sid,o[0]).nc,ap:'negative',bp:'negative',ai:0,bi:o[0]});for(let i=0;i<o.length-1;i++){const a=ident(sid,o[i]),b=ident(sid,o[i+1]);e.push({id:`${sid}-${s}-PAIR-${p(i+2,3)}`,k:'inter-module',a:a.pc,b:b.nc,ap:'positive',bp:'negative',ai:o[i],bi:o[i+1]})}e.push({id:`${sid}-${s}-PAIR-${p(n+1,3)}`,k:'free-positive',a:ident(sid,o.at(-1)).pc,b:iv.pc,ap:'positive',bp:'positive',ai:o.at(-1),bi:0});return{s,o,e}}
function geom(n){return{x0:190,w:28,h:58,y:82,cy:111,pitch:48,W:190+n*48+150,H:222}}
function pts(sid,n,g){const m=new Map(),iv=inv(sid);for(let i=1;i<=n;i++){const q=ident(sid,i),x=g.x0+(i-1)*g.pitch;m.set(q.nc,{x:x-9,y:g.cy});m.set(q.pc,{x:x+g.w+9,y:g.cy})}m.set(iv.nc,{x:147,y:88});m.set(iv.pc,{x:147,y:134});return m}
function marker(id,pol,x,y){const c=pol==='positive'?RED:BLUE,z=pol==='positive'?'+':'−';return`<g id="${id}" class="sld-connector ${pol}" data-connector-id="${id}" data-polarity="${pol}"><circle cx="${x}" cy="${y}" r="6" fill="#10151b" stroke="#d8e1e8"/><circle class="connector-marker connector-marker-${pol}" cx="${x}" cy="${y}" r="4.5" fill="#10151b" stroke="${c}" stroke-width="3"/><text x="${x}" y="${y+3}" text-anchor="middle" fill="${c}" font-size="8" font-weight="900">${z}</text></g>`}
function moduleSvg(sid,i,g){const q=ident(sid,i),x=g.x0+(i-1)*g.pitch,nx=x-9,px=x+g.w+9;return`<g class="sld-module" data-module-id="${q.m}" data-negative-terminal-id="${q.nt}" data-positive-terminal-id="${q.pt}"><rect class="topology-cell sld-module-body" data-electrical-index="${i}" x="${x}" y="${g.y}" width="${g.w}" height="${g.h}" rx="3"/><line x1="${x}" y1="${g.cy}" x2="${x+g.w}" y2="${g.cy}" stroke="#050505" stroke-width="2"/><circle id="${q.nt}" class="sld-module-terminal negative" data-terminal-id="${q.nt}" cx="${x}" cy="${g.cy}" r="3.5" fill="#071019" stroke="${BLUE}" stroke-width="2"/><circle id="${q.pt}" class="sld-module-terminal positive" data-terminal-id="${q.pt}" cx="${x+g.w}" cy="${g.cy}" r="3.5" fill="#071019" stroke="${RED}" stroke-width="2"/><line class="sld-cable-stub" x1="${x}" y1="${g.cy}" x2="${nx}" y2="${g.cy}" stroke="${CABLE}" stroke-width="4" data-cable-jacket-colour="black"/><line class="sld-cable-stub" x1="${x+g.w}" y1="${g.cy}" x2="${px}" y2="${g.cy}" stroke="${CABLE}" stroke-width="4" data-cable-jacket-colour="black"/>${marker(q.nc,'negative',nx,g.cy)}${marker(q.pc,'positive',px,g.cy)}<text x="${x+g.w/2}" y="${g.y+26}" text-anchor="middle" fill="#edf3f8" font-size="10" font-weight="800">M${i}</text><text x="${x+g.w/2}" y="${g.y+42}" text-anchor="middle" fill="#a8b3be" font-size="7">J-BOX</text></g>`}
function inverterSvg(sid){const q=inv(sid);return`<g class="sld-inverter"><rect class="inverter-block" x="20" y="62" width="105" height="98" rx="6"/><text x="72" y="84" text-anchor="middle" fill="#111" font-size="11" font-weight="900">INVERTER INPUT</text><text x="72" y="104" text-anchor="middle" fill="#111" font-size="10">${sid}</text><circle id="${q.nt}" class="sld-inverter-terminal negative" data-terminal-id="${q.nt}" cx="125" cy="88" r="4" fill="#071019" stroke="${BLUE}" stroke-width="2"/><circle id="${q.pt}" class="sld-inverter-terminal positive" data-terminal-id="${q.pt}" cx="125" cy="134" r="4" fill="#071019" stroke="${RED}" stroke-width="2"/><line class="sld-cable-stub" x1="125" y1="88" x2="147" y2="88" stroke="${CABLE}" stroke-width="4" data-cable-jacket-colour="black"/><line class="sld-cable-stub" x1="125" y1="134" x2="147" y2="134" stroke="${CABLE}" stroke-width="4" data-cable-jacket-colour="black"/>${marker(q.nc,'negative',147,88)}${marker(q.pc,'positive',147,134)}</g>`}
function edgeSvg(m,xy,compare){return m.e.map((e,i)=>{const a=xy.get(e.a),b=xy.get(e.b),adj=e.k==='inter-module'&&Math.abs(e.bi-e.ai)===1;let d;if(m.s==='sequential'&&adj)d=`M ${a.x} ${a.y} L ${b.x} ${b.y}`;else{const up=e.k==='free-negative'||(e.k==='inter-module'&&e.bi>e.ai);let y=up?52-(i%3)*7:174+(i%3)*8;if(compare&&m.s==='sequential')y+=up?20:-20;d=`M ${a.x} ${a.y} L ${a.x} ${y} L ${b.x} ${y} L ${b.x} ${b.y}`}const dash=compare&&m.s==='sequential'?' stroke-dasharray="8 6"':'';return`<path d="${d}" fill="none" stroke="${HALO}" stroke-width="7" opacity=".75"/><path id="${e.id}" class="connector-pair-edge sld-cable" data-connector-pair-id="${e.id}" data-connection-kind="${e.k}" data-strategy="${m.s}" data-source-connector-id="${e.a}" data-destination-connector-id="${e.b}" data-source-polarity="${e.ap}" data-destination-polarity="${e.bp}" data-cable-jacket-colour="black" d="${d}" fill="none" stroke="${CABLE}" stroke-width="4"${dash}/>`}).join('')}
function validate(svg,sid,n,models){const cs=[...svg.querySelectorAll('.sld-connector')],ids=cs.map(x=>x.dataset.connectorId),pairs=[...svg.querySelectorAll('.connector-pair-edge')],pids=pairs.map(x=>x.dataset.connectorPairId),bad=[],orph=[];for(const m of models){const u=new Map(ids.map(x=>[x,0]));for(const e of m.e){u.set(e.a,(u.get(e.a)||0)+1);u.set(e.b,(u.get(e.b)||0)+1);const ok=e.k==='free-negative'?e.ap==='negative'&&e.bp==='negative':e.k==='free-positive'?e.ap==='positive'&&e.bp==='positive':e.ap==='positive'&&e.bp==='negative';if(!ok)bad.push(e.id)}for(const [id,c] of u)if(c!==1)orph.push(`${m.s}:${id}:${c}`)}const colours=[...new Set([...svg.querySelectorAll('.sld-cable,.sld-cable-stub')].map(x=>x.getAttribute('stroke')?.toLowerCase()))],pos=svg.querySelectorAll('.connector-marker-positive').length,neg=svg.querySelectorAll('.connector-marker-negative').length,mt=svg.querySelectorAll('.sld-module-terminal').length,it=svg.querySelectorAll('.sld-inverter-terminal').length;const pass=svg.querySelectorAll('.sld-module').length===n&&mt===2*n&&it===2&&ids.length===2*n+2&&new Set(ids).size===ids.length&&pos===n+1&&neg===n+1&&pairs.length===models.length*(n+1)&&new Set(pids).size===pids.length&&colours.length===1&&colours[0]===CABLE&&bad.length===0&&orph.length===0;const ev={schema_version:SLD_SCHEMA,tested_sha:'resolved-by-github-actions-checkout',pass,selected_string_id:sid,wiring_mode:document.querySelector('.wiring-mode[aria-pressed="true"]')?.dataset.mode||'leapfrog',active_strategies:models.map(x=>x.s),module_count:n,module_terminal_count:mt,inverter_terminal_count:it,connector_marker_count:ids.length,positive_connector_marker_count:pos,negative_connector_marker_count:neg,connector_pair_count:pairs.length,connector_pair_count_per_strategy:n+1,connector_ids_unique:new Set(ids).size===ids.length,connector_pair_ids_unique:new Set(pids).size===pids.length,cable_jacket_colour:'black',cable_stroke_values:colours,marker_colours:{positive:RED,negative:BLUE},polarity_continuity:bad.length===0,polarity_errors:bad,orphan_connector_ids:orph,traversal:Object.fromEntries(models.map(x=>[x.s,x.o]))};window.__v11SelectedSldEvidence=ev;console.log(JSON.stringify({event:'selected-string-connector-sld',...ev}));if(!pass)throw new Error(`Selected-string connector SLD contract failed: ${JSON.stringify(ev)}`);return ev}
function renderConnectorSld(){const svg=document.querySelector('#detail-canvas');if(!svg)return;const n=Number(document.querySelector('#modules-per-string')?.value||30),sid=svg.dataset.stringId||window.__v11TopologyEvidence?.selected_string_id||'STR-01',mode=document.querySelector('.wiring-mode[aria-pressed="true"]')?.dataset.mode||'leapfrog',sig=`${SLD_SCHEMA}|${sid}|${n}|${mode}`;if(svg.dataset.sldConnectorSignature===sig&&svg.dataset.sldEvidencePass==='true')return;const g=geom(n),ss=mode==='compare'?['sequential','leapfrog']:[mode],ms=ss.map(s=>model(sid,n,s)),xy=pts(sid,n,g);svg.setAttribute('viewBox',`0 0 ${g.W} ${g.H}`);svg.innerHTML=`<rect width="${g.W}" height="${g.H}" fill="#03080d"/><text x="20" y="24" fill="#f2c94c" font-size="12" font-weight="900">${sid} · ${mode.toUpperCase()} · CONNECTOR-LEVEL SLD</text><text x="20" y="42" fill="#a8b3be" font-size="10">BLACK CABLE · RED/BLUE POLARITY MARKERS AT CONNECTORS</text>${inverterSvg(sid)}${[...Array(n)].map((_,i)=>moduleSvg(sid,i+1,g)).join('')}${ms.map(m=>edgeSvg(m,xy,mode==='compare')).join('')}<g class="sld-connector-legend"><line x1="20" y1="210" x2="55" y2="210" stroke="${CABLE}" stroke-width="4"/><text x="63" y="214" fill="#a8b3be" font-size="10">BLACK PV CABLE</text><circle cx="240" cy="210" r="5" fill="#10151b" stroke="${RED}" stroke-width="3"/><text x="252" y="214" fill="#a8b3be" font-size="10">RED + CONNECTOR MARKER</text><circle cx="465" cy="210" r="5" fill="#10151b" stroke="${BLUE}" stroke-width="3"/><text x="477" y="214" fill="#a8b3be" font-size="10">BLUE − CONNECTOR MARKER</text></g>`;svg.dataset.sldConnectorSignature=sig;svg.dataset.junctionBoxContract='explicit-jbox-terminals-connector-markers-black-cable-v1';svg.dataset.sldEvidencePass=String(validate(svg,sid,n,ms).pass);const note=document.querySelector('#selected-detail-note');if(note&&!note.textContent.includes('Connector markers:'))note.textContent+=` Connector markers: red +, blue −; all factory and field cable jackets remain black.`}
function installConnectorSld(){let pending=false;const run=()=>{if(pending)return;pending=true;requestAnimationFrame(()=>{pending=false;renderConnectorSld()})};new MutationObserver(run).observe(document.documentElement,{childList:true,subtree:true});document.addEventListener('click',e=>{if(e.target.closest('.wiring-mode,.string-strip,#reset,#reset-view'))run()});run()}
if(typeof document!=='undefined'&&typeof MutationObserver!=='undefined')installConnectorSld();
export {SLD_SCHEMA as selectedStringConnectorSldSchemaVersion};
