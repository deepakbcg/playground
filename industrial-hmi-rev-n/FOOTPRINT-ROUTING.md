# Rev N footprint routing working copy

**DO NOT FABRICATE OR POWER.** Open this EasyEDA Standard archive in a separate project. It includes the U1 reroute, 52 of the 55 planned 0603 conversions, and the nominal 7.6 mm BZ1 footprint. [Footprint routing archive](Industrial-HMI-RevN-FOOTPRINTS-DO-NOT-FABRICATE.zip)

## Layout changes

- The board measures 99.2 × 96 mm and uses four layers. The 52 converted parts use the board's existing 0603 land pattern with 1.55 mm pad-center spacing. Parts stay on the top side.
- The edit adds 31 tracks and trims the former terminal ends of three 3V3 tracks for C35 and R52. Eight fixed copper regions were locally cleared for the changes. C85 and C86 use their existing 1210 land pattern.
- BZ1 uses a nominal 12 mm body, 7.6 mm pin spacing and 1.0 mm finished plated holes. Its center moves 1.625 mm left and 1.375 mm up in the PCB view. The square positive pad connects to `SYS_5V` on Top and Inner2. Pad 2 connects to both existing `BUZZ_LOW` branches on Inner2. Measure the actual lead pitch and diameter before accepting this footprint. Check the body height against the enclosure and nearby hardware.

## Three footprint changes remaining

These references retain their 0402 PCB lands. The sourcing schematic and BOM call for 0603 at these positions. Resolve the mismatch before assembly.

| Ref | Layout constraint | Editor action |
| --- | --- | --- |
| C37 | EVE 1.2 V bypass next to the RGB data fanout | Keep the bypass and return close to U8. A 0603 change requires a coordinated edit of the nearby routing, including the LCD_R7 or LCD_G0 escape. |
| R30 | Pixel-clock series resistor inside the BT818 RGB escape | Reserve space for the larger resistor with a coordinated RGB fanout edit. Preserve the series-resistor placement near the source and review the pixel-clock return. |
| R62 | W5500 EXRES resistor beside C81 and Ethernet RX copper | Resolve the resistor and C81 placement together. Preserve a short EXRES connection and ground return and review the RX differential pair. |

Retaining 0402 at these three positions is an alternative to reopening the display and Ethernet routing. That choice requires matching 0402 parts in the schematic, BOM, costed BOM and purchase list.

## Offline verification

- Compared the candidate with the U1 working copy. Checked 212 component instances and the assigned copper for 766 named pads across 174 nets. Every previously connected group of pads retained its connectivity. Rechecked U1's six local connections and the cabinet 5 V output path.
- The closest other-net spacing involving changed pads or tracks was **0.130 mm** (rounded), measured between C77.2 and the adjacent Ethernet AVDD track against the draft **0.125 mm** rule. This check used stored copper geometry.
- Checked the BZ1 pad shapes, hole diameter, pitch, polarity and connections to the four original copper branches. The ZIP passed an archive integrity check and the frozen Rev N verifier passed.
- Native EasyEDA import, schematic-to-PCB synchronization, ERC/DRC, solder mask, drill and CAM inspection are pending. Check the larger moves on power decoupling, including C22, C77 and C80, and review the edited copper regions. The inherited USB and shared 3.3 V issues and the remaining pin-audit tasks are still release blockers. [Rev N release blockers](README.md#release-blockers) · [PCB editor tasks](REV-M-PIN-AUDIT.md#pcb-editor-tasks)

Candidate PCB SHA-256 `11a92831a8bccb501e1ad43535a0a80880cfc28d62507e888382d68a216db977`. Frozen PCB SHA-256 `abff5f3eb8ef2f6e672cd597d545dd7fd53c788953bd98c647032aafd008a2a2`.
