#!/usr/bin/env python3
"""Verify the Rev P package and stored copper. Native EasyEDA checks are separate."""

import argparse
from collections import defaultdict
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
import json
from math import dist
from pathlib import Path
import re
import subprocess
import sys
from zipfile import ZipFile

from shapely.affinity import translate
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import nearest_points, unary_union

from copper_geometry import (Board, LAYERS, MIN_SHARED_EDGE, NEAR_GAP, changed_copper,
                             disc, from_record, mm_point, pad_drill, pieces, points, positive_overlap)

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parent
sys.path.insert(0, str(REPO / "industrial-hmi-rev-n" / "tools"))
from verify_rev_n import attrs, cents, components, refs, rows, U1_PAD_NETS, U1_PIN_NUMBERS

PREFIX = "Industrial-HMI-RevP"
HOLD = "DO-NOT-FABRICATE"
BUZZER = "Footprint_BUZZER-D12-P7.6-PTH.json"
EXTERNAL = {"LCD1", "CELL1"}
DNP = {"TP1", "TP2", "TP3", "TP4", "R4", "R38"}
LOCKED = "U1 U2 U5 U6 U8 U14 U21 U22 U23 J4 D4 D10 Q3".split()
PRICE_RATE = Decimal("92.67")
RULE = .125
BEFORE_CONTACTS = "5c50b9ed31a15b2b3ecd2a13da255f656f167cfe"
BEFORE_EDITOR = "3287d57908d69a05234727b70805f117002ee217"
BEFORE_J4 = "2cde613"
J4_REFERENCE = "Footprint_GCT-USB4105-GF-A-REV-P.json"
J4_TRIM = .051
J4_FACE = (1015.825, 816.0)
J4_PACKAGE = "GCT-USB4105-GF-A-REV-P"
D24_SHIFT = .120
J4_DATA_TRACKS = tuple(f"gge{i}" for i in range(4886, 4894))
EDITOR_PACKAGES = {"U6": "TI-RPJ0009A-REV-P", "U23": "TI-RSE0010A-REV-P", "D25": "TI-DRT0003A-REV-P"}
BUCK_LOADS = ("L4.2", "C94.1", "U6.3", "C15.1", "U2.15", "C34.1", "TP3.1")
REMOVED_FRAGMENTS = {
    "gge5700", "gge5725", "gge5753", "gge5776", "gge5777", "gge5778", "gge5779",
    "gge5808", "gge5833", "gge5849", "gge5925", "gge6096", "gge6167",
}
REINFORCEMENTS = (
    ("C17.1", "gge5387", "1", "gge962101"),
    ("C15.1", "gge4946", "1", "gge962102"),
    ("U2.62", "gge5705", "1", "gge962103"),
    ("X1.2", "gge5362", "1", "gge962104"),
    ("X1.4", "gge5363", "1", "gge962105"),
    *(("J4.SH2", "gge5667", layer, f"gge96210{index}")
      for index, layer in enumerate(LAYERS, 6)),
)
ROUTES = (
    ("R76.2 → mux ground", "GND", ("R76.2", "U22.3")),
    ("U6.4 → input capacitor ground", "GND", ("U6.4", "C93.2", "J1.2")),
    ("U6.5/U6.6 → input capacitor and mux", "SYS_5V", ("U6.5", "U6.6", "C93.1", "U22.1")),
    ("U21.24 → USB input and local bypass", "USB_VBUS", ("U21.24", "C87.1", "Q3.1")),
    ("U21.18 → VBUS sense resistor", "USB_RAW_SENSE", ("U21.18", "R73.2")),
    ("U21.23 → 2.7 V bypass", "USB_REG27", ("U21.23", "C89.1")),
    ("R72.1 → Q3 gate", "USB_FET_GATE", ("R72.1", "Q3.4", "R71.2")),
    ("R78.1 → mux PR1 divider", "CAB_PRI", ("R78.1", "R77.2", "U22.6")),
    ("R83.1 → shared 3.3 V rail", "3V3", ("R83.1", "U23.10", "U6.3")),
)


def cad_name(kind):
    return f"{kind}_{PREFIX}-{HOLD}.json"


def tagged_file(name):
    return subprocess.check_output(
        ["git", "show", f"refs/tags/rev-n:industrial-hmi-rev-n/{name}"], cwd=REPO
    )


def rev_n_sources():
    archive = tagged_file("Industrial-HMI-RevN-FOOTPRINTS-DO-NOT-FABRICATE.zip")
    with ZipFile(BytesIO(archive)) as zipped:
        pcb, schematic = (json.loads(zipped.read(next(n for n in zipped.namelist()
                                                    if n.startswith(f"{kind}_"))))
                          for kind in ("PCB", "Schematic"))
    frozen = json.loads(tagged_file("PCB_Industrial-HMI-RevN-DO-NOT-FABRICATE.json"))
    return frozen, pcb, schematic


def indexed_csv(path, ref_column, count_column):
    indexed = {}
    for row in rows(path):
        designators = refs(row[ref_column])
        if designators == ["TOTAL"]:
            continue
        assert len(designators) == int(row[count_column]), row
        for ref in designators:
            assert ref not in indexed, ref
            indexed[ref] = row
    return indexed


def pad_fields(body):
    return {f[8]: f for s in body if (f := s.split("~"))[0] == "PAD"}


def load_prior_pcb(revision):
    path = (HERE / cad_name("PCB")).relative_to(REPO)
    return json.loads(subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=REPO))


def footprint_drawing_rows():
    rpj = {}
    for pin in range(1, 7):
        side = 1 if pin <= 3 else -1
        width = 1.0 if pin in (4, 6) else .65
        x = side * (.45 if width == 1 else .625)
        y = {1: .25, 2: -.25, 3: -.75, 4: -.75, 5: -.25, 6: .25}[pin]
        rpj[str(pin)] = (x, y, width, .20)
    for pin in (7, 8, 9):
        rpj[str(pin)] = ((pin - 8) * .5, .925, .25, .55)

    rse = {}
    for pin in (1, 2, 3, 4, 6, 7, 8, 9):
        x = .675 if pin < 5 else -.675
        y = {1: .75, 2: .25, 3: -.25, 4: -.75, 6: -.75, 7: -.25, 8: .25, 9: .75}[pin]
        rse[str(pin)] = (x, y, .55, .20 if pin in (2, 3, 7, 8) else .25)
    rse.update({"5": (0, -.9, .30, .60), "10": (0, .9, .30, .60)})
    drt = {"1": (-.575, -.35, .45, .30), "2": (-.575, .35, .45, .30), "3": (.575, 0, .45, .30)}
    return {
        "U6": ("TI TPS62902 Rev A, p.45, RPJ0009A Example Board Layout", rpj),
        "U23": ("TI TS3USB221A Rev C, RSE0010A Example Board Layout, drawing 4220307/A", rse),
        "D25": ("TI MPDS340 p.1 and linked Ultra Librarian DRT0003A Top copper CAD", drt),
    }


def j4_drill_counts(doc):
    records = [row.split("~") for shape in doc["shape"] for row in shape.split("#@$")]
    plated = [f for f in records if f[0] == "PAD" and f[6] == "11" and f[15] == "Y"]
    slots = sum(bool(f[14]) for f in plated)
    holes = sum(f[0] == "HOLE" for f in records)
    vias = sum(f[0] == "VIA" for f in records)
    return slots, len(plated) - slots, holes, vias


def j4_usb_lengths(pcb):
    tracks = {f[5]: f for s in pcb["shape"] if (f := s.split("~"))[0] == "TRACK"}

    def centreline(net, *ids):
        routes = [tracks["gge" + str(ident)] for ident in ids]
        assert all(route[3] == net for route in routes)
        return sum(LineString(points(route[4])).length for route in routes)

    plus_a = centreline("USB_DP_CONN", 4887, 4888)
    minus_b = centreline("USB_DM_CONN", 4889, 4893)
    return (
        (plus_a, minus_b - centreline("USB_DM_CONN", 4889) + centreline("USB_DM_CONN", 4891, 4890)),
        (plus_a + centreline("USB_DP_CONN", 4886), minus_b),
        (centreline("USB_DP", 4519, 4520, 4521, 4522, 4523),
         centreline("USB_DM", 4532, 4533, 4534, 4535, 4536, 4537)),
    )


def verify_j4_routes(pcb, previous, board, drills):
    assert not board.shorts() and not board.opens()
    assert j4_drill_counts(pcb) == (4, 56, 9, 664)
    baseline = Board(pieces(previous, components(previous, False)))
    paths = (
        ("USB_VBUS", "J4.A4", "J4.B4", "C87.1", "D24.1", "Q3.1"),
        ("USB_CC1", "J4.A5", "U21.1", "U21.2"),
        ("USB_CC2", "J4.B5", "U21.4", "U21.5"),
        ("USB_DP_CONN", "J4.A6", "J4.B6", "D25.1", "U23.8"),
        ("USB_DM_CONN", "J4.A7", "J4.B7", "D25.2", "U23.7"),
        ("GND", "J4.SH1", "J4.SH2", "J4.SH3", "J4.SH4", "C87.2", "D24.2"),
    )
    assert all(board.connected(net, *refs) for net, *refs in paths)
    print("  USB paths, both U21 dead-battery pins and all shell ground paths are connected.")
    print("  Live drill source: 4 plated slots, 56 round plated pads, 9 NPTH and 664 vias.")
    print("  Native drill export pending.")
    changes = list(changed_copper(board, baseline))
    clearance = [(gap, p.layer, p.name, q.name, p, q)
                 for p in changes for gap, q in board.clearances(p, .50)]
    gap, layer, first, second, p, q = min(clearance, key=lambda hit: hit[:4])
    assert gap >= RULE, [(g, l, a, b) for g, l, a, b, _, _ in clearance if g < RULE]
    a, b = nearest_points(p.geometry, q.geometry)
    print(f"  J4/D24 changes, minimum copper {gap:.6f} mm on layer {layer}: "
          f"{first} ({a.x:.3f}, {a.y:.3f}) ↔ {second} ({b.x:.3f}, {b.y:.3f}).")
    old_regions = {(p.oid, p.layer) for p in baseline.pieces if p.kind == "SOLIDREGION"}
    changed_regions = sorted((p.oid, p.layer) for p in changes
                             if p.kind == "SOLIDREGION" and (p.oid, p.layer) in old_regions)
    print("  Existing fixed regions locally cleared: "
          + ", ".join(f"{oid} (layer {layer})" for oid, layer in changed_regions) + ".")

    for title, labels, layers, rule in (
        ("NPTH-to-copper", ("locator 1", "locator 2"), LAYERS, .20),
        ("Plated slot-to-foreign copper, outer", ("SH1", "SH2", "SH3", "SH4"), ("1", "2"), .28),
        ("Plated slot-to-foreign copper, inner", ("SH1", "SH2", "SH3", "SH4"), ("21", "22"), .30),
    ):
        nearby = []
        for name in labels:
            drill = drills[name]
            for layer in layers:
                for i in board.query(layer, drill, 1):
                    piece = board.pieces[i]
                    if name.startswith("locator") or piece.net != "GND":
                        nearby.append((drill.distance(piece.geometry), name, layer, piece.name))
        gap, hole, layer, piece = min(nearby)
        assert gap >= rule, (title, gap, hole, layer, piece)
        print(f"  {title} minimum {gap:.6f} mm, {hole} ↔ {piece} on layer {layer}.")

    changed_ids = {(p.oid, p.layer) for p in changes}
    for shape in pcb["shape"]:
        for record in shape.split("#@$"):
            fields = record.split("~")
            if fields[0] == "VIA":
                via_drill = disc(mm_point(*fields[1:3]), float(fields[5]) * .508)
                for name, opening in drills.items():
                    assert via_drill.distance(opening) >= .20, (name, fields[6])
            elif fields[0] == "PAD" and fields[6] == "11" and fields[15] == "Y" and not fields[14]:
                opening = pad_drill(fields)
                for layer in LAYERS:
                    limit = .30 if layer in {"21", "22"} else .28
                    for index in board.query(layer, opening, limit):
                        p = board.pieces[index]
                        if p.net != fields[7] and (p.oid, layer) in changed_ids:
                            assert opening.distance(p.geometry) >= limit, (fields[12], p.name, layer)
            elif fields[0] == "HOLE":
                opening = disc(mm_point(*fields[1:3]), float(fields[3]) * .254)
                for layer in LAYERS:
                    for index in board.query(layer, opening, .20):
                        p = board.pieces[index]
                        if (p.oid, layer) in changed_ids:
                            assert opening.distance(p.geometry) >= .20, (fields[4], p.name, layer)
    print("  Changed copper clears existing round drills. J4 slots and locators clear via drill edges by ≥0.20 mm.")

    tracks = {f[5]: f for s in pcb["shape"] if (f := s.split("~"))[0] == "TRACK"}
    for oid in ("gge4899", "gge4902", "gge4901"):
        assert float(tracks[oid][1]) * .254 >= .47999
    by_name = {(p.layer, p.name): p for p in board.pieces}
    reference = unary_union([p.geometry for p in board.pieces if p.layer == "21" and p.net == "GND"])
    # The two existing D− transitions necessarily have antipads in Inner1.
    transitions = {f[6]: mm_point(*f[1:3]) for s in pcb["shape"]
                   if (f := s.split("~"))[0] == "VIA" and f[4] == "USB_DM_CONN"}
    previous_data_vias = {f[6] for s in previous["shape"] if (f := s.split("~"))[0] == "VIA"
                          and f[4] == "USB_DM_CONN"}
    assert set(transitions) == previous_data_vias == {"gge5593", "gge5594"}
    transition_areas = unary_union([disc(center, .80) for center in transitions.values()])
    for oid in J4_DATA_TRACKS:
        route = tracks[oid]
        centreline = LineString(points(route[4]))
        ground = reference if route[3] == "USB_DP_CONN" else reference.union(transition_areas)
        assert centreline.difference(ground).length < .0001, oid
    for pin, via in (("J4.SH1", "gge5664"), ("J4.SH2", "gge5667")):
        shell, stitch = (by_name["21", key] for key in (pin, via))
        assert positive_overlap(shell.geometry, stitch.geometry)
        assert any(p.kind == "TRACK" and p.layer == "21" and p.net == "GND"
                   and positive_overlap(p.geometry, stitch.geometry) for p in changes)
    print("  Data tracks have Inner1 GND below the routes outside the two existing D− via antipads.")
    print("  Inner1 stitches verified at gge5664 and gge5667. VBUS trunk is 0.48 mm.")


def verify_d24(pcb, baseline, board, j4_copper, j4_body):
    current_parts = components(pcb, False)
    prior_parts = components(baseline, False)
    assert current_parts["C87"][1:] == prior_parts["C87"][1:]
    _, old_head, old_body = prior_parts["D24"]
    _, head, body = current_parts["D24"]
    old_x, old_y = mm_point(*old_head[1:3])
    x, y = mm_point(*head[1:3])
    assert abs(x - old_x - D24_SHIFT) < .00001 and abs(y - old_y) < .00001
    assert head[4:] == old_head[4:], "D24 orientation/instance changed"
    print(f"  D24 centre ({old_x:.3f}, {old_y:.3f}) → ({x:.3f}, {y:.3f}) mm. "
          f"Shift {x - old_x:.3f} mm inward, original orientation.")
    pads = {(p.layer, p.name): p for p in board.pieces}
    for pin, earlier in pad_fields(old_body).items():
        old_pad = next(from_record("~".join(earlier)))
        new_pad = pads["1", f"D24.{pin}"]
        assert old_pad.net == new_pad.net
        assert new_pad.geometry.equals_exact(translate(old_pad.geometry, xoff=D24_SHIFT), .00001)
    nearby = sorted((pads["1", "D24.2"].geometry.distance(geometry), pin)
                    for pin, geometry in j4_copper.items())
    closest = nearby[0][0]
    names = [pin for gap, pin in nearby if abs(gap - closest) < .00001]
    assert closest >= .15 and set(names) == {"A1", "B12", "A4", "B9", "B8"}
    print(f"  Nearest J4 SMT lands to D24.2 are {closest:.6f} mm away: "
          "A1/B12 GND (same net), A4/B9 USB_VBUS and B8 unconnected (separate copper).")
    vbus_j4 = unary_union([j4_copper["A4"], j4_copper["B4"]])
    vbus_gap = pads["1", "D24.1"].geometry.distance(vbus_j4)
    assert vbus_gap <= 3.0
    print(f"  D24.1 edge to nearest J4 VBUS land edge: {vbus_gap:.3f} mm.")
    housing, = (Polygon(points(f[4])) for record in j4_body
                if (f := record.split("~"))[0] == "TRACK" and f[2] == "12")
    # Littelfuse SMF datasheet p.5 maximum body width/depth, in installed orientation.
    diode_body = box(x - 1.00, y - 1.55, x + 1.00, y + 1.55)
    body_gap = diode_body.distance(housing)
    assert body_gap >= .40
    print(f"  Nominal J4 housing to maximum D24 body envelope: {body_gap:.3f} mm, plan view.")

    tracks = {f[5]: f for r in pcb["shape"] if (f := r.split("~"))[0] == "TRACK"}
    old_tracks = {f[5]: f for r in baseline["shape"] if (f := r.split("~"))[0] == "TRACK"}
    for pin, oid in (("1", "gge4900"), ("2", "gge4996")):
        track, old_track = tracks[oid], old_tracks[oid]
        length, old_length = (LineString(points(t[4])).length for t in (track, old_track))
        width, old_width = (float(t[1]) * .254 for t in (track, old_track))
        assert length <= old_length and width >= old_width
        copper = pads["1", oid]
        land = pads["1", f"D24.{pin}"]
        assert land.net == copper.net
        assert positive_overlap(land.geometry, copper.geometry)
        print(f"  D24.{pin} {land.net} Top link: {old_length:.3f} → {length:.3f} mm long, "
              f"{old_width:.3f} → {width:.3f} mm wide, positive pad overlap.")
    gnd_top = pads["1", "gge5646"]
    gnd_inner = pads["21", "gge5646"]
    assert positive_overlap(gnd_top.geometry, pads["1", "gge4996"].geometry)
    vbus_top = pads["1", "gge4900"]
    assert any(p.kind == "VIA" and p.net == vbus_top.net and positive_overlap(p.geometry, vbus_top.geometry)
               for i in board.query("1", vbus_top.geometry) for p in [board.pieces[i]])
    ties = [p for i in board.query("21", gnd_inner.geometry) for p in [board.pieces[i]]
            if p.kind == "TRACK" and p.net == "GND" and positive_overlap(p.geometry, gnd_inner.geometry)]
    for tie in ties:
        length = LineString(points(tracks[tie.oid][4])).length
        width = float(tracks[tie.oid][1]) * .254
        if length <= 1.50 and width >= .59999:
            assert any(p.kind == "SOLIDREGION" and p.net == "GND" and positive_overlap(p.geometry, tie.geometry)
                       for i in board.query("21", tie.geometry) for p in [board.pieces[i]])
            print(f"  D24 return via gge5646 to Inner1 GND: {length:.3f} mm × {width:.3f} mm, "
                  "positive overlap at the via and plane.")
            break
    else:
        raise AssertionError("D24 local Inner1 GND return is missing")


def verify_j4_footprint(pcb, footprints, board, schematic):
    baseline = load_prior_pcb(BEFORE_J4)
    _, current_head, current_body = footprints["J4"]
    _, old_head, old_body = components(baseline, False)["J4"]
    assert current_head[1:3] == old_head[1:3]
    current = pad_fields(current_body)
    old_pads = pad_fields(old_body)
    library = json.loads((HERE / J4_REFERENCE).read_bytes())
    proposed = pad_fields(library["shape"])
    pcb_holes = [f for s in current_body if (f := s.split("~"))[0] == "HOLE"]
    library_holes = [f for s in library["shape"] if (f := s.split("~"))[0] == "HOLE"]
    assert current_head[8] == library["head"]["uuid"] == components(schematic, True)["J4"][1][7]
    assert all(not f[7] for f in proposed.values())
    assert current.keys() == proposed.keys() == old_pads.keys()
    assert {k: f[7] for k, f in current.items()} == {k: f[7] for k, f in old_pads.items()}
    origin = mm_point(library["head"]["x"], library["head"]["y"])

    # B3 sheet 1, recommended land-pattern view. Axial dimensions start at
    # the mating face. The SMT front edge shares the rear-slot axial datum.
    contact_rows = (
        ("A1/B12", -3.20, .60, "GND"), ("A4/B9", -2.40, .60, "USB_VBUS"),
        ("B8", -1.75, .30, ""), ("A5", -1.25, .30, "USB_CC1"),
        ("B7", -.75, .30, "USB_DM_CONN"), ("A6", -.25, .30, "USB_DP_CONN"),
        ("A7", .25, .30, "USB_DM_CONN"), ("B6", .75, .30, "USB_DP_CONN"),
        ("A8", 1.25, .30, ""), ("B5", 1.75, .30, "USB_CC2"),
        ("B4/A9", 2.40, .60, "USB_VBUS"), ("B1/A12", 3.20, .60, "GND"),
    )

    def relative(f, datum=J4_FACE):
        return tuple(v - o for v, o in zip(mm_point(*f), datum, strict=True))

    def to_pcb(geometry):
        return translate(geometry, xoff=J4_FACE[0] - origin[0], yoff=J4_FACE[1] - origin[1])

    def equal(actual, target):
        assert all(abs(a - b) < .00001 for a, b in zip(actual, target, strict=True)), (actual, target)

    print("\nJ4 — GCT USB4105 B3 sheet 1, Recommended PCB Layout and pin/signal table.")
    print("Values are measured on the live PCB relative to the mating face and centreline.")
    print("| SMT land | Drawing x / y / axial length / width (mm) | PCB (mm) | Live net | Result |")
    print("| --- | --- | --- | --- | --- |")
    copper = {}
    for aliases, y, width, net in contact_rows:
        values = (6.78 + 1.15 / 2, y, 1.15, width)
        trim = J4_TRIM if aliases in {"A1/B12", "B1/A12"} else 0.0
        expected_land = (values[0] + trim / 2, y, 1.15 - trim, width)
        for pin in aliases.split("/"):
            f = current[pin]
            actual = (*relative(f[2:4]), *mm_point(*f[4:6]))
            equal(actual, expected_land)
            assert actual[2] >= 1.05
            assert f[1] == "RECT" and f[6] == "1" and float(f[9]) == 0
            assert f[7] == net
            assert current[pin][2:8] == current[aliases.split("/")[0]][2:8]
            copper[pin] = next(from_record("~".join(f))).geometry
            equal(copper[pin].bounds, (J4_FACE[0] + values[0] - 1.15 / 2 + trim,
                                       J4_FACE[1] + y - width / 2,
                                       J4_FACE[0] + values[0] + 1.15 / 2,
                                       J4_FACE[1] + y + width / 2))
            library_pad = next(from_record("~".join(proposed[pin]))).geometry
            assert copper[pin].equals_exact(to_pcb(library_pad), .00001), pin
        expected = " / ".join(f"{v:.3f}" for v in values)
        measured = " / ".join(f"{v:.3f}" for v in actual)
        result = f"APPROVED DEVIATION: {trim:.3f} mm removed at insertion end" if trim else "PASS"
        print(f"| {aliases} | {expected} | {measured} | {net or 'SBU unconnected'} | {result} |")
    assert len({g.bounds for g in copper.values()}) == 12 and len(copper) == 16

    print("| Drill | Drawing x / y (mm) | PCB x / y (mm) | Drawing / PCB drill and copper (mm) | Result |")
    print("| --- | --- | --- | --- | --- |")
    drills = {}
    for pin, x, y, length in (("SH1", 6.78, -4.32, 1.70), ("SH2", 6.78, 4.32, 1.70),
                              ("SH3", 2.60, -4.32, 1.40), ("SH4", 2.60, 4.32, 1.40)):
        f = current[pin]
        assert f[1] == "OVAL" and f[6] == "11" and f[15] == "Y"
        assert current[pin][7] == "GND"
        measured = relative(f[2:4])
        equal(measured, (x, y))
        outer_w, outer_h = mm_point(*f[4:6])
        annuli = list(from_record("~".join(f)))
        assert {p.layer for p in annuli} == set(LAYERS) and all(p.plated for p in annuli)
        drills[pin] = pad_drill(f)
        bounds = drills[pin].bounds
        equal((bounds[2] - bounds[0], bounds[3] - bounds[1]), (length, .60))
        equal((float(f[13]) * .254, outer_w, outer_h), (length, length + .40, 1.00))
        library_pad = next(from_record("~".join(proposed[pin]))).geometry
        equal(annuli[0].geometry.bounds, to_pcb(library_pad).bounds)
        assert annuli[0].geometry.symmetric_difference(to_pcb(library_pad)).area < .00001
        equal(drills[pin].bounds, to_pcb(pad_drill(proposed[pin])).bounds)
        outer = annuli[0].geometry.bounds
        equal((outer[2] - outer[0], outer[3] - outer[1]), (outer_w, outer_h))
        pad_x, pad_y = mm_point(*f[2:4])
        equal(((bounds[2] + bounds[0]) / 2, (bounds[3] + bounds[1]) / 2), (pad_x, pad_y))
        equal(((outer[2] + outer[0]) / 2, (outer[3] + outer[1]) / 2), (pad_x, pad_y))
        print(f"| {pin} | {x:.2f} / {y:+.2f} | {measured[0]:.2f} / {measured[1]:+.2f} | "
              f"{length:.2f} × 0.60 slot, x axis, plated, {outer_w:.2f} × {outer_h:.2f} copper all four layers | PASS |")
    assert len(pcb_holes) == len(library_holes) == 2
    location = [relative(f[1:3]) for f in pcb_holes]
    equal((dist(*location),), (5.78,))
    for index, (f, y, (x_measured, y_measured)) in enumerate(zip(pcb_holes, (-2.89, 2.89), location, strict=True), 1):
        equal((x_measured, y_measured, float(f[3]) * .254), (6.28, y, .65))
        name = f"locator {index}"
        drills[name] = disc(mm_point(*f[1:3]), float(f[3]) * .254)
        lib_hole = library_holes[index - 1]
        equal((x_measured, y_measured, float(f[3]) * .254),
              (*relative(lib_hole[1:3], origin), float(lib_hole[3]) * .254))
        print(f"| {name} | 6.28 / {y:+.2f} | {x_measured:.2f} / {y_measured:+.2f} | Ø0.65 NPTH, 5.78 spacing | PASS |")

    # The live document-layer body outline provides the current mating-face x.
    body, = (points(f[4]) for s in current_body if (f := s.split("~"))[0] == "TRACK" and f[2] == "12")
    origin_x, origin_y = min(x for x, _ in body), mm_point(*current_head[1:3])[1]
    outline, = (points(f[4]) for s in pcb["shape"] if (f := s.split("~"))[0] == "TRACK" and f[2] == "10")
    edge = min(x for x, _ in outline)
    print(f"  Mating face from live footprint outline x={origin_x:.3f} mm, board edge x={edge:.3f} mm, "
          f"centreline y={origin_y:.3f} mm. Keeping the face gives {edge - origin_x:.3f} mm overhang.")
    print(f"  Live untrimmed SMT row x={mm_point(*current['A4'][2:4])[0]:.3f} mm.")

    print("  Approved trim clearance, locator drill to the two trimmed PCB GND lands:")
    for index, pin in enumerate(("A1/B12", "B1/A12"), 1):
        centre = Point(mm_point(*pcb_holes[index - 1][1:3]))
        gap = centre.distance(copper[pin.split("/")[0]]) - .325
        assert gap >= .225
        print(f"    PASS L1: locator {index} ↔ J4.{pin}, {gap:.6f} mm vs 0.225 mm.")
    equal((origin_x, origin_y), J4_FACE)
    assert j4_drill_counts(library) == (4, 0, 2, 0)
    verify_j4_routes(pcb, baseline, board, drills)
    verify_d24(pcb, baseline, board, copper, current_body)
    before, after = j4_usb_lengths(baseline), j4_usb_lengths(pcb)

    def lengths(pair):
        return f"{pair[0]:.3f} / {pair[1]:.3f} / {abs(pair[0] - pair[1]):.3f}"

    print("  USB trace centreline lengths in mm (planar copper only, excludes via barrels and pad traversal).")
    print("  | Segment | Before D+ / D− / skew | Live D+ / D− / skew |")
    print("  | --- | --- | --- |")
    for title, previous, live in zip(("J4 A contacts → U23", "J4 B contacts → U23", "R17/R18 → U2"),
                                     before, after, strict=True):
        print(f"  | {title} | {lengths(previous)} | {lengths(live)} |")
    assert all(abs(dp - dm) <= 5 for dp, dm in after[:2])
    print("  Both orientations meet the 5 mm Full Speed skew rule.")


def verify_editor_footprints(pcb, schematic, board):
    footprints = components(pcb, False)
    symbols = components(schematic, True)
    live = {(p.layer, p.name): p for p in board.pieces}

    def fmt(values):
        return " / ".join(f"{v:.3f}" for v in values)

    for ref, (source, dimensions) in footprint_drawing_rows().items():
        _, h, body = footprints[ref]
        package = EDITOR_PACKAGES[ref]
        lib = json.loads((HERE / f"Footprint_{package}.json").read_bytes())
        lib_origin = mm_point(lib["head"]["x"], lib["head"]["y"])
        assert lib["head"]["uuid"] == h[8] == symbols[ref][1][7] and attrs(h)["package"] == package
        origin_x, origin_y = mm_point(*h[1:3])
        pads, library_pads = pad_fields(body), pad_fields(lib["shape"])
        assert pads.keys() == library_pads.keys() == dimensions.keys()
        print(f"\n{ref} — {source}. Values in mm, Top view relative to package origin.")
        print("| Pad | Drawing x / y / width / height | PCB x / y / width / height | Drill | Result |")
        print("| --- | --- | --- | --- | --- |")
        for pin, target in sorted(dimensions.items(), key=lambda a: int(a[0])):
            f, lib_pad = pads[pin], library_pads[pin]
            x, y = mm_point(*f[2:4])
            measured = (x - origin_x, y - origin_y, *mm_point(*f[4:6]))
            lx, ly = mm_point(*lib_pad[2:4])
            in_library = (lx - lib_origin[0], ly - lib_origin[1], *mm_point(*lib_pad[4:6]))
            match = all(abs(a - b) < .00001 for a, b in zip(measured, target, strict=True))
            print(f"| {pin} | {fmt(target)} | {fmt(measured)} | SMT | {'PASS' if match else 'FAIL'} |")
            assert match and f[6] == "1" and float(f[9]) == 0
            assert all(abs(a - b) < .00001 for a, b in zip(in_library, target, strict=True))
            assert not lib_pad[7]
            if ref == "U23":
                assert f[1] == "POLYGON" and len(f[10].split()) > 16
            if f[7]:
                pad = live["1", f"{ref}.{pin}"]
                assert any(q.net == pad.net and q.kind != "PAD" and positive_overlap(q.geometry, pad.geometry)
                           for idx in board.query("1", pad.geometry) for q in [board.pieces[idx]]), pad.name

    verify_j4_footprint(pcb, footprints, board, schematic)
    usb = (("USB_CC1", "J4.A5", "U21.1", "U21.2"), ("USB_CC2", "J4.B5", "U21.4", "U21.5"),
           ("USB_VBUS", "J4.A4", "J4.B4", "D24.1", "C87.1", "Q3.1"), ("USB_DP_CONN", "J4.A6", "D25.1", "U23.8"),
           ("USB_DM_CONN", "J4.A7", "D25.2", "U23.7"))
    assert all(board.connected(net, *pins) for net, *pins in usb)
    silk = [v for s in pcb["shape"] if s.startswith("TEXT~") for v in [s.split("~")]]
    assert any(v[10] == "Rev P DRAFT" and v[7] == "3" and v[11].startswith("M ") for v in silk)
    assert all(v[7] == "12" for v in silk if v[10] == "DO NOT FABRICATE")
    assert any(v[10] == "DO NOT FABRICATE" for v in silk)


def verify_sources(schematic, pcb, old_schematic, base_parts, bom):
    symbols, footprints = components(schematic, True), components(pcb, False)
    assert len(footprints) == 212 and set(bom) - EXTERNAL == symbols.keys() == footprints.keys()
    assert {ref for ref, row in bom.items() if row["Population"] == "DNP"} == DNP
    assert not EXTERNAL & set(footprints)
    for ref in symbols:
        symbol, footprint = attrs(symbols[ref][1]), attrs(footprints[ref][1])
        for key, col in (("package", "Footprint"), ("BOM_Manufacturer Part", "Manufacturer part number"),
                         ("BOM_Supplier Part", "LCSC part")):
            if ref not in DNP or key == "package":
                assert symbol.get(key, "") == footprint.get(key, "") == bom[ref][col], (ref, key)
        if ref == "J4":
            assert footprint["package"] == J4_PACKAGE
            assert footprints[ref][1][:3] == base_parts[ref][1][:3]
        elif ref == "D24":
            # The J4 installation audit checks the allowed D24 translation.
            assert footprints[ref][1][4:] == base_parts[ref][1][4:]
            assert footprint["package"] == attrs(base_parts[ref][1])["package"]
        elif ref in EDITOR_PACKAGES and footprint["package"] == EDITOR_PACKAGES[ref]:
            before_pads = pad_fields(base_parts[ref][2])
            after_pads = pad_fields(footprints[ref][2])
            assert {pin: (f[6], f[7], f[12]) for pin, f in before_pads.items()} == {
                pin: (f[6], f[7], f[12]) for pin, f in after_pads.items()
            }, ref
            assert footprints[ref][1][4:8] == base_parts[ref][1][4:8]
            assert footprints[ref][1][9:] == base_parts[ref][1][9:]
            x, y = mm_point(*footprints[ref][1][1:3])
            bx, by = mm_point(*base_parts[ref][1][1:3])
            assert abs(x - bx) < .00001 and abs(y - by - (.25 if ref == "U6" else 0)) < .00001
        else:
            assert footprints[ref][2] == base_parts[ref][2], (ref, "placement or native footprint changed")
            assert footprints[ref][1][:3] == base_parts[ref][1][:3]
            assert footprints[ref][1][4:] == base_parts[ref][1][4:]
    old_symbols = components(old_schematic, True)
    for ref in LOCKED:
        pin = attrs(old_symbols[ref][1])
        assert pin["BOM_Manufacturer Part"] == bom[ref]["Manufacturer part number"], ref
    assert all(before == after or (before.startswith("T~L~") and "Rev P" in after)
               for before, after in zip(old_schematic["shape"], schematic["shape"], strict=True)
               if not before.startswith("LIB~"))
    for ref, (_, _, body) in old_symbols.items():
        assert symbols[ref][2] == body
    for filename, doc in ((cad_name("PCB"), pcb), (cad_name("Schematic"), schematic)):
        assert doc["head"]["c_para"]["Title"].startswith("DO NOT FABRICATE")
        assert "Rev P" in doc["head"]["c_para"]["Title"], filename
    assert bom["R68"]["Manufacturer part number"] == "0603WAF9102T5E"
    assert bom["R68"]["Description"] == "91 kΩ"
    assert bom["Q3"]["Manufacturer part number"] == "STL6P3LLH6"
    for ref, package in {"C37": "C0402", "R30": "R0402", "R62": "0402"}.items():
        assert bom[ref]["Footprint"] == package
    buzzer = json.loads((HERE / BUZZER).read_bytes())
    pad_shape = [r.split("~") for r in footprints["BZ1"][2] if r.startswith("PAD~")]
    pads = {r[8]: r for r in pad_shape}
    assert buzzer["head"]["uuid"] == symbols["BZ1"][1][7] == footprints["BZ1"][1][8]
    assert [(p[1], p[7]) for p in pads.values()] == [("RECT", "SYS_5V"), ("ELLIPSE", "BUZZ_LOW")]
    assert all(p[6] == "11" and p[15] == "Y" and cents(Decimal(p[9]) * Decimal(".508")) == 1
               for p in pads.values())
    pitch = dist([float(x) for x in pads["1"][2:4]], [float(x) for x in pads["2"][2:4]]) * .254
    assert abs(pitch - 7.6) < .0001
    numbers = {}
    for line in symbols["U1"][2]:
        if line.startswith("P~"):
            fields = line.split("^^")
            numbers[fields[3].split("~")[4]] = fields[0].split("~")[3]
    assert numbers == U1_PIN_NUMBERS
    print("212 schematic / PCB / BOM designators agree. TP1–TP4 and optional R4/R38 DNP. LCD1 and CELL1 external.")
    print("Zero schematic-to-PCB footprint mismatches. Locked parts, R68 91 kΩ and BZ1 7.60 mm / 1.00 mm PTH checked.")

    with ZipFile(HERE / f"{PREFIX}-EasyEDA-{HOLD}.zip") as zipped:
        names = {cad_name("PCB"), cad_name("Schematic"), BUZZER, J4_REFERENCE}
        names.update(f"Footprint_{attrs(symbols[ref][1])['package']}.json" for ref in EDITOR_PACKAGES
                     if attrs(symbols[ref][1])["package"] == EDITOR_PACKAGES[ref])
        assert zipped.testzip() is None and set(zipped.namelist()) == names
        assert all(zipped.read(name) == (HERE / name).read_bytes() for name in names)
    assert len(list(HERE.glob("*.zip"))) == len(list(HERE.glob("PCB_*.json"))) == len(list(HERE.glob("Schematic_*.json"))) == 1
    print("One live schematic, one live PCB and one ZIP containing the byte-identical sources and local footprint libraries.")
    return footprints


def verify_pricing(bom):
    cost_path = HERE / f"{PREFIX}-BOM-Cost-INR.csv"
    priced = indexed_csv(cost_path, "References", "Quantity per board")
    assert priced.keys() == bom.keys() - DNP
    total = Decimal(0)
    for row in rows(cost_path)[:-1]:
        designators = refs(row["References"])
        for ref in designators:
            assert row["Manufacturer part number"] == bom[ref]["Manufacturer part number"]
            assert row["LCSC part"] == bom[ref]["LCSC part"]
            assert bom[ref]["Footprint"] in row["Footprint"].split(" / ")
        factor = PRICE_RATE if row["Applied currency"] == "USD" else 1
        assert row["Applied currency"] in {"USD", "INR"}
        price = Decimal(row["Applied unit"]) * factor
        assert row["Price source"] and row["Checked IST"] and row["Applied tier"]
        assert cents(price) == Decimal(row["Unit INR"])
        extended = cents(price) * len(designators)
        assert extended == Decimal(row["Extended INR"])
        if designators != ["LCD1"]:
            total += extended
    tail = rows(cost_path)[-1]
    assert tail["References"] == "TOTAL" and Decimal(tail["Extended INR"]) == total
    assert int(tail["Quantity per board"]) == len(priced) - 1
    print(f"{len(priced)} fitted refs priced exactly once, including the external LCD. Board + cell INR {total:.2f}.")

    purchase = rows(HERE / "PURCHASE-LIST.csv")
    covered, mpns = set(), set()
    subtotal, observed = defaultdict(Decimal), {}
    no_display = Decimal(0)
    supplier = None
    for row in purchase[:-1]:
        name = row["Supplier"]
        assert name not in observed and (supplier is None or supplier == name), row
        assert row["Checked IST"] and row["Source URL"]
        if row["Row type"] == "Supplier subtotal":
            assert Decimal(row["Line INR"]) == subtotal[name] and row["Notes"]
            observed[name] = subtotal[name]
            supplier = None
            continue
        assert row["Row type"] == "Part" and row["Supplier code"]
        supplier = name
        designators, mpn = refs(row["References"]), row["Manufacturer part number"]
        assert mpn not in mpns and covered.isdisjoint(designators)
        covered.update(designators)
        mpns.add(mpn)
        for ref in designators:
            assert mpn == ("2354" if ref == "LCD1" else priced[ref]["Manufacturer part number"])
        if "Q3" in designators:
            assert name == "DigiKey India" and row["Supplier code"] == "497-15315-1-ND"
        count, quantity, spares, stock, moq, multiple = (int(row[k]) for k in (
            "Three boards", "Order quantity", "Minimum spares", "Stock shown", "MOQ", "Order multiple"))
        assert int(row["Per board"]) == len(designators) and count == 3 * len(designators)
        assert stock >= quantity >= max(moq, count + spares) and quantity % multiple == 0
        assert spares >= (count + 9) // 10
        factor = PRICE_RATE if row["Currency"] == "USD" else 1
        assert row["Currency"] in {"USD", "INR"}
        unit = Decimal(row["Quoted unit"]) * factor
        if unit < 1 and all(re.fullmatch(r"(?:R|C|FB|L)\d+", ref) for ref in designators):
            assert quantity >= count + 2
        extended = cents(unit * quantity)
        assert cents(row["Unit INR"]) == cents(unit) and Decimal(row["Line INR"]) == extended
        subtotal[name] += extended
        if designators != ["LCD1"]:
            no_display += extended
    assert covered == priced.keys() and supplier is None
    assert purchase[-1]["Row type"] == "Overall subtotal"
    grand = sum(observed.values())
    assert Decimal(purchase[-1]["Line INR"]) == grand
    print(f"{len(mpns)} purchase lines meet listed stock, MOQ, order multiples and spares.")
    for name, sum_inr in observed.items():
        print(f"  {name} INR {sum_inr:.2f}")
    print(f"  Overall INR {grand:.2f}. Excluding LCDs INR {no_display:.2f}.")

    html = (HERE / f"{PREFIX}-Build-Configurator.html").read_text()
    encoded, = re.findall(r'<script[^>]+id="pcb-data"[^>]*>(.*?)</script>', html, re.S)
    configurator = json.loads(encoded)
    assert configurator["fullMainLow"] == configurator["fullMainCost"] == int(total * 100)
    catalog = {entry["ref"]: entry for entry in configurator["parts"] if entry["board"] == "HMI"}
    for ref, row in priced.items():
        assert catalog[ref]["mpn"] == row["Manufacturer part number"], ref
        field = "panelCost" if ref == "LCD1" else "cost"
        assert catalog[ref][field] == int(Decimal(row["Unit INR"]) * 100), ref
        if ref not in EXTERNAL:
            assert catalog[ref]["package"] == bom[ref]["Footprint"], ref
    before = indexed_csv(REPO / "industrial-hmi-rev-m" / "Industrial-HMI-RevM-BOM.csv",
                         "Reference", "Quantity")
    evidence = {}
    for row in rows(HERE / "tools" / "substitution-evidence.csv"):
        for ref in refs(row["Refs"]):
            assert ref not in evidence
            assert row["Old MPN"] == before[ref]["Manufacturer part number"]
            assert row["New MPN"] == bom[ref]["Manufacturer part number"]
            assert all(row[k] for k in ("Old datasheet", "New datasheet", "Ratings checked", "Land and pin check"))
            evidence[ref] = row
    assert evidence.keys() == {ref for ref in before if bom[ref]["Manufacturer part number"] != before[ref]["Manufacturer part number"]}
    print(f"{len(evidence)} sourced MPN changes have evidence. Configurator matches BOM and prices.")


def print_opens(label, board):
    opens = board.opens()
    print(f"{label}: {len(opens)} split named nets")
    for net, groups in opens.items():
        print(f"  {net} — largest group has {len(groups[0])} pads")
        for group in groups[1:]:
            print("    " + ", ".join(sorted(group)))


def print_shorts(label, board):
    shorts = board.shorts()
    print(f"{label}: {len(shorts)} mixed-net copper groups")
    for group in shorts:
        nets = sorted({p.net for p in group if p.net})
        def first_for(net):
            matching = [p for p in group if p.net == net]
            return next((p.name for p in matching if p.kind == "PAD"), matching[0].name)
        print("  " + ", ".join(f"{n} ({first_for(n)})" for n in nets))
    return shorts


def audit_clearance(label, board, baseline):
    changed = list(changed_copper(board, baseline))
    print(f"{label}: {len(changed)} added or changed layer objects")
    if not changed:
        return
    around = [(gap, p.layer, p.name, p.net, other.name, other.net)
              for p in changed for gap, other in board.clearances(p, .5)]
    if around:
        gap, layer, name, net, other, other_net = min(around)
        print(f"  Minimum {gap:.6f} mm on layer {layer}, "
              f"{name} ({net or 'unassigned'}) to {other} ({other_net or 'unassigned'}).")
    else:
        print("  Minimum exceeds 0.5 mm search bound.")
    bad = sorted(set(hit for hit in around if hit[0] < RULE))
    for gap, layer, name, net, other, other_net in bad:
        print(f"  Below rule {gap:.6f} mm on layer {layer}: {name} ({net}) to {other} ({other_net})")
    assert not bad, label


def print_weak_contacts(board, before, label):
    contacts = board.weak_contacts
    edits = list(changed_copper(board, before)) if before else []
    separate = sum(not joined for _, joined in contacts)
    print(f"{label}: {len(contacts)} weak contacts or near-gaps, {separate} between separate copper groups.")
    for contact, joined in sorted(contacts, key=lambda item: (
            LAYERS.index(item[0].first.layer), item[0].first.net,
            item[0].position, item[0].first.name, item[0].second.name)):
        a, b = contact.first, contact.second
        bridge = next((p.name for p in edits if p.layer == a.layer and p.net == a.net
                       and p.oid not in {a.oid, b.oid}
                       and positive_overlap(p.geometry, a.geometry)
                       and positive_overlap(p.geometry, b.geometry)), None)
        status = (f"bridged by {bridge}" if bridge else
                  "alternate copper path" if joined else "OPEN between fragments")
        x, y = contact.position
        print(f"  L{LAYERS.index(a.layer) + 1}/{a.layer} {a.net} {a.name} ↔ {b.name}, "
              f"({x:.6f}, {y:.6f}) mm, shared {contact.length:.6f} mm, gap {contact.gap:.6f} mm — {status}.")


def verify_buck_and_local_contacts(board, pcb):
    by_location = {(p.layer, p.name): p for p in board.pieces}

    def area(layer, name, neighbor):
        a, b = (by_location[layer, label] for label in (name, neighbor))
        assert a.net == b.net
        assert positive_overlap(a.geometry, b.geometry), (layer, name, neighbor)
        return a.geometry.intersection(b.geometry).area

    def verify_triplet(layer, bridge, first, second):
        first_area, second_area = (area(layer, bridge, name) for name in (first, second))
        print(f"  {layer} {first} ↔ {bridge} ↔ {second}. Overlap "
              f"{first_area:.5f} / {second_area:.5f} mm².")

    assert board.connected("3V3", *BUCK_LOADS)
    print("Buck output and distribution geometry")
    verify_triplet("1", "gge962017", "U6.3", "C94.1")
    sense = by_location["1", "gge962017"]
    for a in board.pieces:
        if a.layer == "1" and a.net == sense.net and a.name not in {"U6.3", "C94.1", sense.name}:
            assert not a.geometry.intersects(sense.geometry), (a.name, "unintended VOS tap")
    verify_triplet("22", "gge962014", "gge962012", "gge962011")
    verify_triplet("22", "gge962015", "gge962011", "gge962013")
    area("1", "L4.2", "gge962010")
    area("1", "C94.1", "gge962009")
    area("2", "gge962016", "gge3869")
    for via_group, surfaces in (
        (("gge962001", "gge962002", "gge962003"), (("1", "gge962009"), ("22", "gge962011"))),
        (("gge962004", "gge962005", "gge962006"), (("1", "gge962010"), ("22", "gge962012"))),
        (("gge5610", "gge962007", "gge962008"), (("2", "gge962016"), ("22", "gge962013"))),
    ):
        for via in via_group:
            for layer, endpoint in surfaces:
                area(layer, via, endpoint)
    records = {v[5]: v for s in pcb["shape"] if s.startswith("TRACK~") for v in [s.split("~")]}
    assert not {"gge4947", "gge4940"} & records.keys()
    for trace in ("gge962014", "gge962015"):
        assert abs(float(records[trace][1]) * .254 - 2.20) < .00001
    print("  Two 2.20 mm Inner2 power legs, three plated vias at each transition, "
          "positive overlap into Bottom distribution and VOS tapped at C94.1.")
    for copper in (.0175, .0152):
        area_mil2 = 2.20 * copper / .0254 ** 2
        rise = (1.5 / (.024 * area_mil2 ** .725)) ** (1 / .44)
        assert rise <= 20
        print(f"  IPC-2221 screening at 1.5 A and {copper * 1000:g} µm inner copper gives {rise:.1f} °C rise. "
              "Fabricator stackup and bench thermal test pending.")
    print("Requested local positive-overlap repairs")
    for pin, neighbor, layer, bridge in REINFORCEMENTS:
        verify_triplet(layer, bridge, pin, neighbor)


def mode_gap(board):
    pad, = [p for p in board.pieces if p.name == "U6.7" and p.layer == "1"]
    return min((gap, p.name) for gap, p in board.clearances(pad, .5) if p.net == "SYS_5V")


def verify_copper(current, base, frozen, phase1, before=None):
    print(f"Same-net contact requires positive area overlap or a continuous shared edge ≥ {MIN_SHARED_EDGE:.2f} mm.")
    print(f"Point and shorter edge contacts stay open. Also report finite gaps ≤ {NEAR_GAP:.4f} mm.")
    print("Layers 1, 21, 22, 2. Via and PTH annuli are connected across the stack.")
    print_opens("Rev N FOOTPRINTS", base)
    print_opens("Rev P", current)
    print_shorts("Frozen Rev N", frozen)
    assert not print_shorts("Rev N FOOTPRINTS", base)
    assert not print_shorts("Rev P", current)

    pad_groups = defaultdict(set)
    for (net, name), groups in base.pad_groups.items():
        assert (net, name) in current.pad_groups
        for group in groups:
            if net:
                pad_groups[(net, group)].add(name)
    for (net, _), names in pad_groups.items():
        assert current.connected(net, *names), (net, sorted(names), "new split")
    print("Every previously connected group of named pads stays connected.")
    print("Phase 2 before / after")
    unresolved = []
    for i, (label, net, named) in enumerate(ROUTES, 1):
        was_connected, now_connected = (board.connected(net, *named) for board in (base, current))
        if not now_connected:
            unresolved.append(i)
        old_state = "connected" if was_connected else "OPEN"
        new_state = "connected" if now_connected else "OPEN"
        print(f"  {i}. {net} {label} — {old_state} → {new_state}")
    gap_before, old_object = mode_gap(base)
    gap_after, new_object = mode_gap(current)
    print(f"  10. U6.7 vs SYS_5V — {gap_before:.6f} mm ({old_object}) → {gap_after:.6f} mm ({new_object}); limit {RULE:.3f} mm.")
    if gap_after < RULE:
        unresolved.append(10)
    if phase1:
        assert not list(changed_copper(current, base)) and not list(changed_copper(base, current))
    else:
        print(f"Phase 2 requested findings closed: {10 - len(unresolved)}/10.")
        assert not unresolved, f"Requested copper findings still open: {unresolved}"
    if before:
        print_opens("Pre-repair Rev P with current rule", before)
        print_weak_contacts(before, None, "Pre-repair Rev P")
        print_weak_contacts(current, before, "Final Rev P")
        assert all(joined for _, joined in current.weak_contacts), "unresolved weak contact between copper groups"
        assert REMOVED_FRAGMENTS.isdisjoint(p.oid for p in current.pieces)
        fragments = [p for p in before.pieces if p.oid in REMOVED_FRAGMENTS]
        assert {p.oid for p in fragments} == REMOVED_FRAGMENTS
        for p in sorted(fragments, key=lambda item: item.name):
            assert p.kind == "SOLIDREGION" and p.geometry.area < .01
            i, = (i for i, candidate in enumerate(before.pieces) if candidate is p)
            assert before.groups[before.root(i)] == [p], p.name
            print(f"  Removed {p.name}, layer {p.layer}, {p.net}, {p.geometry.area:.6f} mm², no lands or vias.")
        audit_clearance("Rev P vs pre-repair Rev P", current, before)
    audit_clearance("Rev P vs tagged FOOTPRINTS", current, base)
    audit_clearance("Rev P vs tagged frozen PCB", current, frozen)
    exposed, = [p for p in current.pieces if p.name == "U21.25" and p.layer == "1"]
    for piece in changed_copper(current, base):
        if piece.kind in {"TRACK", "VIA"} and piece.net != exposed.net:
            assert piece.geometry.intersection(exposed.geometry).area == 0, (piece.name, exposed.name)
    print("Changed foreign-net tracks and vias avoid the U21 exposed-pad projection.")
    endpoints = {"1": ("R69.2", "R70.1"), "2": ("R67.2", "R68.1"), "3": ("D1.1", "C82.1", "C83.1"),
                 "4": ("J1.2", "C82.2", "C83.2"), "5": ("L3.1", "C84.2"), "6": ("C84.1",)}
    for pin, expected in U1_PAD_NETS.items():
        name = f"U1.{pin}"
        assert {p.net for p in current.pieces if p.name == name} == {expected}
        assert current.connected(expected, name, *endpoints[pin]), (name, expected)
        print(f"  {name} {expected} connects to {', '.join(endpoints[pin])}.")
    assert current.connected("CAB_5V", "L3.2", "C2.1", "C85.1", "C86.1", "U22.7")
    print("U1 six pads and cabinet 5 V output path checked.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase1", action="store_true", help="Require precisely the tagged FOOTPRINTS copper.")
    args = parser.parse_args()
    frozen, base, old_schematic = rev_n_sources()
    pcb_path = HERE / cad_name("PCB")
    pcb = json.loads(pcb_path.read_bytes())
    schematic = json.loads((HERE / cad_name("Schematic")).read_bytes())
    bom = indexed_csv(HERE / f"{PREFIX}-BOM.csv", "Reference", "Quantity")
    base_parts = components(base, False)
    current_parts = verify_sources(schematic, pcb, old_schematic, base_parts, bom)
    verify_pricing(bom)
    board = Board(pieces(pcb, current_parts))
    previous = None
    if not args.phase1:
        path = pcb_path.relative_to(REPO)
        data = subprocess.check_output(["git", "show", f"{BEFORE_CONTACTS}:{path}"], cwd=REPO)
        prior = json.loads(data)
        previous = Board(pieces(prior, components(prior, False)))
    verify_copper(board, Board(pieces(base, base_parts)),
                  Board(pieces(frozen, components(frozen, False))), args.phase1, previous)
    if not args.phase1:
        assert not board.opens(), "split named pad net"
        verify_buck_and_local_contacts(board, pcb)
        verify_editor_footprints(pcb, schematic, board)
        editor_base = load_prior_pcb(BEFORE_EDITOR)
        audit_clearance("Rev P cumulative vs 3287d57", board,
                        Board(pieces(editor_base, components(editor_base, False))))
    print(f"Live PCB SHA-256 {sha256(pcb_path.read_bytes()).hexdigest()}")
    print("DRAFT — DO NOT FABRICATE. Native EasyEDA import, ERC/DRC, CAM and hardware checks pending.")


if __name__ == "__main__":
    main()
