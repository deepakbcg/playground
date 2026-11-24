# Industrial touchscreen HMI · Rev B

Rev B uses the bare **Raspberry Pi RP2350A**, the microcontroller in Pico 2. It preserves the 94 × 74 mm outline, mounting holes, display connector and isolated RS‑485 connector from the [Rev A design](../industrial-hmi/README.md). The DOP-107BV remains the example mechanical reference. Use the actual DOP and PLC models to finish the cabinet adapter, PLC driver and touchscreen application. [Raspberry Pi Pico 2 datasheet](https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf)

## Design files

| File | Use |
| --- | --- |
| [EasyEDA import ZIP](Industrial-HMI-RevB-EasyEDA.zip) | Import the schematic and routed PCB together through **File → Import → EasyEDA (Standard)** in EasyEDA Pro. |
| [Schematic source](Schematic_Industrial-HMI-RevB.json) · [PCB source](PCB_Industrial-HMI-RevB.json) | Editable EasyEDA Standard documents. |
| [Schematic PDF](Industrial-HMI-RevB-Schematic.pdf) · [PCB preview](Industrial-HMI-RevB-PCB.png) | The PDF has separate pages for the HMI interfaces and the RP2350A circuitry. The preview includes a close-up of the core routing. |
| [BOM](Industrial-HMI-RevB-BOM.csv) | Board parts, assembly options and one of three panel choices. |

The import ZIP uses EasyEDA Standard JSON as the exchange format. The RP2350A placement, critical routing and stencil artwork derive from Raspberry Pi’s **RP2350A Minimal KiCad R4-S1** reference. Its MIT license accompanies the design and is also embedded in the source documents. [EasyEDA Pro import](https://prodocs.easyeda.com/en/import-export/import-easyeda/) · [Raspberry Pi reference design](https://pip.raspberrypi.com/categories/1214-rp2350) · [Reference license](Raspberry-Pi-Reference-LICENSE.txt)

## Pico 2 circuitry

- **U2 is an RP2350A in the QFN-60 package.** The board includes a 12 MHz crystal, a 3.3 V LDO and the passives for the RP2350A’s internal 1.1 V switching regulator. The 3.3 V rail also powers the display receiver and isolated RS‑485 transceiver. Use A4 silicon for prototype sourcing. [RP2350 hardware guide](https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-008280-DS-2-hardware-design-with-rp2350.pdf) · [Raspberry Pi A4 stepping notes](https://www.raspberrypi.com/news/rp2350-a4-rp2354-and-a-new-hacking-challenge/) · [TI TLV1117LV datasheet](https://www.ti.com/lit/ds/symlink/tlv1117lv.pdf)
- **U7 is a 4 MB Winbond W25Q32JVSSIQ.** Fit R20 to connect the flash chip select. R11 is an optional pull-up and ships DNP in this variant. Use an RP2350A firmware configuration with the correct 4 MB flash settings and the GPIO assignments below. [Winbond device specification](https://www.winbond.com/hq/product/code-storage-flash/qspi-nor/w25q-jv/?__locale=en&partNo=W25Q32JVSSIQ)
- **Service uses micro-USB and SWD.** J4 faces the left edge. J5 uses a 3-pin JST-SH connector with 1 SWCLK, 2 GND and 3 SWDIO. Hold SW1 BOOTSEL, tap SW2 RESET, then release BOOTSEL to enter the built-in USB bootloader. Two Schottky diodes allow the controller to run from either cabinet power or USB. J2 display power comes from the cabinet supply.
- **Check the power budget on actual hardware.** Verify the 3.3 V rail at TP3 and the 1.1 V rail at C17 pin 1. Test the regulator temperature with active RS‑485 and the cabinet closed. Check low USB VBUS, USB inrush, enumeration and simultaneous 24 V plus USB. The display rail should remain off during USB-only service.

## Cabinet wiring and firmware assignments

| Connection | Pin order or GPIO |
| --- | --- |
| J1 cabinet supply | 1 +24 V, 2 0 V. Rev A input range remains 20.4–27.6 V. |
| J2 touchscreen | 1 +5 V, 2 panel TX, 3 panel RX, 4 GND. |
| J3 isolated RS‑485 | 1 D0 (−), 2 D1 (+), 3 isolated COM. R4 is the optional 120 Ω termination and is DNP by default. |
| Touchscreen UART0 | GP16 TX and GP17 RX. |
| PLC UART1 | GP20 TX and GP21 RX. GP22 is direction, low to transmit and high to receive. Configure at least 8 mA drive for GP22 and allow up to 100 µs for direction changes. |

The display options remain the 5-inch **NX8048P050-011R**, 7-inch **NX8048P070-011R** and 10.1-inch **NX1060P101-011R-I**. The 10.1-inch option needs a harness validated at 2 A. Modbus RTU remains the PLC protocol assumption. Firmware and the touchscreen project are pending.

## PCB stackup and verification

This is a routed prototype for **two-layer, 1.0 mm FR-4 with 1 oz outer copper**. The nominal thickness follows Raspberry Pi’s USB routing guidance. The two wide USB segments use 0.8 mm traces and a nominal 0.15 mm gap on the straight section. Both run over continuous bottom ground. Confirm the actual fabricator dielectric and differential impedance, and check the enclosure support at the USB connector before ordering. Preserve the 4.75 mm copper separation between logic GND and the isolated RS‑485 region. [Raspberry Pi USB layout guidance](https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-008280-DS-2-hardware-design-with-rp2350.pdf)

Offline checks reconciled **231 schematic pins and 235 physical pads**, confirmed continuity for **41 named nets**, and checked copper clearances, holes, component body overlap, and the USB ground return. The board uses fixed, net-assigned copper regions for the verified geometry. After editor import, inspect both copper layers and preserve the return path and isolation spacing if you edit those regions.

Fabrication release still needs EasyEDA import and native ERC/DRC, a Gerber and plated-slot review, and a stencil and solder-mask review for the QFN exposed pad and nine thermal vias. The first assembled board still needs USB boot and SWD checks, flash read/write verification, rail and thermal checks, and a cabinet HMI/PLC communication test.
