# V11.2 Engineering Spawn Specification

## Part I — Vision, Architecture, History and Design Philosophy

**Document class:** Quantum Spawn / canonical engineering handover  
**Timestamp:** 2026-08-05 17:41 CEST  
**Version:** 1.0 — Part I of IV  
**Programme:** Ventus Ltd Solar Electrical Topology Analysis Engine  
**Repository:** `Ventusltd/v11`  
**Active drawing branch:** `build/v11.2-full-array-sld`  
**Primary build:** `v11.2/`  
**Dependencies:** read-only V8 visual reference; V11 electrical-graph work; Trina TSM-DEG21C.20 manufacturer datasheet  
**Topics:** programme vision, authority boundaries, version history, drawing philosophy, module geometry, connector accounting, success criteria  
**Authority:** this document records the governing intent for V11.2. Where code, browser output or later commentary conflicts with it, the conflict must be identified and resolved deliberately rather than silently normalised.

---

## 1. Purpose of this Quantum Spawn

This document is the first part of a four-part engineering spawn specification for the Solar Electrical Topology Analysis Engine. It exists so a new ChatGPT thread, coding agent, engineer or reviewer can continue the V11.2 programme without reconstructing its intent from a long conversation history.

It is not a transcript. It is not a marketing summary. It is not an attempt to defend every intermediate browser experiment. It is a canonical engineering handover: a statement of what the programme is trying to become, why V11.2 now exists separately from the earlier V11 workbench, which technical boundaries must remain intact, and which failure modes must not be repeated.

The central problem is straightforward to state but easy to obscure:

> A utility-scale solar DC string is not merely a count of modules joined in series. It is a physical electrical installation composed of module junction-box terminals, factory leads, connector ends, mating interfaces, string cables, inverter sockets, routes, dimensions, polarity, evidence and engineering consequences.

Many solar design tools simplify this physical layer into string counts, module blocks, route lengths or abstract polylines. Those abstractions are useful for high-level design, but they hide the part of the system where installation errors, connector mismatch, excess lead management, cable resistance, voltage drop, loop area, induced surge exposure, water ingress, mechanical damage and commissioning ambiguity occur.

The programme exists to make that hidden physical DC layer explicit and traceable.

The long-term ambition remains broad: a deterministic, evidence-backed topology engine capable of representing complete inverter blocks and eventually larger solar electrical systems as typed components, electrical graphs, physical routes, earthing networks and derived calculations.

The immediate V11.2 ambition is narrower by design:

> Reproduce the electrical clarity of the V8 Sequential and Leapfrog connection drawing, then replicate that exact drawing language across the complete 24-string inverter block on one full-screen engineering plane.

V11.2 therefore establishes the drawing authority first. Every module, junction-box terminal, factory lead, connector end, mating interface, string cable and inverter termination must become visible and traceable. Analytical expansion must not again be allowed to obscure the drawing.

---

## 2. Governing programme thesis

The programme is governed by three statements:

**Topology defines what connects. Geometry defines where conductors run. Physics operates on explicit paths.**

These statements must remain separate because they answer different engineering questions.

Topology answers:

- Which positive connector end mates with which negative connector end?
- Which module is electrically before and after another module?
- Which two connector ends form one detachable mating interface?
- Which free string end connects to which string cable?
- Which string cable terminates at which inverter DC socket?
- Which physical DC input belongs to which MPPT?
- Does the string form exactly one continuous, unbranched series circuit?

Geometry answers:

- Where is each module physically positioned?
- Where is the module junction-box and cable-exit datum?
- Where do the two factory leads run?
- Where are connector ends located relative to the module?
- What route does each field conductor follow?
- What is the length of each route segment?
- What circuit loop is enclosed by the positive and negative conductor paths?
- Can a proposed Leapfrog mating pair physically reach without extensions, tension, prohibited bending or unmanaged excess cable?

Physics depends on both. Resistance needs conductor material, cross-section, temperature and length. Voltage drop and I²R loss need current and resistance. Propagation delay needs path length and dielectric assumptions. Surge, EMC and induced-voltage analysis need conductor separation and loop geometry. None of these values should be derived from a decorative browser line whose coordinates were selected merely to make a page look tidy.

The intended authority stack is therefore:

1. Evidence-backed component definitions.
2. Authoritative electrical topology graph.
3. Authoritative physical routing geometry.
4. Separate earthing and bonding graph.
5. Derived engineering calculations.
6. SVG, browser, JSON, CSV, schedules and reports as projections of the same state.

The browser sits at the bottom of the authority chain. It displays engineering state. It does not invent engineering state.

V11.2 is primarily a drawing projection, but it must remain faithful to the component and graph layers. Its function is not to replace the graph with graphics. Its function is to make the graph readable as an electrical installation.

---

## 3. Historical development and lessons

### 3.1 V7 — system overview

V7 demonstrated the value of showing a whole inverter block rather than one isolated example string. It made strings, MPPT grouping and physical organisation visible. Its strength was context: a reader could understand how individual strings belonged to the broader inverter architecture.

That whole-block context remains essential to V11.2. The final drawing cannot become a beautiful single-string example that abandons the 24-string requirement.

### 3.2 V8 — connection clarity

V8 established the successful visual language for module-level wiring. Its key achievement was not colour, polish or animation. Its achievement was that it showed actual module positions and actual connection consequences.

The physical module order remained fixed from M1 to M30. Sequential and Leapfrog were represented by changing the electrical connections, not by moving modules into a topology-friendly arrangement.

In Sequential wiring, adjacent modules are connected in electrical sequence. The two free string ends appear at opposite physical ends of the module row. Where both inverter inputs are at one side, one free end requires an additional far-end return conductor.

In Leapfrog wiring, the same M1–M30 physical row remains fixed. The electrical traversal proceeds through odd-numbered modules outward and even-numbered modules returning. Longer factory-lead interconnects cross over skipped modules, a far-end crossover changes direction, and both free string ends can be presented at the inverter side when the lead-length geometry is feasible.

V8 made this understandable in seconds because it drew separate leads, connectors and joins. It did not reduce the installation to a single line labelled “Sequential” or “Leapfrog”.

V11.2 adopts V8 as the visual reference language.

### 3.3 V10 — broader authority, weaker immediate drawing

V10 pursued a broader authority model, but its browser diagrams became more symbolic. The page could contain useful engineering concepts while being less effective for an installer or designer trying to answer the immediate question: which connector plugs into which connector?

This exposed a recurring danger: architectural sophistication can increase while the drawing becomes less operationally legible.

### 3.4 V11 — stronger engineering kernel and execution discipline

V11 recovered important engineering foundations:

- a dedicated repository and programme state;
- a pinned, read-only laboratory reference;
- deterministic build plans;
- Python and JavaScript simulation work;
- a 24-string, 12-MPPT reference inverter block;
- browser testing in real Chromium;
- public live deployment;
- exact-head CI evidence;
- explicit connector accounting;
- stable connector-end and mating-interface identities;
- graph-backed Sequential and Leapfrog mate differences;
- a connector inspector and machine-readable evidence.

These were substantial achievements. They should not be discarded.

However, the principal browser surface accumulated incompatible goals: array editing, calculations, diagnostics, topology strips, mobile controls, exports, route estimates and live-build monitoring. The page became a dashboard. To fit 24 strings, module rows became compressed. Logical traversal polylines replaced actual mating paths. Text explained details that the drawing should have shown.

The result was paradoxical: the data model became stronger while the main schematic became less like V8.

The lesson is decisive:

> A correct graph does not automatically produce a correct engineering drawing.

### 3.5 The V11.2 reset

V11.2 is the corrective reset. It is not a cosmetic restyle of the existing workbench. It is a separate drawing-only surface under `v11.2/` on branch `build/v11.2-full-array-sld`.

Its purpose is to prevent dashboard requirements from compromising the SLD.

V11 may continue to contain simulation, graph, validation and broader experimental capabilities. V11.2 is the dedicated electrical drawing surface that projects the verified graph across the complete inverter block.

---

## 4. V11.2 product scope

V11.2 has one primary job:

> Draw the complete DC electrical connection topology of one 24-string inverter block on one continuous, full-screen, SCADA-like SVG plane.

It should feel closer to electrical CAD, a protection schematic or a control-room display than to a consumer web application.

The reference boundary is:

- 24 strings;
- 30 modules per string;
- 720 modules;
- 12 MPPT groups;
- 2 strings per MPPT;
- 24 physical DC input pairs.

V11.2 should contain:

- one inverter representation with explicit DC input ownership;
- twelve MPPT group boundaries;
- twenty-four complete strings;
- fixed module positions M1–M30 within every string;
- centre-region junction-box and cable-exit geometry based on manufacturer evidence;
- both module junction-box terminals;
- both black factory leads;
- all module connector ends;
- all mating interfaces;
- two black string cables per string;
- inverter-side connector or socket ends;
- red and blue polarity markers at connector ends;
- stable IDs and measurable coordinates;
- minimal view controls: Sequential, Leapfrog, Fit Width and 100%.

V11.2 should not contain, before the drawing milestone is complete:

- metric-card dashboards;
- long technical commentary;
- generic widgets;
- layout packing;
- random module dragging;
- sales presentation content;
- decorative animation;
- physics panels;
- broad scenario tables;
- controls unrelated to drawing or inspection.

The primary success test is not whether the browser looks sophisticated. The test is whether an electrical engineer can trace every path without guessing.

---

## 5. Manufacturer geometry and evidence discipline

The reference module is the Trina Solar TSM-DEG21C.20 bifacial dual-glass module in the 645–665 W family, using the manufacturer datasheet Version `TSM_EN_2024_A` as the current public evidence basis.

The datasheet declares:

- module dimensions of 2384 × 1303 × 33 mm;
- 132 monocrystalline cells;
- an IP68-rated junction box;
- 4.0 mm² photovoltaic cable;
- portrait factory cable lengths of 350 mm and 280 mm;
- the ability to customise cable length;
- MC4 EVO2 / TS4 connector families, subject to regional specification;
- maximum system voltage of 1500 V DC;
- a 35 A maximum series fuse rating.

The page-two back-view drawing visually places the cable and junction-box region through the middle horizontal area of the portrait module. That is a stronger geometric basis than placing connectors at arbitrary module corners or edges for browser convenience.

The drawing evidence must nevertheless be interpreted carefully. The datasheet provides the overall module dimensions and nominal cable lengths, but it does not tabulate every coordinate needed for a manufacturing drawing. In particular, the exact junction-box root separation, exact lead-exit coordinates, delivered positive/negative side convention and connector contact gender are not fully established by the available sheet.

V11.2 must therefore distinguish:

- **manufacturer-declared dimensions:** authoritative metadata;
- **geometry visible in the manufacturer drawing:** evidence-backed drawing interpretation;
- **screen coordinates:** projection coordinates;
- **unpublished exact datums:** unresolved or provisional;
- **connector gender and exact regional configuration:** unverified until supported by the applicable manufacturer documentation.

The screen may enlarge connectors and lead separation to maintain legibility, but the transformation from actual millimetres to schematic coordinates must be documented. SVG elements should carry actual-dimension metadata even where the visible drawing is explicitly not to scale.

Manufacturer evidence always overrides browser convenience.

---

## 6. Component and graph authority

### 6.1 Typed physical objects

The component layer defines which physical objects exist. At minimum it must represent:

- photovoltaic module;
- module junction box;
- positive junction-box terminal;
- negative junction-box terminal;
- positive factory lead;
- negative factory lead;
- module connector ends;
- mated connector interfaces;
- positive string cable;
- negative string cable;
- string-cable connector ends;
- inverter DC connector or socket ends;
- physical DC input;
- MPPT group.

Every object requires a stable ID. A connector cannot be defined as “the red dot near M17”. The drawing object must resolve to the connector record, and the connector record must resolve to its owner, polarity, mate and path.

### 6.2 Complete-string connector accounting

For a string containing `N` modules:

- module connector ends = `2N`;
- string-cable connector ends = `4`;
- inverter connector or socket ends = `2`;
- complete-system connector ends = `2N + 6`;
- module-to-module mating interfaces = `N − 1`;
- module-to-string-cable interfaces = `2`;
- string-cable-to-inverter interfaces = `2`;
- total mating interfaces = `N + 3`.

For the 30-module reference string:

- 60 module connector ends;
- 4 string-cable connector ends;
- 2 inverter ends;
- 66 complete-system connector ends;
- 29 module-to-module mates;
- 2 module-to-string-cable mates;
- 2 cable-to-inverter mates;
- 33 mating interfaces;
- 33 positive/red connector-end markers;
- 33 negative/blue connector-end markers.

For the complete 24-string block:

- 720 modules;
- 1,440 module connector ends;
- 96 string-cable connector ends;
- 48 inverter connector ends;
- 1,584 complete-system connector ends;
- 696 module-to-module mating interfaces;
- 48 module-to-string-cable interfaces;
- 48 cable-to-inverter interfaces;
- 792 mating interfaces.

Sequential and Leapfrog have identical component and connector counts. They differ in the endpoint pairs of the module-to-module mating interfaces.

This invariant must be protected by tests.

### 6.3 Electrical graph authority

For each connector end, the authoritative graph should identify:

- connector-end ID;
- component owner;
- component class;
- polarity;
- marker colour;
- mate connector-end ID;
- mating-interface ID;
- interface class;
- string ID;
- electrical index where applicable;
- MPPT ID;
- physical DC input ID;
- evidence state.

The browser must not infer a mate from module adjacency, array order, label text or nearest-screen distance.

### 6.4 Drawing projection

V11.2 converts authoritative graph endpoints into SVG geometry.

The renderer may decide how a black cable path curves, which lane it occupies and how much vertical separation is needed to prevent overlap. It may not decide which endpoints are electrically connected.

Each visible mating path must carry its mating-interface ID and source/destination connector-end IDs. Both path ends must land on the corresponding connector DOM nodes.

This is the difference between an engineering projection and a cartoon.

---

## 7. Drawing philosophy

### 7.1 Show, do not explain

The schematic must communicate the topology visually.

A paragraph should not be needed to explain odd-outward/even-return Leapfrog wiring. The drawing should visibly show every longer skipped-module hop, the far-end crossover and the final return through the even modules.

Text should identify components and evidence. It must not compensate for absent connection geometry.

### 7.2 Accuracy before decoration

The priority order is:

1. Correct electrical endpoint pairs.
2. Correct stable identities.
3. Correct physical component ownership.
4. Correct manufacturer dimensions and datums.
5. Correct polarity markers.
6. Correct Sequential and Leapfrog topology.
7. Readable scale and cable-lane separation.
8. Visual polish.

Shadows, gradients and animations have no value if a connector lands on the wrong module.

### 7.3 Cable and polarity visual contract

All physical PV cable bodies are black in the primary SLD:

- module factory leads;
- module-to-module interconnects;
- positive and negative string cables.

Colour identifies polarity at connector ends and terminations only:

- red marker = positive;
- blue marker = negative;
- black path = physical PV cable;
- orange equipment block = inverter.

Connector or contact gender is a separate property and remains unverified until manufacturer evidence establishes it. Gender must never be inferred from red/blue polarity.

### 7.4 Fixed module geometry, changing electrical topology

M1–M30 remain in the same physical order in Sequential and Leapfrog views.

Only the mating endpoint pairs change.

Moving modules to make a topology easier to draw would conceal the actual geometric consequence and invalidate the comparison.

### 7.5 One continuous plane

The 24-string inverter block must exist on one continuous SVG plane.

The user may pan horizontally and vertically. The user may select Fit Width or 100%. The browser must not fragment the system into unrelated cards, widgets or hidden detail panels.

At all times the plane should preserve:

- inverter context;
- MPPT grouping;
- string identity;
- module order;
- connector identity;
- visible connection paths.

### 7.6 Evidence over confidence

Every manufacturer-sensitive or project-sensitive property requires an evidence state.

Examples include:

- module dimensions: manufacturer-declared;
- cable nominal lengths: manufacturer-declared;
- custom Leapfrog leads: project- or manufacturer-declared when obtained;
- exact J-box root coordinates: unresolved unless dimensioned evidence exists;
- connector gender: unverified;
- route vertices: schematic until project geometry is attached;
- first-article reach: untested until measured.

A convincing browser drawing must never upgrade an assumption into a fact.

---

## 8. Product identity and users

V11.2 is not another generic solar layout package. It is not attempting to compete primarily on roof packing, terrain optimisation, proposal generation or sales imagery.

Its product identity is the explicit physical DC electrical layer:

- real string topology;
- explicit module terminals;
- explicit connector ends;
- explicit mating interfaces;
- manufacturer-informed module geometry;
- black physical cable paths;
- explicit inverter terminations;
- traceable evidence;
- deterministic validation.

The intended users include:

- solar electrical designers;
- owner’s engineers;
- EPC electrical engineers;
- commissioning engineers;
- O&M engineers;
- cable and connector specialists;
- module and inverter manufacturers;
- technical investors and insurers investigating design and failure risk.

The distinctive promise is that a user can inspect the installation itself rather than only a summary abstraction.

---

## 9. Definition of success for the first V11.2 drawing milestone

The first drawing milestone succeeds when a competent engineer can open one full-screen plane and verify, without inspecting source code, that:

- the plane contains exactly 24 strings;
- each reference string contains exactly 30 modules;
- the strings are grouped into exactly 12 MPPTs;
- the inverter exposes 24 positive/negative DC input pairs;
- all 720 modules are present;
- every module shows a centre-region junction-box representation;
- every module exposes positive and negative terminals and connector ends;
- every factory lead is visible as a black cable;
- every module-to-module mating interface is visible as its own path;
- every string has two string cables;
- every string cable terminates visibly at the inverter;
- all 1,584 complete-system connector-end IDs are unique;
- all 792 mating-interface IDs are unique;
- every mating path resolves to two existing connector-end IDs;
- Sequential and Leapfrog preserve the same module and connector population;
- Sequential and Leapfrog use different module-to-module endpoint pairs;
- cable bodies remain black;
- positive markers are red;
- negative markers are blue;
- no single logical traversal polyline is presented as the actual wiring;
- the complete system remains readable through pan and zoom on desktop and mobile.

The milestone is not complete merely because the counts exist in JavaScript. The connections must be visibly legible and machine-verifiable.

---

## 10. Non-negotiable engineering laws

1. **Geometry is authoritative only when it has an explicit evidence basis.**
2. **Topology defines connectivity; the SVG does not.**
3. **The browser renders graph endpoints; it never invents mates.**
4. **Physics operates only on explicit conductor paths.**
5. **Module positions remain fixed between Sequential and Leapfrog.**
6. **V8 is the visual reference for connection clarity.**
7. **V11 graph work is retained as the data authority where verified.**
8. **V11.2 is drawing-only until the complete SLD is correct.**
9. **All physical PV cable bodies are black.**
10. **Red and blue identify connector polarity, not cable-jacket colour.**
11. **Connector gender is independent of polarity and cannot be guessed.**
12. **Every connector end and mating interface has a stable unique ID.**
13. **Every visible path terminates on exact connector objects.**
14. **No connection may be inferred from screen proximity or module order.**
15. **Manufacturer evidence overrides schematic convenience.**
16. **Unsupported properties remain explicitly provisional or unverified.**
17. **One full-screen plane replaces a collection of disconnected widgets.**
18. **Electrical and physical accuracy outrank decorative graphics.**
19. **The read-only V8 laboratory source must not be modified.**
20. **Paid IEC wording and confidential Employer’s Requirement prose must not be reproduced publicly.**
21. **One material change is followed by one validation and one reassessment.**
22. **No merge, readiness transition or programme-state advancement occurs without explicit owner authority.**

---

## 11. Handover instruction for a new thread

A clean successor thread should begin with:

> Read `docs/quantum-spawn/202608051741-v11-2-engineering-spawn-part-i.md` in `Ventusltd/v11` on branch `build/v11.2-full-array-sld`. Treat it as the canonical design intent for V11.2. Inspect the exact current branch head and CI before changing code. Continue the first incomplete V11.2 drawing target only. Do not resume dashboard, routing, calculation or earthing expansion until the complete V8-style 24-string SLD is correct and validated.

The successor must understand that V11.2 is not a rejection of the V11 engineering kernel. It is a correction of the presentation boundary. The data authority and the drawing authority must now reinforce one another:

- V11 supplies typed identities and verified electrical topology;
- V11.2 supplies the precise, full-array engineering drawing;
- later routing and physics layers may proceed only after both agree.

---

## 12. Part II boundary

Part II will define the electrical model in detail, including:

- connector-end naming and identity rules;
- mating-interface schemas;
- complete-string accounting;
- exact Sequential graph construction;
- exact Leapfrog graph construction;
- free-end and inverter-terminal conventions;
- module factory-lead evidence;
- lead-length feasibility mathematics;
- graph invariants and failure conditions.

Part I is complete when the programme’s reason, architectural separation and drawing philosophy are unambiguous. It does not authorise the next feature automatically. The next coding step must still be chosen from the exact branch state and validated evidence.