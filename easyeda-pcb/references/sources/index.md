# Local source library

This library supports the PCB rulebook, editor workflow, and release checks offline. Original source files are stored in `vendor/` and covered by their accompanying licenses. The other entries provide locally written notes and publisher links. Use the publisher's current source to confirm values that depend on a software version, fabrication service, device, or assembly option. The notes were checked on 2026-11-24.

Use the [on-demand hardware reference workflow](../hardware-rag.md) to build a separate corpus from selected vendor manuals and reference designs.

## Offline notes with publisher attribution

- [EasyEDA Pro and Standard](easyeda-notes.md) covers migration, copper layers, rules, routing, DRC, and export.
- [JLCPCB fabrication and assembly](jlcpcb-notes.md) covers process limits, physical stackups, impedance, and BOM and placement exports.
- [Texas Instruments](ti-notes.md) covers reference continuity, transitions, and regulator layout. Use the actual device guide for applicable dimensions and recommendations.
- [IPC and IEC standards](standards-notes.md) maps current and heating and insulation coordination to the applicable publications.

## Imported originals

| Publisher | Local original | Pinned source and license |
| --- | --- | --- |
| Andrew Zonenberg | [Schematic review checklist](vendor/pcb-checklist/schematic-checklist.md) and [layout review checklist](vendor/pcb-checklist/layout-checklist.md) | [pcb-checklist at 70d8b77](https://github.com/azonenberg/pcb-checklist/tree/70d8b77d07f7e559a887baf14a22113f4855f2f5), [BSD 3-Clause license and copyright notice](vendor/pcb-checklist/LICENSE) |
| EasyEDA | [CLI overview](vendor/easyeda-client-cli/easyeda-cli.md), [CLI guide for AI assistants](vendor/easyeda-client-cli/cli-for-ai.md), and [design file format](vendor/easyeda-client-cli/easyeda-format.md) | [easyeda-client-cli at 5452c63](https://github.com/easyeda/easyeda-client-cli/tree/5452c638fca802ea29e27277479a56d869feb10a), [upstream license declaration](vendor/easyeda-client-cli/README.md#license), [Apache License 2.0](vendor/easyeda-client-cli/LICENSE) |

Imported Markdown is unchanged from the pinned revisions. The Apache license text was obtained from the [Apache Software Foundation](https://www.apache.org/licenses/LICENSE-2.0.txt). Treat imported guidance as supplemental. Apply the relevant checks to the user’s board, and use installed CLI help and built-in documentation for supported commands and formats.
