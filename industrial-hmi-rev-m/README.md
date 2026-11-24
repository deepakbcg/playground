# Industrial HMI Rev M — dual power and cost review

Rev M is an EasyEDA Standard design draft for the 7-inch, 800 × 480 raw RGB HMI. Either **20.4–27.6 V DC at J1** or **5 V USB-C advertising 3 A at J4** is designed to supply the entire populated HMI. The cabinet input takes priority when both are present. A low-current USB host can program the HMI while the cabinet input powers it. The four-layer PCB measures 99.2 × 96 mm. [Rev L design](../industrial-hmi-rev-l/README.md) · [USB-IF Type-C specification](https://www.usb.org/document-library/usb-type-cr-cable-and-connector-specification-release-25)

## Design files

| File | Contents |
| --- | --- |
| [Hardware specification PDF](Industrial-HMI-RevM-Specification.pdf) | Power, display, interfaces, connector pinouts and mechanical integration. |
| [Claude Code fabrication handoff](CLAUDE.md) | Workstation setup, known routing fixes, release checks and export instructions. |
| [EasyEDA Standard ZIP](Industrial-HMI-RevM-EasyEDA.zip) | Editable Rev M schematic and four-layer PCB routing draft. |
| [Schematic JSON](Schematic_Industrial-HMI-RevM-Draft.json) · [Schematic PDF](Industrial-HMI-RevM-Draft-Schematic.pdf) | Circuit source and drawing. |
| [PCB JSON](PCB_Industrial-HMI-RevM-Draft.json) · [PCB PNG](Industrial-HMI-RevM-PCB.png) | Editable copper draft and the corresponding layer preview. |
| [BOM](Industrial-HMI-RevM-BOM.csv) · [Costed BOM](Industrial-HMI-RevM-BOM-Cost-INR.csv) | Part numbers, fit/DNP choices and the one-board INR estimate. |
| [40-pin panel pinout](Industrial-HMI-RevM-Panel-Pinout.csv) | Connector J2 signals and their board endpoints. |
| [Build configurator](Industrial-HMI-RevM-Build-Configurator.html) | Offline USB-C and cabinet power options with per-feature fit/DNP CSV export. |
| [External relay board ZIP](../industrial-hmi-rev-i/Industrial-HMI-RevI-Relays-EasyEDA.zip) · [Relay board BOM](../industrial-hmi-rev-i/Industrial-HMI-RevI-Relays-BOM.csv) | Four COM/NO/NC outputs on the separate relay board. |

The PCB JSON and PNG use the same routing snapshot. Offline checks matched 831 schematic pin nets to the PCB source and found six open nets and one clearance finding in the routed copper. Native EasyEDA import and rule checks remain pending. See [prototype verification](#prototype-verification) for the affected nets.

The earlier placement preview shows the component bodies before routing adjustments. The copper preview shows the newer component locations. [Placement PNG](Industrial-HMI-RevM-Placement.png)

## Power paths

```text
24 V terminal → fuse, reverse protection and TVS → 5 V cabinet buck ─┐
                                                                    ├→ power mux → SYS_5V
5 V USB-C → CC current detection and USB VBUS switch ────────────────┘                 │
                                                                                     ├→ backlight boost, buzzer, relay coil feed
                                                                                     └→ shared 3.3 V buck → RP2354B, LCD logic,
                                                                                           W5500, serial ports, microSD, RTC
```

| Input | Board power | USB data |
|---|---|---|
| Cabinet only | All fitted HMI circuits | Available when a host is connected |
| USB-C only, 5 V / 3 A source | All fitted HMI circuits | Available if the source is also a USB host |
| Both | Cabinet priority with reverse blocking | Available when USB connects to a host |
| USB-C only, default or 1.5 A advertised | Full board power stays off | Use cabinet power for programming from this host |

**Cabinet input.** U1 changes from a Mean Well isolated module to a TI LMR51635XDDCR synchronous buck. Rev L tied the module’s two returns to board ground. Rev M retains the fuse, reverse-polarity diode and 33 V TVS, and uses the 400 kHz TI EVM as the 5 V design reference. A 10 µH Bourns inductor matches the reference inductance and has 7.5 A RMS and 12 A saturation ratings at the datasheet test conditions. The cabinet buck starts with a 5 V nominal setpoint. The TVS specification gives 53.3 V at its rated pulse current, so the 60 V regulator operating ceiling still requires a measurement at the VIN pin under the specified surge and harness conditions. [TI 5 V EVM](https://www.ti.com/tool/LMR51635EVM) · [Bourns inductor](https://www.bourns.com/docs/product-datasheets/srp1038a.pdf) · [SMBJ datasheet](https://www.littelfuse.com/assetdocs/tvs-diodes-smbj-series-datasheet?assetguid=ba555e99-a12d-4f72-a0b6-86b06c67171e)

**USB-C.** The GCT USB4105-GF-A receptacle carries 5 V and reversible USB 2.0 data. STUSB4500L checks both CC orientations and turns on the USB power-path MOSFET after a valid attach. Its active-low 3 A flag enables the USB input of TPS2121. A default or 1.5 A source can still open the USB data path when the cabinet powers the board. The data switch gates the connection on valid USB VBUS independently of application firmware, including during RP2354B BOOTSEL. The connector has local D+/D− protection and a VBUS TVS. The existing RP2354B 27 Ω series resistors, BOOTSEL, RESET and SWD are retained. [ST sink controller](https://www.st.com/resource/en/datasheet/stusb4500l.pdf) · [GCT connector](https://gct.co/files/drawings/usb4105.pdf) · [TI USB data switch](https://www.ti.com/lit/ds/symlink/ts3usb221a.pdf) · [Raspberry Pi hardware guide](https://pip.raspberrypi.com/categories/1214-rp2350)

**Source selection.** TPS2121 merges cabinet 5 V and qualified USB VBUS onto `SYS_5V` using reverse-blocking FETs and controlled startup. Its cabinet priority divider crosses the nominal 1.06 V threshold at 4.41 V rising. The suggested 44.2 kΩ ILM resistor gives 2.5 A typical, with a 2–3 A specified limit range. Budget at most 1.8 A steady in the tested configuration to allow margin at the low end of that threshold. USB mode passes through the source voltage less the cable and switch drops. The power-path mode prioritizes either-source start and source isolation, with interruption during a loaded handoff subject to prototype measurement. [TI power mux datasheet](https://www.ti.com/lit/ds/symlink/tps2121.pdf)

**One 3.3 V converter.** TPS62902 replaces the RP2354B’s board-level LDO and the separate Ethernet converter. It has a 2 A rating, low-dropout operation and a 17 V input rating. W5500 uses shared 3.3 V, with its local bypass, analog filter, reset pulldown and chip-select pull-up retained. GP4 controls reset and GP5 becomes available. Remove the separate Ethernet power check from the firmware startup sequence. Follow WIZnet reset timing after power and clock settle. The RP2354B’s 1.1 V core regulator and the BT818’s 1.2 V core supply serve their respective ICs. Both isolated RS-485 domains and the optocoupled digital input bank retain their independent field returns. [TI 3.3 V buck](https://www.ti.com/lit/ds/symlink/tps62902.pdf) · [WIZnet hardware design guide](https://docs.wiznet.io/Design-Guide/hardware_design_guide) · [BT818 datasheet](https://brtchip.com/wp-content/uploads/2022/04/DS_BT817_8.pdf)

## 7-inch power budget

| Load | Budget on SYS_5V |
|---|---:|
| Shared 3.3 V, 1.1 A provision at 85% efficiency | 4.27 W |
| Backlight at 133 mA and 10.5 V, 80% boost efficiency | 1.75 W |
| Onboard buzzer at rated voltage | 0.15 W |
| HMI subtotal | 6.17 W |
| Four optional 5 V SPDT relay coils energized | 1.60 W |
| Total with relay board at rated coil voltage | 7.77 W |

These are engineering allocations. At 5 V they imply about 1.23 A for the HMI or 1.55 A with the relay board, before upstream path losses. Check actual full-load and startup draw at the connector and at low VBUS. Verify warm relay pickup and holding voltage over the selected USB supply, cable and harness combination before specifying external relay operation on USB. The J9 optocoupler inputs need field-side excitation to sense a switch, and any load connected to the relay contacts gets power from its field supply. The 5-inch and 10.1-inch panel options need their own panel and backlight current checks. [Rev L panel details](../industrial-hmi-rev-l/README.md#display-and-backlight) · [Backlight driver](https://www.ti.com/lit/ds/symlink/tps61165.pdf) · [Omron G5Q datasheet](https://components.omron.com/eu-en/sites/components.omron.com.eu/files/datasheet_pdf/J155-E1.pdf)

## Isolated RS-485 ports

Fit **YLPTEC TD301D485H** modules at U5 and U14 and **Bourns CDSOT23-SM712** arrays at D4 and D10. Each module integrates signal and power isolation. Both ports use 3.3 V logic, hardware UARTs and manual direction control. CON low transmits and CON high receives. J3 and J7 each carry D0, D1 and their own isolated COM. Fit the respective 120 Ω termination, R4 or R38, when the HMI is at the cable end and the cable calls for it. [YLPTEC datasheet](https://www.lcsc.com/datasheet/C2992421.pdf) · [TI RS-485 Design Guide](https://www.ti.com/lit/an/slla272d/slla272d.pdf)

The YLPTEC pin assignments, 15.24 mm row spacing, 2.54 mm pin pitch and 1.00 mm recommended holes match the PCB. The Bourns array fits the SOT-23 pin assignment, with its common on pin 3. Both arrays return to their own port's isolated COM. The copper and land geometry are preserved. Confirm lead fit and solder joints on the first assembled board. [Bourns datasheet](https://www.bourns.com/docs/product-datasheets/cdsot23-sm712.pdf)

Use **115.2 kbps** as the qualification ceiling from the module datasheet. Allow for its **25 µs maximum direction switching delay**. Verify receive mode at reset, allow the driver to settle before transmitting, and keep transmit enabled through the final stop bit. Check that the 3.3 V rail stays within 3.15–3.45 V at both modules during simultaneous terminated traffic on USB-C and cabinet power. [YLPTEC datasheet](https://www.lcsc.com/datasheet/C2992421.pdf)

During EMC testing, check each connector's TVS discharge path, isolation keepout on all four copper layers, and residual voltage at the module pins under the expected ESD, EFT and surge conditions. TI's tested surge design used the Bourns array with additional protection stages. [PCBWay layout guide](https://www.pcbway.com/blog/PCB_Design_Layout/Industrial_Grade_RS_485_Communication_Interface_Design_and_PCB_Layout_11eb36b2.html) · [TI TIDA-00731](https://www.ti.com/tool/TIDA-00731)

## One-board component cost

The Rev M main-board estimate is **₹9,073.32–₹9,193.32**, including the CR2032. The power and USB changes brought the Rev L estimate of ₹12,024.14 down to ₹10,197.30–₹10,317.30. The two RS-485 substitutions save a further **₹1,123.98**. The display, relay board, bare PCB, assembly, shipping and taxes are outside the estimate. Prices use the 24–25 November 2026 distributor snapshots and a support-parts allowance. USD amounts use the Rev L baseline exchange rate of ₹92.9189 per USD for comparability. [Rev M costed BOM](Industrial-HMI-RevM-BOM-Cost-INR.csv) · [Rev L costed BOM](../industrial-hmi-rev-l/Industrial-HMI-RevL-BOM-Cost-INR.csv)

| RS-485 parts on one board | Previous INR | Updated INR |
|---|---:|---:|
| U5 and U14, YLPTEC TD301D485H at USD 4.0420 each | 1,458.00 | 751.16 |
| D4 and D10, Bourns CDSOT23-SM712 at USD 0.4906 each | 508.32 | 91.18 |
| **Total** | **1,966.32** | **842.34** |

The module quote uses the listed promotional price for LCSC C2992421. D4 and D10 use LCSC C404012. [YLPTEC pricing](https://www.lcsc.com/brand/951-13306.html) · [Bourns pricing](https://www.lcsc.com/product-detail/C404012.html)

| Rev L parts removed or replaced | INR |
|---|---:|
| U1 Mean Well module | 2,405.91 |
| U13 and C51–C54, Ethernet regulator and supporting capacitors | 692.32 |
| U12 and R35–R36, Ethernet isolation buffer and power sense | 58.25 |
| U6 LDO | 31.53 |
| D3 and D5, source diodes | 64.98 |
| J4 Micro-USB | 44.70 |
| **Total removed** | **3,297.69** |

| Rev M added parts | INR | Price basis |
|---|---:|---|
| U1 cabinet buck | 160.41 | [LCSC, USD 1.7263](https://www.lcsc.com/product-detail/C42432812.html) |
| L3 10 µH | 108.93 | [DigiKey India](https://www.digikey.in/en/products/detail/bourns-inc/SRP1038A-100M/4876659) |
| U6 shared 3.3 V buck | 201.63 | [DigiKey India](https://www.digikey.in/en/products/detail/texas-instruments/TPS62902RPJR/14004371?s=N4IgjCBcpgTAnFUBjKAzAhgGwM4FMAaEANwDsoAXAJwFdCQB7KAbXADYB2AVngBYQAukQAOFKCADK1AJakA5iAC%2ByoA) |
| L4 1 µH | 68.05 | [DigiKey India](https://www.digikey.in/en/products/detail/shenzhen-sunlord-electronics-co-ltd/MWSA0402S-1R0MT/14120035) |
| U22 power mux | 233.14 | [DigiKey India](https://www.digikey.in/en/products/detail/texas-instruments/TPS2121RUXR/9859001) |
| U21 Type-C sink | 223.51 | [DigiKey India](https://www.digikey.in/en/products/detail/stmicroelectronics/STUSB4500LQTR/10709019) |
| Q3 power MOSFET | 131.79 | [LCSC, USD 1.4183](https://www.lcsc.com/product-image/C457492.html?whichImg=sch) |
| J4 USB-C | 76.44 | [DigiKey India](https://www.digikey.in/en/products/detail/gct/USB4105-GF-A/11198441?s=N4Ig7CBcoIYE5QIwA5EGYA0IYBcmZAAcBLJAJjDETAFYBfOoA) |
| U23 USB data switch | 86.95 | [DigiKey India list price](https://www.digikey.in/en/products/detail/texas-instruments/TS3USB221ARSER/1985512?s=N4Ig7CBcoIYE5QIwA5EGYA0IYBcmZAAcBLKATgsTABZkBfOoA) · [LCSC stock, 5-piece minimum](https://www.lcsc.com/product-detail/C128396.html) |
| C82–C96, R67–R83, Q4 and D24–D25 | 180–300 | Allowance for the remaining caps, resistors, enable FET and USB protection |
| **New parts** | **1,470.85–1,590.85** | Per fitted board |

### Further savings

| Opportunity | Recommendation |
|---|---|
| **USB-only first build** | Leave out J1, F1, D1, D2, C1, U1, L3, C2, C82–C86, R5 and R67–R70. Fit the mux, its dividers and the USB-C and 3.3 V circuits. This omits about ₹269 of priced parts plus the cabinet connector, fuse, protection and the rest of the buck passives. Add the cabinet block when needed. |
| **Populate only the interfaces needed** | Leave the Ethernet components out for a serial-only build, including the W5500 and magnetic jack, while retaining the shared power stages. The ₹775 Rev L Ethernet parts budget is a planning proxy for that saving. Omit the external relay board and buzzer on benches that only need the HMI. The buzzer alone was ₹310. Keep the unpopulated blocks disabled in firmware. [Rev L Ethernet and BOM](../industrial-hmi-rev-l/README.md#ethernet) |
| **Display controller** | BT818 remains in the full HMI. It supplies graphics acceleration, RGB timing and four-wire resistive sensing. A single 800 × 480 RGB565 frame takes 768,000 bytes against the RP2354B’s 520 kB SRAM, so removing it would change the rendering and touch design. [BT818 datasheet](https://brtchip.com/wp-content/uploads/2022/04/DS_BT817_8.pdf) · [RP2350 datasheet](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf) |

## Prototype verification

The schematic export passed named-net continuity checks for both source paths, USB-C data polarity and both CC pins, the shared logic and Ethernet rail, the five direct Ethernet signals and the field-return separation. The PCB draft still has opens on GND, SYS_5V, USB_VBUS, USB_RAW_SENSE, USB_REG27 and USB_FET_GATE. The offline geometry check found 0.116 mm clearance between the U6 mode land and the adjacent 5 V track at a 0.125 mm check threshold. Resolve those findings and verify the footprints and power routing before EasyEDA ERC and DRC, EMI and hardware characterization.

- Place both buck input capacitors at their switching loops and keep the W5500 clock and analog supply clear of the switch nodes. Recheck USB-C connector retention, stackup, 90 Ω USB routing and enclosure opening within the 100 × 100 mm limit.
- Cold-start from each supply alone and from both connection orders. Verify source priority, backfeed, startup current and loaded handoff. Test 5 V USB-C advertising 3 A, 1.5 A and default current, plus USB-A to C data with cabinet power. Check BOOTSEL in both connector orientations.
- At cold and warm cabinet conditions, run full backlight, both RS-485 links, Ethernet traffic and microSD writes together. Record the 3.3 V rail at the W5500, MCU, card and both isolated modules. Exercise the relay board and measure coil pickup and the current and voltage margins at low USB VBUS. Confirm the required fuse derating, input surge clamp and thermal performance at 20.4 V and 27.6 V cabinet input.
