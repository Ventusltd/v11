const NS='http://www.w3.org/2000/svg';
const svg=document.querySelector('#sld');
const viewport=document.querySelector('#viewport');
const MODULES=30, STRINGS=24, INPUTS_PER_MPPT=2;
const modulePhysical={height_mm:2384,width_mm:1303,jbox_axis_from_bottom_mm:1400,cable_positive_mm:350,cable_negative_mm:280,evidence:'Trina TSM-DEG21C.20 datasheet TSM_EN_2024_A'};
const g={left:205,top:42,rowH:176,mpptGap:28,moduleW:46,moduleH:84,moduleGap:16,inverterW:92,inverterH:116};
let mode='leapfrog';
const el=(name,attrs={},text='')=>{const n=document.createElementNS(NS,name);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,String(v));if(text)n.textContent=text;return n};
const id2=n=>String(n).padStart(2,'0');
const connectorId=(s,m,p)=>`STR-${id2(s)}-M${id2(m)}-${p==='positive'?'POS':'NEG'}-CONNECTOR`;
function order(count,strategy){if(strategy==='sequential')return Array.from({length:count},(_,i)=>i+1);const odd=[],even=[];for(let i=1;i<=count;i+=2)odd.push(i);for(let i=count%2===0?count:count-1;i>=2;i-=2)even.push(i);return odd.concat(even)}
function moduleX(i){return g.left+122+(i-1)*(g.moduleW+g.moduleGap)}
function centreY(row){return g.top+row*g.rowH+g.moduleH/2+36+Math.floor(row/2)*g.mpptGap}
function ptForModule(row,m,p){return{x:moduleX(m)+(p==='positive'?g.moduleW:0),y:centreY(row)}}
function curve(a,b,index,total){const dx=Math.abs(b.x-a.x);const up=index%2===0;const amp=Math.min(54+dx*.16,112);const cy=up?Math.min(a.y,b.y)-amp:Math.max(a.y,b.y)+amp;return`M ${a.x} ${a.y} C ${a.x} ${cy}, ${b.x} ${cy}, ${b.x} ${b.y}`}
function addConnector(group,id,x,y,polarity,extra={}){const c=el('circle',{id,cx:x,cy:y,r:5.2,class:`connector ${polarity}`,tabindex:0,'data-connector-id':id,'data-polarity':polarity,...extra});group.append(c);return c}
function drawString(s,row){const mppt=Math.floor((s-1)/2)+1,input=`PV${s}`;const y=centreY(row),group=el('g',{'data-string-id':`STR-${id2(s)}`,'data-mppt-id':`MPPT-${id2(mppt)}`});
 const bandY=y-g.moduleH/2-33;group.append(el('rect',{x:10,y:bandY-16,width:2110,height:g.moduleH+66,class:'mppt-band'}));
 group.append(el('text',{x:24,y:bandY-1,class:'string-title'},`STR-${id2(s)} · MPPT-${id2(mppt)} · ${input}+ / ${input}− · ${mode.toUpperCase()}`));
 const invX=42,invY=y-g.inverterH/2;group.append(el('rect',{x:invX,y:invY,width:g.inverterW,height:g.inverterH,rx:5,class:'inverter'}));
 group.append(el('text',{x:invX+g.inverterW/2,y:invY+27,'text-anchor':'middle',class:'inverter-label'},'INVERTER'));
 group.append(el('text',{x:invX+g.inverterW/2,y:invY+45,'text-anchor':'middle',class:'inverter-label'},`IN-${id2(s)}`));
 group.append(el('text',{x:invX+g.inverterW/2,y:invY+63,'text-anchor':'middle',class:'inverter-label'},`MPPT-${id2(mppt)}`));
 const invNeg={x:invX+g.inverterW,y:y-20},invPos={x:invX+g.inverterW,y:y+20};
 addConnector(group,`STR-${id2(s)}-IN-${id2(s)}-NEG-INVERTER-SOCKET`,invNeg.x,invNeg.y,'negative',{'data-pv-terminal':`${input}-`});
 addConnector(group,`STR-${id2(s)}-IN-${id2(s)}-POS-INVERTER-SOCKET`,invPos.x,invPos.y,'positive',{'data-pv-terminal':`${input}+`});
 group.append(el('text',{x:invX+20,y:invNeg.y+3,class:'terminal-label'},`${input}−`));group.append(el('text',{x:invX+20,y:invPos.y+3,class:'terminal-label'},`${input}+`));
 const points=new Map();
 for(let m=1;m<=MODULES;m++){const x=moduleX(m),top=y-g.moduleH/2;group.append(el('rect',{x,y:top,width:g.moduleW,height:g.moduleH,rx:2,class:'module-body'}));group.append(el('line',{x1:x+g.moduleW/2,y1:top+4,x2:x+g.moduleW/2,y2:top+g.moduleH-4,class:'module-backline'}));
  const jboxY=top+g.moduleH*(1-modulePhysical.jbox_axis_from_bottom_mm/modulePhysical.height_mm);const jboxX=x+g.moduleW/2-9;group.append(el('rect',{x:jboxX,y:jboxY-5,width:18,height:10,rx:1.5,class:'jbox'}));
  const negRoot={x:jboxX+5,y:jboxY},posRoot={x:jboxX+13,y:jboxY},neg=ptForModule(row,m,'negative'),pos=ptForModule(row,m,'positive');
  group.append(el('circle',{cx:negRoot.x,cy:negRoot.y,r:1.7,class:'jbox-terminal'}));group.append(el('circle',{cx:posRoot.x,cy:posRoot.y,r:1.7,class:'jbox-terminal'}));
  group.append(el('path',{d:`M ${negRoot.x} ${negRoot.y} C ${negRoot.x-8} ${negRoot.y+12}, ${neg.x+6} ${neg.y-12}, ${neg.x} ${neg.y}`,class:'factory-lead'}));
  group.append(el('path',{d:`M ${posRoot.x} ${posRoot.y} C ${posRoot.x+8} ${posRoot.y+12}, ${pos.x-6} ${pos.y-12}, ${pos.x} ${pos.y}`,class:'factory-lead'}));
  addConnector(group,connectorId(s,m,'negative'),neg.x,neg.y,'negative',{'data-module':m});addConnector(group,connectorId(s,m,'positive'),pos.x,pos.y,'positive',{'data-module':m});
  group.append(el('text',{x:x+g.moduleW/2,y:top+g.moduleH+16,'text-anchor':'middle',class:'module-label'},`M${m}`));points.set(`${m}-negative`,neg);points.set(`${m}-positive`,pos)}
 const seq=order(MODULES,mode);
 seq.slice(0,-1).forEach((m,i)=>{const next=seq[i+1],a=points.get(`${m}-positive`),b=points.get(`${next}-negative`);group.append(el('path',{id:`STR-${id2(s)}-MATE-${id2(i+2)}`,d:curve(a,b,i,seq.length),class:'mate-path','data-source-connector-id':connectorId(s,m,'positive'),'data-destination-connector-id':connectorId(s,next,'negative'),'data-interface-class':'module_to_module'}))});
 const first=seq[0],last=seq.at(-1),firstP=points.get(`${first}-negative`),lastP=points.get(`${last}-positive`);
 const negCableInv={x:154,y:invNeg.y},negCableMod={x:176,y:firstP.y},posCableInv={x:154,y:invPos.y},posCableMod={x:176,y:lastP.y};
 addConnector(group,`STR-${id2(s)}-NEG-STRING-CABLE-INVERTER-END`,negCableInv.x,negCableInv.y,'negative');addConnector(group,`STR-${id2(s)}-NEG-STRING-CABLE-MODULE-END`,negCableMod.x,negCableMod.y,'negative');
 addConnector(group,`STR-${id2(s)}-POS-STRING-CABLE-INVERTER-END`,posCableInv.x,posCableInv.y,'positive');addConnector(group,`STR-${id2(s)}-POS-STRING-CABLE-MODULE-END`,posCableMod.x,posCableMod.y,'positive');
 group.append(el('path',{d:`M ${invNeg.x} ${invNeg.y} L ${negCableInv.x} ${negCableInv.y}`,class:'mate-path','data-interface-class':'string_cable_to_inverter'}));
 group.append(el('path',{d:`M ${negCableInv.x} ${negCableInv.y} L ${negCableMod.x} ${negCableMod.y}`,class:'string-cable'}));
 group.append(el('path',{d:`M ${negCableMod.x} ${negCableMod.y} C ${negCableMod.x+10} ${negCableMod.y}, ${firstP.x-10} ${firstP.y}, ${firstP.x} ${firstP.y}`,class:'mate-path','data-interface-class':'module_to_string_cable'}));
 group.append(el('path',{d:`M ${lastP.x} ${lastP.y} C ${lastP.x+18} ${lastP.y}, ${posCableMod.x+25} ${posCableMod.y+38}, ${posCableMod.x} ${posCableMod.y}`,class:'mate-path','data-interface-class':'module_to_string_cable'}));
 group.append(el('path',{d:`M ${posCableMod.x} ${posCableMod.y} L ${posCableInv.x} ${posCableInv.y}`,class:'string-cable'}));
 group.append(el('path',{d:`M ${posCableInv.x} ${posCableInv.y} L ${invPos.x} ${invPos.y}`,class:'mate-path','data-interface-class':'string_cable_to_inverter'}));
 group.dataset.connectorEnds=66;group.dataset.matedInterfaces=33;return group}
function render(){svg.replaceChildren();const width=2140;const height=g.top+STRINGS*g.rowH+12*g.mpptGap+30;svg.setAttribute('viewBox',`0 0 ${width} ${height}`);svg.setAttribute('width',width);svg.setAttribute('height',height);
 for(let mppt=1;mppt<=12;mppt++){const firstRow=(mppt-1)*2;const titleY=centreY(firstRow)-g.moduleH/2-55;svg.append(el('text',{x:12,y:titleY,class:'mppt-title'},`MPPT-${id2(mppt)} · INPUTS ${id2(firstRow+1)}–${id2(firstRow+2)}`));svg.append(drawString(firstRow+1,firstRow));svg.append(drawString(firstRow+2,firstRow+1))}
 svg.dataset.mode=mode;svg.dataset.strings=24;svg.dataset.modulesPerString=30;svg.dataset.completeSystemConnectorEnds=1584;svg.dataset.matedInterfaces=792}
document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>{mode=b.dataset.mode;document.querySelectorAll('[data-mode]').forEach(x=>x.classList.toggle('active',x===b));render()}));
document.querySelector('#fit').addEventListener('click',()=>{const scale=Math.max(.25,viewport.clientWidth/2140);svg.style.width=`${2140*scale}px`;svg.style.height=`${Number(svg.getAttribute('height'))*scale}px`});
svg.addEventListener('click',e=>{const target=e.target.closest?.('.connector,.mate-path');if(!target)return;svg.querySelectorAll('.selected').forEach(x=>x.classList.remove('selected'));target.classList.add('selected')});
render();
