// Evaluates the live Kuiper core placement exactly as the shell does (keyPlace, line 566 of
// globalgrid2050@da7d8f6e kuiper/releases/202609192301-kuiper-shell/index.html), under Node.
const G32 = 2654435769;
function keyPlace(k){ const m = Math.imul((k % 4294967296) >>> 0, G32) >>> 0, th = 2*Math.PI*m/4294967296, r = Math.sqrt(k + 0.5);
  return [r*Math.cos(th), r*Math.sin(th)]; }
const keys = [];
for (let k = 0; k <= 2959; k++) keys.push(k);
for (const k of [8285, 100000, 342795, 4294967295, 4294967296, 44029986938, 2 ** 53 - 1]) keys.push(k);
process.stdout.write(JSON.stringify({ G32, rows: keys.map(k => { const [x, y] = keyPlace(k); return [k, x, y]; }) }));
