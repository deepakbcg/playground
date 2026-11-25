# Industrial HMI Rev N

**DO NOT FABRICATE OR POWER THIS PCB.** The existing `VIN_PROT` track still runs from the protected 24 V cabinet input to U1.1, now correctly assigned to feedback. U1.3 and U1.4 also still have tracks on their former nets. Use these files for editor rework only. [U1 copper findings and editor tasks](REV-M-PIN-AUDIT.md#pcb-editor-tasks)

Rev N updates sourcing and corrects the cabinet converter pin mapping on the 99.2 × 96 mm, four-layer RP2354B HMI. The intended full-HMI power sources are 24 V cabinet power and 5 V USB-C with a 3 A advertisement. Cabinet power has priority. An ordinary USB host can program the externally powered board through BOOTSEL after the layout is cleared for use. [Rev M source](../industrial-hmi-rev-m/README.md)

## Files

| File | What it contains |
| --- | --- |
| [EasyEDA Standard ZIP — DO NOT FABRICATE](Industrial-HMI-RevN-EasyEDA-DO-NOT-FABRICATE.zip) | Schematic, four-layer PCB and local buzzer footprint for editor rework. |
| [Schematic JSON](Schematic_Industrial-HMI-RevN-DO-NOT-FABRICATE.json) · [PCB JSON](PCB_Industrial-HMI-RevN-DO-NOT-FABRICATE.json) | Editable Rev N documents with fabrication-hold labels. |
| [BOM](Industrial-HMI-RevN-BOM.csv) · [Itemized INR pricing](Industrial-HMI-RevN-BOM-Cost-INR.csv) | Fitted and DNP designators, orderable parts, known tiers and availability. |
| [Three-board purchase list](PURCHASE-LIST.csv) | Order quantities with spares, stock snapshots, supplier subtotals and shipping thresholds. |
| [BZ1 footprint](Footprint_BUZZER-D12-P7.6-PTH.json) | EasyEDA Standard library source for the new 12 mm buzzer. |
| [Build configurator](Industrial-HMI-RevN-Build-Configurator.html) · [Panel pinout](Industrial-HMI-RevN-Panel-Pinout.csv) | Offline fit/DNP selections and J2 wiring. |
| [Sourcing checkpoint](REV-N-CHANGES.md) · [Substitution evidence](tools/substitution-evidence.csv) | Sourcing history and current part evidence. |
| [Passive consolidation](REV-N-PASSIVES.md) · [0603 worklist](0603-WORKLIST.csv) | Planned BOM changes, 0402 exceptions and location-by-location PCB checks. |
| [Rev M pin audit](REV-M-PIN-AUDIT.md) · [Per-pin results](REV-M-PIN-AUDIT.csv) | 84 requested pin and shell assignments, six U1 pins, datasheet references and native PCB tasks. |
| [Verification script](tools/verify_rev_n.py) · [Recorded output](tools/verification-output.txt) | Compare this revision to the adjacent Rev M sources. |
| [Claude instructions](CLAUDE.md) · [Reference license](Raspberry-Pi-Reference-LICENSE.txt) | Task constraints and Raspberry Pi reference license. |
| [Schematic PDF](Industrial-HMI-RevN-Draft-Schematic.pdf) · [PCB PNG](Industrial-HMI-RevN-PCB.png) · [Placement PNG](Industrial-HMI-RevN-Placement.png) · [Specification PDF](Industrial-HMI-RevN-Specification.pdf) | Rev M artwork, part numbers superseded by Rev N BOM — re-export pending in EasyEDA. |
| [External relay source](../industrial-hmi-rev-i/Industrial-HMI-RevI-Relays-EasyEDA.zip) | Separate four-channel COM/NO/NC relay board. |

The native PCB silkscreen includes Rev M vector outlines from the frozen baseline. These retain their geometry in this sourcing copy. Update the physical marking in the native editor before a later fabrication release. The PDF and PNG copies may also display the Rev M revision label.

## Cost and population

All **207 fitted main-board and cell positions** are priced at **₹6,009.29** per board. The external Adafruit 2354 LCD is quoted separately at **₹3,339.47**. [Current pricing](Industrial-HMI-RevN-BOM-Cost-INR.csv)

The three-board list covers **107 orderables**. It totals **₹26,083.58** for board parts and cells, or **₹39,441.46** with the three LCDs and one spare. Totals account for 10% spares rounded up per MPN, at least two extras for passives under ₹1, and supplier minimums and order multiples. Line totals use the quoted tier and ₹92.67/USD. Freight, duties, taxes, bare PCBs and optional external relay assemblies are outside these totals. Quantities are based on the public LCSC feed and published distributor listings checked on 25 November 2026 IST, including indexed snapshots. [Purchase list](PURCHASE-LIST.csv)

**Q3 sourcing.** The list buys the original ST STL6P3LLH6 from DigiKey India because LCSC showed three and the order calls for four. [ST Q3 datasheet](https://www.st.com/resource/en/datasheet/stl6p3llh6.pdf) · [Purchase list](PURCHASE-LIST.csv)

**USB-only first build.** Leaving out J1, F1, D1, D2, C1, U1, L3, C2, C82–C86, R5 and R67–R70 removes **₹610.55 in priced parts**. The configuration still uses the USB-C qualification path, mux and 3.3 V buck and requires a source advertising 3 A. The starter is a fit preset for the draft and needs the USB and 3.3 V routing issues closed before use. [Build configurator](Industrial-HMI-RevN-Build-Configurator.html)

Design references include [Raspberry Pi RP2350 hardware resources](https://pip.raspberrypi.com/categories/1214-rp2350), [BT818](https://brtchip.com/wp-content/uploads/2022/04/DS_BT817_8.pdf), [STUSB4500L](https://www.st.com/resource/en/datasheet/stusb4500l.pdf), [TPS2121](https://www.ti.com/lit/ds/symlink/tps2121.pdf) and [TPS62902](https://www.ti.com/lit/ds/symlink/tps62902.pdf). The panel, nominal 5 V and 3.3 V loads, and independent field-side RS-485 returns are documented in the Rev M baseline. [Power budget and interfaces](../industrial-hmi-rev-m/README.md)

## Passive consolidation and 0603

The schematic and BOM retain 31 fitted 0402 positions, including the 16 sensitive placements restored to their checkpoint footprints. The remaining 55 footprint changes are listed in the editor worklist. The PCB and placement artwork still describe the checkpoint layout. In a native EasyEDA working copy, use **Design → Update PCB**, review the footprint changes and resolve the worklist before assembly. C41 retains the existing part because the cheaper candidates examined lost capacitance on its 3.3 V rail. [Sourcing decisions and exceptions](REV-N-PASSIVES.md) · [Region-ordered placement checks](0603-WORKLIST.csv)

## Buzzer and field-input Zeners

**BZ1.** Fit Huaneng TMB12A05 or an equivalent 12 mm, 5 V active magnetic buzzer drawing at most 30 mA. Sharvi SKU `ST2136CO8767` was listed in stock at **₹15.47 excluding tax** on 25 November 2026 IST. Sharvi publishes availability without a quantity, so the three-board list uses the exact Huaneng `C96093` with an order quantity of five. **Measure the purchased part’s lead pitch and diameter before layout.** The library uses 7.6 mm pitch and 1.0 mm finished holes. Some equivalents use 6.5 mm. Pad 1 is square and connects to `SYS_5V`. Pad 2 connects to `BUZZ_LOW`. Q2, D9 and R41 stay fitted as designed. [Sharvi listing](https://sharvielectronics.com/product/tmb12a05-5v-electromagnetic-active-buzzer-pcb-mount-12mm-diameter/) · [Huaneng specification](https://sharvielectronics.com/wp-content/uploads/2025/11/TMB12A05.pdf) · [LCSC orderable](https://www.lcsc.com/product-detail/C96093.html)

**D11, D14, D17 and D20.** Diotec `BZT52B8V2-AQ` maintains 8.2 V, the manufacturer’s ±2% class, AEC-Q101 and the SOD-123F land with the cathode on pad 1. Diotec rates it for 500 mW at a 75°C terminal with the specified copper area. Confirm the field input trip points on the first article because the 5 mA Zener impedance is up to 30 Ω. DigiKey India listed 11,310 units and ₹12.364 per unit at the 10-piece tier used for the 14-piece order. [Diotec ratings](https://diotec.com/en/product/BZT52B8V2-AQ.html) · [DigiKey India](https://www.digikey.in/en/products/detail/diotec-semiconductor/BZT52B8V2-AQ/29178538)

## Cabinet output capacitors

C85/C86 use Samsung `CL32A476KOJNNNE`, 47 µF ±10%, 16 V X5R in the existing 1210 lands. The previous 33 µF orderable had no verified exact quote or DC-bias curve. Samsung’s 25°C curve is about −41.2% at 5.0 V and −43.4% at 5.25 V. The pair is about 55.3 µF typical at 5.0 V and 53.2 µF typical at 5.25 V. Applying 10% initial tolerance and 15% X5R temperature allowance gives a planning estimate of **40.7 µF at 5.25 V**, before aging, with C2 excluded from the calculation. The DC-bias data are typical. [Samsung DC-bias data](https://product.samsungsem.com/mlcc/CL32A476KOJNNN.do) · [LCSC orderable](https://www.lcsc.com/product-detail/C2932477.html)

For Rev N’s 7-inch power budget, applying TI’s 25%-to-75% load-step test to the 1.55 A allocation gives a 0.775 A step. Equation 12 requires about 31 µF effective at 400 kHz for a 250 mV deviation, or about 38 µF using 360 kHz with the −8.5% dither excursion. This supports fitting the Samsung pair for prototype qualification. A full 1.55 A step would require about 75 µF effective at that frequency corner and falls outside this screen. TI’s 3.5 A example calls for around 70 µF for its 1.76 A step at 400 kHz. The original pair had 66 µF nominal before derating. Compare measured startup and worst actual load steps with the 250 mV limit after the U1 reroute. Check ripple and loop stability across line, load and temperature, including the optional relays if fitted. [TI datasheet §§6.5, 8.2.2.5](https://www.ti.com/lit/ds/symlink/lmr51635.pdf) · [Power budget](../industrial-hmi-rev-m/README.md#7-inch-power-budget)

## LCSC retail stock

The costed BOM records the prior 1,000-unit retail screen and refreshed stock for the changed orderables. The purchase list applies the actual three-board order quantity and moves short lines to suppliers with sufficient published stock. [Prior retail screen](REV-N-PASSIVES.md#lcsc-retail-stock-and-0402-follow-up) · [Purchase list](PURCHASE-LIST.csv)

## Release blockers

**U1 cabinet converter routing.** The offline verifier confirms a legacy top-layer track at the center of each affected pad. Reroute all three pads in a new working copy and rebuild the pours. Keep fabrication on hold until native ERC/DRC and a copper review resolve the U1 conflicts, the D25 land mismatch, the J4 drill and slot issues, and the U6 and U23 land differences. [PCB editor tasks](REV-M-PIN-AUDIT.md#pcb-editor-tasks)

| Inherited routing finding | Location |
| --- | --- |
| GND opens | R76.2 and U6.4 |
| SYS_5V opens | U6.5 and U6.6 |
| USB_VBUS open | U21.24 |
| USB_RAW_SENSE open | U21.18 to R73.2 |
| USB_REG27 open | U21.23 to C89.1 |
| USB_FET_GATE open | R72.1 |
| Clearance below draft 0.125 mm rule | 0.116 mm between U6.7 SYS_3V3_MODE and adjacent SYS_5V copper |

Resolve these findings in EasyEDA before exports. Native EasyEDA import, ERC/DRC, mounting and connector fit including the USB shell slots, independent CAM and hardware qualification remain pending.

## Cabinet enable divider

Rev N fits **91 kΩ ±1% at R68** in the existing 0603 footprint, with R67 at 1 MΩ. TI’s EN thresholds multiplied by `1 + R67/R68` give **14.70 V rising and 11.81 V falling** at `VIN_PROT`, after D1. The specified EN limits and initial ±1% resistor tolerances give 12.98–16.47 V rising and 10.44–13.24 V falling. The earlier 330 kΩ value gave 4.94 V rising and 3.97 V falling, close to the buck's dropout region. [TI EN thresholds and equations](https://www.ti.com/lit/ds/symlink/lmr51635.pdf)

At 20.4 V on J1 and an assumed 0.7 V input-path drop, the 91 kΩ divider has about **3.2 V of estimated startup margin** against the 16.47 V upper threshold. The 78.7 kΩ candidate gives about 0.9 V under the same assumptions. After rerouting U1, verify cold start at 20.4 V under full load and capture `VIN_PROT`, `CAB_5V` and `SYS_5V` during a slow supply ramp and brownout, with and without qualified USB power. These checks establish actual startup and handoff behavior.

## Rev O candidates

These are planning ranges per fitted board before engineering and qualification. Compare the actual Rev N dealer tier when evaluating each proposal.

| Candidate | Estimated opportunity | Qualification |
| --- | --- | --- |
| J1/J3/J6/J7/J9 generic screw terminals | ₹200–450 | Match pitch, pin-one orientation, tool access, current, wire gauge and enclosure clearances. |
| J2 generic 40-pin FPC | ₹0–40 | The exact Hirose can already be inexpensive. Verify contact side, FPC thickness, latch and lifecycle. |
| F1 smaller SMD fuse or PTC | ₹5–20 | Preserve fault interruption, surge behavior, operating temperature and cabinet input rating. |
| J10 generic microSD | ₹20–65 | Verify insertion geometry, shell and pad drawing, pin numbering, hot plug and enclosure access. |
| J11 HR911105A-class MagJack | ₹20–100 | Verify center-tap topology, isolation, Ethernet magnetics, LEDs, pegs and footprint. |
| Replace STUSB4500L with CC comparators | ₹80–170 | Implement both CC orientations, dynamic current changes, valid VBUS, detach behavior, inrush and independent BOOTSEL data gating. |
| Enable 1.5 A USB for HMI-only build | ₹0 BOM if existing hardware supports it | Estimated 1.23 A at nominal 5 V is steady state. Demonstrate startup, worst-case cable drop, current limits and enforcement of relay/load exclusion. |
| Remove BT818 | Up to the current BT818 line price before added parts and software | An 8-bit 800 × 480 buffer is 384,000 bytes. Verify memory margin, RGB timing and bandwidth, touch interface and UI performance. |
| Consolidate passive packages and feeder use | ₹0–40 material, up to the vendor’s per-feeder fee for each eliminable SKU | Review DC bias, surge ratings, pin escapes, loading class, PCB reflow and service tier. |

## Workstation setup

| Install or open | Purpose |
| --- | --- |
| Claude Code, signed in | Run locally from the Rev N folder with one of the native installers below and an account with Claude Code access. [Official setup](https://code.claude.com/docs/en/setup) |
| EasyEDA Standard in a desktop browser or the Standard desktop app | Open both source JSONs in the same project using **File → Open → EasyEDA**. Use **File → EasyEDA File Source** to save editable backups. [EasyEDA downloads](https://easyeda.com/page/download) · [Standard source workflow](https://docs.easyeda.com/en/Export/Export-EasyEDA-Source-File/) |
| Python 3 | Run the Rev N offline comparison and the workspace's Gerber ZIP inventory script. It uses the standard library. Use `py -3` on Windows if that is the installed launcher. [Python downloads](https://www.python.org/downloads/) |
| KiCad GerbView | Independently inspect the final Gerber and drill artwork. [KiCad downloads](https://www.kicad.org/download/) · [GerbView](https://www.kicad.org/discover/gerber-viewer/) |
| Git, recommended | Keep the reviewed native source and exports tied to one revision. A dated local copy also works for the handoff. [Git downloads](https://git-scm.com/downloads) |

For Claude Code on macOS, Linux or WSL, follow the official native installer.

```sh
curl -fsSL https://claude.ai/install.sh | bash
claude --version
python3 --version
```

For native Windows PowerShell, use the Windows installer.

```powershell
irm https://claude.ai/install.ps1 | iex
claude --version
py -3 --version
```

Keep the `easyeda-pcb/` and `industrial-hmi-rev-n/` folders together. The instructions can read the skill in place. To make `/easyeda-pcb` available, copy the whole skill folder, including its supporting files, to `.claude/skills/easyeda-pcb/` under the folder where Claude starts. [Claude project instructions](https://code.claude.com/docs/en/memory) · [Claude skills](https://code.claude.com/docs/en/skills)

Use a native EasyEDA session for editor checks and manufacturing exports. In Standard, use an available editor integration or work with the user in the GUI. When Claude needs a user action, identify the exact editor operation and expected result, then continue independent checks while it is pending.

- **Standard GUI automation on an eligible Mac.** Start an interactive Claude Code session, open `/mcp`, and enable `computer-use`. The feature requires an eligible Claude Pro, Max or Ultra account. Grant macOS Accessibility and Screen Recording permissions when prompted and approve the EasyEDA app for that session. [Claude CLI computer use](https://code.claude.com/docs/en/computer-use)
- **EasyEDA Pro automation.** Install Pro Desktop 4.1.60 or later with its bundled CLI. The official examples use native Windows. Confirm CLI support on the host and that `easyeda-pro doctor` shows a connected editor. Import the Standard ZIP into a working copy and confirm the active project. Compare imported pin-to-pad mappings, nets, outline, stack and copper before editing. Use the version-matched CLI documentation and check each result. [Standard-to-Pro import](https://prodocs.easyeda.com/en/import-export/import-easyeda/) · [Pro CLI](https://prodocs.easyeda.com/en/api/guide/cli.html) · [Pro CLI instructions for Claude](https://prodocs.easyeda.com/storage/texts/api/guide/cli-for-ai.md)

To connect the Pro CLI as a local MCP server, run these commands from the Rev N folder after opening the Pro editor. [Claude MCP setup](https://code.claude.com/docs/en/mcp)

```sh
easyeda-pro doctor
claude mcp add --transport stdio easyeda-pro -- easyeda-pro --mcp stdio
claude mcp list
```


From the workspace root, run the offline comparison with Python 3.10 or newer. The script uses the standard library and expects the adjacent Rev M folder.

```sh
python3 industrial-hmi-rev-n/tools/verify_rev_n.py
cd industrial-hmi-rev-n
claude --add-dir ../easyeda-pcb
```

For a fabrication handoff, ask Claude to follow CLAUDE.md and use a working copy in the native editor.
