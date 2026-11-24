# Industrial touchscreen HMI · Rev H

Rev H adds **four optocoupled 24 V DC switch inputs** and **three SPDT outputs** to the Rev G industrial HMI. The board has four independent relay outputs in total. The RP2350A keeps hardware UARTs on both isolated RS-485 ports and PIO RS-232. The BT818 drives the 7-inch RGB resistive display. The four-layer PCB measures **154 × 96 mm**. The six existing mounting holes and connectors stay at their Rev G positions. Two additional mounting holes support the right-hand expansion. Existing RS-485 cables turn upward from J3 and J7 to clear the expansion. [Rev G baseline](../industrial-hmi-rev-g/README.md) · [RP2350 hardware guide](https://pip.raspberrypi.com/categories/1214-rp2350) · [BT818 datasheet](https://brtchip.com/wp-content/uploads/Support/Documentation/Datasheets/ICs/EVE/DS_BT817_8.pdf)

## Design files

| File | Contents |
| --- | --- |
| [EasyEDA import ZIP](Industrial-HMI-RevH-EasyEDA.zip) | Editable schematic and routed PCB in EasyEDA Standard format. |
| [EasyEDA schematic](Schematic_Industrial-HMI-RevH.json) · [Schematic PDF](Industrial-HMI-RevH-Schematic.pdf) | Cabinet interfaces, RP2350A core, BT818, backlight and battery-backed RTC, Ethernet, both isolated ports, four switch inputs, four relay outputs and indicators. |
| [EasyEDA PCB](PCB_Industrial-HMI-RevH.json) · [PCB preview](Industrial-HMI-RevH-PCB.png) | Four-layer board and a detail of the expanded cabinet inputs and outputs. |
| [BOM](Industrial-HMI-RevH-BOM.csv) · [Panel pinout](Industrial-HMI-RevH-Panel-Pinout.csv) | PCB, panel and battery part numbers with all 40 panel cable connections. |

In EasyEDA Pro, use **File → Import → EasyEDA (Standard)** with the ZIP. The RP2350A reference layout and stencil artwork derive from Raspberry Pi’s RP2350A Minimal KiCad R4-S1 reference. The included MIT license accompanies that work. [EasyEDA Pro import](https://prodocs.easyeda.com/en/import-export/import-easyeda/) · [Raspberry Pi reference design](https://pip.raspberrypi.com/categories/1214-rp2350) · [Reference license](Raspberry-Pi-Reference-LICENSE.txt)

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
| J7 isolated RS-485 port 2 | 1 D0 (−), 2 D1 (+), 3 RS2_COM. R38 is optional 120 Ω termination, DNP by default. |
| J8, J10, J11, J12 | Relay outputs 1–4 respectively. Each terminal block is 1 COM, 2 NO, 3 NC. Supply each load externally. |
| J9 switch inputs | 1 field COM (0 V), 2 IN1, 3 IN2, 4 IN3, 5 IN4. Switch external +24 V into each input. |
| Cabinet I/O I²C0 | U17 MCP23008 at 7-bit `0x20`. Expander GP3–6 read IN1–IN4 and GP0–2 drive relays 2–4. GP10 on the RP2350A drives relay 1 directly. |
| M1 Ethernet | 10/100 RJ45. SPI1 GP8 MISO, GP26 SCK and GP11 MOSI. GP25 chip select, GP4 reset and GP5 power sense. |
| BT818 SPI0 | GP16 MISO, GP17 CS_N, GP18 SCK, GP19 MOSI. |
| RTC I²C0 | GP12 SDA, GP13 SCL, 7-bit address `0x52`. |
| BT818 power-down | GP23 PD_N, active low, with a 47 kΩ pull-down. |
| RS-485 port 1 UART1 | GP20 TX, GP21 RX. GP22 low to transmit and high to receive. Allow up to 100 µs for direction changes. |
| RS-485 port 2 UART0 | GP28 TX, GP29 RX and GP14 direction. GP14 low transmits and high receives. |
| Outputs | GP24 status LED, GP10 relay coil and GP6 buzzer. All are active high. |
| Service | Micro-USB, BOOTSEL, RESET and 3-pin SWD. The MCU has 4 MB external flash. |

Six RP2350A GPIOs are unassigned on the schematic. These are GP2, GP3, GP7, GP9, GP15 and GP27. The new I/O expander shares the RTC bus on GP12 and GP13.

The application firmware still needs the PLC register map, Modbus RTU settings and operator screens. For display bring-up, start with the BT818 in single-SPI mode and the backlight off. Use the panel's nominal 33.3 MHz pixel clock, 1056 × 525 total timing and 800 × 480 active area as the starting point. Check rising-edge sampling, active-low syncs and active-high data enable on J2. Apply valid timing and wait at least ten frames before enabling the backlight. Verify the first frame, touch calibration and low-duty brightness on the actual panel. [Panel datasheet](https://cdn-shop.adafruit.com/product-files/2354/Datasheet+.pdf) · [BT81x programming guide](https://brtchip.com/wp-content/uploads/2025/07/BRT_AN_033_BT81X-Series-Programming-Guide.pdf)

## Serial ports and Ethernet

J3 and J7 are independent isolated buses that can operate alongside J6. Keep their isolated COM terminals separate. Each port has its own protection and optional end termination. J6 uses a TI TRS3232E for three-wire RS-232, with logic ground as its signal return. Connect HMI TXD to the peer's RXD and HMI RXD to the peer's TXD. The two interfaces use different physical signaling. A selectable serial port would need hardware that selects the appropriate transceiver with a defined disabled state during changeover. [TRS3232E datasheet](https://www.ti.com/lit/ds/symlink/trs3232e.pdf)

Use two PIO state machines for J6, one each for TX and RX. Start loopback at 19.2 kbit/s, 8 data bits, no parity and one stop bit (8N1). Match the connected device's baud and framing, including parity and stop-bit settings if it requires them. Initialize the TX state machine with the output idle high and use USB for the debug console. Run loopback with the display and both RS-485 ports active to check buffering. [Raspberry Pi PIO UART examples](https://github.com/raspberrypi/pico-examples/tree/master/pio)

Initialize the two RS-485 direction GPIOs high for receive. Set GP28 and GP14 pad drive strength to 8 mA before enabling UART0 transmission. Set direction low at least 100 µs before writing a frame. Once the UART has shifted out the final stop bit, return direction high. Allow for the transceiver's receive-enable time and verify that it receives the earliest peer response. Use GP22 for UART1 direction and GP14 for UART0 direction. Confirm both interfaces with the actual transceiver and PLC. [RP2350 GPIO functions](https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-008373-DS-4-rp2350-datasheet.pdf) · [Pico SDK hardware API](https://www.raspberrypi.com/documentation/pico-sdk/hardware.html) · [Mornsun transceiver datasheet](https://www.mornsun-power.com/public/uploads/pdf/TDx01D485H.pdf)

M1 is a WIZ850io module with the W5500, Ethernet magnetics and RJ45 jack. The carrier uses two through-hole rows of six pins on a 2.54 mm pitch with 20.32 mm row spacing. M1's J1 SPI row is on the right when the jack faces the lower PCB edge. The original mounting positions are retained. J3 and J7 wires exit above the expansion area. Allow enough cable bend radius and top access for terminal screws. Confirm network plug clearance, terminal access and the coin-cell removal path in the enclosure. [WIZ850io pin and mechanical drawings](https://docs.wiznet.io/Product/ioModule/WIZ850io)

The Ethernet circuitry runs from a dedicated TPSM84203 3.3 V supply on the cabinet-powered 5 V rail. The SN74LVC125A buffers four MCU outputs when Ethernet is powered and provides power-off isolation as the Ethernet rail drops. Keep MISO configured as an input without pull-ups and check the Ethernet power-sense input before communication. After the rail is present, set chip select high, hold WIZ850io reset low for at least 500 µs and wait at least 50 ms after releasing reset before starting SPI. Use SPI mode 0 for initial bring-up. An Ethernet link and Modbus TCP require firmware configuration and a network test. [TPSM84203](https://www.ti.com/lit/ds/symlink/tpsm84203.pdf) · [SN74LVC125A](https://www.ti.com/lit/ds/symlink/sn74lvc125a.pdf) · [WIZ850io operating instructions](https://docs.wiznet.io/Product/ioModule/WIZ850io)

## Isolation and field wiring

The four inputs use Vishay VO617A-4X017T optocouplers. Their field sides share J9 COM and their logic sides switch independently. Each RS-485 port uses its own Mornsun TD301D485H module with integrated signal and power isolation. The four relay outputs isolate the load using mechanical contacts. RS-232 uses logic ground as its signal return. [Vishay optocoupler](https://www.vishay.com/docs/83430/vo617a.pdf) · [Mornsun module description](https://www.mornsun-power.com/html/products-detail/TDx01D485H.html) · [Omron relay](https://components.omron.com/eu-en/sites/components.omron.com.eu/files/datasheet_pdf/J155-E1.pdf)

### J9 inputs

1. Connect the external field supply's 0 V to J9 pin 1. Route field +24 V through the switch contact to its IN terminal. Leave the field return separate from HMI logic ground when system-level galvanic isolation is required.
2. Use the switch's NO or NC contact as appropriate. A closed contact applies +24 V and the corresponding expander input reads low. An open contact reads high. In firmware, map this physical state to the configured NO or NC switch convention and debounce it.
3. Test each input at **20.4–27.6 V DC** and with an open contact. Each channel has a reverse LED clamp, a series 8.2 V Zener, two 1 kΩ pulse-rated resistors and a 33 V bidirectional TVS. Typical LED current is about 7 mA at 24 V. Verify switching thresholds, bounce, leakage and surge performance on the assembled unit. [Vishay optocoupler](https://www.vishay.com/docs/83430/vo617a.pdf) · [Nexperia Zener](https://www.nexperia.com/product/BZT52H-B8V2-Q) · [Panasonic resistors](https://industrial.panasonic.com/ww/products/pt/small-and-high-power-chip-resistors/models/ERJP08F1001V)

### Relay outputs and indicators

J8, J10, J11 and J12 use G5Q-1-EU SPDT relays. For each output, COM connects to NC with the coil off and to NO with the coil on. Rev H targets **24 V DC resistive pilot loads up to 1 A per output**. Supply and protect each load externally. Cabinet 5 V supplies the four coils. The coil MOSFETs have hardware gate pull-downs. Test the 5 V rail with all four relays and the buzzer on alongside the backlight, Ethernet and both loaded RS-485 ports. [Omron G5Q series](https://components.omron.com/eu-en/sites/components.omron.com.eu/files/datasheet_pdf/J155-E1.pdf)

D7 is a firmware-controlled green LED near the top edge. Provide a sightline or light pipe in the enclosure. BZ1 is a 5 V active buzzer. Drive it high for a tone and pulse the enable for a beep pattern. The buzzer needs cabinet power and an unobstructed sound path to the enclosure. The selected buzzer specifies a +70 °C upper operating temperature. [Buzzer datasheet](https://shoppui.com/Asset/AI-1027-TWT-5V-R.pdf)

At startup, preload the RP2350A output latches low before enabling GP24, GP10 and GP6 as outputs. Initialize U17 by writing `0x00` to OLAT at register `0x0A`, then `0x78` to IODIR at register `0x00`. GP3–6 read the four active-low inputs and GP0–2 control relay outputs 2–4. GP7 is an unused output. Poll GPIO at register `0x09` and maintain a shadow of the output latch when changing individual relays. The physical RESET switch holds U17 in reset as well. Verify each relay through power-up, physical reset and a firmware restart. [Microchip MCP23008 datasheet](https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP23008-and-MCP23008-Data-Sheet-DS20001919.pdf) · [Microchip reference application](https://www.microchip.com/en-us/application-notes/an972) · [Pico SDK GPIO API](https://www.raspberrypi.com/documentation/pico-sdk/hardware.html)

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

The prototype uses a four-layer, nominal 1.0 mm FR-4 stack. The top and third layers carry signals. The second layer provides the main return plane, and the bottom layer carries signals and ground copper. L2 has a copper opening beneath the inherited USB pair so its reference stays on the bottom layer. The layout separates both RS-485 ports, the common input field domain and all four relay contact domains. Use the selected fabricator’s stack to confirm USB impedance and review the ground opening before fabrication.

Offline checks cover schematic-to-PCB pin matching, routed connectivity, copper and hole spacing, preservation of the existing RP2350A artwork and preservation of the six existing mounting and connector positions. The measured minimum projected copper spacing is 4.75 mm between isolation domains and 4.855 mm between the new input bank and logic. Check the assembled insulation paths, the enclosure and the cable access during prototype bring-up. Confirm solder-mask cover on the existing through-vias near the RP2350A and review the Gerber geometry before fabrication.

Native EasyEDA import, ERC/DRC, Gerber and stencil review and bench validation remain pending. In the first prototype, verify both supply modes, backlight current, LCD and touch operation, RTC switchover, RS-232 loopback, simultaneous traffic on both isolated RS-485 ports, input thresholds and debounce, all four relay transitions, buzzer output and sustained Ethernet transfer in the cabinet. Check the U6 case temperature and 3.3 V rail with both RS-485 ports loaded and the display running. The latest module datasheet lists up to 130 mA of operating current per transceiver. [TI 3.3 V regulator datasheet](https://www.ti.com/lit/ds/symlink/tlv1117lv.pdf) · [Mornsun transceiver datasheet](https://www.mornsun-power.com/public/uploads/pdf/TDx01D485H.pdf)
