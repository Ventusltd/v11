// SUP-D verification: evaluate the ACTUAL Kuiper lib.mjs place(key) under Node and dump full-precision doubles.
// Set KUIPER_LIB to the read-only clone path of globalgrid2050/testcode/202609151339/lib.mjs (commit da7d8f6e).
const libPath = process.env.KUIPER_LIB || '/home/claude/ventusltd/globalgrid2050/testcode/202609151339/lib.mjs';
const { place, GOLDEN, SPACING } = await import(libPath);
const keys = [];
for (let k = 1; k <= 2959; k++) keys.push(k);
for (const k of [8285, 100000, 100001, 342795, 1000000, 10000000, 2 ** 31 - 1]) keys.push(k);
const out = { GOLDEN: GOLDEN, SPACING: SPACING, rows: keys.map(k => { const [x, y] = place(k); return [k, x, y]; }) };
// JSON.stringify prints the shortest round-trip decimal of each double, so the exact bits are recoverable in Python.
process.stdout.write(JSON.stringify(out));
