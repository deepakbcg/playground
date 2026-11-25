# Rev P fabrication notes

**DRAFT — DO NOT FABRICATE.** Resolve J4, complete native EasyEDA DRC and review the Gerber and drill files before release. [Rev P status](REV-P-STATUS.md)

## Board and process

| Item | Rev P requirement |
| --- | --- |
| Outline and material | 99.2 × 96 mm, routed rectangular FR-4, nominal 1.0 mm finished thickness. Check panel and USB-C fit at the thickness limits. |
| Stackup reference | JLCPCB **JLC7628, 1.0 mm, four layers**, the published 7628 × 1 / 0.45 mm copper-clad core / 7628 × 1 option. The order process should confirm the equivalent current 1.0 mm build and its finished inner copper. |
| Layers | L1 Top (EasyEDA 1), L2 Inner1 GND reference (21), L3 Inner2 mixed signals and 3V3 (22), L4 Bottom (2). Keep the two isolated RS-485 field circuits separate from logic GND and from each other on all layers. |
| Copper | Nominal 1 oz outer. Nominal 0.5 oz inner with **at least 15.2 µm finished L3 copper** and **at least 2.067 mm finished width** on each specified 2.20 mm buck leg. A thicker inner option can be qualified against the same thermal limit if the standard process cannot meet these widths. |
| Finish and mask | ENIG recommended for the RP2354B 0.40 mm-pitch QFN-80 and USB/power QFNs. Green LPI mask. Check actual mask/paste openings and dams using the exports. |
| Track / copper clearance | 0.150 mm minimum nominal track used. 0.125 mm design clearance for different-net routing. Check JLC PCB-specific SMD pad-to-pad clearance of 0.150 mm separately. The manufacturer's multilayer trace/space capability floor is 0.09/0.09 mm at 1 oz. |
| Vias | 665 in the current source, all 0.50 mm land / Ø0.25 mm mechanical through drill. Check via-hole to foreign copper ≥0.20 mm, including on inner layers. |
| Component PTH | Inner hole-to-foreign-copper ≥0.30 mm. Use ≥0.28 mm elsewhere. Inspect finished hole dimensions, plating and annuli as separate checks. |
| NPTH and board edge | NPTH-to-copper ≥0.20 mm and copper-to-routed-edge ≥0.20 mm. Check hole-to-hole spacing ≥0.20 mm edge to edge, including connector hardware. |
| Impedance | The current artwork has no controlled-impedance verification. Review USB FS differential routing against a 90 Ω ±15% planning target and the 10/100 PHY-to-MagJack pairs against 100 Ω ±10%. Require a selected stackup and re-evaluation of widths, spacings, return and skew before claiming impedance control. |

[JLCPCB stackup reference](https://cart.jlcpcb.com/client/template/placeOrder/impedance.html) · [JLCPCB multilayer capabilities](https://jlcpcb.com/capabilities/pcb-capabilities/) · [JLCPCB finished copper conventions](https://jlcpcb.com/help/article/user-guide-to-the-jlcpcb-impedance-calculator)

## 3.3 V buck current path

Both dedicated L3 legs, `gge962014` and `gge962015`, are **2.20 mm nominal**. The IPC-2221 internal-trace screening relation is `I = 0.024 × ΔT^0.44 × A^0.725`, with cross-section `A` in mil². At 1.5 A, a 2.20 mm trace is 59.7 mil² at 17.5 µm and 51.8 mil² at 15.2 µm. The predicted rises are **14.3 °C** and **18.0 °C** respectively. The 20 °C limit requires 2.067 mm finished width at 15.2 µm. Check the finished width and copper thickness as a pair with the fabricator. Three parallel vias at each transition and the wider Bottom distribution region are retained. Confirm assembled voltage drop and temperature at 1.5 A in the enclosure. [TI application note SNVA766, PCB trace sizing](https://www.ti.com/lit/an/snva766/snva766.pdf) · [TPS62902 layout guidance](https://www.ti.com/lit/ds/symlink/tps62902.pdf)

## Drill and connector requirements

The current source has **60 round plated component pads**, including the four temporary Ø0.60 mm J4 shell holes, plus the 665 plated vias. The seven existing **Ø3.20 mm NPTH** centres are below. Coordinates are absolute EasyEDA millimetres.

| Feature | x | y |
| --- | ---: | ---: |
| Main-board mounting | 1020.50 | 766.50 |
| Main-board mounting | 1105.50 | 766.50 |
| Main-board mounting | 1020.50 | 831.50 |
| Main-board mounting | 1020.50 | 853.50 |
| Main-board mounting | 1105.50 | 853.50 |
| J11 locator | 1028.285 | 848.15 |
| J11 locator | 1039.715 | 848.15 |

Before release, J4 needs **two 1.70 × 0.60 mm and two 1.40 × 0.60 mm plated slots** with 2.10 × 1.00 mm and 1.80 × 1.00 mm outer solder areas, respectively, and **two Ø0.65 mm NPTH** 5.78 mm apart. The target export consequently has 56 round plated component holes, four plated slots and nine NPTH, with the via count updated if the editor reroute changes it. Check the J4 footprint against the actual board edge, and verify the 60 component holes/slots independently of PTH via drill entries. BZ1 uses two nominal Ø1.00 mm finished PTH. Measure the purchased buzzer before release. [GCT USB4105 B3, sheet 1](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/5492/USB4105.pdf)

The top silkscreen carries **Rev P DRAFT**. The separate **DO NOT FABRICATE** warning is on the EasyEDA Document layer.
