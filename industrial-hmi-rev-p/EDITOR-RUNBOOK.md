# Rev P EasyEDA Standard editor and release checks

**DRAFT — DO NOT FABRICATE.** Use the desktop edition of EasyEDA Standard, KiCad GerbView and Python 3. Save the evidence named below in `industrial-hmi-rev-p/evidence/`. Inspect the installed J4 footprint and D24 placement in step 6 before any fabrication export. Keep the CAD work, exports and screenshots local.

## 1. Import the live project

In EasyEDA Standard desktop, select **Setting → Desktop Client Setting → Running Mode Setting → Projects Offline Mode**. Create a working project with **File → New → Project** and open the [Rev P source ZIP](Industrial-HMI-RevP-EasyEDA-DO-NOT-FABRICATE.zip) through **File → Open → EasyEDA**. If the open dialog takes individual files, extract the ZIP locally and open the schematic, PCB and footprint JSONs. Save the schematic and PCB in the same local project and keep the original ZIP as a backup. Use the embedded footprints for inspection. If the client prompts to publish or upload a library to resolve a binding, cancel and record the unresolved association in step 3.

Open the schematic and PCB together. In the PCB use **Fabrication → PCB Information**. Expect **212 PCB components**, **212 matching schematic designators**, **four copper layers** and a **99.2 × 96.0 mm** outline. The display and coin cell are external fitted items in the BOM. Check that BZ1, J4, D25, U6 and U23 still use the supplied footprint geometries. Save `01-import.png` with the project tree and PCB information. [Desktop modes](https://docs.easyeda.com/en/FAQ/Client/) · [Opening EasyEDA source](https://docs.easyeda.com/en/Export/Export-EasyEDA-Source-File/) · [PCB Information](https://docs.easyeda.com/en/PCB/PCB-Information/)

## 2. Set up layers and design rules

Click empty PCB canvas and choose **Units → mm** in Properties. Open **Tools → Layer Manager…**. Confirm Top / Inner1 / Inner2 / Bottom (EasyEDA 1 / 21 / 22 / 2). Keep Inner1 configured as a signal layer with drawn GND copper so it does not generate a blanket plane. Inner2 carries signals and the two 3V3 power legs. The stackup reference is nominal **1.0 mm, four-layer JLC7628** with 1 oz outer and 0.5 oz inner copper, subject to the stated finished copper and width limits. [Fabrication notes](FAB-NOTES.md)

Open **Tools → Design Rule…**. Apply the default to the design and inspect any assigned net rules. Also check the manual limits in CAM where Standard has no separate rule field.

| EasyEDA setting or manual check | Minimum (mm) |
| --- | ---: |
| Track Width | 0.150 |
| Clearance, different-net copper | 0.125 |
| Via Diameter / Via Drill Diameter | 0.500 / 0.250 |
| Check Object to Board Outline | 0.200 |
| Different-net SMD pad to pad | 0.150 |
| Via-hole edge to foreign copper | 0.200 |
| Component PTH edge to foreign copper, inner / outer | 0.300 / 0.280 |
| NPTH edge to copper | 0.200 |
| Hole edge to hole edge | 0.200 |
| Finished silkscreen line width / character height / clearance to open pads | 0.150 / 1.000 / 0.150 |

Enable **Check Object to Copper Area** and **Check Object to Board Outline**. Use the eye icons in **Layers and Objects → Layers** to inspect each copper layer individually. The board uses fixed `SOLIDREGION` objects. **Shift+B** rebuilds only Copper Areas. Inspect fixed-region boundaries and net names directly, especially where they touch pads/vias or pass near new drills. Correct the polygon locally and verify positive overlap or a continuous edge shared for ≥0.15 mm. Save `02-layer-stack.png` and `02-design-rules.png`. [Layer Manager](https://docs.easyeda.com/en/PCB/Layer-Manager/) · [Design rules](https://docs.easyeda.com/en/PCB/Design-Rule-Check/) · [JLCPCB capabilities](https://jlcpcb.com/capabilities/pcb-capabilities/)

## 3. Compare schematic and PCB

With the schematic active, open **Design → Update PCB** and select the imported PCB. From the PCB, use **Design → Import Changes** for the same comparison. Expect no pending component additions, deletions, footprint changes or pin-net changes. If a footprint comes up unbound, open the schematic component’s **Properties → Footprint** and resolve it against the matching supplied footprint. If an import changes UUIDs, review the footprint name, pin names and geometry before restoring the link. Cancel before applying unexpected changes. Rerun the comparison after any library association changes and save `03-sync.png`. [Update PCB](https://docs.easyeda.com/en/Schematic/Convert-to-PCB/) · [Import Changes](https://docs.easyeda.com/en/PCB/Import-Changes/)

## 4. Show and count all ratlines

In the PCB open **Layers and Objects → Layers**, show **Ratlines**, and open **left navigation → Design → Net**. Clear filters, enable all net checkboxes and refresh the panel. Inspect the Ratlines folder under the net list where available. **Fabrication → PCB Information** should also show the same number of routed and total nets. Expect zero unrouted connections. Save `04-ratlines.png` with visibility and the routing count. [Ratlines](https://docs.easyeda.com/en/PCB/Ratline/) · [Design Manager](https://docs.easyeda.com/en/PCB/Design-Manager/)

## 5. Run DRC and resolve findings

Open **Design → Check DRC** and refresh **left navigation → Design → DRC Error**. Click each finding to locate the affected objects. Expect zero errors on the final design. Resolve findings as follows and repeat the rule check after each edit.

| Finding | Check and correction |
| --- | --- |
| Open, short or wrong net | Compare schematic pad numbers and net labels against the selected tracks and regions. Route into the land with positive overlap, remove wrong-net copper and repeat the schematic comparison and ratline check. |
| Clearance to a fixed region | Inspect both selected nets on the failing layer. Reshape the local polygon or move the trace/via. Check that the remaining same-net pad and via overlaps are still connected. |
| Narrow track or small via | Compare the object with the rule table. Apply the actual width or via size and reroute if widening consumes required clearance. Keep both 3V3 legs at 2.20 mm nominal. |
| Hole, slot, annulus or board edge | Measure from the actual hole or route edge, including on inner layers. Move the part or route or reshape local copper according to the J4 drawing and process limits. Inspect the drill export for plating and alignment. |
| Silkscreen on an open pad | Inspect Top Silk with Top Solder Mask visible, then measure in CAM. Move the text or trim the footprint legend to ≥0.15 mm away from the opening. Keep DO NOT FABRICATE on Document only. |
| Isolation clearance | Check both field domains and all four copper layers. Remove foreign copper and keep return paths on their own sides. Record the measured minimum for each barrier against the installation requirement. |

Save `05-drc.png` with the entire result panel and `05-drc.txt` with the editor version, rule set, final count and disposition of any findings. Use the editor's report if provided, or transcribe these fields. [EasyEDA DRC](https://docs.easyeda.com/en/PCB/Design-Rule-Check/)

## 6. Inspect the critical areas and installed J4/D24

In the PCB use **left navigation → Design → Component** to jump to each designator. Use **Design → Net** in the same panel or select a pad and press **H** to highlight a route. Dimensions below use absolute EasyEDA millimetres. Save the appropriate copper layer name and dimensions in each screenshot.

| Check | Expected result | Evidence |
| --- | --- | --- |
| U1, near (1033.70, 784.00) | U1.1 FB goes to R69.2/R70.1 over the existing ~20.6 mm Bottom route. U1.2 is EN, U1.3 VIN_PROT, U1.4 GND, U1.5 SW to L3.1, and U1.6 CB. Verify the FB route has its Inner1 reference and stays clear of SW/L3. Confirm the C83 input loop and the L3.2 → C85/C86 output route. | `06-u1-top.png`, `06-u1-fb.png` |
| U6 (1031.75, 806.80), L4 (1036.15, 803.50), C94 (1035.30, 800.30) | Compare the corrected RPJ lands with the recorded pad table. Keep the narrow VOS branch from U6.3 attached to C94.1. Inspect L4.2 → C94 → Bottom 3V3 through both 2.20 mm Inner2 legs and the groups of three vias. The stored Top U6.7-to-SYS_5V minimum is 0.300 mm. | `06-buck-top.png`, `06-buck-inner2.png`, `06-buck-bottom.png` |
| J4, mating face at x = 1015.825, y centreline 816.000 | Confirm four plated shell slots on GND, two Ø0.65 mm NPTH and continuity on both CC and data lines and VBUS. Check shell copper and drill-edge clearances from step 2. | `06-j4-slots.png`, `06-j4-routing.png`, `06-d24-spacing.png` |
| D25 (1024.90, 816.15) and U23 (1028.10, 816.15) | D25.1 joins D+, D25.2 D−, and D25.3 GND, with short symmetric data stubs. Compare the 0.70 mm D25 data-pad pitch and the U23 pad and paste shapes with the recorded pad table. Check U23.8/7 on the connector side and U23.1/2 on the gated side. | `06-usb-data.png` |
| R78.1 (1044.775, 799.700) and R83.1 (1029.625, 815.350) | R78.1 overlaps the 0.15 mm Top CAB_PRI branch to the U22.6 divider. R83.1 reaches the main 3V3 rail through the 0.23 mm Top bridge at y = 813.550, with U23.10 and U6.3 in the same net. | `06-r78-cab-pri.png`, `06-r83-3v3.png` |
| RS-485 barriers, U5/J3 near (1087.12, 797.56) and U14/J7 near (1095.30, 821.75) | Check Top, Inner1, Inner2 and Bottom in turn. Verify no copper, via, shield or region bridges either barrier or connects the two domains. D4/R4/J3 stay in the RS_COM domain on the field side, and D10/R38/J7 stay in RS2_COM. Inspect module-pin and mounting-hardware creepage as well as copper separation. Write the smallest gap and its location for each layer and port. | `06-rs485-l1.png` through `06-rs485-l4.png`, `06-rs485-gaps.txt` |

[Recorded pad tables and copper checks](tools/verification-output.txt) · [Footprint edits](REV-P-STATUS.md#offline-editor-task-package)

**J4 and D24 visual check**

1. In the PCB, select J4 and verify that the [supplied footprint](Footprint_GCT-USB4105-GF-A-REV-P.json) is bound. Confirm the 0.051 mm end trim on A1/B12 and B1/A12, 1.099 mm remaining land length and at least 0.225 mm between each locator and its adjacent GND land. The mating face is x = 1015.825 mm with the y centreline at 816.000 mm. [Rev P status and coordinates](REV-P-STATUS.md#j4-geometry-and-reroute-locations)
2. Select each shell pad and verify **Shape → Oval**, **Layer → Multi-Layer**, **Hole Shape → Slot**, and **Plated → Yes** in Properties. The slots run along x. The rear pair is 1.70 × 0.60 mm with 2.10 × 1.00 mm solder areas. The front pair is 1.40 × 0.60 mm with 1.80 × 1.00 mm solder areas. Confirm two Ø0.65 mm NPTH on 5.78 mm centres, inspect copper, mask and paste, and verify the four coincident contact pairs on 12 physical lands.
3. At D24, verify the centre (1024.620, 812.000), orientation and **0.165 mm** spacing from the GND terminal to the co-nearest J4 GND, VBUS and SBU2 lands. Check the short 0.48 mm VBUS link and the GND via and strap to Inner1. On first article, check access to D24 with J4 fitted. Highlight CC1 and CC2 to both U21 connections, then check both data polarities over Inner1 GND and shell stitches `gge5664` and `gge5667`. In GerbView, show the plated drill/route file with Top copper to verify the four slots. Show NPTH with Top copper to measure both locator clearances.
4. Confirm the purchased BZ1's actual pin pitch, lead diameter and positive lead. Check its two plated holes and square positive SYS_5V pad against the part and its enclosure clearance.

[GCT USB4105 B3, sheet 1](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/5492/USB4105.pdf) · [EasyEDA pads and holes](https://docs.easyeda.com/en/PCB/PCB-Tools/)

## 7. Export the native fabrication outputs locally

From the PCB select **Fabrication → PCB Fabrication File (Gerber)**, generate the files and save `RevP-Gerbers.zip` in the evidence folder. Expected manufacturing files are below. Local generation also provides paste or assembly layers in some configurations. Verify that the separate Document drawing never appears in the manufacturing silkscreen.

| File or group | Expected contents |
| --- | --- |
| `Gerber_BoardOutline.GKO` | One closed 99.2 × 96.0 mm outline |
| `Gerber_TopLayer.GTL`, `Gerber_InnerLayer1.G1`, `Gerber_InnerLayer2.G2`, `Gerber_BottomLayer.GBL` | Four copper layers in order. Some builds use `.GP1`/`.GP2`. |
| `Gerber_TopSolderMaskLayer.GTS`, `Gerber_BottomSolderMaskLayer.GBS` | Both solder mask layers |
| `Gerber_TopSilkLayer.GTO` | Top legend with Rev P DRAFT. A populated bottom legend may also export as `.GBO`. |
| `Drill_PTH_Through.DRL` and any separate plated slot/route file | Plated component holes and four J4 plated slots, with vias accounted for by the PTH/via files. Check actual slot toolpaths. |
| `Drill_NPTH_Through.DRL` | Distinct nonplated mount and locator holes |
| Optional paste files `.GTP` / `.GBP` | Stencil openings on populated sides |

For PCBA evidence, use schematic **Fabrication → BOM** and PCB **Fabrication → Pick and Place File**, and export in mm. Save `RevP-Native-BOM.csv` and `RevP-Native-PickPlace.csv`. Reconcile DNP and external items against the curated BOM, verify J4 and all fine-pitch rotations, and check pin 1 and centroid orientation. Save `07-gerber-export.png` with the local export dialog. [Gerber export](https://docs.easyeda.com/en/PCB/Gerber-Generate/) · [BOM export](https://docs.easyeda.com/en/Schematic/Export-BOM/) · [Pick-and-place export](https://docs.easyeda.com/en/PCB/Export-Coordinate/)

## 8. Check the ZIP and inspect it in GerbView

From `industrial-hmi-rev-p/`, run the inventory check and save the output in the evidence folder. Expect exit code 0 and all requested roles present.

```sh
python3 ../easyeda-pcb/scripts/inspect_gerber_zip.py evidence/RevP-Gerbers.zip \
  --layers 4 --require top-mask --require bottom-mask --require top-silk \
  --require pth --require npth > evidence/08-gerber-inventory.txt
```

Open the extracted files in KiCad GerbView with **File → Open Gerber Plot File(s)…** and **File → Open Excellon Drill File(s)…**. Use **Tools → Measure Tool** and turn layers on one at a time. Check the outline, layer order, all masks, silk, and drill registration. Expect **56 round plated component holes, four plated slots** in the PTH or plated route output and **nine NPTH**, including the two J4 locators. Count vias separately, excluding any duplicate entries between standard PTH and the supplemental via file. The live source has 664 vias. Verify the slot centres and shape against the connector drawing. If the exporter creates individual drill hits for a slot, verify that their output represents the required finished plated opening and is accepted by the fabrication process. A clean inventory only verifies file roles. Save `08-outline-and-stack.png`, `08-j4-plated-slots.png`, `08-npth.png` and `08-hole-counts.txt` with counts, sizes and the actual drill/route filenames. [KiCad GerbView](https://docs.kicad.org/master/en/gerbview/gerbview.html)

## 9. Record the Gerber ZIP hash

From `industrial-hmi-rev-p/`, hash the exact ZIP inspected in step 8.

```sh
shasum -a 256 evidence/RevP-Gerbers.zip > evidence/09-gerber-sha256.txt
shasum -a 256 -c evidence/09-gerber-sha256.txt
```

Expect `evidence/RevP-Gerbers.zip: OK`. On a system with GNU coreutils, use `sha256sum` instead of `shasum -a 256`. Repeat steps 7–9 for any regenerated archive.

## 10. Collect the evidence for the final offline cross-check

Export the final PCB and schematic through **File → EasyEDA File Source…**. Save them locally as `RevP-Final-PCB.json` and `RevP-Final-Schematic.json` and include the J4 footprint source. Provide those files, the native DRC record, all screenshots and text reports from steps 1–9, the exact Gerber ZIP with its hash and any BOM/placement files generated. Include the selected stackup, finished copper and width confirmation and a short record of editor changes. Return the saved PCB and Gerbers to cross-check the imported geometry and exported J4 slot and locator drills. Keep the board on hold until the native and offline reviews are complete. [Source export](https://docs.easyeda.com/en/Export/Export-EasyEDA-Source-File/) · [Staged bring-up](BRING-UP.md)
