// D5 test: compare Python projected coords against live Kuiper JavaScript placement.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
const file=process.argv[2];
if(!file)throw new Error('Supply bounded Python projection JSON file');
const p=JSON.parse(readFileSync(file,'utf8'));
assert.equal(p.schema,'ventus.v11.pv.d5.kuiper-projection.v1');
assert.equal(p.coordinate_law,'live-kuiper-g32');
assert.equal(p.identity.includes('LOCAL'),true);
assert.equal(p.input_space_not_physically_simulated,true);
assert.equal(p.GPU_execution_claimed,false);
assert.equal(p.declared_input_space,1073741824);
assert.equal(p.points.length,p.distinct_projected);
const seen=new Set();
for(const q of p.points){
  assert(!seen.has(q.local_case_id),'duplicate case identity');
  seen.add(q.local_case_id);
  const k=q.local_plot_key;
  assert.equal(k,q.local_index);
  assert(Number.isSafeInteger(k)&&k>=0);
  const m=Math.imul((k%4294967296)>>>0,2654435769)>>>0;
  const theta=2*Math.PI*m/4294967296;
  const r=Math.sqrt(k+.5);
  const x=r*Math.cos(theta),y=r*Math.sin(theta);
  assert(Math.abs(x-q.x)<2e-7,'x mismatch key '+k);
  assert(Math.abs(y-q.y)<2e-7,'y mismatch key '+k);
  assert(Number.isInteger(q.screen_code)&&q.screen_code>=0&&q.screen_code<=4);
}
assert(p.points.length>=512);
console.log('Live Kuiper JavaScript/Python agreement: '+p.points.length+' distinct local case addresses; no physics implied.');
