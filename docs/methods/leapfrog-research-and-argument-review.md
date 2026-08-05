# Leapfrog string wiring - research and argument review

## Status

Engineering review of the supplied leapfrog drawings and spreadsheets, the Trina module geometry used by V11, licensed IEC standards, a confidential project Employer's Requirements document, and published PV wiring guidance. This document separates four different claims that must not be conflated:

1. reduced purchased field PV wire;
2. reduced total installed conductor;
3. reduced cost;
4. reduced conductive-loop area and lightning/EMI exposure.

They are not equivalent.

## Evidence handling

The IEC publications used for this review are licensed single-user copies. Their technical conclusions and clause references may inform the engineering method, but their copyrighted text and figures are not reproduced in this repository.

The project Employer's Requirements reviewed are confidential. They are used only as evidence that leapfrog wiring has been expressly specified on a real utility-scale UK project. No confidential project text, drawings, commercial terms or identifying extracts are reproduced here.

## Supplied material reviewed

- `Leapfrog.xlsx`
- `Leapfrogv2(5).xlsx`
- `Leapfrogv3(2).xlsx`
- `Leapfrog String Connections(1).pdf`
- `Leapfrog String Connections Detail(1).pdf`
- Trina TSM-DEG21C.20 module data used by the project
- IEC 62548-1:2023, licensed copy
- IEC TS 62738:2018, licensed copy
- confidential utility-scale solar Employer's Requirements

The overall connection drawing correctly communicates the main architectural purpose: both free string ends can be brought to the inverter/combiner side. The detail drawing shows alternating long inter-module arcs and two polarity paths, but it is not dimensioned and therefore cannot establish manufacturable lead lengths by itself.

## What the licensed standards and project evidence support

### 1. Minimum loop area is an explicit IEC design objective

IEC 62548-1:2023 requires array wiring to be arranged with positive and negative conductors of the same string together and to avoid the creation of loops. Its wiring-system provisions include examples of string wiring with minimum loop area. This is direct standards support for treating the physical outgoing-and-return geometry as an engineering quantity rather than merely a drawing convention.

This supports the statement:

> A leapfrog arrangement is valuable when it demonstrably keeps the two poles close together and reduces enclosed conductive-loop area.

The standard does not say that the topology label alone guarantees a smaller loop. V11 must calculate the actual routed geometry.

### 2. Long DC routes and electrical distance matter to surge protection

IEC 62548-1:2023 requires a lightning-transient risk assessment based on maximum route length between the PCE and module connection points and provides a critical-length method for determining when DC-side SPDs are required. It also recommends protective measures for long DC cables, including shielding, burial, metallic containment or SPDs.

IEC TS 62738:2018 states that the effectiveness of lightning protection depends on electrical distance between the protective device and the modules. It specifically notes reduced effectiveness for longer outlying strings and identifies additional SPDs along string cabling as one possible means of increasing protection.

These provisions support V11 reporting:

- route length by string;
- loop area;
- conductor separation;
- electrical distance to SPD locations;
- propagation delay and distributed parameters.

They do not establish that leapfrog alone removes the need for an SPD or proves a specific transient reduction.

### 3. Leapfrog has contractual utility-scale deployment evidence

The confidential Employer's Requirements expressly require factory-fitted module leads long enough for series interconnection in a leapfrog arrangement. This is strong evidence that leapfrog is not merely a theoretical or marketing topology: it has been specified contractually for a major UK utility-scale solar project by an independent engineering adviser.

Because the source is confidential, the public repository records only this bounded conclusion and does not reproduce the project wording or identify the document.

### 4. Both poles at one end can reduce purchased field PV wire

Published industry guidance describes leapfrog wiring as a way to locate both poles of a PV source circuit at roughly the same point. Where module wire whips are already long enough, it can reduce separately installed field PV wire per source circuit.

This supports the statement:

> Leapfrog can reduce separately installed home-run PV wire.

It does not, by itself, prove that total copper or total conductor length is reduced when the customer must pay for substantially longer factory-fitted module leads.

## Exact geometric argument

Let:

- `N` = number of modules in the string;
- `p` = physical module pitch;
- `s` = separation of the two relevant junction-box cable roots;
- modules remain fixed at positions M1 ... MN.

For an even-numbered string, the authorised leapfrog order is:

`M1, M3, M5, ... M(N-1), MN, M(N-2), ... M2`.

There are `N-2` skipped-module transitions and one adjacent far-end crossover. Relative to sequential wiring, the total ideal internal inter-module span increases by:

`Delta_internal = (N - 2) * p`.

The return conductor needed to bring the far sequential free end back to the near side is longer than the leapfrog return by the same ideal distance:

`Delta_home_run = (N - 2) * p`.

Therefore, in an ideal one-dimensional geometry with leads cut to the minimum required span:

`Delta_total_conductor = Delta_internal - Delta_home_run = 0`.

This is the central correction to simplistic copper-saving claims. Leapfrog relocates conductor from separately installed field cable into factory-fitted module leads. It does not inherently make the complete electrical circuit shorter.

Real designs can move slightly above or below this ideal equality because of connector approach, module-end offsets, inverter location, routing lanes, slack, bend radius and unequal positive/negative roots. Those terms must be modelled explicitly rather than hidden inside a generic savings percentage.

## Review of the supplied spreadsheets

### `Leapfrogv3(2).xlsx`

The workbook compares:

- conventional module leads: 0.35 m positive and 0.28 m negative per module;
- proposed leapfrog leads: 0.84 m positive and 1.89 m negative per module;
- one removed 6 mm2 field return of 39.24 m.

For 30 modules:

- conventional factory lead total = `30 * (0.35 + 0.28) = 18.90 m`;
- conventional field return = `39.24 m`;
- conventional total = `58.14 m`;
- leapfrog factory lead total = `30 * (0.84 + 1.89) = 81.90 m`;
- leapfrog field return = `0 m`;
- leapfrog total = `81.90 m`.

The proposed leapfrog case therefore uses:

`81.90 - 58.14 = 23.76 m`

more total conductor per string under the workbook's own assumptions.

The row labelled `Saving m = 23.76` is consequently mislabelled. It is an additional total conductor quantity, not a length saving.

The workbook nevertheless derives a small monetary saving because it assumes:

- 6 mm2 string cable: about 0.80 currency units/m;
- 4 mm2 factory cable: about 0.60 currency units/m.

Its arithmetic is effectively:

- avoided 6 mm2 cost: `39.24 * 0.80 = 31.392`;
- added 4 mm2 cost: `63.00 * 0.60 = 37.800`;

which actually gives a net cost increase of 6.408 if the signs are applied conventionally. The displayed `Saving $ = 6.408` reverses that interpretation. The commercial conclusion is therefore not reliable without a clean cost model and confirmed module-option pricing.

### `Lengths estimate` sheet

This sheet reports approximately 1,975 m/MWp of cable saving and about EUR1.106 million over 700 MW. It compares only separately installed near-end/far-end field routes. It does not include:

- the additional factory-fitted module-lead conductor;
- the price premium charged by the module manufacturer;
- extra copper mass and embodied material;
- lead management/clipping labour;
- transport and packaging effects;
- replacement-module/O&M stocking implications;
- excess-lead handling.

It is therefore a field-PV-wire procurement estimate, not a complete cable, copper, CAPEX or LCOE comparison.

### Connector descriptions

The workbook text that equates positive/negative polarity directly with male/female pins should not be used as engineering authority. Connector contact gender, housing presentation and polarity marking must follow the exact Stäubli/Trina connector documentation and the delivered module configuration. V11 should identify logical positive and negative terminals separately from connector housing/contact gender until manufacturer evidence is attached.

## Review of 1.4 m + 1.4 m leads

Using the project geometry:

- module width = 1.303 m;
- module gap = 0.030 m;
- pitch `p = 1.333 m`;
- assumed junction-box root separation `s = 0.840 m`.

The straight combined reach required for a skipped-module connection is:

`D = 2p - s = 1.826 m`.

Two 1.4 m leads provide 2.8 m combined usable length, giving 0.974 m straight reserve. This is sufficient, but it is also substantially oversized relative to the ideal geometric requirement.

If repeated over most of a 30-module string, nearly one metre of reserve per mated pair can create a large quantity of excess cable. Excess cable must not be coiled into loops because that can undermine the IEC minimum-loop-area objective.

The correct procurement objective is not merely `long enough`. It is:

> the shortest manufacturable pair of leads that satisfies the worst-case connector-to-connector route, bend-radius, clipping, tolerance and installation-access requirements with a declared reserve.

## Arguments that remain defensible

### Strong arguments

1. Both free string ends can be presented near the same inverter/combiner side.
2. Separately installed field PV wire and field terminations can be reduced.
3. Positive and negative home runs can be routed together more consistently.
4. The topology can reduce conductive-loop area when the actual lead routes are kept close and verified geometrically.
5. Reduced loop area can reduce susceptibility to lightning-induced overvoltage and EMI.
6. Installation repeatability may improve when the module and cable-routing system is designed specifically for the topology.
7. The arrangement has documented contractual deployment in utility-scale UK solar.

### Conditional arguments

1. Lower CAPEX - only after manufacturer lead-option premium, field wire, labour, clips and O&M spares are included.
2. Lower resistive loss - only if the resistance of the longer 4 mm2 factory leads plus connectors is below the removed field-cable resistance.
3. Lower copper mass - not established and often unlikely where leads are substantially oversized.
4. Lower total conductor length - not inherent; ideal geometry is approximately neutral, while the supplied 0.84/1.89 m case increases total length.
5. Improved surge performance - plausible through loop-area reduction, but it requires explicit geometry and transient analysis rather than topology labels alone.

### Arguments that should be withdrawn

1. `Leapfrog inherently saves large quantities of total copper.`
2. `The field-home-run reduction equals total cable saving.`
3. `A 1.4 m lead is sufficient because it exceeds one module width.`
4. `Longer leads automatically reduce loop area.`
5. `The spreadsheet's EUR700 MW saving is bankable without module-option pricing and installation evidence.`
6. `Leapfrog compliance alone proves adequate lightning protection.`

## Required V11 method

V11 should calculate and report separately:

1. standard factory-lead length by polarity;
2. leapfrog factory-lead length by polarity;
3. number of mated inter-module connections;
4. two free string leads;
5. external positive and negative route lengths;
6. conductor cross-section and declared resistance for every segment;
7. connector count and resistance;
8. total conductor metres by cross-section;
9. copper mass by cross-section;
10. installed cost by component class;
11. positive/negative route vertices;
12. signed and absolute loop area;
13. excess lead length and its routing method;
14. maximum PCE-to-module route length used for the IEC critical-length test;
15. SPD locations and electrical distance to the protected modules.

The software must expose at least four different outputs:

- field PV wire saving;
- total conductor difference;
- copper-mass difference;
- installed-cost difference.

No one of these may be labelled simply `cable saving`.

## Release conditions

Before a project or purchase-order conclusion is issued, obtain:

- dimensioned rear module/J-box drawing;
- positive and negative cable-root coordinates;
- usable lead measurement datum;
- connector mating and bend-radius requirements;
- manufacturer quote for each custom lead option;
- confirmed conductor construction and resistance;
- sample-module first-article fit test;
- installed routing/clipping trial;
- loop-area comparison from explicit route vertices;
- resistance/loss comparison using declared cable data;
- project lightning ground-flash density;
- IEC 62548-1 critical-length assessment;
- SPD coordination and electrical-distance assessment;
- O&M replacement strategy for non-standard modules.

## Conclusion

Leapfrog is a legitimate and deployed PV wiring method. Its strongest engineering case is presenting both string ends together and enabling low-loop-area routing, directly aligned with IEC wiring principles. Its strongest commercial case is reducing separately installed field PV wire and associated labour.

It should not be sold as an automatic total-copper or total-conductor saving. Under the supplied 0.84 m / 1.89 m lead assumptions, the leapfrog string contains 23.76 m more total conductor than the conventional string, before accounting for practical slack. The financial result depends on the relative prices and resistances of custom 4 mm2 factory leads and removed 6 mm2 field cable, not on field-cable metres alone.