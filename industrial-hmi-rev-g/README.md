# Industrial touchscreen HMI · Rev G

Rev G is the lower-BOM revision of the 24 V industrial HMI. It uses the bare **RP2350A** with a **Bridgetek BT818** controller and a **7-inch raw RGB resistive touchscreen**. Both isolated RS-485 ports use the RP2350A's built-in UARTs. RS-232 uses PIO. The four-layer PCB measures **106 × 96 mm** and uses the Rev F mounting and connector positions. Rev G removes eight populated bridge-circuit parts and uses direct GPIO for the relay, buzzer and status LED. [Rev F baseline](../industrial-hmi-rev-f/README.md) · [RP2350 hardware guide](https://pip.raspberrypi.com/categories/1214-rp2350) · [BT818 datasheet](https://brtchip.com/wp-content/uploads/Support/Documentation/Datasheets/ICs/EVE/DS_BT817_8.pdf)

## Design files

| File | Contents |
| --- | --- |
| [EasyEDA import ZIP](Industrial-HMI-RevG-EasyEDA.zip) | Editable schematic and routed PCB in EasyEDA Standard format. |
| [EasyEDA schematic](Schematic_Industrial-HMI-RevG.json) · [Schematic PDF](Industrial-HMI-RevG-Schematic.pdf) | Cabinet interfaces, RP2350A core, BT818, backlight and battery-backed RTC, Ethernet, both isolated ports, the relay and indicators. |
| [EasyEDA PCB](PCB_Industrial-HMI-RevG.json) · [PCB preview](Industrial-HMI-RevG-PCB.png) | Four-layer board and the isolated RS-485 and relay routing detail. |
| [BOM](Industrial-HMI-RevG-BOM.csv) · [Panel pinout](Industrial-HMI-RevG-Panel-Pinout.csv) | PCB, panel and battery part numbers with all 40 panel cable connections. |

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
| J8 dry contact | 1 COM, 2 NO, 3 NC. Uses an external load supply. |
| M1 Ethernet | 10/100 RJ45. SPI1 GP8 MISO, GP26 SCK and GP11 MOSI. GP25 chip select, GP4 reset and GP5 power sense. |
| BT818 SPI0 | GP16 MISO, GP17 CS_N, GP18 SCK, GP19 MOSI. |
| RTC I²C0 | GP12 SDA, GP13 SCL, 7-bit address `0x52`. |
| BT818 power-down | GP23 PD_N, active low, with a 47 kΩ pull-down. |
| RS-485 port 1 UART1 | GP20 TX, GP21 RX. GP22 low to transmit and high to receive. Allow up to 100 µs for direction changes. |
| RS-485 port 2 UART0 | GP28 TX, GP29 RX and GP14 direction. GP14 low transmits and high receives. |
| Outputs | GP24 status LED, GP10 relay coil and GP6 buzzer. All are active high. |
| Service | Micro-USB, BOOTSEL, RESET and 3-pin SWD. The MCU has 4 MB external flash. |

Six RP2350A GPIOs are unassigned on the schematic. These are GP2, GP3, GP7, GP9, GP15 and GP27. Rev G leaves their package pads unconnected.

The application firmware still needs the PLC register map, Modbus RTU settings and operator screens. For display bring-up, start with the BT818 in single-SPI mode and the backlight off. Use the panel's nominal 33.3 MHz pixel clock, 1056 × 525 total timing and 800 × 480 active area as the starting point. Check rising-edge sampling, active-low syncs and active-high data enable on J2. Apply valid timing and wait at least ten frames before enabling the backlight. Verify the first frame, touch calibration and low-duty brightness on the actual panel. [Panel datasheet](https://cdn-shop.adafruit.com/product-files/2354/Datasheet+.pdf) · [BT81x programming guide](https://brtchip.com/wp-content/uploads/2025/07/BRT_AN_033_BT81X-Series-Programming-Guide.pdf)

## Serial ports and Ethernet

J3 and J7 are independent isolated buses that can operate alongside J6. Keep their isolated COM terminals separate. Each port has its own protection and optional end termination. J6 uses a TI TRS3232E for three-wire RS-232, with logic ground as its signal return. Connect HMI TXD to the peer's RXD and HMI RXD to the peer's TXD. The two interfaces use different physical signaling. A selectable serial port would need hardware that selects the appropriate transceiver with a defined disabled state during changeover. [TRS3232E datasheet](https://www.ti.com/lit/ds/symlink/trs3232e.pdf)

Use two PIO state machines for J6, one each for TX and RX. Start loopback at 19.2 kbit/s, 8 data bits, no parity and one stop bit (8N1). Match the connected device's baud and framing, including parity and stop-bit settings if it requires them. Initialize the TX state machine with the output idle high and use USB for the debug console. Run loopback with the display and both RS-485 ports active to check buffering. [Raspberry Pi PIO UART examples](https://github.com/raspberrypi/pico-examples/tree/master/pio)

Initialize the two RS-485 direction GPIOs high for receive. Set GP28 and GP14 pad drive strength to 8 mA before enabling UART0 transmission. Set direction low at least 100 µs before writing a frame. Once the UART has shifted out the final stop bit, return direction high. Allow for the transceiver's receive-enable time and verify that it receives the earliest peer response. Use GP22 for UART1 direction and GP14 for UART0 direction. Confirm both interfaces with the actual transceiver and PLC. [RP2350 GPIO functions](https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-008373-DS-4-rp2350-datasheet.pdf) · [Pico SDK hardware API](https://www.raspberrypi.com/documentation/pico-sdk/hardware.html) · [Mornsun transceiver datasheet](https://www.mornsun-power.com/public/uploads/pdf/TDx01D485H.pdf)

M1 is a WIZ850io module with the W5500, Ethernet magnetics and RJ45 jack. The carrier uses two through-hole rows of six pins on a 2.54 mm pitch with 20.32 mm row spacing. M1's J1 SPI row is on the right when the jack faces the lower PCB edge. All six Rev E mounting positions are retained. J3 wires exit over the extension, so leave clearance to route them. Confirm network plug clearance, terminal access and the coin-cell removal path in the enclosure. [WIZ850io pin and mechanical drawings](https://docs.wiznet.io/Product/ioModule/WIZ850io)

The Ethernet circuitry runs from a dedicated TPSM84203 3.3 V supply on the cabinet-powered 5 V rail. The SN74LVC125A buffers four MCU outputs when Ethernet is powered and provides power-off isolation as the Ethernet rail drops. Keep MISO configured as an input without pull-ups and check the Ethernet power-sense input before communication. After the rail is present, set chip select high, hold WIZ850io reset low for at least 500 µs and wait at least 50 ms after releasing reset before starting SPI. Use SPI mode 0 for initial bring-up. An Ethernet link and Modbus TCP require firmware configuration and a network test. [TPSM84203](https://www.ti.com/lit/ds/symlink/tpsm84203.pdf) · [SN74LVC125A](https://www.ti.com/lit/ds/symlink/sn74lvc125a.pdf) · [WIZ850io operating instructions](https://docs.wiznet.io/Product/ioModule/WIZ850io)

## Dry contact, status LED and buzzer

The **J8 dry contact** uses a G5Q-1-EU SPDT relay. COM connects to NC with the coil off and to NO with the coil on. Rev G targets **24 V DC resistive pilot loads up to 1 A**, with the load's own supply and protection. Confirm contact load, external protection and temperature on the assembled unit before field use. Cabinet 5 V powers the relay coil. A MOSFET with a gate pull-down keeps the coil off during reset and until firmware drives it. [Relay datasheet](https://components.omron.com/eu-en/sites/components.omron.com.eu/files/datasheet_pdf/J155-E1.pdf)

D7 is a firmware-controlled green LED near the top edge. Provide a sightline or light pipe in the enclosure. BZ1 is a 5 V active buzzer. Drive it high for a tone and pulse the enable for a beep pattern. The buzzer needs cabinet power and an unobstructed sound path to the enclosure. The selected buzzer specifies a +70 °C upper operating temperature. [Buzzer datasheet](https://shoppui.com/Asset/AI-1027-TWT-5V-R.pdf)

At startup, preload the RP2350A output latches low before enabling GP24, GP10 and GP6 as outputs. The hardware pull-downs hold the two MOSFET gates low while the MCU pins are inputs. Scope both gates through power-up, reset and a firmware restart to check for unintended pulses. [Pico SDK GPIO API](https://www.raspberrypi.com/documentation/pico-sdk/hardware.html)

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

The prototype uses a four-layer, nominal 1.0 mm FR-4 stack. The top and third layers carry signals. The second layer provides the main return plane, and the bottom layer carries signals and ground copper. L2 has a copper opening beneath the inherited USB pair so its reference stays on the bottom layer. Separate copper regions serve both RS-485 ports and the relay contacts. Use the selected fabricator’s stack to confirm USB impedance and review the ground opening before fabrication.

Offline checks cover schematic-to-PCB pin matching, routed connectivity, copper and hole spacing, and preservation of the Rev F mounting and connector positions. The RP2350A reference tracks remain in place. Rev G adds GPIO escapes and trims the adjacent top copper pours. Six interface and output connections are routed directly from the MCU. Confirm solder-mask cover on the new through-vias under the QFN perimeter during the Gerber review. Measured PCB copper separation between isolation domains is at least 4.75 mm across the board artwork. The spacing measurement covers PCB copper geometry. Confirm the assembled isolation paths and limits against the enclosure and application requirements.

Native EasyEDA import, ERC/DRC, Gerber and stencil review and bench validation remain pending. In the first prototype, verify both supply modes, backlight current, LCD and touch operation, RTC switchover, RS-232 loopback, simultaneous traffic on both isolated RS-485 ports, relay drop-out, buzzer output and sustained Ethernet transfer in the cabinet. Check the U6 case temperature and 3.3 V rail with both RS-485 ports loaded and the display running. The latest module datasheet lists up to 130 mA of operating current per transceiver. [TI 3.3 V regulator datasheet](https://www.ti.com/lit/ds/symlink/tlv1117lv.pdf) · [Mornsun transceiver datasheet](https://www.mornsun-power.com/public/uploads/pdf/TDx01D485H.pdf)
