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

## U1 mismatches corrected in Rev N

All three Rev M mismatches are against the [LMR51635 Rev B Table 5-1](https://www.ti.com/lit/ds/symlink/lmr51635.pdf). The [TI EVM Figure 3-1](https://www.ti.com/lit/ug/sluuct3a/sluuct3a.pdf) confirms the same mapping.

| U1 pin | TI function | Rev M schematic and pad net | Rev N schematic and pad net |
| --- | --- | --- | --- |
| 1 | FB | `VIN_PROT` | `CAB_FB` |
| 3 | VIN | `GND` | `VIN_PROT` |
| 4 | GND | `CAB_FB` | `GND` |

Pins 2 EN, 5 SW and 6 CB had the correct nets. The Rev N symbol now uses the TI numbers at the existing wire attachment points. The revised PCB footprint uses the DDC0006A example's six 1.10 × 0.60 mm lands and retains the pad centers. Existing tracks, vias and copper regions still reflect the Rev M layout.

**Fabrication hold.** The Rev N PCB source has a legacy top-layer track at the center of each affected pad. Track `gge4878` carries protected cabinet input `VIN_PROT` into U1.1 (`CAB_FB`), track `gge4979` carries GND into U1.3 (`VIN_PROT`), and track `gge4827` carries `CAB_FB` into U1.4 (GND). These copper contacts conflict with the corrected pad nets. Resolve them in the native editor before fabrication or power-up.

## PCB editor tasks

1. **Reroute U1 before applying cabinet power.** Remove the old fanout to pads 1, 3 and 4. Connect pad 3 to `VIN_PROT` and the local input bypass capacitors. Connect pad 4 to the ground plane with a short local return and suitable vias. Connect pad 1 to the R69/R70 divider midpoint and route the feedback sense away from pad 5, the switch node and L3. Check the widened lands against adjacent copper and rebuild the pours. [TI DDC0006A and layout guidance](https://www.ti.com/lit/ds/symlink/lmr51635.pdf)
2. **Review U6 and U23 lands.** U6 pads 4 and 6 are 0.65 × 0.20 mm with center offsets of 0.625 mm from the center on that edge. TI RPJ0009A gives 1.00 × 0.20 mm and a 0.45 mm offset. U6 pads 7–9 are approximately 0.25 × 0.40 mm versus TI's 0.25 × 0.55 mm. U23 pads 2, 3, 7 and 8 are 0.55 × 0.25 mm versus TI's 0.55 × 0.20 mm. U23 pads 5 and 10 are 0.25 × 0.60 mm on 1.90 mm centers versus TI's 0.30 × 0.60 mm on 1.80 mm centers. Compare the native mask, paste and pad patterns with the manufacturer drawings and resolve the differences before assembly. [TI RPJ0009A](https://www.ti.com/lit/ds/symlink/tps62902.pdf) · [TI RSE0010A](https://www.ti.com/lit/ds/symlink/ts3usb221a.pdf)
3. **Replace the D25 land pattern.** Pads 1 and 2 are 1.06 mm center-to-center in Rev M. TI's DRT terminals are 0.70 mm center-to-center, with each terminal offset 0.35 mm from the package centerline. Use the DRT footprint and check solderable overlap and spacing. [TI DRT package drawing](https://www.ti.com/lit/ml/mpds340/mpds340.pdf)
4. **Correct J4 drilling and physical lands.** Add the two Ø0.65 mm non-plated locator holes on 5.78 mm centers. Replace the four round Ø0.60 mm shell drills with the two 1.70 × 0.60 mm and two 1.40 × 0.60 mm plated slots specified by GCT. The 16 contact designations use 12 physical SMT lands. Confirm the four coincident pairs A1/B12, A4/B9, B4/A9 and B1/A12 resolve to one physical land each in the native export. [GCT drawing B3, recommended PCB layout](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/5492/USB4105.pdf)
5. **Close the inherited copper and clearance issues.** R76.2 and U6.4 on GND, U6.5 and U6.6 on `SYS_5V`, U21.24 on `USB_VBUS`, U21.18 to R73.2 on `USB_RAW_SENSE`, U21.23 to C89.1 on `USB_REG27`, and R72.1 on `USB_FET_GATE`. The 0.116 mm spacing between U6.7 and `SYS_5V` is below the draft's 0.125 mm rule. Run native ERC and DRC, inspect the updated drill overlay and verify cabinet 5 V startup on a current-limited supply.
6. **Place and reroute the 0603 passives.** Use **Design → Update PCB** from the schematic in the same EasyEDA Standard working copy. Review the 55 intended footprint changes and the 31 retained 0402 positions. Reconnect each new pad, verify iron access, rebuild copper and repeat ERC/DRC and the release checks after the placement pass. [0603 worklist](0603-WORKLIST.csv) · [0402 exceptions](REV-N-PASSIVES.md#lcsc-retail-stock-and-0402-follow-up)
7. **Place and reroute BZ1.** Measure the purchased buzzer’s pitch, lead diameter and polarity before layout. Import the 7.6 mm footprint as an EasyEDA Standard PCB library and confirm the BZ1 symbol resolves to it in Footprint Manager. Reassign it there if the editor gives the imported library a new ID. Use Ø1.0 mm finished plated holes for the measured part and connect square pad 1 to `SYS_5V` and pad 2 to `BUZZ_LOW`. Check the larger body around R41, Q2 and D9, acoustic port access and enclosure clearance. Keep the driver circuit and reconnect its two buzzer nets before rebuilding all copper and inspecting plated holes and DRC. [BZ1 footprint](Footprint_BUZZER-D12-P7.6-PTH.json) · [Purchased-part note](README.md#buzzer-and-field-input-zeners)
