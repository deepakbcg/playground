# Industrial HMI Rev M pin audit

The [per-pin CSV](REV-M-PIN-AUDIT.csv) compares the Rev M schematic net at each symbol pin, the PCB's assigned pad net, and the expected connection from the manufacturer's pin table and the circuit. The audit covers all **84 pin and shell-pad assignments** on the eight requested parts, plus the six pins on U1. All 84 requested assignments match. The three mismatches are on U1. Schematic and PCB metadata agree even where routed copper is open.

| Rev M part | Pins checked | Datasheet table or drawing |
| --- | ---: | --- |
| U6 · TPS62902RPJR | 9 | TI Table 5-1, Tables 7-1 and 7-2 for MODE and VSET. Open PG is allowed. Open VSET selects 3.3 V with the 40.2 kΩ MODE setting. [TI TPS62902](https://www.ti.com/lit/ds/symlink/tps62902.pdf) |
| U21 · STUSB4500LQTR | 24 + EP | ST Table 1, QFN-24 column, and §§2.2 and 3.3. Includes the grounded exposed pad and the two CC dead-battery connections. [ST STUSB4500L](https://www.st.com/resource/en/datasheet/stusb4500l.pdf) |
| U22 · TPS2121RUXR | 12 | TI §6 pin-functions table, VQFN-HR column. Table 9-3 covers the CP2-grounded priority mode. [TI TPS2121](https://www.ti.com/lit/ds/symlink/tps2121.pdf) |
| U23 · TS3USB221ARSER | 10 | TI Table 4-1 and the function table. S is low for channel 1. OE is active low. [TI TS3USB221A](https://www.ti.com/lit/ds/symlink/ts3usb221a.pdf) |
| D24 · SMF6.0A | 2 | Rev M specifies the generic part text. The audit uses Littelfuse's unidirectional diagram and SMF6.0A electrical row. The board numbers cathode 1 and anode 2. [Littelfuse SMF](https://www.littelfuse.com/assetdocs/tvs-diodes-smf-datasheet?assetguid=7eb8a5b6-bdd0-4561-8f19-0c3cc6f9b2af) |
| D25 · TPD2EUSB30DRTR | 3 | TI Table 5-1 DRT column and Figure 5-1. D+ is 1, D− is 2, GND is 3. [TI TPD2EUSB30](https://www.ti.com/lit/ds/symlink/tpd2eusb30.pdf) |
| Q4 · 2N7002,215 | 3 | Nexperia Table 2. Pin 1 gate, 2 source and 3 drain. [Nexperia 2N7002](https://assets.nexperia.com/documents/data-sheet/2N7002.pdf) |
| J4 · USB4105-GF-A | 16 contacts + 4 shell lands | GCT sheet 1, both Pin/Signal/Mating Sequence tables and the recommended PCB layout. All four shell lands connect to GND. [GCT drawing B3](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/5492/USB4105.pdf) |

## U1 pin-map correction

Rev M assigned three pads to the wrong nets. Rev P uses the corrected pin map and carries forward the U1 reroute.

| U1 pin | Function | Rev M net | Rev P net |
| --- | --- | --- | --- |
| 1 | FB | `VIN_PROT` | `CAB_FB` |
| 2 | EN | `CAB_EN` | `CAB_EN` |
| 3 | VIN | `GND` | `VIN_PROT` |
| 4 | GND | `CAB_FB` | `GND` |
| 5 | SW | `CAB_SW` | `CAB_SW` |
| 6 | CB | `CAB_CB` | `CAB_CB` |

[TI LMR51635 pin functions and DDC0006A package](https://www.ti.com/lit/ds/symlink/lmr51635.pdf)

Use the [current Rev P layout and release status](REV-P-STATUS.md) for open items. The [per-pin audit CSV](REV-M-PIN-AUDIT.csv) retains the original Rev M findings for traceability.
