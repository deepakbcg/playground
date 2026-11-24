# Fabrication and assembly release

## Freeze a reproducible revision

Save a named revision of the native project with its schematic, PCB, and any custom library content needed to open it correctly. Record the EasyEDA edition/version, intended copper count and physical layer order, fab/assembly service, board thickness and finish, copper weights, and stackup ID or approved stackup drawing. Record feature-specific instructions where applicable, including impedance classes and test requirements, slots, via treatment, castellations, edge plating, and panelization. Check against the manufacturer’s actual service options for this build. [Fabricator capability notes](sources/jlcpcb-notes.md#rigid-pcb-capabilities)

Run the schematic checks available in the editor and review electrical intent against the relevant datasheets. Apply reviewed schematic changes, rebuild all copper, restore full rule checks and ratline visibility, and run the final PCB DRC. Compare schematic and PCB connectivity using editor checks or netlist evidence and resolve every unexpected unrouted connection. Record the checks with their revision, result, and evidence. Document intentional exceptions with the rule, objects, reason, and evidence or approval relevant to the exception. A change to the source, stackup, assembly variant, or export options invalidates affected checks and artifacts. Regenerate and recheck them from the resulting revision.

## Review the actual export

Export Gerber and drill files to a fresh location. Include outline, all intended copper layers, and mask and silk where specified. Include actual plated and non-plated drill and route outputs for the required holes and slots. Paste files serve the stencil or assembly workflow when requested. Confirm custom fabrication layers and how the manufacturer interprets each one. [Pro fabrication export notes](sources/easyeda-notes.md#pro-fabrication-and-assembly-export), [Standard fabrication export notes](sources/easyeda-notes.md#standard-fabrication-export)

Use the archive inspector on native EasyEDA filenames as a quick inventory. Supply the expected layer count from the design or release spec. In the standard top-to-bottom order, the inspector's `inner-1` is EasyEDA Inner1 and corresponds to physical L2. On a six-layer board, `inner-4` corresponds to physical L5. Verify the order against the board's layer map. Add `--require` for files expected for the build, such as mask on both sides, plated through drill data, or a non-plated drill file for round mounting holes emitted as drills.

```sh
skill_dir=/path/to/easyeda-pcb
python3 "$skill_dir/scripts/inspect_gerber_zip.py" board-gerbers.zip --layers 6 \
  --require top-mask --require bottom-mask --require pth --require npth
```

The script returns `0` when the expected native filename roles are present and no inventory problems were found, `1` for missing required roles, unexpected numbered inner layers, duplicate roles or zero-byte recognized files, and `2` for invocation or archive access errors. It reads the ZIP directory and reports unclassified names for review. `pth` checks for at least one native plated through drill file. If there are both plated component holes and vias, verify that the relevant drill files together contain the full feature set with the intended plating. Blind or buried spans and routed slots require a separate check. For custom or renamed exports, map the files using the export settings, file attributes, and CAM viewer. File integrity, artwork, connectivity, polarity, and manufacturability each need their own evidence.

Open the exact outgoing ZIP in a CAM/Gerber viewer, preferably independent of the editor. Overlay outline, copper, mask, and drills, and inspect each copper layer in physical order. Confirm:

- The outline is closed and has the expected dimensions and cutouts. The artwork and drill files share the correct units, registration, orientation, and origin. Inspect the bottom-side view in the proper orientation.
- Each physical copper layer has the required geometry, plane polarity, clearances and antipads. Check plane splits and return paths against the route layers. Confirm copper and drill setback at the outline, cutouts and slots.
- Pads and mounting holes appear at the intended coordinates and diameters. Match plating, drill spans, slots, any special hole constructions, and route layers to their documented intent. Check that intended mask openings, via treatment, paste apertures, and legible silkscreen are present.
- The manufacturer maps the requested files, layers and drill types correctly. If an authorized fab preview or DFM report is available, resolve discrepancies with the selected service before release. A viewer screenshot establishes what was rendered. It cannot demonstrate netlist equivalence, which requires editor or connectivity evidence.

## Check assembly deliverables when requested

Generate BOM and placement (CPL or pick-and-place) from the same revision and assembly variant. Define the set of fitted parts and compare designators across the PCB, BOM and CPL. Account for DNP, hand-fit, mechanical, and through-hole exceptions according to assembler requirements. Verify each fitted line's exact MPN, package, quantity, supplier identifier when the assembler requires it, and approved alternates. Check each placement's origin, units, centroid, side and rotation convention, especially bottom-side parts, polarized parts, connector orientation and pin 1. Use the assembler's placement preview when available. Resolve library origin and rotation errors before ordering. [BOM and placement notes](sources/jlcpcb-notes.md#bom-and-placement)

## Handoff evidence

For an actual release request, provide the frozen revision and the files produced, plus a short record of what was verified and by which evidence. Include the layer order and manufacturer process selection, electrical and DRC results plus any approved exceptions, CAM/DFM results, and assembly verification where applicable. Mark absent evidence as pending. Tie the exact final export to the revision, for example with an archive checksum if more than one copy could circulate. Share draft files labeled with release blockers if the evidence does not support release yet.
