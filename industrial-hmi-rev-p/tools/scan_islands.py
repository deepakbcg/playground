#!/usr/bin/env python3
"""List copper islands in the live Rev P PCB.

An island is a group of copper objects on one layer that contains no pad and no via and
does not positively overlap other same-net copper. Groups are built from positive area
overlap only (point, line and shared-edge contacts do not join), plus plated barrels
across the four layers, which matches how EasyEDA Pro's DRC decides connectivity.
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path
import sys

from copper_geometry import LAYERS, MM_PER_UNIT, pieces, positive_overlap
from shapely.ops import unary_union
from shapely.strtree import STRtree

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / "industrial-hmi-rev-n" / "tools"))
from verify_rev_n import components  # noqa: E402

PCB = HERE / "PCB_Industrial-HMI-RevP-DO-NOT-FABRICATE.json"


def groups(all_pieces):
    parent = list(range(len(all_pieces)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    barrels = {}
    by_layer = defaultdict(list)
    for i, piece in enumerate(all_pieces):
        by_layer[piece.layer].append(i)
        if piece.plated:
            parent[root(i)] = root(barrels.setdefault(piece.oid, i))
    for layer, ids in by_layer.items():
        tree = STRtree([all_pieces[i].geometry for i in ids])
        for a in ids:
            for hit in tree.query(all_pieces[a].geometry, predicate="intersects"):
                b = ids[hit]
                if b < a and positive_overlap(all_pieces[a].geometry, all_pieces[b].geometry):
                    parent[root(a)] = root(b)
    grouped = defaultdict(list)
    for i, piece in enumerate(all_pieces):
        grouped[root(i)].append(piece)
    return list(grouped.values())


def islands(pcb):
    found = []
    for group in groups(pieces(pcb, components(pcb, False))):
        if any(p.kind in {"PAD", "VIA"} for p in group):
            continue
        shape = unary_union([p.geometry for p in group])
        layer, = {p.layer for p in group}
        nets = sorted({p.net for p in group})
        found.append((layer, nets, sorted(p.oid for p in group), shape))
    return sorted(found, key=lambda item: (LAYERS.index(item[0]), item[3].bounds))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pcb", nargs="?", default=PCB, type=Path)
    args = parser.parse_args()
    found = islands(json.loads(args.pcb.read_bytes()))
    print(f"{len(found)} copper islands with no pad, no via and no positive overlap to other copper.")
    for layer, nets, oids, shape in found:
        x0, y0, x1, y1 = shape.bounds
        u = [v / MM_PER_UNIT for v in shape.bounds]
        print(f"  layer {layer} {'/'.join(n or 'no net' for n in nets)} {', '.join(oids)}: "
              f"{shape.area:.4f} mm², x {x0:.3f}–{x1:.3f} y {y0:.3f}–{y1:.3f} mm "
              f"(units x {u[0]:.1f}–{u[2]:.1f} y {u[1]:.1f}–{u[3]:.1f})")
    return found


if __name__ == "__main__":
    main()
