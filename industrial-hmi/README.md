# Industrial touchscreen HMI · Rev A

This controller is a prototype for a Delta DOP retrofit. It uses a 24 V DC cabinet supply and one isolated, two-wire RS-485 port. The first panel is a 7-inch resistive touchscreen. The same controller and harness support the listed 5-inch and 10.1-inch panels. Cabinet cutout, PLC protocol and machine behavior depend on the exact DOP and PLC models.

## EasyEDA files

| File | Use |
| --- | --- |
| [EasyEDA ZIP](Industrial-HMI-RevA-EasyEDA.zip) | Import the schematic and routed PCB together in EasyEDA Pro via **File → Import → EasyEDA (Standard)**. |
| [Schematic source](Schematic_Industrial-HMI-RevA.json) and [PCB source](PCB_Industrial-HMI-RevA.json) | Editable EasyEDA Standard JSON files. In Standard, open via **File → Open → EasyEDA**. |
| [Schematic PDF](Industrial-HMI-RevA-Schematic.pdf) and [PCB preview](Industrial-HMI-RevA-PCB.png) | Review without the editor. |
| [BOM](Industrial-HMI-RevA-BOM.csv) | Populate the board parts and choose one touchscreen. |

The ZIP contains both Standard-format sources for Pro import. Verify the import, component bindings and schematic-to-PCB comparison in the same project before applying any updates. The import workflow is documented by EasyEDA. [EasyEDA Pro import guide](https://prodocs.easyeda.com/en/import-export/import-easyeda/) · [EasyEDA Standard source format](https://docs.easyeda.com/en/DocumentFormat/EasyEDA-Format-Standard/)

## Display and DOP fit

| Option | Display module | Resolution | Vendor supply rating | Module PCB outline |
| --- | --- | --- | --- | --- |
| Small | Nextion NX8048P050-011R | 800 × 480 | 5 V, 1 A | 136.9 × 84 mm |
| Baseline | Nextion NX8048P070-011R | 800 × 480 | 5 V, 1 A | 181 × 108 mm |
| Large | Nextion NX1060P101-011R-I | 1024 × 600 | 5 V, 2 A | 258 × 152 mm |

The vendor outlines describe the bare modules. Use the matching drawing to locate the glass, active area, screw holes, cable and microSD access. The product and drawing links identify the intended panel variants. [5-inch product](https://itead.cc/product/5-0-nextion-intelligent-series-hmi-touch-display/) · [5-inch drawing](https://cdn.nextion.tech/wp-content/uploads/2022/03/NX8048P050-011R_dimension.pdf) · [7-inch product](https://itead.cc/product/7-0-nextion-intelligent-series-hmi-resistivecapacitive-touch-display-without-enclosure/) · [7-inch drawing](https://cdn.nextion.tech/wp-content/uploads/2022/03/NX8048P070-011R_dimension.pdf) · [10.1-inch product](https://itead.cc/product/10-1-nextion-intelligent-series-hmi-touch-display/) · [10.1-inch drawing](https://cdn.nextion.tech/wp-content/uploads/2022/03/NX1060P101-011R-I_dimension.pdf)

For the 7-inch example, the Delta DOP-107BV installation guide lists a 196.9 × 142.9 mm panel cutout. A bezel or adapter plate would cover that opening and mount the 181 × 108 mm Nextion module behind the panel. Confirm the actual opening, panel thickness, mounting method and cable clearance before cutting. Delta also lists 7-inch DOPs with smaller openings. The DOP-105CQ is a 5.6-inch model, and the DOP-110CS and DOP-110WS use different openings. Confirm the suffix and the existing panel drawing for each retrofit. [Delta DOP-107BV installation guide](https://filecenter.deltaww.com/Products/download/06/060302/Manual/DELTA_IA-HMI_DOP-107BV_TC-SC-EN-TUR_20191016.pdf) · [Delta DOP-100 catalog](https://landing.deltaww.com/IA/downloadcenter/catalogue/3.Control/DOP-100/DELTA_IA-HMI-DOP-100_C_EN_20200109_web.pdf)

## Electrical connections

| Connector | Pin order | Use |
| --- | --- | --- |
| J1, 2-position screw terminal | 1 +24 V, 2 0 V | Regulated 24 V DC nominal, prototype operating range 20.4–27.6 V at J1. |
| J2, JST XH 4-position | 1 +5 V, 2 panel TX, 3 panel RX, 4 GND | Short internal harness. Cross-check mating ends by signal name before applying power. The three vendor drawings show the same four signals. |
| J3, 3-position screw terminal | 1 D0 (−), 2 D1 (+), 3 COM | 2-wire half-duplex RS-485. Map the PLC by polarity or D0/D1 and use the isolated COM as the cable reference. |

- **Power.** The fused input uses a 100 V Schottky diode for reverse protection, a 33 V standoff TVS, and a Traco THN 15-4811WI converter rated 5 V at 3 A. The converter input and output returns tie to logic GND. The 5 V load budget is 2.0 A for the large display plus 0.25 A for the controller and auxiliaries. Verify worst-case current, rail drop and temperature at full brightness. The 1.5 A time-delay fuse is a prototype choice near Traco's 1.6 A recommendation and needs inrush validation. [Traco converter datasheet](https://www.tracopower.com/sites/default/files/products/datasheets/thn15wi_datasheet.pdf) · [Littelfuse SMBJ33A](https://www.littelfuse.com/de/products/overvoltage-protection/tvs-diodes/surface-mount/smbj/smbj33a)
- **Display and service.** The Pico drives UART0 TX/RX on GP16/GP17. Separate TI buffers handle the 3.3 V and 5 V domains in both directions. The Pico's VSYS feed is diode-ORed with its onboard USB power path. For USB-only service, check that J2 stays off. At 2 A use a short harness with power conductors and crimp contacts rated for the load, and verify the voltage at the display itself. [Raspberry Pi Pico datasheet](https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf) · [TI SN74LV1T34 datasheet](https://www.ti.com/lit/ds/symlink/sn74lv1t34.pdf) · [JST XH ratings and drawings](https://www.jst-mfg.com/product/pdf/eng/eXH.pdf)
- **PLC port.** Isolated module U5 uses UART1 on GP20/GP21 and GP22 for direction. The pull-up holds receive at reset. Configure GP22 for at least 8 mA drive, drive it low to send, and allow for the module’s maximum 100 µs mode-switch delay on each edge. The external RS-485 TVS returns to RS_COM. R4 is a 120 Ω optional end-of-line resistor, DNP by default. The module already contains a weak bias network. Use RS_COM and GND as separate nets. [Mornsun transceiver datasheet](https://www.mornsun-power.com/public/uploads/pdf/TDx01D485H.pdf) · [Modbus serial-line guide](https://www.modbus.org/file/secure/modbusoverserial.pdf)

## Prototype PCB

- **Mechanical.** The board measures 94 × 74 mm and has four Ø3.2 mm NPTH holes. Hole centers are 4.5 mm from their adjacent edges. J1 faces the top, J3 faces the right and the Pico USB connector faces left. The PCB mounts behind the touchscreen on separate standoffs. The Pico solders onto two 20-pin headers with the USB port facing the board edge.
- **Stackup.** Proposed 1.6 mm FR-4 with two 1 oz copper layers. Top carries components and most signals. Bottom carries crossover tracks, a wide display return, and separate GND and RS_COM copper areas.
- **Rules.** 0.254 mm minimum trace width and general clearance. Use at least 0.40 mm around VIN nets and 0.50 mm routed copper-to-board edge. Vias use a 0.90 mm pad and 0.40 mm drill. The main 5 V feed and return use 1.27 mm traces. Both copper layers reserve a 4.25 mm minimum strip between the logic and isolated RS-485 regions. Keep copper, mounting metal and any shield connection out of this strip. [JLCPCB PCB capabilities](https://jlcpcb.com/capabilities/pcb-capabilities/)
- **Verification.** Offline checks matched 114 schematic pins to PCB pads and confirmed continuity for all 18 named nets. The routed copper measured at least 0.334 mm general clearance and 0.501 mm around VIN, before copper pours. The checks also covered drill spacing, mounting exclusions, body overlap and separation of the isolated region. Native EasyEDA import, electrical rule check, design rule check, copper fill inspection and Gerber review remain open. Rebuild pours with **Shift+B**, inspect the isolation strip and mounting keepouts on both layers, and verify that the ratlines are clear before exporting.

## PLC application and bench acceptance

The initial application assumes the HMI is the Modbus RTU client and the PLC is the server. Use a status page with live values, a communication indicator, and an explicit stale-data state. An existing DOPSoft screen project needs to be rebuilt for the selected display. Match the installed PLC's physical interface, driver, baud rate, parity, station and tag map before firmware or screen integration. The prototype PCB implements one serial port. DOP applications that use Ethernet or multiple serial ports need an interface revision.

1. On an unpowered assembly, verify connector pin numbering, reverse-protection polarity, the 5 V rail for shorts, and separation between GND and RS_COM.
2. At the ends of the 20.4–27.6 V input range, confirm the display receives 4.75–5.25 V under its rated load, including cold starts and a backlight step. Check fuse inrush behavior, diode temperature and 5 V rail sag. Test USB-only and simultaneous 24 V plus USB service.
3. Verify the harness orientation and power first, then check both UART directions and touch events.
4. With a test PLC, check at least 1,000 Modbus transactions without errors at the selected settings. Disconnect the cable and confirm the screen flags stale data. Reconnect and verify it recovers without issuing a write.
5. Before cabinet deployment, confirm the bezel fit and enclosure temperature and run the site's applicable ESD, EFT, surge and emissions tests. Board-level or enclosure-level compliance and ingress protection have yet to be demonstrated.
