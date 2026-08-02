# V11 module-layout placement study

## Purpose

This study defines an independently implemented module-placement engine for the V11 browser. It does not copy OpenSolar code, page structure, imagery, proprietary algorithms or protected interface elements.

Public OpenSolar documentation was reviewed only to identify ordinary product capabilities that users expect from solar-layout software: manual module placement, rectangular filling, portrait or landscape orientation, row and column gaps, alternating-row offsets and row-based stringing. OpenSolar's published terms prohibit downloading, aggregating, mirroring or incorporating its site without permission, so V11 uses only general geometric concepts and original code.

## V11 design boundary

The first layout authority is a two-dimensional local-coordinate plane measured in metres. A layout contains one rectangular buildable boundary, zero or more rectangular exclusion obstacles and a set of uniquely identified modules. Every module has an x/y centre, width, height, rotation and optional string identifier.

The engine must support deterministic rectangle fill, manual movement, snapping, portrait/landscape rotation, alternating-row offsets, collision detection, boundary validation, obstacle exclusion and automatic string assignment. Every operation returns a complete immutable layout value rather than mutating hidden browser state.

## Geometry laws

A module is represented as an axis-aligned footprint after applying either zero or ninety-degree rotation. A valid module footprint must lie wholly inside the buildable boundary, must not intersect an obstacle and must not overlap another module. Edge touching is allowed; positive-area overlap is not.

Rectangle fill starts at a defined origin and advances in columns and rows using module dimensions plus explicit gaps. Alternating rows may be offset by half a module pitch or a user-selected distance. Candidate modules that do not fit are omitted rather than clipped.

Manual movement uses deterministic snapping. Coordinates are rounded to the nearest configured grid interval before validation. A failed move returns a structured error and leaves the prior layout unchanged.

Automatic string assignment sorts valid modules by row and then horizontal position. Rows may be traversed consistently left-to-right or as a snake. Modules are divided into strings of a requested maximum length without changing their physical positions.

## Relationship to the inverter-block model

The laboratory reference inverter block remains 24 strings by 30 modules. The placement engine is designed to create or edit the physical coordinates of those 720 modules. Later integration will derive string routes and electrical traversal from these coordinates rather than accepting aggregate cable lengths.

## Evidence state

This unit proves computational geometry and browser behaviour only. It does not yet model terrain, shading, roof planes, geospatial projections, structural loading, tracker kinematics or planning setbacks. Those remain future bounded capabilities.
