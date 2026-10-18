import {BILLION,decode,morphPoint,getPreviewKeys} from './kuiper_core.mjs';
const $=id=>document.getElementById(id);
const canvas=$('wafer'),ctx=canvas.getContext('2d');
let schema,view=0,aim=0,zoom=1,panX=0,panY=0,selected=0,renderPoints=[],down=null;
const PREVIEW=getPreviewKeys(2048);
const serif=(n)=>n.toLocaleString('en-GB');
function resize(){const d=Math.min(2,window.devicePixelRatio||1);
 const rect=canvas.getBoundingClientRect();canvas.width=Math.max(20,Math.round(rect.width*d));
 canvas.height=Math.max(20,Math.round(rect.height*d));ctx.setTransform(d,0,0,d,0,0);draw();}
function project(x,y){const r=canvas.getBoundingClientRect();
 const sc=Math.min(r.width,r.height)*.43*zoom;return [r.width/2+(x+panX)*sc,r.height/2-(y+panY)*sc];}
function drawingPoint(key){
 const v=morphPoint(schema,key,view);
 const [x,y]=project(v.x,v.y);
 return {x,y,key};
}
function draw(){if(!schema)return;
 const rect=canvas.getBoundingClientRect(),w=rect.width,h=rect.height;
 ctx.clearRect(0,0,w,h);
 ctx.strokeStyle='#304561';ctx.lineWidth=.7;
 const [xx,yy]=project(0,0);ctx.beginPath();ctx.moveTo(0,yy);ctx.lineTo(w,yy);
 ctx.moveTo(xx,0);ctx.lineTo(xx,h);ctx.stroke();
 renderPoints=[];ctx.fillStyle='#7893b1';
 for(const key of PREVIEW){
   const p=drawingPoint(key);if(p.x<0||p.y<0||p.x>w||p.y>h)continue;
   renderPoints.push(p);ctx.beginPath();ctx.arc(p.x,p.y,1.4,0,Math.PI*2);ctx.fill();
 }
 const sel=drawingPoint(selected);
 ctx.strokeStyle='#ffca68';ctx.lineWidth=2;
 ctx.beginPath();ctx.arc(sel.x,sel.y,6,0,Math.PI*2);ctx.stroke();
 ctx.fillStyle='#f8dc94';ctx.font='12px system-ui';ctx.fillText('Case '+selected,Math.min(w-104,Math.max(3,sel.x+11)),Math.max(13,sel.y-10));
 $('summary').textContent=serif(BILLION)+' virtual case IDs · '+serif(PREVIEW.length)+' drawn address previews · ZERO assumed hardware results';
 $('status').textContent=(view<.5?'Kuiper address':'Parameter-neighbourhood projection')+
   ' · scroll to zoom, drag to pan, click point to inspect; current scale '+zoom.toFixed(2)+'×.';
}
function selectedInfo(key){
 selected=key;
 let values=decode(schema,key);
 $('key').value=String(key);
 $('caseDetail').textContent=JSON.stringify({study:'V11 D4 billion-case virtual lattice',
    key,virtual_id:schema.namespace+'/'+key,evidence:'ADDRESS_ONLY__NOT_TESTED',
    params:values,physics:'No arc or dielectric conclusion can be inferred from address placement'},null,2);
 draw();
}
function animationTo(target){
 aim=target;const initial=view;let t0=null;
 function step(ts){if(t0===null)t0=ts;const p=Math.min(1,(ts-t0)/720);
 const smooth=p*p*(3-2*p);view=initial+(target-initial)*smooth;
 $('viewSlider').value=String(view);draw();if(p<1&&aim===target)requestAnimationFrame(step);}
 requestAnimationFrame(step);
}
async function launch(){
 try{
 const res=await fetch('./case-schema.json',{cache:'no-cache'});
 if(!res.ok)throw Error('case schema HTTP '+res.status);
 schema=await res.json();decode(schema,0);decode(schema,BILLION-1);
 $('waferBtn').onclick=()=>animationTo(0);
 $('gridBtn').onclick=()=>animationTo(1);
 $('resetBtn').onclick=()=>{zoom=1;panX=0;panY=0;draw();};
 $('viewSlider').oninput=()=>{aim=view=Number($('viewSlider').value);draw();};
 $('findBtn').onclick=()=>{
  const n=Number($('key').value);
  if(!Number.isSafeInteger(n)||n<0||n>=BILLION){$('status').textContent='Invalid virtual case key: 0..999999999';return;}
  selectedInfo(n);
 };
 $('key').onkeydown=e=>{if(e.key==='Enter')$('findBtn').click();};
 canvas.addEventListener('wheel',e=>{
   e.preventDefault();zoom=Math.max(.15,Math.min(150,zoom*Math.exp(-e.deltaY*.001)));draw();
 },{passive:false});
 canvas.onpointerdown=e=>{down={x:e.clientX,y:e.clientY,px:panX,py:panY};canvas.setPointerCapture(e.pointerId);};
 canvas.onpointermove=e=>{
  if(!down)return;const r=canvas.getBoundingClientRect();
  const sc=Math.min(r.width,r.height)*.43*zoom;
  panX=down.px+(e.clientX-down.x)/sc;panY=down.py-(e.clientY-down.y)/sc;draw();
 };
 canvas.onpointerup=e=>{
  if(!down)return;const near=down;
  down=null;
  if(Math.hypot(e.clientX-near.x,e.clientY-near.y)>5)return;
  const r=canvas.getBoundingClientRect(),cx=e.clientX-r.left,cy=e.clientY-r.top;
  let best=Infinity,key=null;
  for(const p of renderPoints){const d=Math.hypot(p.x-cx,p.y-cy);if(d<best){best=d;key=p.key;}}
  if(best<15&&key!==null)selectedInfo(key);
 };
 window.addEventListener('resize',resize);
 resize();selectedInfo(0);
 }catch(err){$('summary').textContent='Could not load case schema';$('caseDetail').textContent=String(err);
 $('status').textContent='Serve this directory with a local HTTP server or GitHub Pages; file:// fetch may be blocked.';}
}
launch();
