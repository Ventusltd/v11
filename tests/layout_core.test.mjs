import assert from 'node:assert/strict';
import test from 'node:test';
import {performance} from 'node:perf_hooks';
import {fillRectangle,moveModule,rotateModule,assignStrings,validateLayout,LayoutError} from '../browser/layout-core.mjs';

const base=(limit=24)=>fillRectangle({boundary:{x_min:0,y_min:0,x_max:20,y_max:12},moduleWidthM:1,moduleHeightM:2,gapXM:.1,gapYM:.1,obstacles:[{id:'O1',x_min:8,x_max:10,y_min:4,y_max:8}],limit});
const isolated=()=>({schema_version:'globalgrid2050.v11.module-layout.v1',boundary:{x_min:0,y_min:0,x_max:10,y_max:10},obstacles:[],modules:[{id:'MOD-0001',x_m:5,y_m:5,width_m:1,height_m:2,rotation_deg:0,row:0,column:0,string_id:null}]});

test('fills a valid deterministic layout',()=>{const a=base(),b=base();assert.deepEqual(a,b);assert.equal(validateLayout(a).length,0);assert.equal(a.modules.length,24)});
test('moves with numeric snapping',()=>{const moved=moveModule(isolated(),'MOD-0001',5.26,5.24,.05);assert.equal(moved.modules[0].x_m,5.25);assert.equal(moved.modules[0].y_m,5.25)});
test('keeps a legal boundary-flush no-op move valid',()=>{const layout=fillRectangle({boundary:{x_min:0,y_min:0,x_max:10,y_max:10},moduleWidthM:1.134,moduleHeightM:2.384,limit:1}),original=layout.modules[0],moved=moveModule(layout,original.id,original.x_m,original.y_m,.05);assert.equal(moved.modules[0].x_m,original.x_m);assert.equal(moved.modules[0].y_m,original.y_m);assert.equal(validateLayout(moved).length,0)});
test('rejects colliding and outside movement',()=>{assert.throws(()=>moveModule(base(2),'MOD-0001',1.6,1),LayoutError);assert.throws(()=>moveModule(base(2),'MOD-0001',-1,-1),LayoutError)});
test('rotates selected module when geometry permits',()=>{const rotated=rotateModule(isolated(),'MOD-0001');assert.equal(rotated.modules[0].rotation_deg,90);assert.equal(validateLayout(rotated).length,0)});
test('rejects rotation outside boundary',()=>assert.throws(()=>rotateModule(base(1),'MOD-0001'),LayoutError));
test('assigns complete strings',()=>assert.equal(new Set(assignStrings(base(24),6,true).modules.map(module=>module.string_id)).size,4));
test('fills 720 modules within bounded runtime',()=>{const start=performance.now();const layout=fillRectangle({boundary:{x_min:0,y_min:0,x_max:90,y_max:60},moduleWidthM:1.134,moduleHeightM:2.384,gapXM:.03,gapYM:.05,limit:720});assert.equal(layout.modules.length,720);assert.equal(validateLayout(layout).length,0);assert.ok(performance.now()-start<5000)});
