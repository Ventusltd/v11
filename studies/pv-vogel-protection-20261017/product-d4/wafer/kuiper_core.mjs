// Original V11 D4 address/selection implementation; math follows the LIVE
// 202610050010 Kuiper Belt law, blob c506a252f27fa8b80e849eb63bbb6699eaf674f0.
// No historical Kuiper ledger is modified. These are VIRTUAL study keys.
export const G32=2654435769;
export const TWO32=4294967296;
export const BILLION=1_000_000_000;
export function place(key) {
  if(!Number.isSafeInteger(key)||key<0)throw Error('nonnegative safe integer required');
  const m=Math.imul(key>>>0,G32)>>>0;
  const turns=m/TWO32,angle=2*Math.PI*turns,r=Math.sqrt(key+.5);
  return {key,m,turns,angle,r,x:r*Math.cos(angle),y:r*Math.sin(angle)};
}
export function decode(schema,key) {
  if(!schema||schema.schema!=='v11.pv.module-protection.billion/1'||schema.size!==BILLION)
    throw Error('unrecognised immutable billion-case source contract');
  if(!Number.isSafeInteger(key)||key<0||key>=schema.size)throw Error('out-of-range case index');
  const out={};let rem=key;
  for(const axis of schema.axes){
    if(!axis?.values?.length)throw Error('missing axis values');
    const d=rem%axis.values.length;rem=Math.floor(rem/axis.values.length);
    out[axis.name]=axis.values[d];
  }
  if(rem!==0)throw Error('radix overrun');
  return out;
}
export function parameterPoint(schema,key) {
  const v=decode(schema,key);
  const architectures=schema.axes[0].values,faults=schema.axes[1].values;
  const a=architectures.indexOf(v.architecture),f=faults.indexOf(v.fault_zone);
  if(a<0||f<0)throw Error('unexpected axis dimensions');
  // Jitter encodes other dimensions only as a visual aid, NOT a distance metric.
  const m=Math.imul((key>>>0),2246822519)>>>0;
  const q=Math.imul(((key>>>0)^0x9e3779b9),3266489917)>>>0;
  return {x:(a-1.5)*.55+((m/TWO32)-.5)*.20,
          y:(f-4.5)*.18+((q/TWO32)-.5)*.10,
          architecture:a,fault:f};
}
export function getPreviewKeys(count=2048) {
  if(!Number.isInteger(count)||count<1||count>4096)throw Error('preview budget 1..4096');
  const keys=new Set([0,1,2,BILLION-1]);
  let i=0;
  while(keys.size<count)keys.add((i++*1_000_003)%BILLION);
  return [...keys].slice(0,count).sort((a,b)=>a-b);
}
export function relativeWaferPoint(key) {
  const p=place(key),R=Math.sqrt(BILLION-.5);
  return {x:p.x/R,y:p.y/R};
}
export function morphPoint(schema,key,t) {
  if(!(Number.isFinite(t)&&t>=0&&t<=1))throw Error('morph fraction must be 0..1');
  const a=relativeWaferPoint(key),b=parameterPoint(schema,key);
  return {x:(1-t)*a.x+t*b.x,y:(1-t)*a.y+t*b.y};
}
