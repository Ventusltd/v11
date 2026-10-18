import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {place,decode,morphPoint,relativeWaferPoint,getPreviewKeys,BILLION,G32,TWO32} from './kuiper_core.mjs';
const schema=JSON.parse(readFileSync(new URL('./case-schema.json',import.meta.url),'utf8'));

test('exact live Kuiper Belt 20261005 golden modulo law',()=>{
 assert.equal(G32,2654435769);
 const a=place(0),b=place(1);
 assert.equal(a.m,0);
 assert.equal(b.m,G32);
 assert.ok(Math.abs(a.r-Math.sqrt(.5))<1e-15);
 assert.ok(Math.abs(b.turns-G32/TWO32)<1e-15);
 assert.equal(place(TWO32).m,a.m);
 assert.ok(place(TWO32).r>a.r);
 assert.equal(place(BILLION-1).key,BILLION-1);
 assert.throws(()=>place(-1));
});
test('one-billion axis product and keys decoding are immutable',()=>{
 assert.equal(schema.size,BILLION);
 assert.equal(schema.axes.reduce((n,x)=>n*x.values.length,1),BILLION);
 const zero=decode(schema,0),max=decode(schema,BILLION-1);
 for(const axis of schema.axes){
    assert.equal(zero[axis.name],axis.values[0]);
    assert.equal(max[axis.name],axis.values[axis.values.length-1]);
 }
 assert.throws(()=>decode(schema,BILLION));
 assert.throws(()=>decode({size:BILLION,schema:'wrong'},1));
});
test('Vogel and parameter views address EXACTLY the same test key',()=>{
 for(const k of [0,1,2,50,999999,500000000,BILLION-1]){
   const a=morphPoint(schema,k,0),b=morphPoint(schema,k,1);
   const q=relativeWaferPoint(k);
   assert.ok(Math.abs(a.x-q.x)<1e-12&&Math.abs(a.y-q.y)<1e-12);
   assert.ok(Number.isFinite(b.x)&&Number.isFinite(b.y));
   const h=morphPoint(schema,k,.5);
   assert.ok(Math.abs(h.x-(a.x+b.x)/2)<1e-12);
 }
});
test('bounded preview is not billion points or scenario verdicts',()=>{
 const keys=getPreviewKeys(2048);
 assert.equal(keys.length,2048);
 assert.equal(new Set(keys).size,2048);
 assert.ok(keys.includes(0));
 assert.ok(keys.includes(BILLION-1));
 assert.ok(keys.every(k=>Number.isInteger(k)&&k>=0&&k<BILLION));
 assert.throws(()=>getPreviewKeys(5000));
});
