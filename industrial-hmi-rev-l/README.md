# Industrial touchscreen HMI · Rev L

Rev L replaces the plug-in Ethernet module with a board-mounted W5500 and a magnetic RJ45. It uses a **99.2 × 96 mm four-layer HMI** and a **96 × 56 mm two-layer relay board**. The HMI keeps four optocoupled 24 V switch inputs, two isolated RS-485 ports, PIO RS-232, RJ45 Ethernet, battery-backed RTC, the buzzer and the green status LED. The four mechanical COM/NO/NC relays mount on the separate board. The RP2354B handles the four inputs and relay commands directly, and its in-package 2 MB flash holds the firmware. The top-side microSD socket shares SPI0 with the display. Both outlines are below 100 × 100 mm and can be quoted separately. [Rev K baseline](../industrial-hmi-rev-k/README.md) · [RP2350 hardware guide](https://pip.raspberrypi.com/categories/1214-rp2350)

## Design files

| File | Contents |
| --- | --- |
| [Build configurator](Industrial-HMI-RevL-Build-Configurator.html) | Offline feature map, power options, parts estimates and fit/DNP export for staged assembly. |
| [EasyEDA import ZIP](Industrial-HMI-RevL-EasyEDA.zip) | Editable HMI schematic and routed prototype PCB in EasyEDA Standard format. |
| [EasyEDA schematic](Schematic_Industrial-HMI-RevL.json) · [Schematic PDF](Industrial-HMI-RevL-Schematic.pdf) | Cabinet interfaces, RP2354B core, BT818, backlight and battery-backed RTC, Ethernet, both isolated serial ports, direct GPIO input bank, relay link, indicators and shared-SPI microSD. |
| [EasyEDA PCB](PCB_Industrial-HMI-RevL.json) · [PCB preview](Industrial-HMI-RevL-PCB.png) | Four-layer HMI and a detail of the RP2354B and service area. |
| [BOM](Industrial-HMI-RevL-BOM.csv) · [Costed BOM](Industrial-HMI-RevL-BOM-Cost-INR.csv) · [Panel pinout](Industrial-HMI-RevL-Panel-Pinout.csv) | PCB, panel and battery part numbers with all 40 panel cable connections. |
| [Relay board EasyEDA ZIP](../industrial-hmi-rev-i/Industrial-HMI-RevI-Relays-EasyEDA.zip) · [Relay schematic PDF](../industrial-hmi-rev-i/Industrial-HMI-RevI-Relays-Schematic.pdf) | Separate two-layer board with four independently isolated COM/NO/NC terminals. |
| [Relay board preview](../industrial-hmi-rev-i/Industrial-HMI-RevI-Relays-PCB.png) · [Relay board BOM](../industrial-hmi-rev-i/Industrial-HMI-RevI-Relays-BOM.csv) | Relay board layout and fitted parts. |

In EasyEDA Pro, use **File → Import → EasyEDA (Standard)** with the ZIP. The QFN-80 footprint, core buck and crystal layout, and stencil artwork derive from Raspberry Pi’s RP2350B Minimal KiCad R4-S1 reference. Rev L omits the reference external flash and its select links and retains the momentary BOOTSEL circuit for the RP2354B’s internal flash. The included MIT license accompanies that work. [EasyEDA Pro import](https://prodocs.easyeda.com/en/import-export/import-easyeda/) · [Raspberry Pi reference design](https://pip.raspberrypi.com/categories/1214-rp2350) · [Reference license](Raspberry-Pi-Reference-LICENSE.txt)

## Cabinet power and startup qualification

**U1 is a Mean Well SKMW15W8-05**. It supplies 5 V at up to 3 A from the fused, reverse-protected 24 V cabinet feed. Its 9–75 V input rating applies at the module. J1 is designed for 20.4–27.6 V DC. Both converter returns share board GND. Remote on/off and trim are open, so U1 starts when cabinet voltage is applied and uses its factory output setting. Pin 1 goes in the square pad. The 25.4 × 25.4 × 10.2 mm housing uses the existing 1.30 mm holes. Check enclosure clearance above the housing and below the soldered leads. [Mean Well datasheet](https://www.simpex.ch/wp-content/uploads/2026/05/SKMW15W8_DKMW15W8-spec-SI.pdf)

| U1 pin | Function | PCB connection |
| --- | --- | --- |
| 1 | +VIN | VIN_PROT |
| 2 | −VIN | GND |
| 3 | Remote on/off | Open |
| 4 | −VOUT | GND |
| 5 | Trim | Open |
| 6 | +VOUT | PANEL_5V |

The 5 V capacitors connected directly to U1 total **68 µF nominal** on the HMI and **115 µF** with the stock relay board fitted. C11 adds 10 µF through D3. The stated U1 output capacitance limit is 680 µF. Allow for any external capacitance and downstream startup loads. At 15 W output, estimated steady input current is **0.87 A** at 20.4 V cabinet input, using 88% typical conversion efficiency and 0.9 V allowed for the fuse, diode and path drop. F1's 1.5 A nominal rating corresponds to **1.125 A** at 25 °C after Littelfuse's continuous-use derating, before adjusting for fuse ambient temperature. Mean Well measured 0.699 A at 24 V and full load and demonstrated module turn-on at −40 °C and 24 V. The report provides no input-current trace at turn-on. [Mean Well datasheet](https://www.simpex.ch/wp-content/uploads/2026/05/SKMW15W8_DKMW15W8-spec-SI.pdf) · [Mean Well verification report](https://www.simpex.ch/wp-content/uploads/2026/05/SKMW15W8-05-rpt.pdf) · [Littelfuse 452 series datasheet](https://www.littelfuse.com/assetdocs/fuse-452-and-454-datasheet?assetguid=8c87aa93-80a7-4ea8-8749-a19ba03901c2)

**F1 stays at 1.5 A slow-blow for the prototype.** Mean Well recommends 4 A slow-blow for the module. Approve any change only after checking the cabinet supply's available fault current and current limit, upstream protection, D1 and D2 surge limits, and PCB and wiring limits. The module's Class B reference circuit includes an input common-mode choke. Evaluate EMC on the assembled HMI with its cabinet harness. [Mean Well application circuit](https://www.simpex.ch/wp-content/uploads/2026/05/SKMW15W8_DKMW15W8-spec-SI.pdf#page=4) · [D1 datasheet](https://www.diodes.com/datasheet/download/B2100A.pdf)

1. With USB unplugged, log input current at J1, VIN_PROT, and PANEL_5V at TP1 referenced to TP2. Use the intended cabinet supply and harness. Capture a startup from discharged rails at **20.4, 24.0 and 27.6 V**, at room temperature and at the intended cold limit. Use firmware that sets full backlight on startup. Capture the first power-up and the subsequent backlight turn-on.
2. At full brightness, exercise Ethernet, sustained SD writes and all four relay coils. Capture the load step and run a hot enclosure soak at the intended maximum cabinet temperature. Verify that PANEL_5V settles within **4.75–5.25 V**, that the HMI boots and stays running, and that the steady input current is under F1's temperature-adjusted continuous limit. Compare the measured U1 case temperature and output load with Mean Well's derating curve.
3. Record peak input current, pulse duration, and integrated current squared over the inrush pulse. Compare with F1's time-current and pulse-life limits and D1's surge limits. Repeat power cycling at the intended cadence and check that F1 holds and the HMI starts every time. Qualify input-fault clearing separately with the actual cabinet protection. [Littelfuse fuse selection guide](https://m.littelfuse.com/~/media/electronics/product_catalogs/littelfuse_fuseology_selection_guide.pdf%20.pdf)

## Display and backlight

The design targets **Adafruit PID 2354, panel CH700WV03A-T**. It has an 800 × 480 display, RGB888, a 3.3 V logic interface and four-wire resistive touch. The panel is 164.9 × 100.0 mm with a 154.08 × 85.92 mm active area. J2 is a bottom-contact Hirose FH12 40-position, 0.5 mm-pitch FPC connector. Confirm the cable contact orientation and enclosure fit with a sample. Each additional size and each Delta DOP cabinet cutout needs its own mechanical drawing and panel definition. [Adafruit panel](https://www.adafruit.com/product/2354) · [Panel datasheet](https://cdn-shop.adafruit.com/product-files/2354/Datasheet+.pdf) · [Hirose connector](https://www.hirose.com/en/product/p/CL0586-0527-7-55)

The TPS61165 backlight driver uses the cabinet-powered 5 V rail. R25 sets a nominal **133 mA** LED current. The panel specifies **140 mA typical** and **9.3–10.5 V** forward voltage. Use 10 kHz PWM from the BT818 for dimming. During USB-only service, the 3.3 V logic may power up and the cabinet-fed backlight supply stays off. [TPS61165 datasheet](https://www.ti.com/lit/ds/symlink/tps61165.pdf) · [Panel datasheet](https://cdn-shop.adafruit.com/product-files/2354/Datasheet+.pdf)

## Cabinet wiring and MCU assignments

| Interface | Assignment |
| --- | --- |
| J1 cabinet input | 1 +24 V, 2 0 V. Designed for 20.4–27.6 V DC. |
| J2 LCD | 40-position FPC with RGB888, pixel clock, enable, sync, resistive touch, logic power and backlight. |
| J3 isolated RS-485 port 1 | 1 D0 (−), 2 D1 (+), 3 isolated COM. R4 is an optional 120 Ω termination, DNP by default. |
| J6 RS-232 | 1 HMI TXD, 2 HMI RXD, 3 logic GND. PIO TX on GP0 and RX on GP1. J6 retains the RS-232 level translator. |
| J7 isolated RS-485 port 2 | 1 D0 (−), 2 D1 (+), 3 RS2_COM. The connector uses 3.5 mm pitch. R38 is optional 120 Ω termination, DNP by default. |
| J8 link to relay board | 1 logic GND, 2 cabinet 5 V, 3 DO1, 4 DO2, 5 DO3, 6 DO4. Match pin numbers at relay board J1. |
| J9 optocoupled inputs | 1 field COM (0 V), 2 IN1, 3 IN2, 4 IN3, 5 IN4. External 24 V DC switched into each channel. |
| Direct digital inputs | GP33, GP34, GP35 and GP36 read IN1–IN4 respectively. Optocoupler outputs are active low. |
| Direct relay commands | GP37, GP38, GP39 and GP40 drive DO1–DO4 respectively. J8 commands are active high. |
| J11 Ethernet | 10/100 RJ45. SPI1 GP8 MISO, GP26 SCK and GP11 MOSI. GP25 chip select, GP4 reset and GP5 power sense. |
| BT818 SPI0 | GP16 MISO, GP17 CS_N, GP18 SCK, GP19 MOSI. |
| J10 microSD SPI0 | Shares GP16 MISO through U19, GP18 SCK and GP19 MOSI. GP10 is card CS_N and U19 enable. |
| RTC I²C0 | GP12 SDA, GP13 SCL, 7-bit address `0x52`. |
| BT818 power-down | GP23 PD_N, active low, with a 47 kΩ pull-down. |
| RS-485 port 1 UART1 | GP20 TX, GP21 RX. GP22 low to transmit and high to receive. Allow up to 100 µs for direction changes. |
| RS-485 port 2 UART0 | GP28 TX, GP29 RX and GP14 direction. GP14 low transmits and high receives. |
| Local outputs | RP2354B GP24 status LED and GP6 buzzer. Both are active high. |
| Service | Micro-USB, BOOTSEL, RESET and 3-pin SWD. The MCU has 2 MB of in-package QSPI flash. |

Sixteen RP2354B GPIOs are unassigned on the schematic. These are GP2, GP3, GP7, GP9, GP15, GP27, GP30–GP32 and GP41–GP47. I²C0 serves the RTC at address `0x52`. Use the Pico SDK’s per-pin GPIO functions for GP33–GP40.

The application firmware still needs the PLC register map, Modbus RTU settings and operator screens. For display bring-up, start with the BT818 in single-SPI mode and the backlight off. Use the panel's nominal 33.3 MHz pixel clock, 1056 × 525 total timing and 800 × 480 active area as the starting point. Check rising-edge sampling, active-low syncs and active-high data enable on J2. Apply valid timing and wait at least ten frames before enabling the backlight. Verify the first frame, touch calibration and low-duty brightness on the actual panel. [Panel datasheet](https://cdn-shop.adafruit.com/product-files/2354/Datasheet+.pdf) · [BT81x programming guide](https://brtchip.com/wp-content/uploads/2025/07/BRT_AN_033_BT81X-Series-Programming-Guide.pdf)

## Firmware flash and service

Configure the Pico SDK board for RP2354B with `PICO_RP2350A=0` and `PICO_FLASH_SIZE_BYTES=2097152`. Leave room in the 2 MiB flash map for settings, alignment and updates. Check the actual application size before selecting an update scheme. BOOTSEL uses the QSPI chip-select strap through a 1 kΩ resistor and remains available over USB alongside SWD and the separate RESET button. Keep runtime settings in onboard flash. The microSD remains available for logs and backups. [Raspberry Pi hardware design guide](https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-008280-DS-2-hardware-design-with-rp2350.pdf) · [Pico SDK board configuration](https://github.com/raspberrypi/pico-sdk/blob/master/src/boards/include/boards/pico2.h)

## microSD storage

J10 is a Hirose DM3D-SF push-pull socket on the top side. Insert the card from the left PCB edge, between the 24 V connector and the USB connector. The inserted card extends about 3.3 mm beyond the PCB outline. The case needs clearance for that overhang and a recess for fingers to grip the card. Check card access with the display and cabinet enclosure installed. Change cards with the HMI powered off. The D2 input TVS moves toward J1 to make space for the socket, and its cathode still connects to the fused, reverse-protected 24 V rail. [Hirose recommended mounting pattern](https://www.hirose.com/product/download/?distributor=mouser&lang=en&num=DM3AT-SF-PEJM5&type=catalogue)

U19 buffers the card's MISO and turns off when GP10 is high. The BT818 uses its own select on GP17. D23 protects the four SPI signals near the card port and the socket shield is tied to logic ground. Local bypass capacitors decouple the socket and buffer. The card-detect contacts are open, and firmware can probe for the card with a bounded timeout. [TI SN74LVC1G125](https://www.ti.com/lit/ds/symlink/sn74lvc1g125.pdf) · [TI TPD4E1B06](https://www.ti.com/lit/ds/symlink/tpd4e1b06.pdf)

1. Drive both chip selects high, set SPI0 to mode 0, and initialize the card at 100–400 kHz. Supply at least 74 initial clocks with the card deselected and MOSI high, then select the card and enter SPI mode with CMD0. Keep the BT818 deselected through this operation. Continue display startup when card initialization times out.
2. Serialize access to SPI0. Set the appropriate SPI clock before asserting chip select. Raise card CS after each transaction and provide one idle byte with both devices deselected. Start bring-up at a conservative SPI rate and qualify the rate with the final harness, card and display.
3. Queue log writes and give display and touch transfers bus time between card operations. Use a bounded card busy timeout. Keep boot and the active HMI configuration in onboard flash. Periodically flush file data and stop logging cleanly before removing power. [SD Association physical layer specification](https://www.sdcard.org/downloads/pls/) · [Shared SPI timing](https://elm-chan.org/docs/mmc/mmc_e.html#spi) · [FatFs data logging](https://elm-chan.org/fsw/ff/doc/sync.html)

## Serial ports and Ethernet

J3 and J7 are independent isolated buses that can operate alongside J6. Keep their isolated COM terminals separate. Each port has its own protection and optional end termination. J6 uses a TI TRS3232E for three-wire RS-232, with logic ground as its signal return. Connect HMI TXD to the peer's RXD and HMI RXD to the peer's TXD. The two interfaces use different physical signaling. A selectable serial port would need hardware that selects the appropriate transceiver with a defined disabled state during changeover. [TRS3232E datasheet](https://www.ti.com/lit/ds/symlink/trs3232e.pdf)

Use two PIO state machines for J6, one each for TX and RX. Start loopback at 19.2 kbit/s, 8 data bits, no parity and one stop bit (8N1). Match the connected device's baud and framing, including parity and stop-bit settings if it requires them. Initialize the TX state machine with the output idle high and use USB for the debug console. Run loopback with the display and both RS-485 ports active to check buffering. [Raspberry Pi PIO UART examples](https://github.com/raspberrypi/pico-examples/tree/master/pio)

Initialize the two RS-485 direction GPIOs high for receive. Set GP28 and GP14 pad drive strength to 8 mA before enabling UART0 transmission. Set direction low at least 100 µs before writing a frame. Once the UART has shifted out the final stop bit, return direction high. Allow for the transceiver's receive-enable time and verify that it receives the earliest peer response. Use GP22 for UART1 direction and GP14 for UART0 direction. Confirm both interfaces with the actual transceiver and PLC. [RP2350 GPIO functions](https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-008373-DS-4-rp2350-datasheet.pdf) · [Pico SDK hardware API](https://www.raspberrypi.com/documentation/pico-sdk/hardware.html) · [Mornsun transceiver datasheet](https://www.mornsun-power.com/public/uploads/pdf/TDx01D485H.pdf)

U20 is the **WIZnet W5500** with integrated MAC, PHY, and hardware TCP/IP. J11 is the **LINK-PP LPJ4011ABNL** 10/100 magnetic RJ45. It faces the bottom PCB edge. The jack uses two separate PHY center taps. The TX tap is biased from filtered analog 3.3 V through 10 Ω and bypassed to GND. The RX tap sits at the 49.9 Ω termination midpoint and is AC-coupled to GND. C70 and C71 are the 6.8 nF RX series capacitors used in WIZnet's WIZ850io reference. The jack includes cable-side termination, magnetics, and link and activity LEDs. The port has no PoE circuit. [WIZnet reference schematic](https://docs.wiznet.io/assets/files/wiz850io_sch_v110-3fcc19fc2acaf16f15c5f08f9c8330cb.pdf) · [LPJ4011ABNL drawing](https://cdn.promelec.ru/upload/grab/datasheet.lcsc.com/lcsc/2507101715_LINK-PP-LPJ4011ABNL_C49274777.pdf)

The W5500 retains the cabinet-powered TPSM84203 3.3 V rail and the SN74LVC125A input buffer. FB1 filters the analog supply. X3 is a 25 MHz crystal with 18 pF starting load capacitors. Verify oscillator frequency and startup on hardware. PMODE is strapped high for auto-negotiation. C74 couples the jack shell to logic ground and the shell should make contact with the conductive enclosure at the opening. The nominal jack face extends 0.85 mm past the board edge. Confirm the port cutout and cable plug clearance using the connector drawing. [W5500 datasheet](https://docs.wiznet.io/img/products/w5500/W5500_ds_v110e.pdf) · [WIZnet hardware design guide](https://docs.wiznet.io/Design-Guide/hardware_design_guide)

Keep MISO configured as an input without pull-ups. Wait for ETH_POWER_OK, set chip select high, hold reset low for at least 500 µs, and wait 50 ms after releasing reset before the first SPI access. Start at 1 MHz in mode 0 and read VERSIONR for 0x04. The hardware supports the existing SPI1 firmware pinout. Firmware supplies the unit MAC address and IP configuration and polls the W5500 because INTn is open. Bench-test 10 and 100 Mb/s links, Modbus TCP, enclosure ESD, and Ethernet traffic while the display, microSD and isolated serial ports operate. [W5500 register and timing specification](https://docs.wiznet.io/img/products/w5500/W5500_ds_v110e.pdf)

The discrete Ethernet parts budget is **₹774.52 per board**, including ₹150 for the additional passives. The plug-in module was ₹2,113.57 in the Rev K cost estimate. The resulting Rev L main-board component budget is **₹12,024.14** before shipping, taxes and assembly. Jack price uses LCSC and the 24 November ECB rate. [Costed BOM](Industrial-HMI-RevL-BOM-Cost-INR.csv) · [ECB rates](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html)

## Optocoupled inputs and external relays

### J9 switch wiring

Wire field-supply 0 V to J9 pin 1. Route external field +24 V through each NO or NC switch to its input terminal. The four field inputs share a return and use a Lite-On LTV-847S quad optocoupler for isolation from logic. For system-level galvanic isolation, keep the external field return separate from logic ground. A closed contact applies 24 V and the corresponding GPIO reads low. Configure each channel's NO/NC interpretation and debounce in firmware. [Lite-On LTV-847S datasheet](https://media.digikey.com/pdf/data%20sheets/lite-on%20pdfs/ltv-817_827_847%28m%2Cs%2Cs_ta1%29.pdf)

Each input uses a 2 kΩ series resistor, an 8.2 V series Zener, a reverse clamp across the LED and a bidirectional 33 V TVS at the input. The design targets 20.4–27.6 V DC for the active state and an open switch for the inactive state. At 24 V the nominal LED current is about 7 mA. Verify input thresholds and protection on the assembled board. [Nexperia Zener](https://www.nexperia.com/product/BZT52H-B8V2-Q) · [Littelfuse SMF TVS series](https://www.littelfuse.com/~/media/electronics/datasheets/tvs_diodes/littelfuse_tvs_diode_smf_datasheet.pdf.pdf)

### Relay board

Use a short straight-through **six-position JST XH harness** within the enclosure. Connect HMI J8 to relay board J1 with each pin number matched, including pin 1. Both boards use the same keyed header. Use XHP-6 receptacle housings and contacts matched to the wire gauge. Pin 2 carries cabinet-fed 5 V. Pins 3–6 carry active-high 3.3 V commands. The relay-board gate pull-downs default the coils off when a command is open. Check the 5 V rail at the relay board when switching all four coils with the display powered. [JST XH series](https://www.jst.com/products/crimp-style-connectors-wire-to-board-type/xh-connector/)

Relay board J2–J5 are outputs 1–4 respectively. Each has pin 1 COM, pin 2 NO and pin 3 NC. COM connects to NC when its coil is off. Each contact set is isolated from logic and from the other relay contact sets. Use an external load supply and protection. The design targets **24 V DC resistive loads up to 1 A per relay**. [Omron G5Q series](https://components.omron.com/eu-en/sites/components.omron.com.eu/files/datasheet_pdf/J155-E1.pdf)

The status LED and 5 V buzzer are on the HMI. Configure GP33–GP36 as inputs and keep the existing external pull-ups enabled in hardware. Preload GP37–GP40 low before enabling their output drivers. The relay board’s 100 kΩ gate pull-downs hold the four MOSFETs off during reset or with the control harness disconnected. Use the physical RESET button to verify coil release, then verify the application’s power-up output policy.

## Battery-backed RTC

**U10 is a Micro Crystal RV-3028-C7** with an integrated crystal. It runs from switched 3.3 V and uses a primary 3 V **CR2032** on its VBACKUP pin. The cell powers timekeeping during cabinet outages. R31 and R32 each pull the bus up to switched 3.3 V through 4.7 kΩ. CLKOUT and INT_N are open and EVI is tied to GND. [RV-3028-C7 application manual](https://www.microcrystal.com/fileadmin/Media/Products/RTC/App.Manual/RV-3028-C7_App-Manual.pdf)

BT1 is a Keystone 3034 retainer. Keep the retainer's access notch toward the lower board edge and check that the case leaves room to slide the cell out. Install the cell after reflow with its **positive face up**. Confirm about 4.1 mm of retainer height above the PCB and allow clearance for insertion and removal. [Keystone 3034 drawing](https://www.mouser.com/datasheet/2/215/3034-743109.pdf) · [Panasonic CR2032](https://www.digikey.com/en/products/detail/panasonic-bsg/CR2032/P189-ND/31939)

### Provision and test the RTC

1. Power the HMI from the cabinet or USB. Read U10 at address `0x52` with I²C0 at 100 kHz. Poll EEbusy in Status `0x0E` bit 7 until the initial EEPROM refresh completes.
2. On first provisioning, use the manual's configuration EEPROM update procedure in sections 4.6.7–4.6.9. Read-modify-write the RAM mirror of Backup `0x37` with `(old & 0xD3) | 0x1C`. This sets level switching (`BSM=11`), keeps fast-edge detection enabled (`FEDE=1`), clears the trickle charger enable bit (`TCE=0`) and preserves the calibration bit. Factory parts ship with switchover disabled.
3. With stable main power, disable automatic refresh by setting EERD in Control 1 `0x0F` bit 3, wait for EEbusy to clear, write the new Backup RAM value, then write `0x00` followed by `0x11` to EECMD `0x27`. Wait at least 10 ms before polling EEbusy. When it clears, restore automatic refresh. Read the configuration back after a complete power cycle. Program EEPROM during provisioning or when the configuration changes.
4. Set the calendar to UTC and clear the power-on reset flag. Disconnect cabinet power and USB for at least 60 seconds. Restore power and check that time advanced by the elapsed interval and that the power-on reset flag stayed clear. A set power-on reset flag at boot means the stored timestamp needs validation before logging or displaying it.

The HMI application still needs to integrate the RTC read and time-setting flows. [Configuration and switchover procedures](https://www.microcrystal.com/fileadmin/Media/Products/RTC/App.Manual/RV-3028-C7_App-Manual.pdf)

## PCB stackup and verification

The main HMI uses four layers with a nominal 1.0 mm FR-4 stack and adapts the RP2350B R4-S1 reference artwork around the QFN-80. The main bottom layer supplies the USB pair's return through the inherited opening in L2. L2 is primarily ground, with local routing for the core-to-card SPI MOSI escape and the W5500 section. The relay board uses two copper layers and a local ground pour in its low-voltage section. Each contact set is kept separate from that section and from the other relay contact sets.

The prototype passes offline PCB connectivity and copper geometry checks, including the RJ45 plane clearance and the two locating-hole clearances. The bare board remains 99.2 × 96.0 mm. Projected trace length, excluding via barrels and the RX series capacitors, is 5.86 and 5.45 mm for TX and about 13.66 mm per RX leg. These lengths exclude electrical skew from transitions and coupling. Confirm the 100 Ω routing and return paths on the chosen fabrication stackup and review the 25 MHz layout and shell bonding. Run native EasyEDA DRC and inspect fabrication plots before release. Board bring-up includes the Ethernet tests, cabinet power startup, USB-only operation, boot and reset, the LCD and touchscreen, RTC backup, SD logging, both RS-485 ports, RS-232, optocoupled inputs and the existing relay harness.
