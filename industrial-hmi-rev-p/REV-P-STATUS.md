# Rev P status

**Draft — DO NOT FABRICATE OR POWER.** The live design is the Rev P [EasyEDA Standard project ZIP](Industrial-HMI-RevP-EasyEDA-DO-NOT-FABRICATE.zip). Work starts from the Rev N FOOTPRINTS archive at the annotated `rev-n` tag. The board is 99.2 × 96 mm with Top, Inner1, Inner2 and Bottom copper on EasyEDA layers 1, 21, 22 and 2.

## What changed since Rev M

- Carried forward Rev N sourcing and LCSC retail repricing, the 8.2 V field-input Zeners, and the same-land 47 µF 1210 cabinet output capacitors C85/C86. The prototype material estimate is **₹6,009.05** per board and cell. The three-board list totals **₹26,160.51** before displays, freight, tax or PCB and assembly costs, and **₹39,518.39** with displays. Q3 stays ST `STL6P3LLH6`. LCSC showed three, so the list buys four cut-tape units from DigiKey India, which listed 9,472. [BOM and sourcing evidence](README.md) · [DigiKey Q3 listing](https://www.digikey.in/en/products/detail/stmicroelectronics/STL6P3LLH6/5170838)
- Corrected the cabinet buck pin map to U1.1 FB, U1.2 EN, U1.3 VIN, U1.4 GND, U1.5 SW and U1.6 CB. The carried-forward routing removes the old wrong-net contacts, places C83 at U1 VIN/GND, and routes FB to the R69/R70 divider. R68 is `0603WAF9102T5E`, 91 kΩ. The calculated EN threshold is about 14.70 V rising and 11.81 V falling at VIN_PROT. [Per-pin audit](REV-M-PIN-AUDIT.md) · [TI LMR51635 data sheet](https://www.ti.com/lit/ds/symlink/lmr51635.pdf)
- Carried forward 52 passive conversions to 0603. The earlier 16 exceptions (C14, C39, C40, C68–C73, R12, R57–R61 and R63) preserve sensitive crystal, bypass, Ethernet and dense-route placements. Rev P also keeps C37, R30 and R62 in 0402 for the EVE 1.2 V bypass, BT818 pixel-clock series termination and W5500 EXRES near the Ethernet RX pair. The footprint, fitted part and sourcing documents agree for all designators.
- BZ1 fits a TMB12A05 5 V active magnetic buzzer with a nominal 12 mm body, 7.6 mm pitch and two 1.00 mm finished plated holes. Square pad 1 connects to SYS_5V. Pad 2 connects to BUZZ_LOW. The body moved 1.625 mm left and 1.375 mm up from the Rev M placement. [Footprint](Footprint_BUZZER-D12-P7.6-PTH.json) · [Buzzer data sheet](https://sharvielectronics.com/wp-content/uploads/2025/11/TMB12A05.pdf)

| 0402 part | Retained rating | LCSC stock at check |
| --- | --- | ---: |
| C37 Samsung CL05B104KB54PNC | 100 nF, 50 V, ±10%, X7R | 2,200 [C307331](https://www.lcsc.com/product-detail/C307331.html) |
| R30 Yageo RC0402FR-0722RL | 22 Ω, ±1%, 62.5 mW, 50 V | 7,684,600 [C114765](https://www.lcsc.com/product-detail/C114765.html) |
| R62 UNI-ROYAL 0402WGF1242TCE | 12.4 kΩ, ±1%, 62.5 mW, 50 V | 285,000 [C11692](https://www.lcsc.com/product-detail/C11692.html) |

LCSC public product-detail feed checked on 25 November 2026 IST. The 100-piece quantities for these three lines reflect LCSC's MOQs. Carry-forward order lines retain the dated stock and price sources in the [purchase list](PURCHASE-LIST.csv).

## Copper closure

Phase 1 preserved the tagged FOOTPRINTS copper exactly. Phase 2 closes all ten requested findings in the stored geometry. Component placements and footprints are identical to the Phase 1 PCB. The coordinates below are absolute EasyEDA positions in millimetres.

| # | Location | Verified edit |
| --- | --- | --- |
| 1 | R76.2 at (1040.075, 799.100) | Added the 0.15 mm GND top trace and off-pad via `gge961054` at (1041.550, 799.400) to the existing ground group shared with U22.3. |
| 2 | U6.4 at (1031.125, 806.050) | Added a 0.36 mm GND escape to via `gge961017` at (1030.475, 806.150) and the plane return shared with C93.2. |
| 3 | U6.5/6 at (1031.125, 806.550/807.050) | Joined VIN/EN to C93.1 and the mux output with 0.36 mm Top/Bottom copper and via `gge961019` at (1030.475, 807.020). |
| 4 | U21.24 at (1021.300, 808.500) and C87.1 | Routed STUSB4500L VDD to the existing USB_VBUS trunk through via `gge961102` at (1020.700, 808.620). Joined C87.1 to the trunk with a 0.36 mm Inner2 stub. Moved C89's ground via `gge5644` to (1019.140, 808.750) and rerouted its Top connection to C89.2. |
| 5 | U21.18 at (1021.950, 805.350) and R73.2 at (1020.525, 810.400) | Connected VBUS_VS_DISCH to the 560 Ω sense resistor through via `gge961301` at (1020.280, 811.075) and a 0.15 mm Inner2 trace to the existing U21.18 escape. Shifted a local section of Top CC1 trace `gge4853` beside J4.SH3. |
| 6 | U21.23 at (1021.300, 808.000) | Added a 0.15 mm Top `USB_REG27` bypass route to C89.1 after shortening the unused end of 3V3 trace `gge4343`. |
| 7 | R72.1 at (1025.625, 805.100) | Connected Q3.4 and R71.2 to R72.1 with 0.15 mm Top/Inner2 tracks through new via `gge961004` at (1024.425, 804.225) and the existing R72 via. |
| 8 | R78.1 at (1044.775, 799.700) | Added a 0.55 mm long, 0.15 mm wide `CAB_PRI` branch from `gge4868` to the pad centre. The old copper was about 0.000001 mm from the pad and did not overlap it. |
| 9 | R83.1 at (1029.625, 815.350) | Bridged its Top 3V3 island to the main rail with a 2.60 mm long, 0.23 mm wide trace at y = 813.550 mm. U23.10 and U6.3 now share that group. |
| 10 | U6.7 near (1031.250, 807.475) | Set back the end of the adjacent SYS_5V trace `gge4935`. The limiting gap is now **0.125999 mm**, against U6.6, up from 0.116002 mm. |

The through vias use the existing 0.50 mm land and 0.25 mm drill. Fixed copper clearances were opened in Top 3V3 region `gge5673`, Inner1 GND regions `gge5955`, `gge5956`, `gge5958`, `gge5962`, and Bottom GND regions `gge5850`, `gge5852`, `gge5853`. The minimum clearance involving added or changed copper was **0.128 mm** from Top `USB_CC1` to J4.SH3. Both tagged comparisons meet the **0.125 mm** draft rule. The offline check found zero mixed-net groups and preserved every previously connected pad group. [Recorded verification](tools/verification-output.txt) · [TI TPS62902 layout guidance](https://www.ti.com/lit/ds/symlink/tps62902.pdf) · [ST STUSB4500L data sheet](https://www.st.com/resource/en/datasheet/stusb4500l.pdf)

## 3.3 V distribution and copper contacts

The incoming review recorded “3.3 V buck output was not connected in Rev M–N (point contact)”. The stored Rev M and Rev N sources show **1.236 mm²** of overlap from L4.2 into Top region `gge5675`, and further positive overlap through `gge5610` to the Bottom rail. The stored sources do confirm the **0.23 mm** link to C94.1 and the single-via tie to the rail at that location. Those geometries were insufficient to verify the requested 1.5 A path.

- The new path runs from L4.2 through three plated vias to a **2.20 mm Inner2 trace**, through the C94 copper and a second **2.20 mm Inner2 trace**, then through three plated vias into a widened Bottom distribution region. C94.1 also has three plated connections to the Inner2 copper. The nominal IPC-2221 screen gives 18.0 °C rise at 1.5 A and 15.2 µm finished Inner2 copper. Confirm minimum finished copper and track width, via plating, voltage drop and temperature. [Fabrication notes](FAB-NOTES.md)
- U6.3 now senses directly at C94.1 through a dedicated **0.15 mm Top trace**. The old sense branch and the narrow L4.2–C94.1 trace were removed. Clearing the old Top region around VOS required a separate **0.38 mm Inner2 connection** for the microSD branch between existing vias `gge5613` and `gge5611`.
- Clearances were opened locally in Top 3V3 region `gge5673`, Bottom ground regions `gge5853`, `gge5878`, `gge5880`, and Inner1 ground regions `gge5964`, `gge5967`. [TI TPS62902 layout guidance](https://www.ti.com/lit/ds/symlink/tps62902.pdf) · [TI via and power copper guidance](https://www.ti.com/lit/an/slva959b/slva959b.pdf)

| Pad | Positive-overlap reinforcement |
| --- | --- |
| C17.1, 1V1 | 0.30 mm Top connection to `gge5387`. |
| C15.1, 3V3 | 0.42 mm Top connection to `gge4946`. |
| U2.62, GND | 0.20 mm Top connection into `gge5705`. |
| X1.2 and X1.4, GND | 0.28 mm Top ground links to `gge5362` and `gge5363`, respectively. |
| J4.SH2, GND | 0.32 mm copper overlaps the shell land and `gge5667` on all four layers, bridging the 0.010 mm gap. Recheck it when fitting the required plated slots. |

The verifier accepts positive area overlap or a continuous shared edge of at least **0.15 mm**. Point contacts and shorter edges are open; nearby finite gaps are reported separately. The updated rule joins the larger existing pour seams that previously made GND, 3V3 and DI_COM appear split. Additional direct bridges reinforce 32 locations. Thirteen isolated pour fragments with no lands, vias or tracks were removed, totaling **0.034 mm²**. The 50 remaining weak pairs have an alternate copper path, including pairs with a new direct bridge. The report lists each pair with its layer, coordinates, shared length, gap and disposition. The final design has **zero split named pad nets and zero mixed-net copper groups**. The minimum clearance on this pass was **0.129 mm**, and the cumulative Rev N comparison was **0.128 mm**, both above the 0.125 mm rule. [Recorded verification](tools/verification-output.txt)

## Offline editor-task package

- **U6.** Updated RPJ0009A pads 4 and 6 to 1.00 × 0.20 mm at 0.45 mm offset, and pads 7–9 to 0.25 × 0.55 mm. Correcting the package datum shifted the footprint origin 0.25 mm while preserving the side-pad row positions. VIN, GND, SW and VOS retain their positive-overlap routes. [TI TPS62902, p.45, RPJ0009A Example Board Layout](https://www.ti.com/lit/ds/symlink/tps62902.pdf#page=45)
- **U23.** Corrected all ten lands to the RSE0010A drawing, including the 0.55 × 0.20 mm inner row lands, 0.30 × 0.60 mm end lands on 1.80 mm centres, and 0.05 mm corner radii. [TI TS3USB221A, drawing 4220307/A](https://www.ti.com/lit/ds/symlink/ts3usb221a.pdf)
- **D25.** The DRT0003A CAD lands are 0.45 × 0.30 mm in the installed orientation. D+ and D− use symmetric ±0.35 mm offsets. Existing D+, D− and GND tracks positively overlap the new lands, so the routed data pair was retained. [TI MPDS340 p.1](https://www.ti.com/lit/ml/mpds340/mpds340.pdf) · [DRT0003A copper land data](https://static.ultralibrarian.com/part-previews/footprints/5163958/detailed-DRT0003A.svg)
- **Copper and marking.** The new land shapes and widened 3V3 tracks passed the stored-geometry clearance check with a minimum **0.132428 mm**. No fixed regions needed further trimming for this package. Silkscreen reads **Rev P DRAFT**. The separate warning remains on Document layer 12. [Pad tables and checks](tools/verification-output.txt)

## Editor and release tasks

1. **J4, USB4105-GF-A.** The offline trial found the drawing's rear shell slot/annulus intersects Inner2 USB_VBUS and Bottom USB_CC2. The front locator crosses Top USB_CC1, and the opposite locator approaches Top VBUS. The live board retains the four round plated shell holes and no locators. It still has 16 contact designations on 12 physical SMT lands and 0.128 mm CC1-to-shell clearance. Apply the complete connector footprint and reroute the affected nets together, then check the mechanical datum, shell grounds, annuli and export. [GCT B3 sheet 1](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/5492/USB4105.pdf)
2. **U1 FB and BZ1.** The optional R69/R70 relocation is deferred. A ≤3 mm FB divider placement and a quiet route around the U1 switch and L3 copper were not verified offline. Review the existing 20.6 mm Bottom CAB_FB route over Inner1 GND, and test noise and transient response. Measure BZ1 lead pitch, diameter and polarity against the nominal 7.6 mm footprint and check enclosure fit. [U1 routing history](../industrial-hmi-rev-n/U1-REROUTE.md)
3. **Native release.** Import the corrected libraries and the live schematic/PCB pair, compare schematic and PCB, inspect the copper and isolation boundaries, then run native DRC. Inspect the generated Gerbers and plated/nonplated drills in an independent CAM viewer. [Editor runbook](EDITOR-RUNBOOK.md) · [Fabrication notes](FAB-NOTES.md)

### Bring-up after release checks

1. Start the cabinet buck alone with a current-limited supply. Confirm CAB_5V, cold start at 20.4 V and loaded output ripple and transient response.
2. Bring up USB-C and the power mux. Check current advertisement, source gating and handoff, and test both input sources independently.
3. **Before fitting U2, U8 or U20**, power the board from a current-limited supply. Measure 3.3 V across C94 and at a far load such as C34. **Abort if either reading exceeds 3.45 V.** Verify startup, load regulation and temperature, including the 1.5 A rail test. Check the battery-backed RTC supply before fitting the cell.
4. Fit and test RP2354B, BOOTSEL, RESET and SWD.
5. Fit BT818, then the display and backlight, and then verify each field interface, serial port, storage and Ethernet.

[Staged bring-up procedure](BRING-UP.md)

## Future candidates

These are planning ranges per fitted board before engineering and qualification. Compare the actual Rev N dealer tier when evaluating each proposal.

| Candidate | Estimated opportunity | Qualification |
| --- | --- | --- |
| J1/J3/J6/J7/J9 generic screw terminals | ₹200–450 | Match pitch, pin-one orientation, tool access, current, wire gauge and enclosure clearances. |
| J2 generic 40-pin FPC | ₹0–40 | The exact Hirose can already be inexpensive. Verify contact side, FPC thickness, latch and lifecycle. |
| F1 smaller SMD fuse or PTC | ₹5–20 | Preserve fault interruption, surge behavior, operating temperature and cabinet input rating. |
| J10 generic microSD | ₹20–65 | Verify insertion geometry, shell and pad drawing, pin numbering, hot plug and enclosure access. |
| J11 HR911105A-class MagJack | ₹20–100 | Verify center-tap topology, isolation, Ethernet magnetics, LEDs, pegs and footprint. |
| Replace STUSB4500L with CC comparators | ₹80–170 | Implement both CC orientations, dynamic current changes, valid VBUS, detach behavior, inrush and independent BOOTSEL data gating. |
| Enable 1.5 A USB for HMI-only build | ₹0 BOM if existing hardware supports it | Estimated 1.23 A at nominal 5 V is steady state. Demonstrate startup, worst-case cable drop, current limits and enforcement of relay/load exclusion. |
| Remove BT818 | Up to the current BT818 line price before added parts and software | An 8-bit 800 × 480 buffer is 384,000 bytes. Verify memory margin, RGB timing and bandwidth, touch interface and UI performance. |
| Consolidate passive packages and feeder use | ₹0–40 material, up to the vendor’s per-feeder fee for each eliminable SKU | Review DC bias, surge ratings, pin escapes, loading class, PCB reflow and service tier. |
