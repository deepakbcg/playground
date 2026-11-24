# PCB design rulebook

Use this rulebook to turn a board's requirements into EasyEDA checks. Read [stackup and layout](stackup-and-layout.md) for layer selection, placement, and routing. Mark each rule **provisional** while its inputs or evidence are pending, **verified** when the selected process and actual implementation agree, or **blocked** when a required constraint cannot be met with the current geometry or process.

## Set the manufacturing and circuit limits

1. Record copper layer count and order, the exact fabricator service and stackup, finished board and copper thicknesses, panel/edge processes, finish and mask, assembly service, and via process. A setting for one copper weight or fabrication service can be invalid for another.
2. For each rule, keep the applicable process limit, any stricter circuit or assembly requirement, the implemented constraint, and the preferred routing value. For comparable minimum limits, apply the largest required minimum. For a permitted range, use the intersection. Satisfy nominal targets and tolerances separately. A calculated pair gap still has to satisfy the relevant fab clearances. If constraints conflict, change geometry, stackup, package, or process and recheck the affected rules.
3. Apply net and layer rules before creating critical routes. Use a scoped exception for a fine-pitch escape only when its dimensions satisfy the approved fabrication process and the circuit. Record the affected nets, pads or region, extent, rationale, and verification. Outside that scope, use the normal rules.
4. Confirm the effective rule on a representative object after assigning the rules. On heritage boards, check already-routed geometry against the new rules. Review disabled checks and region overrides. Where EasyEDA lacks a suitable check, capture measured geometry, calculation, CAM evidence, or a fab approval as applicable. Use the [EasyEDA rule workflow](easyeda-workflow.md) for edition-specific setup.

## Rules to enter or verify

| Rule | Set or derive | Verify |
| --- | --- | --- |
| Ordinary trace | Width floor and preferred width by signal class and applicable layer. Define a clearance matrix for traces, pads, vias, and copper pours where the process differentiates them. | Measure any neck-down and its length, inspect small-pitch exits, and run DRC after fill. Check same-net manufacturing requirements and specific object clearances separately when needed. |
| Board edge and cutouts | Copper setbacks and hole/pad setbacks by routed edge, routed slot and score line. Define any approved exceptions for edge connectors, edge plating or castellations. | Measure at the actual fabrication outline and cutouts, overlay drills, and confirm the routing or scoring method. |
| Drill and vias | Via pad diameter, CAD hole diameter, span, hole-to-hole and hole-to-copper spacing, annular ring, and aspect ratio on the fab's measurement basis. Define drill and pad independently for component PTH. | Verify hole and pad clearance on every relevant layer, especially inner antipads. A concentric round pad has nominal radial ring `(pad diameter − CAD hole diameter) / 2`. Confirm the fabricator's basis for drill compensation, registration and minimum ring. For component fit use the finished-hole tolerance and worst-case pin dimensions. |
| Slots and mounting | Plating, finished size, allowed slot aspect ratio and tool radius, end geometry, and hardware and copper keepouts. | Check pad or slot definitions against the drawing, CAM outputs and manufacturer mapping. Confirm PTH and NPTH classifications. |
| Mask, paste and silk | Mask expansion or contraction, minimum web and mask-to-adjacent copper clearance. Paste aperture and stencil based on assembly and component requirements. Silk-to-pad/edge space, stroke width and text height. | Review artwork on each side. Inspect narrow mask webs, exposed or tented vias, large thermal-pad paste, and legibility at pad and component edges. An open via beside a pad can wick solder if a solderable opening connects them. Inspect mask overlap and confirm the via treatment with the assembler. |
| Power and return | Worst-case continuous and pulse current, copper thickness, voltage-drop budget and allowed heating. Size each segment, return, plane neck, thermal spoke, and via group. | Estimate loss and drop with the warm-copper resistance of the whole path. Check connector, fuse, and shunt ratings and thermals. Verify high-current cases with a suitable thermal method and prototype measurements. |
| Differential and controlled impedance | Required target and tolerance, routed layer, reference plane(s), width, edge-to-edge gap, and coplanar ground gap if used. Record intra-pair skew and any inter-pair timing budget independently. | Calculate from approved physical stackup and check routed values, reference continuity, layer changes and launches. Verify fab ordering notes and test requirements. |
| Electrical separation | Required clearance, creepage and solid insulation from the applicable requirements for the actual voltages, transients, materials, and use environment. | Examine top, bottom, internal layers and mechanical interfaces, including plated slots, hardware and board surfaces. Record the evidence for any insulation claim. [Insulation coordination notes](sources/standards-notes.md#insulation-coordination) |

## Provisional starter settings

This example is for ordinary low-voltage, low-current signal nets on rigid 2-, 4-, or 6-layer FR-4 with nominal 1 oz outer copper, ordinary mechanical through vias, and a routed perimeter. Values are planning choices with margin over selected capability examples. Fine-pitch escapes, defined impedance, RF launches, power, safety spacing, component holes, slots, and via-in-pad each need their own rules. The [fabricator notes](sources/jlcpcb-notes.md#rigid-pcb-capabilities) explain the process assumptions behind the example. Confirm the actual layer copper weights, hole process, edge method and assembly options before applying it to a released design.

| Setting | Provisional value | Application |
| --- | --- | --- |
| Ordinary trace width | 0.20 mm (7.87 mil) | Use as the route setting and class minimum for the initial layout. |
| Ordinary different-net copper clearance | 0.20 mm (7.87 mil) | Assign within the ordinary signal class. Add separate rules or measured checks for holes, edges, power and sensitive-net interactions. |
| Standard through via | Ø0.60 mm pad, Ø0.30 mm CAD hole | Start with a full-stack through via. The nominal radial ring is 0.15 mm. Confirm the actual fab via process and target dimensions. Use a separately qualified via style for dense or special escapes. |
| Copper to routed perimeter or routed cutout | 0.30 mm (11.81 mil) | Apply to copper on all layers. Check hole and pad setbacks, scoring and special edges separately. |

For a project-specific rule sheet, use one row per constraint with these fields.

| Constraint | Scope | Fab or assembly limit | Circuit requirement | Implemented rule and units | Source and verification |
| --- | --- | --- | --- | --- | --- |
| Trace width | Default low-current outer-layer signals | Confirm for selected service and copper weight | No additional minimum for this example | 0.20 mm provisional | Check chosen fab limits, apply in EasyEDA, and rerun DRC on the final revision. |

Keep all design values in one unit system and convert with `1 mil = 0.0254 mm`. After entering values, check editor rounding and measure at least one applied geometry per affected rule. If several Net Classes or Region Rules can apply, verify the effective rule at their boundary and at the narrowest detail.

For example, a solved differential gap of 0.13 mm conflicts with a selected process requiring at least 0.15 mm for that pair. Sweep gap and width together within the process limits, then verify impedance and tolerance on the actual routing layer. If no geometry works, choose a different referenced layer, stackup, or approved process. Hold the affected rule until the conflict is resolved.

## First-pass power calculation

For a uniform copper segment, estimate `R = ρ × length / (width × copper thickness)`. Use consistent units and choose copper resistivity for the expected temperature. Compute `Vdrop = I × R` and `P = I² × R` segment by segment. Include both supply and return, plus vias, pads, thermal spokes, contacts, and component losses. For example, using `ρ ≈ 1.724 × 10⁻⁸ Ω·m` at 20 °C, a 20 mm long, 0.50 mm wide, 35 µm thick segment has about 19.7 mΩ of resistance. At 1 A that is about 19.7 mV and 19.7 mW for the segment. The acceptable current also depends on temperature rise, nearby copper, airflow, fabrication tolerances, and faults or surges. Check those separately where the current matters. [Conductor current and heating notes](sources/standards-notes.md#conductor-current-and-heating)

Use the [local source library](sources/index.md) for offline source notes and the schematic and layout sign-off checklists.
