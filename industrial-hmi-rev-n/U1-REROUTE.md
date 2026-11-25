# Rev N U1 reroute working copy

**DO NOT FABRICATE OR POWER.** The archive contains an edited four-layer PCB, its matching schematic and the BZ1 footprint library. The frozen Rev N source remains available for comparison. [U1 reroute working copy](Industrial-HMI-RevN-U1-REROUTE-DO-NOT-FABRICATE.zip) · [Frozen Rev N archive](Industrial-HMI-RevN-EasyEDA-DO-NOT-FABRICATE.zip)

## Routing changes

| Connection | Working-copy routing |
| --- | --- |
| U1.1 `CAB_FB` | A short top-layer escape west of U1 connects to the new bottom trace and returns to the existing via at the R69.2/R70.1 divider junction. |
| U1.2 `CAB_EN` | Existing route to the R67/R68 junction. |
| U1.3 `VIN_PROT` | Top-layer routes to C82.1 and C83.1. The protected input copper also connects D1.1, D2.1, C1.1 and R67.1. |
| U1.4 `GND` | Local top-layer copper joins C83.2 and C82.2, with three stitching vias to bottom and Inner1 ground. |
| U1.5 `CAB_SW` and U1.6 `CAB_CB` | The switch connection to L3.1 stays in place. C84.2 feeds from that copper, and C84.1 routes separately to U1.6. |

C83 rotates into the space below U1 to put the high-frequency input capacitor across pins 3 and 4. C84 moves above U1 to clear the ground return. The edit removes the three legacy pad fanouts, two conflicting vias and the replaced local connections. It also clears the new FB copper from seven existing ground polygons. Those polygons are fixed copper regions in this source. Review them directly in EasyEDA when checking the ground return and fabrication output. [TI LMR51635 layout guidelines, §8.4](https://www.ti.com/lit/ds/symlink/lmr51635.pdf)

## Offline checks

- Reopened the packaged PCB and checked copper connectivity from all six U1 pads through their expected local endpoints. Also checked `CAB_5V` from L3.2 to C2/C85/C86, R69.1 and U22.7. Ground pads already connected to J1.2 retain that connection in the checked geometry.
- Screened the U1 pads, moved pads and new track and via copper against other-net pads, tracks, vias and solid copper on the relevant layers. The smallest measured local clearance was **0.165 mm** between bottom-layer FB copper and GND, above the draft **0.125 mm** rule.
- Measured **0.60 mm** between the C83 and U1 body outlines and **0.25 mm** between C84 and L3. Check purchased bodies, placement tolerances and solder access in the editor.
- The bottom FB trace is **20.6 mm** long. About **96%** of its centerline is over Inner1 GND in the stored geometry. The existing remote divider makes this longer than TI’s recommended short FB connection. Verify noise pickup and regulator behavior on the prototype.
- Confirmed all **212** PCB designators and the schematic connectivity. C83 and C84 are the only component placements changed. The source PCB still passes the frozen Rev N verifier.

Candidate PCB SHA-256 `916ecb30d7e2db67cf853e62ae0ee61f671f19de48904d3597d96f6df0f5ef62`. Frozen PCB SHA-256 `abff5f3eb8ef2f6e672cd597d545dd7fd53c788953bd98c647032aafd008a2a2`.

## Native checks before release

Open this ZIP in a separate EasyEDA Standard working copy. Inspect the new U1 tracks, fixed copper regions and three ground vias. Run native ERC and DRC and inspect all four copper layers. The 0603 and buzzer placement work and the other board findings remain open. Once the complete board clears those checks, verify cabinet startup, load-step response and handoff with a current-limited setup. [Remaining board editor tasks](REV-M-PIN-AUDIT.md#pcb-editor-tasks) · [Cabinet-output qualification](README.md#cabinet-output-capacitors)
