import json, sys
s = json.load(open(sys.argv[1]))
pm = s["per_method_means"]
cells = [f"d{d}_N{n}" for d in (2, 4, 6) for n in (64, 256, 1024)]
def g(v): return f"{v:.3g}"
def table(metric, methods, title, show_range=False):
    print(f"\n**{title}**\n")
    print("| method | " + " | ".join(c.replace('_', ' ') for c in cells) + " |")
    print("|---|" + "---|" * len(cells))
    for m in methods:
        vals = []
        for c in cells:
            st = pm[c][m][metric]
            v = g(st["mean"])
            if show_range and st["min"] != st["max"]:
                v += f" ({g(st['min'])}-{g(st['max'])})"
            vals.append(v)
        print(f"| {m} | " + " | ".join(vals) + " |")
spec = ["vogel2d", "vogel_paired", "sobol", "lhs", "random", "grid_corners"]
extra = ["golden_lattice_paired", "corners_plus_sobol", "corners_plus_vogel_paired", "corners_plus_golden_lattice"]
table("planted_regions_missed", spec + extra, "Planted regions missed (mean over seeds, (min-max) where seeds differ); totals 7 / 9 / 10 at d = 2 / 4 / 6", True)
table("cd_centred_l2", spec + extra, "Centred L2 discrepancy (sqrt of scipy CD), mean")
table("min_pairwise_distance", spec + extra, "Minimum pairwise distance, mean")
table("covering_radius_ref", spec + extra, "Covering radius (20 000-point reference set), mean")
table("corner_fraction_hit_side0p05", spec + extra, "Fraction of 2^d vertex boxes (side 0.05) hit, mean")
print("\n**Mean rank over the 9 (d, N) cells, six specified methods (1 = best)**\n")
r = s["rankings"]["specified_methods"]
print("| metric | " + " | ".join(spec) + " |")
print("|---|" + "---|" * len(spec))
for metric, e in r.items():
    mr = {x["method"]: x["mean_rank"] for x in e["mean_rank_over_cells"]}
    tag = "" if e["primary_metric"] else " (supplementary)"
    print(f"| {metric}{tag} ({e['better']} better) | " + " | ".join(f"{mr[m]:.2f}" for m in spec) + " |")
print("\nmissed in every design by vogel:", s["findings"]["regions_missed_by_vogel_in_every_design"])
print("missed by every specified method:", s["findings"]["regions_missed_by_every_specified_method_every_seed"])
print("h2h:", json.dumps(s["conclusion"]["recommended_composite_wave2_phaseD"]["head_to_head_same_vertex_block"]))
print("csv sha", s["outputs"]["csv_sha256"], "script sha", s["producer"]["script_sha256"])
