# Industrial touchscreen HMI · Rev E

Rev E adds dedicated RS-232 and RJ45 Ethernet to the Rev D platform. It pairs the bare **RP2350A**, the microcontroller used in Pico 2, with a **Bridgetek BT818** graphics controller and a **7-inch raw RGB touchscreen**. The prototype keeps the 24 V cabinet input, isolated half-duplex RS-485 and battery-backed RTC. The board extends from 94 × 74 mm to 94 × 96 mm to fit both new connectors. The BT818 generates LCD timing and reads touch while the RP2350A runs the HMI application and communicates with the PLC. [Rev D baseline](../industrial-hmi-rev-d/README.md) · [RP2350 hardware guide](https://pip.raspberrypi.com/categories/1214-rp2350) · [BT818 datasheet](https://brtchip.com/wp-content/uploads/Support/Documentation/Datasheets/ICs/EVE/DS_BT817_8.pdf)

## Design files

| File | Contents |
| --- | --- |
| [EasyEDA import ZIP](Industrial-HMI-RevE-EasyEDA.zip) | Editable schematic and routed PCB in EasyEDA Standard format. |
| [EasyEDA schematic](Schematic_Industrial-HMI-RevE.json) · [Schematic PDF](Industrial-HMI-RevE-Schematic.pdf) | Cabinet interfaces, RP2350A core, BT818, backlight and battery-backed RTC, RS-232 and Ethernet circuitry. |
| [EasyEDA PCB](PCB_Industrial-HMI-RevE.json) · [PCB preview](Industrial-HMI-RevE-PCB.png) | Four-layer board and the RS-232 and Ethernet routing detail. |
| [BOM](Industrial-HMI-RevE-BOM.csv) · [Panel pinout](Industrial-HMI-RevE-Panel-Pinout.csv) | PCB, panel and battery part numbers with all 40 panel cable connections. |

In EasyEDA Pro, use **File → Import → EasyEDA (Standard)** with the ZIP. The RP2350A reference layout and stencil artwork derive from Raspberry Pi’s RP2350A Minimal KiCad R4-S1 reference. The included MIT license accompanies that work. [EasyEDA Pro import](https://prodocs.easyeda.com/en/import-export/import-easyeda/) · [Raspberry Pi reference design](https://pip.raspberrypi.com/categories/1214-rp2350) · [Reference license](Raspberry-Pi-Reference-LICENSE.txt)

## Display and backlight

The design targets **Adafruit PID 2354, panel CH700WV03A-T**. It has an 800 × 480 display, RGB888, a 3.3 V logic interface and four-wire resistive touch. The panel is 164.9 × 100.0 mm with a 154.08 × 85.92 mm active area. J2 is a bottom-contact Hirose FH12 40-position, 0.5 mm-pitch FPC connector. Confirm the cable contact orientation and enclosure fit with a sample. Each additional size and each Delta DOP cabinet cutout needs its own mechanical drawing and panel definition. [Adafruit panel](https://www.adafruit.com/product/2354) · [Panel datasheet](https://cdn-shop.adafruit.com/product-files/2354/Datasheet+.pdf) · [Hirose connector](https://www.hirose.com/en/product/p/CL0586-0527-7-55)

The TPS61165 backlight driver uses the cabinet-powered 5 V rail. R25 sets a nominal **133 mA** LED current. The panel specifies **140 mA typical** and **9.3–10.5 V** forward voltage. Use 10 kHz PWM from the BT818 for dimming. During USB-only service, the 3.3 V logic may power up and the cabinet-fed backlight supply stays off. [TPS61165 datasheet](https://www.ti.com/lit/ds/symlink/tps61165.pdf) · [Panel datasheet](https://cdn-shop.adafruit.com/product-files/2354/Datasheet+.pdf)

## Cabinet wiring and MCU assignments

| Interface | Assignment |
| --- | --- |
| J1 cabinet input | 1 +24 V, 2 0 V. Designed for 20.4–27.6 V DC. |
| J2 LCD | 40-position FPC with RGB888, pixel clock, enable, sync, resistive touch, logic power and backlight. |
| J3 isolated RS-485 | 1 D0 (−), 2 D1 (+), 3 isolated COM. R4 is an optional 120 Ω termination, DNP by default. |
| J6 RS-232 | 1 HMI TXD, 2 HMI RXD, 3 logic GND. UART0 GP0 TX and GP1 RX. |
| M1 Ethernet | 10/100 RJ45. SPI1 GP8 MISO, GP26 SCK and GP11 MOSI. GP25 chip select, GP4 reset and GP5 power sense. |
| BT818 SPI0 | GP16 MISO, GP17 CS_N, GP18 SCK, GP19 MOSI. |
| RTC I²C0 | GP12 SDA, GP13 SCL, 7-bit address `0x52`. |
| BT818 power-down | GP23 PD_N, active low, with a 47 kΩ pull-down. |
| RS-485 UART1 | GP20 TX, GP21 RX. GP22 low to transmit and high to receive. Allow up to 100 µs for direction changes. |
| Service | Micro-USB boot and 3-pin SWD. The MCU has 4 MB external flash. |

The application firmware still needs the PLC register map, Modbus RTU settings and operator screens. For display bring-up, start with the BT818 in single-SPI mode and the backlight off. Use the panel's nominal 33.3 MHz pixel clock, 1056 × 525 total timing and 800 × 480 active area as the starting point. Check rising-edge sampling, active-low syncs and active-high data enable on J2. Apply valid timing and wait at least ten frames before enabling the backlight. Verify the first frame, touch calibration and low-duty brightness on the actual panel. [Panel datasheet](https://cdn-shop.adafruit.com/product-files/2354/Datasheet+.pdf) · [BT81x programming guide](https://brtchip.com/wp-content/uploads/2025/07/BRT_AN_033_BT81X-Series-Programming-Guide.pdf)

## Serial ports and Ethernet

J3 and J6 can operate independently. J3 serves an isolated RS-485 bus. J6 uses a TI TRS3232E for three-wire RS-232, with logic ground as its signal return. Connect HMI TXD to the peer's RXD and HMI RXD to the peer's TXD. The two interfaces use different physical signaling. A selectable serial port would need hardware that selects the appropriate transceiver with a defined disabled state during changeover. [TRS3232E datasheet](https://www.ti.com/lit/ds/symlink/trs3232e.pdf)

M1 is a WIZ850io module with the W5500, Ethernet magnetics and RJ45 jack. The carrier uses two through-hole rows of six pins on a 2.54 mm pitch with 20.32 mm row spacing. M1's J1 SPI row is on the right when the jack faces the lower PCB edge. The bottom extension includes two additional M3 mounting positions near the new connectors. The four Rev D mounting positions are retained. Confirm network plug clearance, terminal access and the coin-cell removal path in the enclosure. [WIZ850io pin and mechanical drawings](https://docs.wiznet.io/Product/ioModule/WIZ850io)

The Ethernet circuitry runs from a dedicated TPSM84203 3.3 V supply on the cabinet-powered 5 V rail. The SN74LVC125A buffers four MCU outputs when Ethernet is powered and provides power-off isolation as the Ethernet rail drops. Keep MISO configured as an input without pull-ups and check the Ethernet power-sense input before communication. After the rail is present, set chip select high, hold WIZ850io reset low for at least 500 µs and wait at least 50 ms after releasing reset before starting SPI. Use SPI mode 0 for initial bring-up. An Ethernet link and Modbus TCP require firmware configuration and a network test. [TPSM84203](https://www.ti.com/lit/ds/symlink/tpsm84203.pdf) · [SN74LVC125A](https://www.ti.com/lit/ds/symlink/sn74lvc125a.pdf) · [WIZ850io operating instructions](https://docs.wiznet.io/Product/ioModule/WIZ850io)

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

The prototype uses a four-layer, nominal 1.0 mm FR-4 stack. The top and third layers carry signals. The second layer provides the main return plane, and the bottom layer carries signals and ground copper. L2 has a copper opening beneath the inherited USB pair so its reference stays on the bottom layer. The board preserves 4.75 mm copper separation at the isolated RS-485 boundary. Use the selected fabricator’s stack to confirm USB impedance and review the ground opening before fabrication.

Offline checks verified 107 nets, 462 schematic pins against 470 physical pads, copper clearance, drill spacing and the USB return path. The layout retains the Rev D copper tracks and vias and preserves 4.75 mm between logic copper and the isolated RS-485 region.

Native EasyEDA import, ERC/DRC, Gerber and stencil review and bench validation remain pending. In the first prototype, verify both supply modes, backlight current, LCD and touch operation, RTC switchover, RS-232 loopback, isolated RS-485 communication and sustained Ethernet transfer in the cabinet.
