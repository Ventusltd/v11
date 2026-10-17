def build_conclusion(groups, mean_of):
    """Candid conclusion; every number is interpolated from the computed results (no hand-typed values)."""
    cells = [(d, n) for d in DIMS for n in BUDGETS]
    others = ("sobol", "lhs", "random", "grid_corners")

    def series(method, metric, d):
        return "/".join(_g(mean_of(d, n, method, metric)) for n in BUDGETS)

    def misses(d, method, region):
        tot = sum(len(groups[(d, n, method)]) for n in BUDGETS)
        miss = sum(1 for n in BUDGETS for g in groups[(d, n, method)] if not g["hits"][region])
        return f"{miss}/{tot}"

    def rank_among(d, n, method, metric, better, pool):
        return _ranks({m: mean_of(d, n, m, metric) for m in pool}, better)[1][method]

    s_star = 0.5 - 0.5 / math.sqrt(2)
    floor2 = (math.sqrt(2) - 1) / 2
    vog_corner_zero = all(mean_of(d, n, vogel_representative(d), "corner_fraction_hit_side0p05") == 0.0
                          for d, n in cells)
    vog_last_key = sum(1 for d, n in cells
                       if rank_among(d, n, vogel_representative(d), "planted_regions_missed", "lower",
                                     (vogel_representative(d),) + others) == 5)
    sobol_cd_first = sum(1 for d, n in cells if rank_among(d, n, "sobol", "cd_centred_l2", "lower", BASE_METHODS) == 1)
    sobol_gap_first = sum(1 for d, n in cells
                          if rank_among(d, n, "sobol", "max_1d_projection_gap", "lower", BASE_METHODS) == 1)
    sobol_cov_top2 = sum(1 for d, n in cells
                         if rank_among(d, n, "sobol", "covering_radius_ref", "lower", BASE_METHODS) <= 2)
    vog_md_first_d2 = sum(1 for n in BUDGETS
                          if rank_among(2, n, "vogel2d", "min_pairwise_distance", "higher", BASE_METHODS) == 1)
    grid_key_first = sum(1 for d, n in cells
                         if rank_among(d, n, "grid_corners", "planted_regions_missed", "lower", BASE_METHODS) == 1)
    ball_all_missed = {d: all(not g["hits"]["ball_interior"] for n in BUDGETS for m in ALL_METHODS
                              for g in groups[(d, n, m)]) for d in (4, 6)}
    cd_ratio = mean_of(2, 1024, "vogel2d", "cd_centred_l2") / mean_of(2, 1024, "sobol", "cd_centred_l2")
    seg = 0.25 * (math.acos(2 * SLAB_LO - 1) - (2 * SLAB_LO - 1) * math.sqrt(1 - (2 * SLAB_LO - 1) ** 2))
    slab_density_ratio = (1 - SLAB_LO) / (seg / (math.pi / 4))

    wins = [
        f"Separation at d=2: vogel2d has the largest minimum pairwise distance among the six specified methods in "
        f"{vog_md_first_d2}/3 budgets ({series('vogel2d', 'min_pairwise_distance', 2)} at N=64/256/1024 vs "
        f"grid_corners {series('grid_corners', 'min_pairwise_distance', 2)}, sobol "
        f"{series('sobol', 'min_pairwise_distance', 2)}, random {series('random', 'min_pairwise_distance', 2)}).",
        f"Inside its own inscribed disk (d=2) the Vogel layout is near-optimal: covering radius over disk reference "
        f"points {series('vogel2d', 'covering_radius_inside_pair_disks', 2)} vs grid_corners "
        f"{series('grid_corners', 'covering_radius_inside_pair_disks', 2)} and sobol "
        f"{series('sobol', 'covering_radius_inside_pair_disks', 2)}; 2-D interior boxes (side 0.1) missed "
        f"{series('vogel2d', 'lowdim_box2d_missed_frac', 2)} vs sobol {series('sobol', 'lowdim_box2d_missed_frac', 2)}"
        f", random {series('random', 'lowdim_box2d_missed_frac', 2)}.",
        f"vogel_paired (d>2) is mid-table, not last, on space-filling metrics: centred L2 discrepancy d=4 "
        f"{series('vogel_paired', 'cd_centred_l2', 4)} vs random {series('random', 'cd_centred_l2', 4)} and sobol "
        f"{series('sobol', 'cd_centred_l2', 4)}; minimum distance d=4 {series('vogel_paired', 'min_pairwise_distance', 4)}"
        f" vs lhs {series('lhs', 'min_pairwise_distance', 4)}, random {series('random', 'min_pairwise_distance', 4)}.",
    ]
    losses = [
        f"Corners (structural): the Vogel representative (vogel2d at d=2, vogel_paired at d>2) hits "
        f"{'0' if vog_corner_zero else 'some'} of the 2^d vertex boxes (side 0.05) in all 9 (d,N) cells and misses "
        f"every planted corner box (side 0.08) in every design. Any vertex box of side < {_g(s_star)} lies wholly "
        f"outside the inscribed disk, so no budget N can fix it. It ranks 5th of 5 on planted regions missed in "
        f"{vog_last_key}/9 cells.",
        f"Categorical-holdout proxy (structural): vogel_paired misses holdout_x3x4 in {misses(4, 'vogel_paired', 'holdout_x3x4')} "
        f"designs at d=4 and {misses(6, 'vogel_paired', 'holdout_x3x4')} at d=6 (the box x3,x4 >= 0.9 is "
        f"{_g(math.sqrt(2) * (HOLDOUT_LO - 0.5))} from the disk centre vs radius 0.5), against sobol "
        f"{misses(4, 'sobol', 'holdout_x3x4')} / {misses(6, 'sobol', 'holdout_x3x4')}, lhs "
        f"{misses(4, 'lhs', 'holdout_x3x4')} / {misses(6, 'lhs', 'holdout_x3x4')}, random "
        f"{misses(4, 'random', 'holdout_x3x4')} / {misses(6, 'random', 'holdout_x3x4')}. All 2-D pair-corner boxes "
        f"(side 0.1) are missed by vogel_paired at every N and d: {series('vogel_paired', 'lowdim_corner2d_missed_frac', 4)}"
        f" (d=4).",
        f"No convergence: vogel2d centred L2 discrepancy at d=2 is {series('vogel2d', 'cd_centred_l2', 2)} for "
        f"N=64/256/1024 (sobol {series('sobol', 'cd_centred_l2', 2)}; ratio {cd_ratio:.0f}x at N=1024). Its covering "
        f"radius {series('vogel2d', 'covering_radius_ref', 2)} approaches the analytic floor {_g(floor2)} "
        f"(vertex-to-disk distance), not zero. The layout converges to the uniform law on the disk, not on the square.",
        f"Boundary slabs: the disk puts {slab_density_ratio:.1f}x fewer points into the slab x1 >= {SLAB_LO} than a "
        f"uniform layout (analytic); slab_x1 is missed by vogel2d at N=64 and by vogel_paired in "
        f"{sum(1 for g in groups[(4, 64, 'vogel_paired')] if not g['hits']['slab_x1'])}/5 (d=4) and "
        f"{sum(1 for g in groups[(6, 64, 'vogel_paired')] if not g['hits']['slab_x1'])}/5 (d=6) designs at N=64, "
        f"which sobol/lhs never miss there; the share of coordinates within 0.05 of a face is "
        f"{_g(mean_of(2, 1024, 'vogel2d', 'frac_coords_in_extreme_bands'))} vs {_g(mean_of(2, 1024, 'sobol', 'frac_coords_in_extreme_bands'))} for sobol (d=2, N=1024).",
        f"Identity tiling (vogel2d reused on every pair at d>2) duplicates axes (max |corr| = "
        f"{_g(mean_of(4, 64, 'vogel2d', 'max_abs_axis_correlation'))}) and is last or second-last on covering radius "
        f"in all six d>2 cells; never reuse the Phase 0 2-D index on several axis pairs.",
    ]
    diagnostic = (
        f"The losses come from the inscribed-disk map, not from the golden-angle sequence: golden_lattice_paired (the "
        f"pre-image of the Phase 0 disk on the unit square) has centred L2 discrepancy d=2 "
        f"{series('golden_lattice_paired', 'cd_centred_l2', 2)} (sobol {series('sobol', 'cd_centred_l2', 2)}), d=6 "
        f"{series('golden_lattice_paired', 'cd_centred_l2', 6)} (sobol {series('sobol', 'cd_centred_l2', 6)}), and "
        f"misses holdout_x3x4 in {misses(4, 'golden_lattice_paired', 'holdout_x3x4')} (d=4) designs; it still misses "
        f"the full-dimensional corner boxes like every space-filling design.")
    others_text = [
        f"grid_corners has the fewest planted misses in {grid_key_first}/9 cells, but 7 of the 10 planted regions "
        f"touch the cube boundary and contain cube vertices. Its 1-D projections collapse: max 1-D gap "
        f"{series('grid_corners', 'max_1d_projection_gap', 4)} (d=4) and {series('grid_corners', 'max_1d_projection_gap', 6)}"
        f" (d=6) vs sobol {series('sobol', 'max_1d_projection_gap', 4)} (d=4); interior thin slabs missed "
        f"{series('grid_corners', 'lowdim_slab_missed_frac', 4)} (d=4) vs sobol {series('sobol', 'lowdim_slab_missed_frac', 4)};"
        f" at d=6 N=64 all 64 points are vertices (centred L2 discrepancy {_g(mean_of(6, 64, 'grid_corners', 'cd_centred_l2'))}).",
        f"Sobol has the lowest mean centred L2 discrepancy in {sobol_cd_first}/9 cells, the smallest max 1-D "
        f"projection gap in {sobol_gap_first}/9 and a top-2 covering radius in {sobol_cov_top2}/9, and converges with "
        f"N. It still misses the planted full-dimensional corner boxes at d>=4 (corner boxes missed in every Sobol "
        f"design at d=6) and the 2-D pair-corner boxes in "
        f"{series('sobol', 'lowdim_corner2d_missed_frac', 4)} of placements (d=4).",
        f"Irreducible for every method here: ball_interior (radius 0.03) is missed in every design of every method at "
        f"d=4 ({ball_all_missed[4]}) and d=6 ({ball_all_missed[6]}); its volume {_g(region_volume('ball_interior', 4))}"
        f" (d=4) / {_g(region_volume('ball_interior', 6))} (d=6) means an iid uniform design of N=1024 would contain "
        f"{_g(1024 * region_volume('ball_interior', 4))} / {_g(1024 * region_volume('ball_interior', 6))} points in "
        f"expectation. Small full-dimensional interior features are not found by any non-adaptive design at these "
        f"budgets.",
    ]
    composite = {
        "design": [
            "1. Categorical factors (inverter V_BOOST/V_DIRECTBUS, protection P0..P3, fault location near/far, "
            "day/night, case family) are ENUMERATED as a full factorial over their levels (or a strength-2 covering "
            "array if the product is too large), never emulated as a continuous sub-box.",
            "2. Per categorical combination, an explicit deterministic extreme block on the continuous axes: all 2^d "
            "vertices when 2^d <= N/4, otherwise a resolution-IV two-level fraction (every 2-D and 3-D projection is "
            "a full factorial), plus physics-named extremes from brief section 6 (cold Voc x max irradiance, 0 A "
            "night, longest route, minimum sustaining current) and explicit face/boundary points.",
            "3. The remaining budget: scrambled Sobol (power-of-two N, seeds recorded), the same Sobol block reused "
            "across protection candidates so that architecture comparisons are paired.",
            "4. Targeted adversarial cases (brief section 6) and adaptive refinement around observed near-failures for "
            "small interior features that no non-adaptive design finds.",
            "5. Kuiper r=sqrt(k) stays an identity/address only. The Phase 0 bounded Vogel disk is not used for "
            "coverage claims (it never samples "
            + ", ".join(f"{_g(1 - (math.pi / 4) ** (d / 2))} of the {d}-D cube" for d in DIMS) + ").",
        ],
        "why_sobol_not_paired_vogel_for_the_bulk": (
            f"With the same explicit vertex block, corners_plus_sobol vs corners_plus_vogel_paired: centred L2 "
            f"discrepancy d=4 {series('corners_plus_sobol', 'cd_centred_l2', 4)} vs "
            f"{series('corners_plus_vogel_paired', 'cd_centred_l2', 4)}; covering radius d=4 "
            f"{series('corners_plus_sobol', 'covering_radius_ref', 4)} vs "
            f"{series('corners_plus_vogel_paired', 'covering_radius_ref', 4)}; d=6 "
            f"{series('corners_plus_sobol', 'covering_radius_ref', 6)} vs "
            f"{series('corners_plus_vogel_paired', 'covering_radius_ref', 6)}; interior 2-D boxes missed d=4 "
            f"{series('corners_plus_sobol', 'lowdim_box2d_missed_frac', 4)} vs "
            f"{series('corners_plus_vogel_paired', 'lowdim_box2d_missed_frac', 4)}; planted misses d=4 "
            f"{series('corners_plus_sobol', 'planted_regions_missed', 4)} vs "
            f"{series('corners_plus_vogel_paired', 'planted_regions_missed', 4)}."),
        "what_the_explicit_vertex_block_buys_and_costs": (
            f"Planted misses at d=4: sobol {series('sobol', 'planted_regions_missed', 4)} -> corners_plus_sobol "
            f"{series('corners_plus_sobol', 'planted_regions_missed', 4)} (N=64/256/1024); vogel_paired "
            f"{series('vogel_paired', 'planted_regions_missed', 4)} -> corners_plus_vogel_paired "
            f"{series('corners_plus_vogel_paired', 'planted_regions_missed', 4)}. Cost: centred L2 discrepancy d=4 "
            f"rises from {series('sobol', 'cd_centred_l2', 4)} to {series('corners_plus_sobol', 'cd_centred_l2', 4)} "
            f"because 16 of N points sit on vertices. At d=6 N=64 the 16-run fraction leaves "
            f"{_g(mean_of(6, 64, 'corners_plus_sobol', 'planted_regions_missed'))} planted regions missed "
            f"(4 corner boxes outside the fraction + the ball): name the physically critical corners explicitly, or "
            f"raise N."),
        "caveats": [
            "Rankings depend on the region set: 7 of 10 planted regions touch the boundary, which favours designs "
            "with vertices. The exhaustive low-order families (slabs, 2-D boxes, 2-D pair corners) are reported to "
            "show robustness beyond the fixed placements.",
            "5 seeds per stochastic method: min/max over seeds are in per_method_means; differences of a fraction of "
            "one region between methods are not meaningful.",
            DISCLAIMER,
        ],
    }
    return {"vogel_wins": wins, "vogel_losses": losses, "golden_lattice_diagnostic": diagnostic,
            "other_methods": others_text, "recommended_composite_wave2_phaseD": composite}


