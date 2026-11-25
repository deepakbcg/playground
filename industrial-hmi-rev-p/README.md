# Industrial HMI Rev P

**Draft — DO NOT FABRICATE OR POWER.** This 99.2 × 96 mm, four-layer EasyEDA Standard design uses the RP2354B and BT818. The release status tracks copper verification, remaining editor work and prototype bring-up. [Rev P status](REV-P-STATUS.md)

| Files | Contents |
| --- | --- |
| [EasyEDA ZIP](Industrial-HMI-RevP-EasyEDA-DO-NOT-FABRICATE.zip) | The live [schematic](Schematic_Industrial-HMI-RevP-DO-NOT-FABRICATE.json), [PCB](PCB_Industrial-HMI-RevP-DO-NOT-FABRICATE.json) and the BZ1, D25, U6 and U23 footprint libraries. |
| [BOM](Industrial-HMI-RevP-BOM.csv) · [Costed BOM](Industrial-HMI-RevP-BOM-Cost-INR.csv) · [Three-board purchase list](PURCHASE-LIST.csv) | Fitted parts, DNPs, cost and supplier quantities with spares. |
| [Build configurator](Industrial-HMI-RevP-Build-Configurator.html) · [Panel pinout](Industrial-HMI-RevP-Panel-Pinout.csv) | Staged population and display connector wiring. |
| [Pin audit](REV-M-PIN-AUDIT.md) · [Pin audit CSV](REV-M-PIN-AUDIT.csv) · [Substitution evidence](tools/substitution-evidence.csv) | Datasheet assignments and sourcing rationale. |
| [Specification PDF](Industrial-HMI-RevP-Specification.pdf) | Rev P specifications with marked historical reference pages. |
| [Schematic PDF](Industrial-HMI-RevP-Draft-Schematic.pdf) · [PCB preview](Industrial-HMI-RevP-PCB.png) · [Placement preview](Industrial-HMI-RevP-Placement.png) | Rev M/N artwork — re-export pending in EasyEDA. |
| [Editor runbook](EDITOR-RUNBOOK.md) · [Fabrication notes](FAB-NOTES.md) · [Bring-up](BRING-UP.md) | Native EasyEDA review, evidence and staged bench tests. |
| [J4 approved-trim footprint](Footprint_GCT-USB4105-GF-A-REV-P.json) | GCT B3 geometry with the approved locator clearance trim. See the D24 clearance blocker before applying it. |
| [Verifier](tools/verify_rev_p.py) · [Recorded verification](tools/verification-output.txt) · [Reference license](Raspberry-Pi-Reference-LICENSE.txt) | Stored-geometry checks and reference license. |

Run the verifier from this checkout with Python and Shapely 2.1 or newer. Keep the local annotated `rev-n` tag available for the copper comparisons.

```sh
python3 -m pip install 'shapely>=2.1,<3'
python3 industrial-hmi-rev-p/tools/verify_rev_p.py
```
