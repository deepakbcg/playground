# EasyEDA source notes

Checked 2026-11-24. These notes correspond to the publisher articles below. For actual operations, use the editor edition and version shown by the project.

## Pro migration and schematic sync

- **Standard import.** Standard and Pro regenerate copper differently. Recheck zone boundaries and net assignments, thermal reliefs and opens after import. Verify the imported footprints and attachments as well as the outline and routing. [Import EasyEDA Standard Edition](https://prodocs.easyeda.com/en/import-export/import-easyeda/)
- **Schematic sync.** Pro creates or updates the PCB from the schematic's Design menu. The PCB also has a schematic change import action. Review the proposed changes before applying them. [Pro Quick Start, conversion](https://prodocs.easyeda.com/en/quick-start.html#convert-schematic-to-pcb)

## Pro CLI and source format

The desktop CLI reaches a running editor through the local bridge. Use installed help and the built-in client reference to discover the available options. Confirm the session, project path and board, then verify command results and any output files. Project and source formats vary by version. Version requirements differ between the pinned GitHub documents and the online guide, so check the installed client. [Online command-line guide](https://prodocs.easyeda.com/en/api/guide/cli.html), [online automation guide](https://prodocs.easyeda.com/storage/texts/api/guide/cli-for-ai.md), [pinned CLI guides and format notes](index.md#imported-originals)

## Pro layer manager

The Layer Manager controls physical copper count and type. Inner layers may carry tracks and local pours or represent dedicated planes. A dedicated plane can use negative editing conventions while the exported artwork is positive. Inspect assignments and plane divisions, rebuild, then confirm the output in CAM. [Pro Layer Manager](https://prodocs.easyeda.com/en/pcb/tools-layer-manager/)

## Pro rules and nets

Pro can bind geometric constraints and additional route rules to nets or net classes. Regional rules can further affect route geometry. The Nets panel lists groups, differential pairs and ratlines. Confirm the intended nets and the actual constraints in the active board. [Pro Design Rules](https://prodocs.easyeda.com/en/pcb/design-design-rule/), [Pro Nets panel](https://prodocs.easyeda.com/en/pcb/side-left-panel-net/)

## Pro copper and DRC

Rebuild copper and internal planes before checking clearance and connectivity. The board DRC lists findings for the configured rules and can locate affected objects. Verify deck settings and the ratline list as part of the final check. Export provides optional checks for DRC and net connectivity. [Pro Copper Region](https://prodocs.easyeda.com/en/pcb/place-copper-region/), [Pro PCB DRC](https://prodocs.easyeda.com/en/pcb/design-check-drc/), [Pro PCB settings](https://prodocs.easyeda.com/en/pcb/settings-pcb/)

## Pro fabrication and assembly export

Export board fabrication files from the PCB, then select the fabrication layers and options for the build. Native names distinguish top, bottom, numbered inner copper, and drill types. Some older releases use the `GPn` suffix for internal planes. The BOM and placement list have separate export commands. Inspect the saved files and the chosen assembly variant. [Pro Gerber export](https://prodocs.easyeda.com/en/pcb/export-pcb-fabrication-file-gerber/), [Pro Quick Start, manufacturing export](https://prodocs.easyeda.com/en/quick-start.html#output-manufacturing-files)

## Standard schematic sync and layers

Update the PCB from the schematic or import changes through the PCB. Review the diff, especially footprint replacement and net reassignment. The Layer Manager controls copper count and types. Hidden layers remain in the board and can be exported. Inspect actual inner-layer types, copper and plane nets. [Standard Import Changes](https://docs.easyeda.com/en/PCB/Import-Changes/), [Standard Layer Manager](https://docs.easyeda.com/en/PCB/Layer-Manager/)

## Standard rules and routing

Rules can be assigned to nets and use the active canvas units. Enable the relevant copper and outline checks. For paired routing, use matching `_P`/`_N` or `+`/`-` names and assign pair rules first. The pair router can place geometry that violates rules. Inspect actual geometry and rerun DRC after rebuilding copper. [Standard DRC](https://docs.easyeda.com/en/PCB/Design-Rule-Check/), [Standard Route Tracks](https://docs.easyeda.com/en/PCB/Route/)

## Standard fabrication export

Standard exports a fabrication ZIP with artwork and drill outputs. The documented inner copper suffixes are `Gn` for signal layers and `GPn` for dedicated planes. Some cutout geometry belongs in the outline rather than a drill file. Confirm the actual output for each intended hole and slot. [Standard Gerber export](https://docs.easyeda.com/en/PCB/Gerber-Generate/)
