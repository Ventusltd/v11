# Study: movable module geometry for the V11 inverter-block browser

## Purpose

This study defines an original V11 geometry and optimisation layer for moving photovoltaic modules while preserving the laboratory-derived 24-string inverter-block boundary.

The fixed electrical reference remains 24 strings, 30 modules per string, 720 modules, 475.2 kWp DC and one 352 kVA inverter. The new question is how physical placement changes conductor routing, string path length, loop-area proxies, worst-string exposure and later shading calculations.

## External products and permitted distillation

OpenSolar is used only as a public user-experience reference. Its public support material describes useful operator concepts including filling rectangular areas, changing row and column gaps, panel orientation, clearance, modules per row, alternating-row offsets and row-based manual stringing. V11 does not copy OpenSolar source code, visual assets, private APIs or proprietary algorithms. OpenSolar is not treated as an open-source dependency.

Public reference:
https://support.opensolar.com/hc/en-us/articles/12354276533647-How-to-design-commercial-projects-in-OpenSolar

pvlib-python is an open, BSD-3-Clause licensed photovoltaic modelling library. It may be evaluated later for solar position, irradiance, temperature and energy-yield calculations, but this first geometry study has no pvlib runtime dependency.

Public reference:
https://github.com/pvlib/pvlib-python

NREL's System Advisor Model documents array dimensions, external shading, self-shading, multiple subarrays and its 3D shade-calculator concepts. V11 may use those published physical concepts and may later evaluate the open SAM SDK, subject to explicit dependency and licence review. This study does not copy SAM implementation code.

Public references:
https://sam.nrel.gov/photovoltaic/
https://samrepo.nrelcloud.org/help/pv_shading.html

## Original V11 model

The first V11 placement engine creates deterministic coordinates for all 720 modules. String membership and module identity remain immutable while physical coordinates may change.

The initial mutation families are row shifts, bounded individual-module moves, physical-position swaps, staggered rows, compacted geometry and mixed operations.

Each candidate is rejected or heavily penalised if it creates physical collisions. Every evaluation confirms 720 unique module identities, 24 strings and 30 modules per string.

## Initial objective

The first objective combines complete electrical traversal distance, home-run distance to a declared inverter origin, a geometry-derived loop-area proxy and a prohibitive collision penalty.

Sequential and leapfrog traversals are evaluated over the same physical coordinates. This makes it possible to ask whether a physical move benefits one topology, both topologies or neither.

## Deliberate limitations

The first campaign does not yet model terrain surfaces, verified module keep-out polygons, tracker kinematics, solar-position shading, mismatch, bypass diodes, civil constraints, pile locations, trench obstacles or exact swept loop area.

Those are later layers. The immediate purpose is to establish a deterministic, testable geometry authority that the browser can use for drag-and-drop module movement.

## Browser direction

The intended browser interaction is to select a module, row or string; drag or enter a displacement; preserve or deliberately change string membership; reject collisions; redraw sequential and leapfrog traversal; update route, loop and worst-string metrics; and export the resulting layout and evidence state.

The Python study remains the reference implementation until JavaScript parity tests establish browser equivalence.

## Workflow

The `V11 Module Placement Study` workflow executes ten bounded jobs. Each job is hard-capped at five minutes and writes a separate evidence artefact.

The workflow explores independent seeds and mutation families rather than repeatedly executing one identical test.

## Success boundary

This study passes when all 720 module identities survive every campaign, all 24 string memberships remain valid, collisions are counted deterministically, repeated evaluation is byte-stable, every mutation family completes under the five-minute job limit and each job uploads a machine-readable candidate layout and metric report.

A passing study does not establish an optimal solar-plant layout. It establishes a trustworthy V11 module-placement kernel on which the working browser can be built.
