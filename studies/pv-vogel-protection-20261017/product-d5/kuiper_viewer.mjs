/* V11 D5 original drawing adapter. Data controls positions; display never infers electrical paths.
 * V11 D5-local case indices are NOT globally allocated permanent Kuiper keys.
 * Refer to kuiper-belt law and kuiper-drawing-engine source catalogue.
 * This is a browser visualisation, not an SPICE or manufacturer circuit viewer.
 */
const canvas=document.querySelector("#chart"),ctx=canvas.getContext("2d");
const file=document.querySelector("#file"),filter=document.querySelector("#filter");
const detail=document.querySelector("#detail"),status=document.querySelector("#status");
const reset=document.querySelector("#reset"),toggle=document.querySelector("#animate");
const legend=document.querySelector("#legend");
const colors=["#4bd4ce","#f9b454","#f27470","#b895ec","#8dd15b"];
const labels=["Not flagged by simple algebra — NOT safe","Voltage-rating hypothesis",
 "Electronics dissipation hypothesis","Device/control failure hypothesis","Bypass-diode heat hypothesis"];
labels.forEach((name,i)=>{
 const d=document.createElement("div");const b=document.createElement("span");
 b.className="swatch";b.style.background=colors[i];d.append(b,document.createTextNode(name));legend.append(d);
});
let points=[],data=null,zoom=1,cx=0,cy=0,animating=true,hover=null,drag=null;
function dimensions(){
 const r=canvas.getBoundingClientRect();const dpr=Math.min(window.devicePixelRatio||1,2);
 canvas.width=Math.max(1,Math.floor(r.width*dpr));
 canvas.height=Math.max(1,Math.floor(r.height*dpr));
 return {w:r.width,h:r.height,dpr};
}
let view=dimensions();
function fit(){
 if(!points.length)return;
 const r=Math.max(1,...points.map(p=>Math.hypot(p.x,p.y)));
 cx=0;cy=0;zoom=.44*Math.min(view.w,view.h)/r;
}
function screen(p){return [view.w/2+(p.x-cx)*zoom,view.h/2-(p.y-cy)*zoom];}
function frame(t){
 ctx.setTransform(view.dpr,0,0,view.dpr,0,0);
 ctx.clearRect(0,0,view.w,view.h);
 ctx.fillStyle="#071426";ctx.fillRect(0,0,view.w,view.h);
 const want=filter.value,rad=Math.max(1,Math.min(3,zoom*1.5));
 for(const p of points){
  if(want!=="all"&&String(p.screen_code)!==want)continue;
  const [x,y]=screen(p);
  if(x<0||y<0||x>view.w||y>view.h)continue;
  ctx.beginPath();ctx.fillStyle=colors[p.screen_code]||"#888";
  ctx.arc(x,y,rad,0,Math.PI*2);ctx.fill();
 }
 if(hover){
  const [x,y]=screen(hover);const pulse=animating?5+2*Math.sin(t/300):6;
  ctx.lineWidth=2;ctx.strokeStyle="#fff";
  ctx.beginPath();ctx.arc(x,y,pulse,0,2*Math.PI);ctx.stroke();
 }
 requestAnimationFrame(frame);
}
function parseProjection(raw){
 const x=JSON.parse(raw);
 if(x.schema!=="ventus.v11.pv.d5.kuiper-projection.v1" ||
    !Array.isArray(x.points)||x.points.length>50000 ||
    x.points.length!==x.distinct_projected ||
    x.input_space_not_physically_simulated!==true ||
    !String(x.identity).includes("LOCAL")){
    throw Error("Unsupported/unverified Kuiper projection, refusal to display");
 }
 if(new Set(x.points.map(p=>p.local_case_id)).size!==x.points.length)
    throw Error("Duplicate case identities");
 for(const p of x.points){
  if(!Number.isFinite(p.x)||!Number.isFinite(p.y)||
     !Number.isInteger(p.screen_code)||p.screen_code<0||p.screen_code>4)
     throw Error("Invalid point coordinates or screen label");
 }
 return x;
}
file.addEventListener("change",async ()=>{
 try{
  const uploaded=file.files?.[0];if(!uploaded)return;
  if(uploaded.size>20_000_000)throw Error("Refusing oversized projection");
  const obj=parseProjection(await uploaded.text());
  data=obj;points=obj.points;hover=null;fit();
  status.textContent=points.length.toLocaleString()+" projected of "+
      obj.declared_input_space.toLocaleString()+" input cases. Law: "+
      obj.coordinate_law+". NOT a measured fault simulation.";
  detail.textContent="Select a dot to inspect its local case ID.";
 }catch(e){status.textContent="Cannot load projection: "+e.message}
});
function position(e){const r=canvas.getBoundingClientRect();return [e.clientX-r.left,e.clientY-r.top];}
function nearest(x,y){
 let pick=null,best=144;
 for(const p of points){
  if(filter.value!=="all"&&String(p.screen_code)!==filter.value)continue;
  const [px,py]=screen(p),d=(x-px)**2+(y-py)**2;
  if(d<best){best=d;pick=p;}
 }
 return pick;
}
canvas.addEventListener("pointerdown",e=>{
 const [x,y]=position(e);drag={x,y,cx,cy,moved:false};canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener("pointermove",e=>{
 const [x,y]=position(e);
 if(drag){
  const dx=x-drag.x,dy=y-drag.y;if(Math.abs(dx)+Math.abs(dy)>3)drag.moved=true;
  cx=drag.cx-dx/zoom;cy=drag.cy+dy/zoom;
 }else hover=nearest(x,y);
});
canvas.addEventListener("pointerup",e=>{
 const [x,y]=position(e);
 if(drag&&!drag.moved){
  hover=nearest(x,y);
  detail.textContent=hover?JSON.stringify({
      case_id: hover.local_case_id,
      plot_key: hover.local_plot_key,
      architecture: hover.arch,
      fault: hover.fault,
      component_failure: hover.failure,
      screen_label: labels[hover.screen_code],
      source: "Hypothesis only: open exact V11 D5 circuit manifest independently"
   },null,2):"No nearby dot.";
 }
 drag=null;
});
canvas.addEventListener("wheel",e=>{
 e.preventDefault();
 const [x,y]=position(e);
 const wx=cx+(x-view.w/2)/zoom, wy=cy-(y-view.h/2)/zoom;
 zoom=Math.min(1e5,Math.max(1e-7,zoom*Math.exp(-e.deltaY*.001)));
 cx=wx-(x-view.w/2)/zoom;cy=wy+(y-view.h/2)/zoom;
},{passive:false});
reset.addEventListener("click",fit);
toggle.addEventListener("click",()=>{animating=!animating;toggle.textContent=animating?"Stop animation":"Start animation";});
window.addEventListener("resize",()=>{view=dimensions();fit();});
requestAnimationFrame(frame);
