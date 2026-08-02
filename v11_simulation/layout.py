"""Deterministic 2D solar-module placement and movement engine."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json, math
from typing import Any, Mapping

class LayoutError(ValueError): pass

def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

def layout_hash(value: object) -> str:
    return "sha256:" + sha256(canonical_json(value).encode()).hexdigest()

def _num(name: str, value: Any, minimum: float | None = None) -> float:
    try: result=float(value)
    except (TypeError,ValueError) as exc: raise LayoutError(f"{name} must be numeric") from exc
    if not math.isfinite(result): raise LayoutError(f"{name} must be finite")
    if minimum is not None and result < minimum: raise LayoutError(f"{name} must be >= {minimum}")
    return result

def footprint(module: Mapping[str,Any]) -> dict[str,float]:
    rotation=int(module.get("rotation_deg",0))%180
    if rotation not in (0,90): raise LayoutError("rotation must be 0 or 90 degrees")
    w=_num("width_m",module["width_m"],0.001); h=_num("height_m",module["height_m"],0.001)
    if rotation==90: w,h=h,w
    x=_num("x_m",module["x_m"]); y=_num("y_m",module["y_m"])
    return {"left":x-w/2,"right":x+w/2,"bottom":y-h/2,"top":y+h/2,"width":w,"height":h}

def intersects(a: Mapping[str,float], b: Mapping[str,float]) -> bool:
    return min(a["right"],b["right"]) > max(a["left"],b["left"]) and min(a["top"],b["top"]) > max(a["bottom"],b["bottom"])

def validate_layout(layout: Mapping[str,Any]) -> list[str]:
    errors=[]; boundary=layout["boundary"]; mods=layout.get("modules",[]); obstacles=layout.get("obstacles",[])
    ids=[m.get("id") for m in mods]
    if len(ids)!=len(set(ids)): errors.append("module ids must be unique")
    fps=[]
    for m in mods:
        try: f=footprint(m)
        except Exception as exc: errors.append(f"{m.get('id','?')}: {exc}"); continue
        if f["left"] < boundary["x_min"] or f["right"] > boundary["x_max"] or f["bottom"] < boundary["y_min"] or f["top"] > boundary["y_max"]: errors.append(f"{m['id']}: outside boundary")
        for obstacle in obstacles:
            of={"left":obstacle["x_min"],"right":obstacle["x_max"],"bottom":obstacle["y_min"],"top":obstacle["y_max"]}
            if intersects(f,of): errors.append(f"{m['id']}: intersects obstacle {obstacle['id']}")
        fps.append((m["id"],f))
    for i,(aid,a) in enumerate(fps):
        for bid,b in fps[i+1:]:
            if intersects(a,b): errors.append(f"{aid}: overlaps {bid}")
    return errors

def fill_rectangle(*, boundary:Mapping[str,float], module_width_m:float, module_height_m:float, gap_x_m:float=0.02, gap_y_m:float=0.02, orientation:str="portrait", stagger_m:float=0.0, obstacles:list[dict[str,Any]]|None=None, limit:int|None=None) -> dict[str,Any]:
    if orientation not in {"portrait","landscape"}: raise LayoutError("orientation must be portrait or landscape")
    w,h=_num("module_width_m",module_width_m,0.001),_num("module_height_m",module_height_m,0.001)
    rotation=0
    if orientation=="landscape": rotation=90
    fpw,fph=(h,w) if rotation==90 else (w,h)
    gx,gy=_num("gap_x_m",gap_x_m,0),_num("gap_y_m",gap_y_m,0); stagger=_num("stagger_m",stagger_m,0)
    layout={"schema_version":"globalgrid2050.v11.module-layout.v1","boundary":dict(boundary),"obstacles":deepcopy(obstacles or []),"modules":[]}
    row=0; y=boundary["y_min"]+fph/2
    while y+fph/2 <= boundary["y_max"]+1e-12:
        x=boundary["x_min"]+fpw/2+(stagger if row%2 else 0)
        col=0
        while x+fpw/2 <= boundary["x_max"]+1e-12:
            m={"id":f"MOD-{len(layout['modules'])+1:04d}","x_m":round(x,9),"y_m":round(y,9),"width_m":w,"height_m":h,"rotation_deg":rotation,"row":row,"column":col,"string_id":None}
            candidate=deepcopy(layout); candidate["modules"].append(m)
            if not validate_layout(candidate): layout["modules"].append(m)
            if limit and len(layout["modules"])>=limit: break
            x += fpw+gx; col+=1
        if limit and len(layout["modules"])>=limit: break
        y += fph+gy; row+=1
    layout["layout_hash"]=layout_hash({k:v for k,v in layout.items() if k!="layout_hash"})
    return layout

def move_module(layout:Mapping[str,Any], module_id:str, x_m:float, y_m:float, *, snap_m:float=0.01) -> dict[str,Any]:
    result=deepcopy(layout); snap=_num("snap_m",snap_m,0.000001)
    found=False
    for m in result["modules"]:
        if m["id"]==module_id:
            m["x_m"]=round(round(_num("x_m",x_m)/snap)*snap,9); m["y_m"]=round(round(_num("y_m",y_m)/snap)*snap,9); found=True; break
    if not found: raise LayoutError(f"unknown module {module_id}")
    errors=validate_layout(result)
    if errors: raise LayoutError("; ".join(errors))
    result["layout_hash"]=layout_hash({k:v for k,v in result.items() if k!="layout_hash"}); return result

def rotate_module(layout:Mapping[str,Any], module_id:str) -> dict[str,Any]:
    result=deepcopy(layout)
    for m in result["modules"]:
        if m["id"]==module_id: m["rotation_deg"]=90 if int(m.get("rotation_deg",0))%180==0 else 0; break
    else: raise LayoutError(f"unknown module {module_id}")
    errors=validate_layout(result)
    if errors: raise LayoutError("; ".join(errors))
    result["layout_hash"]=layout_hash({k:v for k,v in result.items() if k!="layout_hash"}); return result

def assign_strings(layout:Mapping[str,Any], modules_per_string:int=30, *, snake:bool=True) -> dict[str,Any]:
    if modules_per_string<=0: raise LayoutError("modules_per_string must be positive")
    result=deepcopy(layout); rows={}
    for m in result["modules"]: rows.setdefault(round(m["y_m"],9),[]).append(m)
    ordered=[]
    for row_index,y in enumerate(sorted(rows)):
        row=sorted(rows[y],key=lambda m:m["x_m"],reverse=snake and row_index%2==1); ordered.extend(row)
    for i,m in enumerate(ordered): m["string_id"]=f"STR-{i//modules_per_string+1:02d}"; m["electrical_index"]=i%modules_per_string+1
    result["layout_hash"]=layout_hash({k:v for k,v in result.items() if k!="layout_hash"}); return result
