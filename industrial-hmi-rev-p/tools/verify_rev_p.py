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

from copper_geometry import Board, changed_copper, pieces

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
ROUTES = (
    ("R76.2 → mux ground", "GND", ("R76.2", "U22.3")),
    ("U6.4 → input capacitor ground", "GND", ("U6.4", "C93.2", "J1.2")),
    ("U6.5/U6.6 → input capacitor and mux", "SYS_5V", ("U6.5", "U6.6", "C93.1", "U22.1")),
    ("U21.24 → USB input and local bypass", "USB_VBUS", ("U21.24", "C87.1", "Q3.1")),
    ("U21.18 → divider", "USB_RAW_SENSE", ("U21.18", "R73.2")),
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
    for ref in LOCKED:
        pin = attrs(components(old_schematic, True)[ref][1])
        assert pin["BOM_Manufacturer Part"] == bom[ref]["Manufacturer part number"], ref
    assert all(before == after or (before.startswith("T~L~") and "Rev P" in after)
               for before, after in zip(old_schematic["shape"], schematic["shape"], strict=True)
               if not before.startswith("LIB~"))
    for ref, (_, _, body) in components(old_schematic, True).items():
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


def mode_gap(board):
    pad, = [p for p in board.pieces if p.name == "U6.7" and p.layer == "1"]
    return min((gap, p.name) for gap, p in board.clearances(pad, .5) if p.net == "SYS_5V")


def verify_copper(current, base, frozen, phase1):
    print("Copper check uses positive area overlap above source coordinate precision.")
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
    for i, (label, net, named) in enumerate(ROUTES, 1):
        before, after = (board.connected(net, *named) for board in (base, current))
        print(f"  {i}. {net} {label} — {'connected' if before else 'OPEN'} → {'connected' if after else 'OPEN'}")
    gap_before, old_object = mode_gap(base)
    gap_after, new_object = mode_gap(current)
    print(f"  10. U6.7 vs SYS_5V — {gap_before:.6f} mm ({old_object}) → {gap_after:.6f} mm ({new_object}); limit {RULE:.3f} mm.")
    if phase1:
        assert not list(changed_copper(current, base)) and not list(changed_copper(base, current))
    audit_clearance("Rev P vs tagged FOOTPRINTS", current, base)
    audit_clearance("Rev P vs tagged frozen PCB", current, frozen)
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
    verify_copper(Board(pieces(pcb, current_parts)), Board(pieces(base, base_parts)),
                  Board(pieces(frozen, components(frozen, False))), args.phase1)
    print(f"Live PCB SHA-256 {sha256(pcb_path.read_bytes()).hexdigest()}")
    print("DRAFT — DO NOT FABRICATE. Native EasyEDA import, copper rebuild, ERC/DRC, CAM and hardware pending.")


if __name__ == "__main__":
    main()
