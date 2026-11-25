# Rev P staged prototype bring-up

Start with a prototype from the reviewed CAD and Gerber package after the fabrication hold is cleared. Plan a staged assembly with U2, U8 and U20 physically unpopulated through step 3. Disconnect the display, microSD, field wiring, relay board and CR2032 at the start. Use a current-limited bench supply with a voltmeter and scope. Record source voltage and current, rail min/max during startup and under load, and the population for each stage. Limits below are bench settings and current estimates are engineering references unless attributed to a part data sheet.

With power off, confirm polarity and pin 1 on J1, J4, U1, U6 and polarized components. Check for a hard short from each rail to its return and between cabinet and USB power paths. Check that RS_COM, RS2_COM and DI_COM do not show a DC short to logic GND or each other. Let charged capacitors discharge before fitting or removing parts.

## 1. Cabinet buck alone

Populate U1 and its input protection, fuse, inductor, feedback network and capacitors. Leave U22, U6 and downstream loads unpopulated. Feed J1.1 positive with J1.2 as the return. Start at **24.0 V with a 100 mA current limit** and no added load. Expect CAB_5V at C85/C86 to settle near **5.0 V**. Use **4.75–5.25 V** as the initial screening window. After inrush, the current should fall well below the 100 mA limit. Stop if it remains at the limit or the rail oscillates.

Check cold starts at **20.4 V and 27.6 V**. Probe VIN_PROT at C83 and CAB_5V at C85 with short ground leads. With a **0.20 A load** on CAB_5V, expect roughly **50 mA at 24 V** assuming 85% efficiency, plus quiescent current. Record startup, ripple and step-load response. With a slow input ramp, the nominal U1 thresholds are **14.7 V rising / 11.8 V falling at VIN_PROT**. Record the actual thresholds separately from the J1 voltage. Check the Bottom CAB_FB route for switching noise. [Rev P power changes](REV-P-STATUS.md#what-changed-since-rev-m) · [TI LMR51635 data sheet](https://www.ti.com/lit/ds/symlink/lmr51635.pdf)

## 2. USB-C and power mux

With U6 and the logic loads still absent, populate J4, USB-C protection, U21/Q3 and U22 with its dividers and passives. Include the USB data switch and control network for the later BOOTSEL test. Measure raw USB_VBUS at C87.1, USB_SW_VBUS at U22.2, CAB_5V at U22.7 and SYS_5V at TP1 relative to TP2. Start at **100 mA** on the cabinet source with no added SYS_5V load. For USB, use a USB-C test source or fixture that advertises the specified current while limiting and measuring delivered current. A plain 5 V bench lead to VBUS cannot test CC attachment.

| Source test | Expected result |
| --- | --- |
| Cabinet only | Around 5 V at CAB_5V and SYS_5V. J4 VBUS stays unpowered. |
| USB-C only, 5 V / 3 A advertised | 4.75–5.25 V at the source under the light test load, less cable drop at C87.1. Q3 conducts after valid attachment and SYS_5V follows with the mux drop. Test both plug orientations. |
| USB-C only, default or 1.5 A advertised | The source may present about 5 V at C87.1. The full SYS_5V rail stays off under a test load. |
| Both sources | Cabinet has priority in its valid range. The divider crosses its nominal rising threshold at about 4.41 V on CAB_5V. Measure SYS_5V droop and recovery when connecting or removing either source. Confirm no sustained reverse current into the idle source. |

Try a **100 mA dummy load** on SYS_5V and measure current at each input. Expect approximately 100 mA from USB if selected, or about 25 mA from a 24 V cabinet supply at 85% buck efficiency, plus control and conversion losses. Verify inrush, backfeed, both orientations and loaded transfer before moving on. Record the minimum voltage and duration of any handoff dip. [ST STUSB4500L data sheet](https://www.st.com/resource/en/datasheet/stusb4500l.pdf) · [TI TPS2121 data sheet](https://www.ti.com/lit/ds/symlink/tps2121.pdf)

## 3. Shared 3.3 V before expensive ICs

**Keep U2 (RP2354B), U8 (BT818) and U20 (W5500) physically unpopulated.** Fit U6, L4, C93, C94 and the U6 support circuit. Confirm U6.3 VOS connects to C94.1. At first power use the proven cabinet path with a **100 mA limit at 24 V**. Measure **C94.1 to C94.2** and the far point **C34.1 to C34.2**. Use a scope with local ground connections and capture startup as well as steady state.

- **Abort immediately if either point exceeds 3.45 V**, including during startup or a load release. Expect about **3.30 V** at both points and **3.15–3.45 V** throughout the screening tests.
- Start with a **0.10 A** electronic load on a suitable 3V3 distribution point away from C94 and expect roughly **78 mA at 5 V on SYS_5V**, assuming 85% conversion efficiency.
- Increase in steps to **1.1 A** and then **1.5 A** on 3V3. Expect roughly **0.85 A** and **1.16 A** on SYS_5V at 5 V, plus small control loads. At 24 V with 85% cabinet-buck efficiency, the 1.5 A test needs about **0.29 A from J1**. Raise the cabinet source limit only after earlier steps pass, to about **0.40 A** at 24 V for this load test. Leave the backlight and relay load disconnected.
- At 1.5 A, measure voltage drop from C94 to the distribution rail and temperature rise over ambient for the two Inner2 legs and their via transitions, with the intended enclosure and enough time to reach a steady temperature. This test qualifies the rail distribution against the ≤20 °C design target. Repeat startup and load release on qualified USB-C before proceeding. [TPS62902 data sheet](https://www.ti.com/lit/ds/symlink/tps62902.pdf) · [Copper calculation and requirements](FAB-NOTES.md#33-v-buck-current-path)

## 4. MCU, SWD, BOOTSEL and RTC

Fit U2 and its reference support parts only after the rail check passes. Expect **3.30 V** at C15 and **1.10 V** at C17 once the core regulator starts. Keep the **100 mA cabinet limit at 24 V** to start, with the display and interfaces absent. Log steady current in reset, USB BOOTSEL and a minimal heartbeat firmware build. As a scale for the MCU-only increment at 5 V, the Pico 2 reference board measures about 5.5 mA in idle USB boot and 12–13 mA with its simple firmware examples. Use the actual Rev P measurement as the population baseline. [Pico 2 reference measurements, table 2](https://pip-assets.raspberrypi.com/categories/1005-raspberry-pi-pico-2/documents/RP-008299-DS-3-pico-2-datasheet.pdf#page=14)

Connect SWD at J5 with the board powered by the cabinet and a shared debug ground. Check programming and read-back. Verify **SW2 RESET** starts the firmware and **SW1 BOOTSEL** held through reset enumerates USB boot on a data-capable host. Test both cable orientations. Confirm TP1 and the 3.3 V rail remain regulated while programming.

Fit U10 and check for an I²C response at **0x52** and **3.3 V** main supply. With the holder empty, configure and read back backup switchover and ensure the charger is disabled. Check the cell polarity, then install the primary CR2032, approximately **3.0 V** at BT1. Cycle main power and confirm retained time. Low-current battery measurements should use a suitable instrument. The RTC's timekeeping current is on the order of tens of nA. [RP2350/RP2354 data sheet](https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-008373-DS-4-rp2350-datasheet.pdf) · [Micro Crystal RTC application manual](https://www.microcrystal.com/fileadmin/Media/Products/RTC/App.Manual/RV-3028-C7_App-Manual.pdf)

## 5. BT818, panel, backlight and storage

Fit BT818 and its crystal/support network. With the backlight disabled, expect **3.3 V** at C34 and **about 1.2 V** at C37. Initialize the EVE controller and verify SPI identification. Typical BT818 normal-operation current is **30 mA on 3.3 V** before panel and backlight load. Record the increase above the MCU-only current with the panel and backlight off, then power down to connect J2. Check against the actual panel's contact orientation, timing and touch technology. Run RGB colour bars and touch calibration before enabling full backlight.

For the specified 7-inch panel, budget **10.5 V across the lit LED string at 133 mA**, approximately **0.35 A added at SYS_5V** at full brightness assuming 80% boost efficiency. Start with low PWM duty, then ramp it and check voltage, current and backlight temperature. Repeat the current estimate for a different panel. With a panel attached, verify clock/pixel timing and uninterrupted display refresh while writing and reading a microSD card. Check separate chip select behavior while the other SPI device is idle. If using BZ1, expect at most **30 mA** additional at 5 V when it sounds. [Panel pinout](Industrial-HMI-RevP-Panel-Pinout.csv) · [BT818 data sheet](https://brtchip.com/wp-content/uploads/2022/04/DS_BT817_8.pdf#page=46) · [TI backlight driver data sheet](https://www.ti.com/lit/ds/symlink/tps61165.pdf)

## 6. Commission the interfaces one at a time

| Feature | Functional check and expected electrical result |
| --- | --- |
| Ethernet, U20 and J11 | Check the 3.3 V rail at the W5500; bring its hardware reset high only after power and the clock settle. Connect a known-good link partner, check 10/100 link and exchange traffic. Typical full-link operating current is **about 132 mA on 3.3 V**, about **0.10 A added at SYS_5V** at 85% buck efficiency. |
| Isolated RS-485, U5/J3 and U14/J7 | Verify **3.15–3.45 V** at each module between pins 1 and 2. Each module draws **about 35 mA typical idle** and up to **120 mA operating** on 3.3 V per the part data sheet. Keep each isolated COM on its field side. Test each link with an isolated test peer, suitable end termination where needed and both directions of traffic before loading both ports simultaneously. Use an isolated or differential probe on the field side. |
| RS-232, U11/J6 | Verify 3.3 V supply, line idle and loopback with J6.1 TXD crossed to a peer RXD, and J6.2 RXD crossed to its TXD. J6.3 is logic GND. Expect about **0.3 mA typical on 3.3 V** with no RS-232 load. Record incremental steady current and check PIO framing under simultaneous UART and display activity. |
| Inputs, U18/J9 | Use a separate, current-limited 24 V field supply. Connect return to J9.1 and send +24 V through a switch to each input pin in turn. Expect **about 7 mA per closed contact at 24 V** from the field supply and an active-low logic input. Test open and closed states for each channel, then test both cabinet-range endpoints and configured NO/NC interpretation. |
| External relays, J8 | With power off, connect the keyed pin-for-pin link. J8.1 is GND and J8.2 is SYS_5V. The commands are nominal **0/3.3 V**, with coils off on reset. Check dry COM/NO/NC continuity one relay at a time without field loads, then all four. Expect around **80 mA per energized coil**, or **0.32 A on 5 V** for four. Measure warm pickup, hold voltage and the minimum SYS_5V when switching. |

[WIZnet W5500 operating current](https://docs.wiznet.io/Product/Chip/Ethernet/W5500/migration-from-w5200) · [YLPTEC TD301D485H data sheet](https://datasheet.lcsc.com/lcsc/2405211629_YLPTEC-TD301D485H_C2992421.pdf) · [TI TRS3232E data sheet](https://www.ti.com/lit/ds/symlink/trs3232e.pdf) · [Input and relay wiring](../industrial-hmi-rev-l/README.md#j9-switch-wiring)

Run all fitted functions together on cabinet and qualified USB power, then check cold start, warmed operation and loaded handoff. The 7-inch configuration budgets **1.23 A steady on SYS_5V**, or **1.55 A with four relays energized**, before upstream losses. Use **1.8 A steady on SYS_5V** as the design ceiling for this setup. Verify the cabinet supply, USB source and cable can support measured inrush and operating current. Record the worst SYS_5V and 3.3 V readings, temperature, resets, link errors and SD write errors with the cabinet at **20.4 V** and **27.6 V** and with the chosen USB source at its measured loaded voltage. [Power budget basis](../industrial-hmi-rev-m/README.md#7-inch-power-budget)
