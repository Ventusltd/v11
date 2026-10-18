# Standards licensing controls — V11 PV protection research

**Status:** Mandatory conservative handling rule for this public GitHub research project. Applies to research notes, code, agent instructions, simulation inputs and GitHub Actions artefacts.

## Licensed reference access is not republication permission

The study owner has supplied IEC 62548-1:2023 (Edition 1.0) and IEC TS 62738:2018 (Edition 1.0) under documents visibly labelled **single-user** and **copyright-protected**. This V11 repository, including its GitHub Actions runner and public downloadable artefacts, is **not** an authorised redistribution channel for those publications.

Treat the exact contractual permission beyond the visible copyright/single-user notices as **unverified**; seek IEC or the authorised distributor's written clarification before any broader use or new automated redistribution workflow. This project intentionally follows the more restrictive approach below.

## Allowed research outputs for this repository

- Independently written original engineering analysis, physical equations, SPICE circuits, circuit test fixtures and manufacturer datasheet observations, with their own input provenance.
- Bibliographic references (standard designation, edition/year, title, public IEC catalogue URL) and targeted section identifiers to help the legitimate licence holder inspect the relevant text in their own licensed copy.
- High-level, original compliance questions and records such as 'working-voltage assumption', 'pollution degree unknown', 'IEC edition to check', 'external test evidence pending', 'HOLD'.
- Independently derived electrical numbers with clear assumptions, without replicating licensed standard tables or normative text.

## Prohibited without appropriate written permission / additional rights

- Commit, attach, mirror, publish, embed or link publicly to the supplied complete PDF files, page images, screenshots, diagrams, tables or substantial wording.
- Copy normative tables, numbered prescriptions, detailed IEC formula sheets, exact compliance limits copied from the licensed documents, or licence watermark/order information into source code, test fixtures, generated files, log output, issues, PR descriptions, wiki pages, public podcasts or hosted demos.
- Upload the licensed PDFs to GitHub, public object stores, GitHub Actions inputs/outputs, public search indexes, embeddings/vector databases or external agent workspaces.
- Treat access to the licence holder's PDFs as permission to redistribute documents to collaborators, bots, independent agents or third parties. Each relevant user's access rights must be confirmed separately.
- Share any full or partial machine-readable extracted transcription of a standard through this public repository.

## Required workflow

1. Use a licensed standard only as a restricted **reference**. Do not save its text to V11 or to public model input files.
2. Record standard number, edition, relevant section identifier, uncertainty and original engineering interpretation in a public *reference register*, not the section text itself.
3. Mark unexamined sources '**NOT EXAMINED**', including IEC 60664-1 or IEC 61730 when the actual licensed wording has not been reviewed. A public preview or manufacturer page is not a substitute for a complete normative document.
4. Keep a public engineering requirements matrix that describes **our own engineering design questions**, not a copied IEC requirements table. Direct the licence holder to consult their own authorised copy for exact requirements and values.
5. For circuit isolation/insulation, record measured voltage stresses, component datasheets, environmental parameters and pending independent review. Do not fabricate creepage/clearance dimensions, compliance claims or laboratory results.
6. Before a commit/PR/artifact release, review all newly added files and generated logs for copyrighted IEC excerpts, page graphics, copies of restricted PDFs or licensee identification. The automated guard below is only a limited defence, not proof of compliance.
7. Ask IEC/distributor for written permission when a contemplated extract, derived digital requirements database, shared agent context, training corpus, reproducible compliance table or public standards annex may exceed permitted use.
8. Do not assume a later IEC amendment or edition is covered by the two licensed publications supplied. Check edition applicability without distributing its content.

## Public standards register (bibliographic metadata only)

| Reference | Edition | Role in D2 module research | Source handling |
|---|---|---|---|
| IEC 62548-1, *Photovoltaic (PV) arrays — Part 1: Design requirements* | 2023-12 Ed. 1.0 | PV array design, module bypass/blocking diodes, safety and backfeed; relevant section locators include 7.2.11, 7.2.12, Annexes C, D, F and G | Licensed single-user copy; **no normative text in V11** |
| IEC TS 62738, *Ground-mounted photovoltaic power plants — Design guidelines and recommendations* | 2018-08 Ed. 1.0 | Context for restricted-access utility scale plant interfaces; distinct from product-level eFuse qualification | Licensed single-user copy; **no normative text in V11** |
| IEC 60664-1 | Applicable edition and amendment to confirm | Physical insulation coordination and dielectric test questions | Public bibliographic reference only; **licensed text not supplied** |
| IEC 61730-1 | Edition applicability to confirm | Module construction and safety qualification questions | Public bibliographic reference only; **licensed text not supplied** |

**Owner action required for standards compliance:** Obtain correct licences/permissions and review the applicable clauses through the owner's authorised channels; obtain qualified test-laboratory and independent engineering evaluation. This repo does not carry IEC standard content and the simulator does not confer compliance.

**No statement in this document is a legal determination about the owner's particular licence; when in doubt, do not publish the material.**
