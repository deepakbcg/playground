# Texas Instruments source notes

Checked 2026-11-24. These application notes cover specific TI products and design examples. Use the selected device and interface documentation for numeric limits and geometry.

## High-speed routing and reference transitions

Review each high-speed route alongside its reference copper. Plane splits, cutouts and antipads can interrupt the return path. When moving between two ground references, nearby stitching vias can give return current a short transition. Keep the two traces and their transitions symmetric, account for via stubs and connectors in the channel, and verify delay and skew against the interface budget. See the reference-continuity and transition examples and the differential routing sections. [High-Speed Layout Guidelines for Signal Conditioners and USB Hubs, SLLA414A, Rev. A](https://www.ti.com/lit/an/slla414a/slla414a.pdf)

## Buck converter placement and routing

Trace the switching and return currents to identify the compact loops that placement must preserve. Keep the input capacitor and its return close to the switching stage. Limit switch-node copper to what the device requires. Keep feedback away from switching paths and sense the output and its return as the regulator documentation specifies. Verify placement and copper after making thermal or mechanical changes. [Five steps to a great PCB layout for a step-down converter, SLYT614](https://www.ti.com/lit/an/slyt614/slyt614.pdf)
