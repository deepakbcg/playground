# Rev M PCB fabrication handoff

## Objective and baseline

Prepare the 99.2 × 96.0 mm four-layer Rev M HMI for a **first-article PCB fabrication release**. The circuit and fitted parts are the Rev M baseline. The existing routed board is a draft. Use a named working copy and keep the supplied source recoverable.

- Open both JSON documents in [Industrial-HMI-RevM-EasyEDA.zip](Industrial-HMI-RevM-EasyEDA.zip). They are EasyEDA Standard schematic and PCB sources. Match the active schematic and PCB before editing.
- Use the [specification sheet](Industrial-HMI-RevM-Specification.pdf), [README](README.md), [component BOM](Industrial-HMI-RevM-BOM.csv) and [panel pinout](Industrial-HMI-RevM-Panel-Pinout.csv) for design intent. Use the [configurator](Industrial-HMI-RevM-Build-Configurator.html) to record the fit/DNP choices for this build.
- Use the EasyEDA PCB skill from `../easyeda-pcb/SKILL.md` or the installed `/easyeda-pcb` skill. Read its editor workflow, layout, rule and release references. Prefer the official manufacturer references, including the Raspberry Pi RP2350B Minimal R4-S1 for the MCU core. Preserve its license. Check adaptations for the RP2354B in-package flash and the Rev M USB-C circuit. [Raspberry Pi design resources](https://pip.raspberrypi.com/categories/1214-rp2350)
- Maintain the main-board outline, mounting, hardware UARTs, USB-C and cabinet power paths, RP2354B, J2 panel pinout, independent RS-485 returns and the approved YLPTEC/Bourns parts. Use the separate Rev I relay board source only if the relay board is also in scope. [Rev I relay source](../industrial-hmi-rev-i/Industrial-HMI-RevI-Relays-EasyEDA.zip)

## Workstation setup

| Install or open | Purpose |
| --- | --- |
| Claude Code, signed in | Run locally from the Rev M folder with one of the native installers below and an account with Claude Code access. [Official setup](https://code.claude.com/docs/en/setup) |
| EasyEDA Standard in a desktop browser or the Standard desktop app | Open both source JSONs in the same project using **File → Open → EasyEDA**. Use **File → EasyEDA File Source** to save editable backups. [EasyEDA downloads](https://easyeda.com/page/download) · [Standard source workflow](https://docs.easyeda.com/en/Export/Export-EasyEDA-Source-File/) |
| Python 3 | Run the workspace's Gerber ZIP inventory script. It uses the standard library. Use `py -3` on Windows if that is the installed launcher. [Python downloads](https://www.python.org/downloads/) |
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

Keep the `easyeda-pcb/` and `industrial-hmi-rev-m/` folders together. The instructions can read the skill in place. To make `/easyeda-pcb` available, copy the whole skill folder, including its supporting files, to `.claude/skills/easyeda-pcb/` under the folder where Claude starts. [Claude project instructions](https://code.claude.com/docs/en/memory) · [Claude skills](https://code.claude.com/docs/en/skills)

Use a native EasyEDA session for editor checks and manufacturing exports. In Standard, use an available editor integration or work with the user in the GUI. When Claude needs a user action, identify the exact editor operation and expected result, then continue independent checks while it is pending.

- **Standard GUI automation on an eligible Mac.** Start an interactive Claude Code session, open `/mcp`, and enable `computer-use`. The feature requires an eligible Claude Pro, Max or Ultra account. Grant macOS Accessibility and Screen Recording permissions when prompted and approve the EasyEDA app for that session. [Claude CLI computer use](https://code.claude.com/docs/en/computer-use)
- **EasyEDA Pro automation.** Install Pro Desktop 4.1.60 or later with its bundled CLI. The official examples use native Windows. Confirm CLI support on the host and that `easyeda-pro doctor` shows a connected editor. Import the Standard ZIP into a working copy and confirm the active project. Compare imported pin-to-pad mappings, nets, outline, stack and copper before editing. Use the version-matched CLI documentation and check each result. [Standard-to-Pro import](https://prodocs.easyeda.com/en/import-export/import-easyeda/) · [Pro CLI](https://prodocs.easyeda.com/en/api/guide/cli.html) · [Pro CLI instructions for Claude](https://prodocs.easyeda.com/storage/texts/api/guide/cli-for-ai.md)

To connect the Pro CLI as a local MCP server, run these commands from the Rev M folder after opening the Pro editor. [Claude MCP setup](https://code.claude.com/docs/en/mcp)

```sh
easyeda-pro doctor
claude mcp add --transport stdio easyeda-pro -- easyeda-pro --mcp stdio
claude mcp list
```

## Close the layout findings

1. Reproduce the outstanding findings in the native editor. Check all endpoints on the following six nets. The endpoints listed come from the offline routing review.
   - **GND** at R76.2 and U6.4.
   - **SYS_5V** feeding U6.5 and U6.6.
   - **USB_VBUS** at U21.24.
   - **USB_RAW_SENSE** between U21.18 and R73.2.
   - **USB_REG27** between U21.23 and C89.1.
   - **USB_FET_GATE** at R72.1.
2. Resolve the measured **0.116 mm** gap between U6.7 `SYS_3V3_MODE` and the adjacent `SYS_5V` trace. The draft check used **0.125 mm**. Set the effective rule from the selected process and design, then verify the repair after rebuilding copper.
3. Confirm the fabricator, stackup ID, finish, finished thickness, copper weights, via process, and assembly variant. Start stackup review with the project's nominal 1.0 mm FR-4 target. Derive release widths, gaps, setbacks and clearances from the chosen process. Check 90 Ω differential USB and 100 Ω differential Ethernet MDI using the actual reference layers and fabricator stackup. Review RGB timing, return paths, regulator hot loops and power trace current. [JLCPCB stackup and impedance](https://jlcpcb.com/impedance) · [WIZnet hardware guide](https://docs.wiznet.io/Design-Guide/hardware_design_guide)
4. Check USB4105-GF-A J4 land, shell slot and mating geometry against GCT's drawing. Confirm plated retention slots and how the fab maps them. Verify five mounting holes, the RJ45 locating holes and shell stakes, and access for the FPC, SD card, RTC cell, BOOTSEL, RESET and SWD. Check the enclosure and cable clearances with the selected connector and display drawings. [GCT drawing](https://gct.co/files/drawings/usb4105.pdf)
5. Preserve both RS-485 field domains and the input bank return on every copper layer. Inspect the short TVS discharge paths to local COM and the copper keepouts through the stack. Review D4/D10 clamp selection against the intended surge level. Preserve optional DNP R4/R38 termination in the default variant. Verify the YLPTEC module hole and lead fit and the Bourns TVS pinout from the current drawings. [TI surge reference](https://www.ti.com/tool/TIDA-00731) · [YLPTEC datasheet](https://www.lcsc.com/datasheet/C2992421.pdf)

## Verify and export

- Complete the available schematic electrical checks. Compare schematic-to-PCB reference, footprint, pin and net membership. Record intentional NCs and the fitted variant. Rebuild all copper, make every ratline visible, then run full native DRC. Require zero unexpected opens, shorts and unresolved rule violations. Record any approved exception with its rule, location, rationale and evidence.
- Freeze one CAD revision and save its editable source, final schematic PDF and build settings. In Standard use **Fabrication → PCB Fabrication File (Gerber)**. Generate the native Gerber ZIP with the closed outline, top through bottom copper, both solder masks, specified silkscreen and applicable plated and non-plated drill and slot outputs. Export paste for the stencil or assembly variant. [Standard Gerber export](https://docs.easyeda.com/en/PCB/Gerber-Generate/)
- Map copper top to bottom as **L1 Top, L2 Inner1, L3 Inner2, L4 Bottom**. L2 is primarily a return layer with local routes. Verify the actual copper and layer mapping from the export. In an independent CAM viewer, overlay copper, outline, mask and drills. Inspect dimensions, registration, hole counts and plating, inner clearances, critical connector fits and the isolation barriers. Use a local integrity check and the inventory helper as additional checks.

```sh
python3 ../easyeda-pcb/scripts/inspect_gerber_zip.py \
  release/Industrial-HMI-RevM-Gerbers.zip --layers 4 \
  --require top-mask --require bottom-mask --require top-silk \
  --require pth --require npth
```

- The inventory script checks native filename roles. Confirm component holes and plated slots in the actual drill or route files even when the script finds a plated via drill file. Review any unclassified CAM outputs. Use the intended fabricator's exact layer and drill conventions.
- For PCBA, export the assembly BOM, CPL and assembly drawing from the frozen revision and selected variant. Match reference sets, quantities, part numbers, side, pin 1, rotation, origin and units. Identify DNP and hand-fit parts separately, including the CR2032 after reflow and any THT parts the assembler will omit. Verify supplier codes and the assembly preview if available. [JLCPCB assembly file requirements](https://jlcpcb.com/help/article/pcb-assembly-faqs)
- Deliver `release/` with the native source, schematic PDF, Gerber/drill ZIP, fabrication notes and release report. Add BOM/CPL and assembly notes if PCBA is requested. Record the revision, CAD version, stackup, checks actually run, screenshots or reports, remaining limitations, and SHA-256 of the Gerber ZIP. Keep the relay board's manufacturing data in its own package if ordered.
- When editor access or release evidence is pending, label the output **Draft** and give the remaining actions with locations and expected results. Keep any external upload, quote submission or purchase subject to the user's authorization. A first-article fabrication release is followed by hardware qualification before production.

## Start a session

From the workspace root, run the following in your terminal. An adjacent skill folder is accessible through the added directory.

```sh
cd industrial-hmi-rev-m
claude --add-dir ../easyeda-pcb
```

Paste this prompt into Claude Code.

> Follow CLAUDE.md and the EasyEDA PCB skill. Finish the Rev M first-article fabrication package from the current EasyEDA Standard source. Start by identifying the editor session and the outstanding PCB findings. Resolve them, freeze a revision, and produce the native manufacturing exports with verification evidence. If an editor action needs me, state the exact action and continue the independent checks. Keep all outputs local.
