"""Read stored EasyEDA Standard copper on the four Rev P board layers."""

from collections import defaultdict
from dataclasses import dataclass

from shapely.geometry import LineString, Point, Polygon, box
from shapely.strtree import STRtree

MM_PER_UNIT = 0.254
LAYERS = ("1", "21", "22", "2")
# The source typically rounds coordinates to five EasyEDA units after the
# decimal point. Ignore boundary slivers within that coordinate precision.
LINEAR_TOLERANCE = 0.000002
CIRCLE_STEPS = 64


def mm_point(x, y):
    return float(x) * MM_PER_UNIT, float(y) * MM_PER_UNIT


def points(encoded):
    values = encoded.split()
    return [mm_point(x, y) for x, y in zip(values[::2], values[1::2], strict=True)]


def external_polygon(encoded):
    shape = Polygon(points(encoded))
    if not shape.is_valid:
        raise ValueError(f"Invalid copper polygon {encoded[:100]}")
    return shape


def disc(center, diameter):
    return Point(center).buffer(diameter / 2, quad_segs=CIRCLE_STEPS)


@dataclass(frozen=True)
class Piece:
    oid: str
    name: str
    kind: str
    net: str
    layer: str
    geometry: object
    plated: bool = False


def from_record(record, ref=""):
    fields = record.split("~")
    kind = fields[0]
    if kind == "TRACK" and fields[2] in LAYERS:
        _, width, layer, net, path, oid, *_ = fields
        trace = LineString(points(path)).buffer(float(width) * MM_PER_UNIT / 2, quad_segs=CIRCLE_STEPS)
        yield Piece(oid, oid, kind, net, layer, trace)
    elif kind == "SOLIDREGION" and fields[1] in LAYERS:
        _, layer, net, ring, shape_type, oid, *_ = fields
        if shape_type != "solid":
            raise ValueError(f"Unhandled copper region {shape_type} {oid}")
        yield Piece(oid, oid, kind, net, layer, external_polygon(ring))
    elif kind == "PAD" and fields[6] in (*LAYERS, "11"):
        _, form, x, y, width, height, layer, net, pad, radius, ring, angle, oid, *_ = fields
        assert angle == "0", (oid, angle)
        center = mm_point(x, y)
        width, height = float(width) * MM_PER_UNIT, float(height) * MM_PER_UNIT
        if form == "ELLIPSE":
            assert abs(width - height) < LINEAR_TOLERANCE, oid
            shape = disc(center, width)
        elif form == "RECT" and ring:
            shape = external_polygon(ring)
        elif form == "RECT":
            cx, cy = center
            shape = box(cx - width / 2, cy - height / 2, cx + width / 2, cy + height / 2)
        else:
            raise ValueError(f"Unsupported copper pad {form} {oid}")
        plated = layer == "11" and fields[15] == "Y"
        if plated:
            assert not fields[14], (oid, "slot requires explicit geometry handling")
            shape = shape.difference(disc(center, 2 * float(radius) * MM_PER_UNIT))
        for physical_layer in LAYERS if layer == "11" else (layer,):
            yield Piece(oid, f"{ref}.{pad}" if ref else oid, kind, net, physical_layer, shape, plated)
    elif kind == "VIA":
        _, x, y, diameter, net, hole_radius, oid, *_ = fields
        center = mm_point(x, y)
        shape = disc(center, float(diameter) * MM_PER_UNIT).difference(
            disc(center, 2 * float(hole_radius) * MM_PER_UNIT))
        for layer in LAYERS:
            yield Piece(oid, oid, kind, net, layer, shape, True)


def pieces(pcb, components):
    by_index = {index: ref for ref, (index, _, _) in components.items()}
    result = []
    for index, shape in enumerate(pcb["shape"]):
        records = shape.split("#@$")
        for record in records:
            result.extend(from_record(record, by_index.get(index, "")))
    return result


def positive_overlap(a, b):
    # DE-9IM dimension 2 excludes point and line tangencies. The erosion
    # discards only overlaps thinner than the source coordinate precision.
    if not a.relate_pattern(b, "2********"):
        return False
    overlap = a.intersection(b)
    return not overlap.buffer(-LINEAR_TOLERANCE / 2).is_empty


class Board:
    def __init__(self, all_pieces):
        self.pieces = all_pieces
        self.by_layer = {layer: [i for i, p in enumerate(all_pieces) if p.layer == layer]
                         for layer in LAYERS}
        self.trees = {layer: STRtree([all_pieces[i].geometry for i in ids])
                      for layer, ids in self.by_layer.items()}
        self.parent = list(range(len(all_pieces)))
        barrels = {}
        for i, piece in enumerate(all_pieces):
            if piece.plated:
                self.join(i, barrels.setdefault(piece.oid, i))
            for j in self.query(piece.layer, piece.geometry):
                if j < i and positive_overlap(piece.geometry, all_pieces[j].geometry):
                    self.join(i, j)
        self.groups = defaultdict(list)
        self.pad_groups = defaultdict(set)
        for i, piece in enumerate(all_pieces):
            group = self.root(i)
            self.groups[group].append(piece)
            if piece.kind == "PAD":
                self.pad_groups[(piece.net, piece.name)].add(group)

    def query(self, layer, geometry, distance=None):
        tree = self.trees[layer]
        hits = (tree.query(geometry, predicate="intersects") if distance is None else
                tree.query(geometry, predicate="dwithin", distance=distance))
        return (self.by_layer[layer][i] for i in hits)

    def root(self, i):
        while self.parent[i] != i:
            self.parent[i] = self.parent[self.parent[i]]
            i = self.parent[i]
        return i

    def join(self, a, b):
        self.parent[self.root(b)] = self.root(a)

    def connected(self, net, *pad_names):
        return bool(set.intersection(*(self.pad_groups[(net, name)] for name in pad_names)))

    def opens(self):
        net_groups = defaultdict(lambda: defaultdict(set))
        for (net, pad), groups in self.pad_groups.items():
            if net:
                for group in groups:
                    net_groups[net][group].add(pad)
        return {
            net: sorted(groups.values(), key=lambda group: (-len(group), sorted(group)))
            for net, groups in sorted(net_groups.items()) if len(groups) > 1
        }

    def shorts(self):
        return [
            group for group in self.groups.values()
            if len({piece.net for piece in group if piece.net}) > 1
        ]

    def clearances(self, piece, distance):
        for index in self.query(piece.layer, piece.geometry, distance):
            other = self.pieces[index]
            if piece.net != other.net:
                yield piece.geometry.distance(other.geometry), other


def changed_copper(board, baseline):
    """Compare per object and layer; geometrically identical records do not count."""
    old = {(p.oid, p.layer): p for p in baseline.pieces}
    assert len(old) == len(baseline.pieces), "duplicate source copper IDs"
    assert len({(p.oid, p.layer) for p in board.pieces}) == len(board.pieces), "duplicate edited copper IDs"
    for piece in board.pieces:
        prior = old.get((piece.oid, piece.layer))
        if prior is None or prior.net != piece.net or not prior.geometry.equals(piece.geometry):
            yield piece
