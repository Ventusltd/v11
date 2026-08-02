import assert from 'node:assert/strict';import test from 'node:test';import {fillRectangle,moveModule,rotateModule,assignStrings,validateLayout} from '../browser/layout-core.mjs';
const base=(limit=24)=>fillRectangle({boundary:{x_min:0,y_min:0,x_max:20,y_max:12},moduleWidthM:1,moduleHeightM:2,gapXM:.1,gapYM:.1,obstacles:[{id:'O1',x_min:8,x_max:10,y_min:4,y_max:8}],limit});
test('fills a valid deterministic layout',()=>{const a=base(),b=base();assert.deepEqual(a,b);assert.equal(validateLayout(a).length,0);assert.equal(a.modules.length,24)});
test('moves with snapping',()=>{const moved=moveModule(base(1),'MOD-0001',2.26,2.24,.05);assert.equal(moved.modules[0].x_m,2.25)});
test('rotates selected module',()=>assert.equal(rotateModule(base(1),'MOD-0001').modules[0].rotation_deg,90));
test('assigns complete strings',()=>assert.equal(new Set(assignStrings(base(24),6,true).modules.map(m=>m.string_id)).size,4));
