# Leapfrog string wiring - research and argument review

## Status

Engineering review of the supplied leapfrog drawings and spreadsheets, the Trina module geometry used by V11, and published PV wiring guidance. This document separates four different claims that must not be conflated:

1. reduced purchased field PV wire;
2. reduced total installed conductor;
3. reduced cost;
4. reduced conductive-loop area and lightning/EMI exposure.

They are not equivalent.

## Supplied material reviewed

- `Leapfrog.xlsx`
- `Leapfrogv2(5).xlsx`
- `Leapfrogv3(2).xlsx`
- `Leapfrog String Connections(1).pdf`
- `Leapfrog String Connections Detail(1).pdf`
- Trina TSM-DEG21C.20 module data used by the project

The overall connection drawing correctly communicates the main architectural purpose: both free string ends can be brought to the inverter/combiner side. The detail drawing shows alternating long inter-module arcs and two polarity paths, but it is not dimensioned and therefore cannot establish manufacturable lead lengths by itself.

## What external guidance supports

### 1. Both poles at one end can reduce purchased field PV wire

Yaskawa-Solectria describes leapfrog wiring as a way to locate both poles of a PV source circuit at roughly the same point. Where module wire whips are already long enough, it reports a reduction of roughly 30-60 ft of field PV wire per source circuit compared with daisy-chain wiring. Its argument is explicitly an installed-BOS material and labour argument, especially when combined with Y-connectors.

Source: https://www.solectria.com/blog/using-y-connectors-in-string-inverter-systems-part-ii/

This supports the statement:

> Leapfrog can reduce separately installed home-run PV wire.

It does not, by itself, prove that total copper or total conductor length is reduced when the customer must pay for substantially longer factory-fitted module leads.

### 2. Minimising conductive-loop area is a strong and independent justification

IEC 62548 wiring guidance requires or recommends array wiring to minimise conductive-loop area to reduce lightning-induced overvoltage. Schneider Electric's Electrical Installation Guide, Phoenix Contact's PV lightning guidance, and IEA PVPS lightning guidance all repeat the same physical principle: a PV string circuit forms a loop/antenna, and the larger its enclosed area, the more energy can be electromagnetically coupled into it.

Sources:

- https://webstore.iec.ch/en/publication/64171
- https://www.electrical-installation.org/enwiki/Photovoltaic_architectures_-_common_characteristics
- https://www.phoenixcontact.com/en-gb/products/surge-protection/surge-protection-for-photovoltaic-systems
- IEC TS 62738: https://webstore.iec.ch/en/publication/26942

This supports the statement:

> Leapfrog is potentially valuable when it causes the outgoing and return portions of the DC circuit to remain close together and demonstrably reduces enclosed loop area.

The benefit is not automatic. A poor physical installation with long separated or coiled leads can defeat the topology's intended loop-area advantage.

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

If repeated over most of a 30-module string, nearly one metre of reserve per mated pair can create a large quantity of excess cable. Excess cable must not be coiled into loops; lightning/EMI guidance recommends minimising loops, and research on induced currents recommends avoiding coils and using controlled routing where excess cannot be eliminated.

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
13. excess lead length and its routing method.

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
- O&M replacement strategy for non-standard modules.

## Conclusion

Leapfrog is a legitimate and deployed PV wiring method. Its strongest engineering case is presenting both string ends together and enabling low-loop-area routing. Its strongest commercial case is reducing separately installed field PV wire and associated labour.

It should not be sold as an automatic total-copper or total-conductor saving. Under the supplied 0.84 m / 1.89 m lead assumptions, the leapfrog string contains 23.76 m more total conductor than the conventional string, before accounting for practical slack. The financial result depends on the relative prices and resistances of custom 4 mm2 factory leads and removed 6 mm2 field cable, not on field-cable metres alone.