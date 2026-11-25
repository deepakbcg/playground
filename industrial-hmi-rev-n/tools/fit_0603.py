#!/usr/bin/env python3
"""Screen proposed 0603 placements against the held EasyEDA Standard PCB."""

import argparse
import csv
from dataclasses import dataclass
import json
import math
from pathlib import Path
import sys

from verify_rev_n import attrs, components, HERE, HOLD_SUFFIX, refs, rows


MM_PER_UNIT = 0.254
MIN_COPPER_MARGIN = 0.125
EPSILON = 0.0001
PREFIX = "Industrial-HMI-RevN"
BODY_TEMPLATES = {"R": "R67", "C": "C87", "F": "FB1"}
SENSITIVE_NET_PREFIXES = (
    "USB_DP", "USB_DM", "XIN", "XOUT", "EVE_XI", "EVE_XO",
    "ETH_XI", "ETH_XO", "ETH_RX", "ETH_TX", "ETH_JACK",
)
HEADERS = [
    "Ref", "Value", "Nets", "Old footprint", "New footprint", "Region",
    "PCB x (mm)", "PCB y (mm)", "Rotation (deg clockwise)",
    "Fit status", "Nearest conflict", "Gap (mm)", "Required gap (mm)",
    "Clearance shortfall (mm)", "Suggested action",
]


def mm(value):
    return float(value) * MM_PER_UNIT


def points(encoded):
    coords = list(map(mm, encoded.split()))
    return list(zip(coords[::2], coords[1::2], strict=True))


@dataclass(frozen=True)
class Box:
    left: float
    top: float
    right: float
    bottom: float

    @classmethod
    def enclose(cls, coordinates):
        x, y = zip(*coordinates)
        return cls(min(x), min(y), max(x), max(y))

    @classmethod
    def around(cls, x, y, width, height):
        return cls(x - width / 2, y - height / 2, x + width / 2, y + height / 2)

    def corners(self):
        return [(self.left, self.top), (self.right, self.top),
                (self.right, self.bottom), (self.left, self.bottom)]

    def distance(self, other):
        """Edge clearance, negative for overlapping axis-aligned boxes."""
        dx = max(other.left - self.right, self.left - other.right)
        dy = max(other.top - self.bottom, self.top - other.bottom)
        return math.hypot(max(dx, 0), max(dy, 0)) if max(dx, dy) > 0 else max(dx, dy)

    def inside(self, outline):
        return min(self.left - outline.left, outline.right - self.right,
                   self.top - outline.top, outline.bottom - self.bottom)


@dataclass(frozen=True)
class Copper:
    name: str
    net: str
    layers: frozenset
    bounds: Box
    segment: tuple | None = None
    radius: float = 0

    def clearance(self, box):
        if self.segment is None:
            return box.distance(self.bounds)
        a, b = self.segment
        return segment_box_distance(a, b, box) - self.radius


@dataclass(frozen=True)
class Check:
    name: str
    gap: float
    required: float

    @property
    def margin(self):
        return self.gap - self.required


def segment_box_distance(a, b, box):
    """Exact distance to a rectangle, via clipping and closest edge points."""
    x, y = a
    dx, dy = b[0] - x, b[1] - y
    enter, leave = 0.0, 1.0
    for origin, direction, low, high in (
        (x, dx, box.left, box.right), (y, dy, box.top, box.bottom),
    ):
        if direction:
            first, last = sorted(((low - origin) / direction, (high - origin) / direction))
            enter, leave = max(enter, first), min(leave, last)
        elif not low <= origin <= high:
            enter, leave = 1.0, 0.0
    if enter <= leave:
        return 0.0

    length_squared = dx * dx + dy * dy
    distances = [max(0.0, box.distance(Box.around(*point, 0, 0))) for point in (a, b)]
    if length_squared:
        for px, py in box.corners():
            t = max(0.0, min(1.0, ((px - x) * dx + (py - y) * dy) / length_squared))
            distances.append(math.hypot(x + t * dx - px, y + t * dy - py))
    return min(distances)


def surface(layer):
    return frozenset({"1", "2"} if layer == "11" else {layer})


def pad_box(pad):
    vertices = points(pad[10]) if pad[10] and pad[1] != "ELLIPSE" else []
    if vertices:
        return Box.enclose(vertices)
    return Box.around(*map(mm, pad[2:6]))


def pin_rows(body):
    return [line.split("~") for line in body if line.startswith("PAD~")]


def body_box(body):
    coordinates = [point for line in body if line.startswith("TRACK~")
                   for fields in [line.split("~")] if fields[2] == "12"
                   for point in points(fields[4])]
    return Box.enclose(coordinates) if coordinates else None


def net_label(net):
    return net or "NC / unnamed"


def pcb_geometry(pcb, parts):
    edges = []
    bodies = {}
    obstacles = []
    for designator, (_, _, body) in parts.items():
        pads = pin_rows(body)
        layers = frozenset(layer for pad in pads for layer in surface(pad[6]))
        if (bounds := body_box(body)) is not None:
            bodies[designator] = bounds, layers
        for pad in pads:
            name = f"{designator}.{pad[8]} pad ({net_label(pad[7])})"
            obstacles.append((designator, Copper(name, pad[7], surface(pad[6]), pad_box(pad))))

    for shape in pcb["shape"]:
        fields = shape.split("~")
        if fields[0] == "TRACK":
            layer = fields[2]
            if layer == "10":
                edges.extend(points(fields[4]))
            if layer in {"1", "2"}:
                xy = points(fields[4])
                radius = mm(fields[1]) / 2
                for a, b in zip(xy, xy[1:]):
                    box = Box.enclose([a, b])
                    bounds = Box(box.left - radius, box.top - radius,
                                 box.right + radius, box.bottom + radius)
                    name = f"{fields[5]} track ({net_label(fields[3])})"
                    obstacles.append(("", Copper(name, fields[3], surface(layer), bounds, (a, b), radius)))
        elif fields[0] in {"VIA", "HOLE"}:
            x, y, diameter = map(mm, fields[1:4])
            is_via = fields[0] == "VIA"
            net, oid = (fields[4], fields[6]) if is_via else ("", fields[4])
            name = f"{oid} via ({net_label(net)})" if is_via else f"{oid} mounting or locator hole"
            obstacles.append(("", Copper(name, net, surface("11"),
                                         Box.around(x, y, diameter, diameter),
                                         ((x, y), (x, y)), diameter / 2)))

    outline = Box.enclose(edges)
    if set(edges) != set(outline.corners()):
        raise ValueError("The board outline is not a rectangular loop")
    return outline, bodies, obstacles


def rotation(pads):
    first, second = sorted(pads, key=lambda pad: pad[8])
    assert (first[8], second[8]) == ("1", "2")
    dx = mm(second[2]) - mm(first[2])
    dy = mm(second[3]) - mm(first[3])
    angle = math.degrees(math.atan2(dy, dx)) % 360
    cardinal = round(angle / 90) * 90
    if abs(cardinal - angle) > 0.01:
        raise ValueError(f"Unsupported pad axis angle {angle:.2f}")
    return cardinal % 360


def project(box, source, destination, angle):
    cosine = (1, 0, -1, 0)[angle // 90]
    sine = (0, 1, 0, -1)[angle // 90]
    coordinates = []
    for x, y in box.corners():
        x, y = x - source[0], y - source[1]
        coordinates.append((destination[0] + x * cosine - y * sine,
                            destination[1] + x * sine + y * cosine))
    return Box.enclose(coordinates)


def projected_placement(ref, parts):
    _, header, body = parts[ref]
    center = tuple(map(mm, header[1:3]))
    existing_pads = sorted(pin_rows(body), key=lambda pad: pad[8])
    angle = rotation(existing_pads)
    _, source_header, source_body = parts[BODY_TEMPLATES[ref[0]]]
    origin = tuple(map(mm, source_header[1:3]))
    template_pads = sorted(pin_rows(source_body), key=lambda pad: pad[8])
    assert rotation(template_pads) == 0
    body_outline = project(body_box(source_body), origin, center, angle)
    proposed_pads = [(old, project(pad_box(new), origin, center, angle))
                     for old, new in zip(existing_pads, template_pads, strict=True)]
    envelope = Box.enclose(body_outline.corners() +
                           [point for _, box in proposed_pads for point in box.corners()])
    return center, angle, envelope, proposed_pads


def screen(ref, placement, outline, bodies, obstacles):
    _, _, envelope, pads = placement
    layer = surface(pads[0][0][6])
    checks = [Check("board edge", envelope.inside(outline), MIN_COPPER_MARGIN)]
    for other, (box, sides) in bodies.items():
        if ref != other and layer & sides:
            checks.append(Check(f"{other} body / courtyard", envelope.distance(box), 0))

    for owner, obstacle in obstacles:
        if owner == ref or not layer & obstacle.layers:
            continue
        if envelope.distance(obstacle.bounds) > 1.0:
            continue
        if owner or " hole" in obstacle.name:
            checks.append(Check(obstacle.name, obstacle.clearance(envelope), 0))
        for pad, box in pads:
            if not pad[7] or pad[7] != obstacle.net:
                checks.append(Check(f"{obstacle.name} vs pin {pad[8]}", obstacle.clearance(box),
                                    MIN_COPPER_MARGIN))
    return min(checks, key=lambda item: item.margin)


def fit_row(ref, placement, check, outline, before, after, bom):
    center, angle, _, pads = placement
    nets = [pad[7] for pad, _ in pads]
    x, y = center[0] - outline.left, center[1] - outline.top
    side = "West" if x < 33 else "Center" if x < 66 else "East"
    row = "North" if y < 32 else "Middle" if y < 64 else "South"
    if check.margin >= -EPSILON:
        status = "fits-in-place"
        action = "Place at existing center. Verify pad overlap, reconnect tracks and run native DRC."
    elif check.gap < -EPSILON and any(net.startswith(SENSITIVE_NET_PREFIXES) for net in nets):
        status = "keep-0402-recommended"
        action = "Review the sensitive escape in EasyEDA. Prefer retaining 0402 if 0603 requires a longer or unmatched route."
    else:
        status = "needs-nudge"
        action = "Resolve highlighted clearance with a nudge or local reroute. Reconnect tracks and run native DRC."
    return dict(zip(HEADERS, [
        ref, bom[ref]["Description"], " / ".join(map(net_label, nets)), before, after,
        f"{row} {side}", f"{x:.3f}", f"{y:.3f}", angle, status, check.name,
        f"{check.gap:.3f}", f"{check.required:.3f}",
        f"{max(0.0, -check.margin):.3f}", action,
    ], strict=True))


def calculate():
    pcb = json.loads((HERE / f"PCB_{PREFIX}-{HOLD_SUFFIX}.json").read_bytes())
    schematic = json.loads((HERE / f"Schematic_{PREFIX}-{HOLD_SUFFIX}.json").read_bytes())
    parts = components(pcb, False)
    symbols = components(schematic, True)
    bom = {ref: row for row in rows(HERE / f"{PREFIX}-BOM.csv")
           for ref in refs(row["Reference"])}
    converted = []
    for ref, (_, header, _) in parts.items():
        before = attrs(header)["package"]
        after = attrs(symbols[ref][1])["package"]
        if before != after and ref[0] in BODY_TEMPLATES:
            assert attrs(parts[BODY_TEMPLATES[ref[0]]][1])["package"] == after == "0603"
            converted.append((ref, before, after))

    outline, bodies, obstacles = pcb_geometry(pcb, parts)
    placements = {ref: projected_placement(ref, parts) for ref, _, _ in converted}
    for ref, (_, _, envelope, pads) in placements.items():
        bodies[ref] = envelope, surface(pads[0][0][6])
    worklist = [
        fit_row(ref, placements[ref], screen(ref, placements[ref], outline, bodies, obstacles),
                outline, before, after, bom)
        for ref, before, after in converted
    ]
    region_order = {f"{row} {col}": i for i, (row, col) in
                    enumerate((r, c) for r in ("North", "Middle", "South")
                              for c in ("West", "Center", "East"))}
    return sorted(worklist, key=lambda row: (
        region_order[row["Region"]], float(row["PCB y (mm)"]), float(row["PCB x (mm)"]), row["Ref"],
    ))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Write CSV to this file instead of stdout")
    args = parser.parse_args()
    worklist = calculate()
    if args.output:
        with args.output.open("w", encoding="utf-8", newline="") as target:
            write_worklist(target, worklist)
    else:
        write_worklist(sys.stdout, worklist)


def write_worklist(target, worklist):
    writer = csv.DictWriter(target, HEADERS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(worklist)


if __name__ == "__main__":
    main()
