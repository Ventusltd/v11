"""Scratch helper: render README tables/blocks from the summary JSON (so no number is hand-typed)."""
import hashlib, json, sys
from pathlib import Path
exp = Path(sys.argv[1])
s = json.loads((exp / "sampling-benchmark-summary.json").read_text())
pm = s["per_method_means"]
cells = [f"d{d}_N{n}" for d in (2, 4, 6) for n in (64, 256, 1024)]
spec = ["vogel2d", "vogel_paired", "sobol", "lhs", "random", "grid_corners"]
extra = ["golden_lattice_paired", "corners_plus_sobol", "corners_plus_vogel_paired", "corners_plus_golden_lattice"]
g = lambda v: f"{v:.3g}"
out = {}
def table(metric, rng=False):
    L = ["| method | " + " | ".join(c.replace("_", " ") for c in cells) + " |", "|---|" + "---|" * len(cells)]
    for m in spec + extra:
        vals = []
        for c in cells:
            st = pm[c][m][metric]
            v = g(st["mean"])
            if rng and st["min"] != st["max"]:
                v += f" ({g(st['min'])}-{g(st['max'])})"
            vals.append(v)
        name = m if m in spec else f"*{m}*"
        L.append(f"| {name} | " + " | ".join(vals) + " |")
    return "\n".join(L)
out["T_MISSES"] = table("planted_regions_missed", True)
out["T_CD"] = table("cd_centred_l2")
out["T_MIND"] = table("min_pairwise_distance")
out["T_COV"] = table("covering_radius_ref")
out["T_CORNER"] = table("corner_fraction_hit_side0p05")
r = s["rankings"]["specified_methods"]
L = ["| metric (better) | " + " | ".join(spec) + " |", "|---|" + "---|" * len(spec)]
for metric, e in r.items():
    mr = {x["method"]: x["mean_rank"] for x in e["mean_rank_over_cells"]}
    tag = "**" if e["primary_metric"] else ""
    L.append(f"| {tag}{metric}{tag} ({e['better']}) | " + " | ".join(f"{mr[m]:.2f}" for m in spec) + " |")
out["T_MEANRANK"] = "\n".join(L)
rt = s["ranking_text"]
prim = {k for k, e in r.items() if e["primary_metric"]}
blk, keep = [], False
for line in rt:
    if line.startswith("[") and "] " in line and " is better" in line:
        keep = line[1:line.index("]")] in prim
        if keep and blk and blk[-1] != "":
            blk.append("")
    if line == "":
        continue
    if line.startswith("=== EXTENDED"):
        keep = False
    if keep:
        blk.append(line)
out["B_RANKING"] = "\n".join(blk).strip("\n")
L = []
for line in rt:
    if line.startswith("=== EXTENDED"):
        keep = True
        continue
    if keep and line.startswith("["):
        L.append(line)
out["B_EXTENDED"] = "\n".join(L)
seeds = s["planted_region_misses_by_seed"]["d4_N256"]
regs = list(seeds["sobol"].keys())
L = ["| method | " + " | ".join(regs) + " |", "|---|" + "---|" * len(regs)]
for m in spec + extra:
    name = m if m in spec else f"*{m}*"
    L.append(f"| {name} | " + " | ".join(seeds[m][x] for x in regs) + " |")
out["T_REGIONS_D4N256"] = "\n".join(L)
pr = s["config"]["planted_regions"]
names = ["corner_box_1", "corner_box_2", "corner_box_3", "corner_box_4", "corner_box_5", "slab_x1", "ball_interior", "ridge_x1x2", "holdout_x3x4", "corner6d"]
L = ["| region | definition | volume share of cube, d = 2 / 4 / 6 | contains a cube vertex |", "|---|---|---|---|"]
for nm in names:
    present = {d: pr[f"d{d}"].get(nm) for d in (2, 4, 6)}
    vols = " / ".join(g(e["volume_fraction_of_cube"]) if e else "-" for e in present.values())
    verts = sorted({("yes" if e["contains_a_cube_vertex"] else "no") for e in present.values() if e})
    if nm.startswith("corner_box_"):
        vx = " / ".join("(" + ",".join(str(v) for v in e["vertex"]) + ")" if e else "-" for e in present.values())
        deftxt = f"axis-aligned box of side 0.08 at vertex {vx} (d = 2 / 4 / 6)"
    elif nm == "ball_interior":
        c = present[6]["centre"]
        deftxt = "ball of radius 0.03 centred at the first d components of (" + ", ".join(f"{x:g}" for x in c) + ")"
    else:
        deftxt = next(e for e in present.values() if e)["definition"]
        ds = [str(d) for d, e in present.items() if e]
        if len(ds) < 3:
            deftxt += f"; defined for d = {', '.join(ds)}"
    deftxt = deftxt.replace("|", "\\|")
    L.append(f"| {nm} | {deftxt} | {vols} | {'/'.join(verts)} |")
out["T_REGIONS_DEF"] = "\n".join(L)
out["CSV_SHA"] = s["outputs"]["csv_sha256"]
out["SCRIPT_SHA"] = s["producer"]["script_sha256"]
out["SUMMARY_SHA"] = hashlib.sha256((exp / "sampling-benchmark-summary.json").read_bytes()).hexdigest()
out["CSV_ROWS"] = str(s["outputs"]["csv_rows"])
tpl = Path(sys.argv[2]).read_text()
for k, v in out.items():
    tpl = tpl.replace("{{" + k + "}}", v)
assert "{{" not in tpl, [l for l in tpl.splitlines() if "{{" in l]
Path(sys.argv[3]).write_text(tpl)
print("README assembled", len(tpl), "chars")
