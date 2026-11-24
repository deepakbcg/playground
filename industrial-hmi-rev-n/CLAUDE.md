# Rev N task and release checks

**DO NOT FABRICATE OR POWER THIS PCB.** The old protected 24 V input track still reaches U1.1, now assigned to feedback. Keep this source on fabrication hold. Make the copper changes and run the release checks in a separate working copy before generating fabrication files.

Work from the [README](README.md), [pin audit and editor tasks](REV-M-PIN-AUDIT.md), [itemized sourcing decisions](REV-N-CHANGES.md) and [EasyEDA Standard source ZIP on fabrication hold](Industrial-HMI-RevN-EasyEDA-DO-NOT-FABRICATE.zip). Read the adjacent [EasyEDA PCB skill](../easyeda-pcb/SKILL.md). Use targeted queries or a parser for the multi-megabyte PCB JSON and PDFs. Use the PDF only as inherited artwork and inspect relevant pages as needed.

## Scope

- Rev N includes sourcing changes and the corrected U1 symbol and footprint. Use a separate named copy for native PCB work and preserve both source folders.
- Keep the four-layer 99.2 × 96 mm outline, mounting, interface pinouts, approved part numbers, USB-C valid-attach and 3 A power gates, cabinet priority, shared 3.3 V regulator, and independent RS-485 returns unless an electrical revision explicitly changes them.
- Keep the project local. Purchase, cart, quote upload and pushes are outside this handoff.

## Release checks

1. Run `python3 tools/verify_rev_n.py` from the Rev N folder. Open the EasyEDA Standard schematic and PCB from the ZIP in the same native project. Compare reference designators, component attributes, footprint pads, named nets, outline and stack before changes.
2. Reroute the legacy copper near U1 in EasyEDA. Rev N already assigns pad 1 to `CAB_FB`, pad 3 to `VIN_PROT` and pad 4 to GND and uses the TI DDC0006A example land dimensions. Remove each obsolete fanout and connect the three pads to the specified circuits. Confirm that the imported enable divider uses R67 at 1 MΩ and R68 at 91 kΩ. [U1 editor task](REV-M-PIN-AUDIT.md#pcb-editor-tasks) · [TI datasheet](https://www.ti.com/lit/ds/symlink/lmr51635.pdf)
3. Correct D25 and J4, review the U6 and U23 land differences, and close the six inherited open nets and the 0.116 mm clearance beside U6.7. Rebuild pours, inspect ratlines and run full native ERC and DRC. Compare schematic and PCB pins, nets and the fitted/DNP variant. [Footprints and routing tasks](REV-M-PIN-AUDIT.md#pcb-editor-tasks)
4. Confirm fabrication stackup, thickness, copper weights, via process, slots and enclosure alignment. Start with the project’s nominal 1 mm four-layer stack and verify impedance on the selected process. Check 90 Ω USB and 100 Ω Ethernet MDI, RGB return paths, regulator hot loops, optocoupler spacing, both RS-485 barriers and the USB receptacle shell slots. Check confirmation measurements at both supply inputs and full load. [GCT USB drawing](https://gct.co/files/drawings/usb4105.pdf)
5. Update the physical revision marker and re-export the artwork in EasyEDA. Freeze the reviewed source, then use native EasyEDA fabrication export for all four copper layers, outline, both solder masks, relevant silkscreen, plated and non-plated drill/slot files, and paste when required. Export BOM and CPL for the fitted variant. Identify manual and post-reflow parts separately.
6. Inspect the Gerber and drill overlay in an independent CAM viewer. Run the skill’s Gerber ZIP inspector with four copper layers and the required masks, silk and drill outputs. Check dimensions, plated slots, layer registration, pin one, CPL angle/origin/units and BOM quantities. Archive the native source and verified exports with the revision, rule settings, exercise results and SHA-256.
7. Verify cabinet cold start at 20.4 V at J1 under full load. Record `VIN_PROT`, `CAB_5V` and `SYS_5V` during a slow cabinet ramp and brownout, with and without a qualified USB source. Verify default/1.5 A host programming with cabinet power, 3 A USB full-load start, reverse current and BOOTSEL in both orientations. Verify X3 startup and frequency and the U6 output capacitor's effective capacitance. If considering the stocked C85/C86 substitute, check U1 startup, ripple and load-step response with the selected capacitors. Test Ethernet, microSD, backlight, both RS-485 buses and optional relay coils at low supply and temperature corners. Record first-article results before production.

Keep the fabrication hold in the source names, document titles and Document-layer label on this draft. Clear the corresponding hold in a new release revision only after the PCB rework and native release checks pass.
