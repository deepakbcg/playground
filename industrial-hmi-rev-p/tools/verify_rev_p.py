#!/usr/bin/env python3
"""Verify the Rev P package and stored copper. Native EasyEDA checks are separate."""

import argparse
from collections import defaultdict
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
import subprocess
import sys
from zipfile import ZipFile

from copper_geometry import (Board, LAYERS, MIN_SHARED_EDGE, NEAR_GAP, changed_copper,
                             pieces, positive_overlap)

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
    from math import dist
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
        names = {cad_name("PCB"), cad_name("Schematic"), BUZZER}
        assert zipped.testzip() is None and set(zipped.namelist()) == names
        assert all(zipped.read(name) == (HERE / name).read_bytes() for name in names)
    assert len(list(HERE.glob("*.zip"))) == len(list(HERE.glob("PCB_*.json"))) == len(list(HERE.glob("Schematic_*.json"))) == 1
    print("One live schematic, one live PCB and one ZIP containing the byte-identical sources and BZ1 library.")
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
        print(f"  Minimum {gap:.6f} mm on layer {layer}, {name} ({net}) to {other} ({other_net}).")
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
        assert abs(float(records[trace][1]) * .254 - 1.40) < .00001
    print("  Two 1.40 mm Inner2 power legs, three plated vias at each transition, "
          "positive overlap into Bottom distribution and VOS tapped at C94.1.")
    print("  Trace sizing assumes ≥35 µm finished Inner2 copper. Thermal qualification at 1.5 A pending.")
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
    print(f"Live PCB SHA-256 {sha256(pcb_path.read_bytes()).hexdigest()}")
    print("DRAFT — DO NOT FABRICATE. Native EasyEDA import, copper rebuild, ERC/DRC, CAM and hardware pending.")


if __name__ == "__main__":
    main()
