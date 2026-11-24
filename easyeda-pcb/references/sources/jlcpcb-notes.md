# JLCPCB source notes

Checked 2026-11-24. Treat the figures below as a dated reference for this fabricator. Check the actual quote and enabled options before choosing release rules.

## Rigid PCB capabilities

The published general 1 oz track width and spacing figures are 0.10 mm for two layers and 0.09 mm for multilayer. The manufacturer publishes separate limits for other copper weights and for different object pairs. The regular routed perimeter and routed slots are listed with 0.20 mm copper setback. Scoring and special edges have their own requirements. [PCB capabilities, track and outline sections](https://jlcpcb.com/capabilities/pcb-capabilities/)

The ordinary via and component hole tables serve different purposes. The guide gives separate via-hole and via-pad sizing, plated component annular rings, inner-layer hole-to-copper clearance, and plated and non-plated slots. Confirm the order's via diameter and treatment options and the intended tool versus finished-hole dimension. Mask web capability can vary by mask color and outer copper thickness. Check paste and silk against actual manufacturing artwork. [PCB capabilities, holes, mask and legend sections](https://jlcpcb.com/capabilities/pcb-capabilities/)

## Stackup and impedance

Choose a listed construction using layer count, finished thickness and copper weights. Retain its stackup identifier. Use the calculator with the actual routing layer, continuous reference plane(s), transmission-line type, impedance target and conductor gap. Coplanar structures also need the gap to ground. Check supported copper options and confirm that the selected order matches the calculation. [Controlled impedance stackups](https://jlcpcb.com/impedance), [Impedance Calculator user guide](https://jlcpcb.com/help/article/user-guide-to-the-jlcpcb-impedance-calculator)

## BOM and placement

The BOM identifies the designators, package and part to be fitted. Keep selected and DNP designators aligned with the assembly variant. The placement list identifies the designator and center position in mm, side, and rotation. Compare BOM and placement designators and verify part substitutions, orientation and centering in the assembly preview. [BOM guide](https://jlcpcb.com/help/article/bill-of-materials-for-pcb-assembly), [pick-and-place specification](https://jlcpcb.com/help/article/pick-place-file-for-pcb-assembly), [matching issues](https://jlcpcb.com/help/article/common-bom-and-cpl-matching-issues-and-explanations)

EasyEDA Pro and Standard provide BOM and placement export actions. The documented Standard placement export is available through the File or Fabrication menu. Verify the written file's units and headers for the selected assembler. [EasyEDA BOM and placement exports](https://jlcpcb.com/help/article/how-to-generate-the-bom-and-pick%26place-file-from-easyeda)
