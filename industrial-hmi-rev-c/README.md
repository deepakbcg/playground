# Industrial touchscreen HMI · Rev C

Rev C pairs the bare **RP2350A**, the microcontroller used in Pico 2, with a **Bridgetek BT818** graphics controller and a **7-inch raw RGB touchscreen**. The prototype keeps the 94 × 74 mm controller-board outline, 24 V cabinet supply and isolated half-duplex RS-485 from Rev B. The BT818 generates LCD timing and reads touch while the RP2350A runs the HMI application and communicates with the PLC. [Rev B design](../industrial-hmi-rev-b/README.md) · [RP2350 hardware guide](https://pip.raspberrypi.com/categories/1214-rp2350) · [BT818 datasheet](https://brtchip.com/wp-content/uploads/Support/Documentation/Datasheets/ICs/EVE/DS_BT817_8.pdf)

## Design files

| File | Contents |
| --- | --- |
| [EasyEDA import ZIP](Industrial-HMI-RevC-EasyEDA.zip) | Editable schematic and routed PCB in EasyEDA Standard format. |
| [EasyEDA schematic](Schematic_Industrial-HMI-RevC.json) · [Schematic PDF](Industrial-HMI-RevC-Schematic.pdf) | Cabinet interfaces, RP2350A core, BT818 and backlight circuitry. |
| [EasyEDA PCB](PCB_Industrial-HMI-RevC.json) · [PCB preview](Industrial-HMI-RevC-PCB.png) | Four-layer board and the RGB routing detail. |
| [BOM](Industrial-HMI-RevC-BOM.csv) · [Panel pinout](Industrial-HMI-RevC-Panel-Pinout.csv) | PCB and panel part numbers with all 40 cable connections. |

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
| BT818 SPI0 | GP16 MISO, GP17 CS_N, GP18 SCK, GP19 MOSI. |
| BT818 power-down | GP23 PD_N, active low, with a 47 kΩ pull-down. |
| RS-485 UART1 | GP20 TX, GP21 RX. GP22 low to transmit and high to receive. Allow up to 100 µs for direction changes. |
| Service | Micro-USB boot and 3-pin SWD. The MCU has 4 MB external flash. |

The application firmware still needs the PLC register map, Modbus RTU settings and operator screens. For display bring-up, start with the BT818 in single-SPI mode and the backlight off. Use the panel's nominal 33.3 MHz pixel clock, 1056 × 525 total timing and 800 × 480 active area as the starting point. Check rising-edge sampling, active-low syncs and active-high data enable on J2. Apply valid timing and wait at least ten frames before enabling the backlight. Verify the first frame, touch calibration and low-duty brightness on the actual panel. [Panel datasheet](https://cdn-shop.adafruit.com/product-files/2354/Datasheet+.pdf) · [BT81x programming guide](https://brtchip.com/wp-content/uploads/2025/07/BRT_AN_033_BT81X-Series-Programming-Guide.pdf)

## PCB stackup and verification

The prototype uses a four-layer, nominal 1.0 mm FR-4 stack. The top and third layers carry signals. The second layer provides the main return plane, and the bottom layer carries signals and ground copper. L2 has a copper opening beneath the inherited USB pair so its reference stays on the bottom layer. The board preserves 4.75 mm copper separation at the isolated RS-485 boundary. Use the selected fabricator’s stack to confirm USB impedance and review the ground opening before fabrication.

Offline geometry checks reconciled 370 schematic pins with 377 physical pads and verified continuity on 83 named nets, copper clearances, hole spacing and the USB return path. The EasyEDA import, native ERC/DRC, Gerbers, QFN stencil and solder mask, and bench validation remain pending. In the first prototype, verify both supply modes, backlight current, LCD and touch operation, and Modbus communication in the cabinet.
