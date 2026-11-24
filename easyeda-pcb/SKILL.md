---
name: easyeda-pcb
description: Lead requirements intake and plan, design, edit, or review 2-, 4-, and 6-layer PCBs. Use for schematic design and PCB planning with or without an editor, EasyEDA Pro or Standard work, hardware references, prototype review, or fabrication and assembly handoff.
---

# EasyEDA PCB Design

Work from the user's requested stage and the available design evidence. For an existing board, identify its edition, source revision, and intended copper layer count before editing. When a new native EasyEDA project is requested and its edition is open, use Pro as the starting assumption. Preserve the user's layer count when feasible and explain any proposed change with the routing, return-path, mechanical, or fabrication constraint that drives it.

If EasyEDA is unavailable, use the [editor-independent workflow](references/easyeda-workflow.md#work-without-the-editor). Continue requirements, schematic design or review, layout planning, and checks supported by the available artifacts. Record which editor checks still need evidence.

## Lead new hardware projects

For a new board, an open-ended build request, or a request to manage hardware development, start with the [hardware project playbook](references/project-playbook.md). Lead the requirements interview. Read existing evidence, ask the next questions that affect a decision, and record the answers, constraints, risks, and acceptance tests. Use the existing project brief or the [project record template](assets/project-record.md) when a working record is needed. Continue reversible design work where the known constraints allow it. Apply the relevant stage review before committing a build or calling it complete.

For a targeted edit or review, start at the requested stage with the supplied evidence. Reopen a requirements question when its answer can change the requested result.

## Select the relevant references

- For editor operations, native automation, or schematic-to-PCB synchronization, read [EasyEDA workflow](references/easyeda-workflow.md).
- For defining or auditing PCB rules, use the [PCB design rulebook](references/design-rules.md). Use its rule matrix and provisional starter settings to build a board-specific rule sheet.
- For layer selection, placement, routing, or layout review, read [stackup and layout](references/stackup-and-layout.md).
- For fabrication or assembly, read [release checks](references/release-checks.md). Use the [Gerber archive inspector](scripts/inspect_gerber_zip.py) for the filename inventory of a native EasyEDA Gerber ZIP when available.
- For vendor-specific requirements, evaluation boards, or free PCB ebook downloads, read the [on-demand hardware reference workflow](references/hardware-rag.md). Use the connected EasyEDA RAG MCP server or the local CLI to search by part and source. Ingest selected references when needed. Verify retrieved requirements against the matching original and board context.
- For source details and supplemental checklists, use the [local source library](references/sources/index.md).

## Design and review workflow

Always prefer an applicable official manufacturer reference design when designing a new circuit or substantially changing an existing one. Verify the match and document any adaptations using the [reference design checklist](references/hardware-rag.md#adapt-an-official-reference-design).

1. Identify the requirements, constraints, and evidence that affect the requested work. Use the playbook intake for project-level gaps, and label any assumptions that affect the design or review.
2. Verify schematic intent and part identity before placement. Check the exact orderable part and package revision against its datasheet, especially pin-to-pad mapping, numbering view, pin 1 or polarity, exposed pads, mounting features, and connector orientation. Resolve relevant electrical-check findings and reconcile schematic and PCB connectivity before routing or releasing. After source or library edits, inspect the import changes and affected pads, nets, and routes.
3. Choose a fabricator stackup and define rules before committing constrained routes. Record physical L1 through Ln roles, reference planes for critical routes, process constraints, and applicable device or interface requirements. Use the actual manufacturer service and stackup for release values. Treat unconfirmed values as provisional and state what would change if the fabrication process changes.
4. Fix the outline, mounting, connectors, and keepouts first. Place the critical functional groups and check escape routing and return paths before routing the rest. Rebuild pours and internal planes after changes. Run the relevant electrical and design-rule checks and inspect final copper and connectivity. A clean DRC result covers the enabled rules, so verify critical geometry and circuit-specific constraints separately.
5. Deliver the requested design, review, or release package. For a review, give each material finding a location (net, designator, layer, or export file), impact, fix, and way to verify it. For a release, tie the final reports and manufacturing files to one frozen source revision. Hold release for unresolved connectivity or process conflicts, required checks without evidence, or missing manufacturing data. Label in-progress exports as drafts and identify open items.

Use the evidence you can access. If editor execution or native files are unavailable, provide concrete edition-specific instructions or a bounded review of the supplied artifacts. Report which edits, exports, checks, and inspections were actually performed and what remains open. Keep authorization for fabrication orders and external uploads tied to the user's request.
