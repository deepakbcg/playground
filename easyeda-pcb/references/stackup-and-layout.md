# Stackup, design rules, and layout

## Choose the layer map before critical routing

The following are starting layer assignments from top to bottom. Confirm that the fabricator offers the matching physical stackup and assign a continuous reference to each critical routed segment.

| Copper layers | Starting layer assignment | Feasibility check |
| --- | --- | --- |
| 2 | L1 components and signals. L2 mostly continuous GND. Route power on L1 or in local copper where its return path remains intact. | Route the critical paths first. Check that L2 crossings and voids leave a direct return under them. Check whether the available dielectric thickness supports any required impedance without impractical traces. |
| 4 | L1 signal, L2 GND, L3 GND, L4 signal. Distribute power with traces or local pours if they meet the rail's current and drop limits. | Both outer signal layers can use adjacent GND. If L3 is needed for power, keep critical routes on L1 unless L4 has a verified continuous reference and a return path at transitions. Treat a split L3 as multiple disconnected reference regions. |
| 6 | L1 signal, L2 GND, L3 signal, L4 power, L5 GND, L6 signal. | Use L2 and L5 as references for the outer layers. For L3, choose dielectric spacing and solver settings that account for coupling to L2 and L4. Keep critical L3 routing away from L4 splits when that plane materially affects return or impedance. If L4 serves as a second inner signal layer, verify L4's reference to L5 and the coupling between L3 and L4. |

Use the lowest layer count that meets placement, escape, return-path, rail distribution, impedance, mechanical, and fab constraints with useful margin. Move from 2 to 4 when ground continuity or routing density breaks down. Move from 4 to 6 when the 4-layer trial needs an additional referenced route layer or a power distribution layer while preserving reference copper. If constrained to a given layer count, test placement and escape changes before recommending a different stackup or package. For an already routed board, changing the stackup reopens all affected return-path, impedance, via span, and CAM checks.

## Place the circuits that govern routing

1. Lock the board outline, mounting, connector access and antenna or isolation keepouts. Verify the mating parts, screw and washer envelope, and bottom-side assembly clearance.
2. Place connectors, protection components, the regulator power stage, clock sources, and parts that determine dense or high-speed escape. Reserve a short discharge return beside the protection device. Place decoupling to shorten the path from the IC supply pin through the capacitor and back to ground, including both vias and plane connections.
3. Try the most constrained escape and signal path first using the [PCB design rulebook](design-rules.md). If the shortest route would cross a reference gap, change placement, the path, or the layer map before routing the remaining nets. Use through vias when the escape and return paths permit. Get fabrication approval for blind or buried vias, microvias, and via-in-pad fill and capping before committing the design.
4. Route regulator switching loops and sensitive analog nodes early. Keep feedback and other high-impedance signals clear of the switch node and inductor. For current sensing, follow the part's Kelvin connection points and keep the sense pair out of load-current paths. Place oscillators close to their pins and follow the device's load, grounding and keepout guidance.

## Controlled impedance and timing

Find targets and tolerances in the interface or device guidance. Record per-layer reference plane, stackup ID, copper thickness, dielectric height and properties, solder mask assumptions, and conductor geometry. Use the fabricator's calculator or confirmed field-solver result for the selected stackup and geometry. Enter the resulting single-ended width or pair width and edge-to-edge gap. Include the ground gap for coplanar structures. Verify the actual route, pads, escapes, and transitions against the chosen geometry. Record ordering requirements and the agreed tolerances, including test or coupon requirements where applicable. A layer count or target impedance alone leaves dimensions undetermined. [Fabricator stackup and calculator notes](sources/jlcpcb-notes.md#stackup-and-impedance)

Track intra-pair skew separately from inter-net/group timing. Apply the device's measurement boundaries and delay or length budget, including package delay and vias where specified. Keep pair transitions symmetrical and minimize unnecessary layer changes, stubs, and tightly packed tuning segments. Trace the return path visually, including under connectors, through via fields, and across plane splits, voids, and cutouts. Where a signal changes between ground reference planes, place suitable nearby ground stitching vias. If the reference nets differ, redesign the route or explicitly verify a suitable AC return transition for the frequency and circuit. [High-speed layout notes](sources/ti-notes.md#high-speed-routing-and-reference-transitions)

## Inspect critical regions after copper rebuild

- **Mechanical and placement:** verify outline dimensions, cutouts, mounting holes, connector mating direction and reach, component height, enclosure and fastener clearance, and fabrication and assembly keepouts. Compare against dimensioned mechanical drawings if a 3D model is missing or uncertain.
- **Power and noise:** inspect regulator hot loops and feedback sensing, power and thermal paths, and return from the load to its source. Follow the device's layout guide for switch-node copper and ground. [Buck converter layout notes](sources/ti-notes.md#buck-converter-placement-and-routing)
- **Analog and RF:** place sensitive nodes away from switching currents, clocks, and digital return paths. Follow part-specific grounding and RF geometry guidance. Check antenna keepouts on every applicable layer, including mechanical and enclosure constraints.
- **Planes and pours:** inspect plane continuity and net membership, thermal connections, isolated islands, slivers, necks, and disconnected vias. If a ground pour is intended as a reference, verify electrical attachment and continuous coverage under the route. Use the final plane shape after fill, especially around holes, slots, and dense via fields.
- **Inspection and bring-up:** when in scope, preserve accessible test and programming pads for power, ground, and key interfaces. Check probe and fixture access on the assembled board.
