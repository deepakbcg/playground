#!/usr/bin/env python3
"""Compare the held Rev N draft with Rev M. This is not a release check."""
from collections import Counter
import csv
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZipFile

HERE = Path(__file__).resolve().parents[1]
BASE = HERE.with_name("industrial-hmi-rev-m")
MONEY = Decimal("0.01")
ALLOWED_ATTRIBUTES = {"BOM_Manufacturer Part", "BOM_Manufacturer", "BOM_Supplier Part"}
VALUE_LABELS = {
    "C3": ("47 uF 25 V", "47 µF 35 V"),
    "C7": ("1 uF 10 V", "1 µF 16 V"),
    "C84": ("100 nF 16 V", "100 nF 100 V"),
    "R68": ("330 kΩ", "91 kΩ"),
}
PANEL = {"LCD1", "CELL1"}
LOCKED = set("U1 U2 U5 U6 U8 U14 U21 U22 U23 D4 D10 J4 X1".split())
U1_PIN_NUMBERS = {"FB": "1", "EN": "2", "VIN": "3", "GND": "4", "SW": "5", "CB": "6"}
U1_PAD_NETS = {
    "1": "CAB_FB", "2": "CAB_EN", "3": "VIN_PROT",
    "4": "GND", "5": "CAB_SW", "6": "CAB_CB",
}
HOLD_MARK = "DO NOT FABRICATE"
HOLD_SUFFIX = HOLD_MARK.replace(" ", "-")
PCB_HOLD_LABEL = "gge900001"
SCH_TITLE = "Industrial touchscreen HMI"
LEGACY_U1_NETS = {"1": "VIN_PROT", "3": "GND", "4": "CAB_FB"}


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def refs(label):
    return [ref.strip() for ref in label.split(",")]


def attrs(header):
    tokens = header[3].removesuffix("`").split("`")
    assert len(tokens) % 2 == 0 and len(set(tokens[::2])) * 2 == len(tokens), header[3]
    return dict(zip(tokens[::2], tokens[1::2]))


def components(doc, sch):
    prefix, field = ("T~P~", 12) if sch else ("TEXT~P~", 10)
    found = {}
    for i, shape in enumerate(doc["shape"]):
        if shape.startswith("LIB~"):
            head, *body = shape.split("#@$")
            ref, = (line.split("~")[field] for line in body if line.startswith(prefix))
            assert ref not in found, ref
            found[ref] = i, head.split("~"), body
    return found


def cents(value):
    return Decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)


def geometry(doc, sch):
    specific = {"Title", "Release status"}
    stable = {key: value for key, value in doc.items() if key not in {"head", "shape"}}
    stable["head"] = {**doc["head"], "c_para": {
        key: value for key, value in doc["head"]["c_para"].items() if key not in specific
    }}
    new_shapes = list(doc["shape"])
    for ref, (i, header, body) in components(doc, sch).items():
        attributes = attrs(header)
        if sch and ref in VALUE_LABELS:
            old, new = VALUE_LABELS[ref]
            if attributes["name"] == new:
                attributes["name"] = old
                for j, line in enumerate(body):
                    if line.startswith("T~N~"):
                        fields = line.split("~")
                        if fields[12] == new:
                            fields[12] = old
                            body[j] = "~".join(fields)
        header[3] = "`".join(item for pair in attributes.items()
                             if pair[0] not in ALLOWED_ATTRIBUTES for item in pair)
        new_shapes[i] = "#@$".join(["~".join(header), *body])
    if sch:
        new_shapes = [x.replace("REV N  /  ", "REV M  /  ", 1)
                      if x.startswith("T~L~") else x for x in new_shapes]
        new_shapes = [x.replace(f"~{HOLD_MARK} - {SCH_TITLE}~", f"~{SCH_TITLE}~", 1)
                      if x.startswith("T~L~") else x for x in new_shapes]
    else:
        new_shapes = [x for x in new_shapes if not is_pcb_hold_label(x)]
    stable["shape"] = new_shapes
    return stable


def pad_records(doc):
    lands = Counter()
    for ref, (_, header, body) in components(doc, False).items():
        for line in body:
            fields = line.split("~")
            if fields[0] == "PAD":
                lands[ref, attrs(header)["package"], fields[8], fields[7]] += 1
    return lands


def is_pcb_hold_label(shape):
    fields = shape.split("~")
    return (fields[:2] == ["TEXT", "L"] and fields[7] == "12"
            and fields[10] == HOLD_MARK and fields[13] == PCB_HOLD_LABEL)


def verify_legacy_u1_copper(pcb):
    pads = {fields[8]: fields for fields in
            (s.split("~") for s in components(pcb, False)["U1"][2]) if fields[0] == "PAD"}
    copper = {}
    for shape in pcb["shape"]:
        fields = shape.split("~")
        if fields[0] == "TRACK" and fields[2] == "1" and fields[3] in LEGACY_U1_NETS.values():
            points = list(map(Decimal, fields[4].split()))
            copper.setdefault(fields[3], set()).update(zip(points[::2], points[1::2]))
    for pin, track_net in LEGACY_U1_NETS.items():
        pad = pads[pin]
        assert tuple(map(Decimal, pad[2:4])) in copper[track_net], pin
        assert pad[7] == U1_PAD_NETS[pin] and pad[7] != track_net
        print(f"FABRICATION HOLD: U1.{pin} ({pad[7]}) is still contacted by {track_net} copper.")


def normalize_u1(before, after, schematic):
    """Check the only allowed library shape changes and remove them for comparison."""
    index, before_head, before_body = components(before, schematic)["U1"]
    after_index, after_head, after_body = components(after, schematic)["U1"]
    assert index == after_index and before_head == after_head
    seen = set()
    for old, new in zip(before_body, after_body, strict=True):
        if schematic and old.startswith("P~"):
            old_parts, new_parts = old.split("^^"), new.split("^^")
            connection, number_label = new_parts[0].split("~"), new_parts[4].split("~")
            function = new_parts[3].split("~")[4]
            number = U1_PIN_NUMBERS[function]
            assert connection[3] == number_label[4] == number
            connection[3] = old_parts[0].split("~")[3]
            number_label[4] = connection[3]
            new_parts[0], new_parts[4] = "~".join(connection), "~".join(number_label)
            assert new_parts == old_parts, function
            seen.add(number)
        elif not schematic and old.startswith("PAD~"):
            old_fields, new_fields = old.split("~"), new.split("~")
            number = new_fields[8]
            assert new_fields[7] == U1_PAD_NETS[number]
            scale = Decimal("0.254")
            assert cents(Decimal(new_fields[4]) * scale) == Decimal("1.10")
            assert cents(Decimal(new_fields[5]) * scale) == Decimal("0.60")
            old_vertices, new_vertices = old_fields[10].split(), new_fields[10].split()
            assert new_vertices[::2] == old_vertices[::2]
            y = Decimal(new_fields[3])
            assert [cents((Decimal(v) - y) * scale) for v in new_vertices[1::2]] == [
                Decimal("-0.30"), Decimal("-0.30"), Decimal("0.30"), Decimal("0.30")
            ]
            for field in (5, 7, 10):
                new_fields[field] = old_fields[field]
            assert new_fields == old_fields, number
            seen.add(number)
        else:
            assert new == old, old
    assert seen == U1_PAD_NETS.keys()
    after["shape"][index] = before["shape"][index]


def main():
    prefix = "Industrial-HMI-RevN"
    cad = {}
    for kind in ("Schematic", "PCB"):
        before = json.loads((BASE / f"{kind}_Industrial-HMI-RevM-Draft.json").read_bytes())
        after = json.loads((HERE / f"{kind}_{prefix}-{HOLD_SUFFIX}.json").read_bytes())
        is_schematic = kind == "Schematic"
        before_geometry, after_geometry = geometry(before, is_schematic), geometry(after, is_schematic)
        normalize_u1(before_geometry, after_geometry, is_schematic)
        assert before_geometry == after_geometry, kind
        params = after["head"]["c_para"]
        assert params["Title"].startswith(HOLD_MARK) and "Rev N" in params["Title"]
        assert params["Release status"].startswith(HOLD_MARK) and "U1.1" in params["Release status"]
        if is_schematic:
            labels = [s for s in after["shape"] if s.startswith("T~L~")]
            assert sum(f"~{HOLD_MARK} - {SCH_TITLE}~" in s for s in labels) == 1
        else:
            hold_label, = (s.split("~") for s in after["shape"] if is_pcb_hold_label(s))
            assert hold_label[11].startswith("M ") and hold_label[12] != "none"
            verify_legacy_u1_copper(after)
            lands = pad_records(after)
            before_lands = pad_records(before)
            assert Counter({key: value for key, value in before_lands.items() if key[0] != "U1"}) == Counter(
                {key: value for key, value in lands.items() if key[0] != "U1"}
            )
            print(f"PCB copper, drill and source geometry outside U1 allowances match Rev M. {lands.total()} pads.")
            counts = Counter(x.split("~")[0] for x in after["shape"])
            print("Top-level shape counts " + ", ".join(f"{kind} {count}" for kind, count in sorted(counts.items())))
            q3 = {pin: net for ref, _, pin, net in lands if ref == "Q3"}
            assert q3 == {**dict.fromkeys("123", "USB_VBUS"), "4": "USB_FET_GATE",
                          **dict.fromkeys("56789", "USB_SW_VBUS")}
            print("Q3 pad nets match Rev M.")
            print("U1 pin numbers, pad nets and DDC0006A lands checked. U1 copper rerouting is pending.")
        cad[kind] = components(after, is_schematic)

    bom = {}
    for row in rows(HERE / f"{prefix}-BOM.csv"):
        designators = refs(row["Reference"])
        assert len(designators) == int(row["Quantity"]), row
        for ref in designators:
            assert ref not in bom, ref
            bom[ref] = row
    assert set(bom) - PANEL == set(cad["PCB"]) == set(cad["Schematic"])
    before_bom = {ref: row for row in rows(BASE / "Industrial-HMI-RevM-BOM.csv")
                  for ref in refs(row["Reference"])}
    assert bom["Q3"]["Manufacturer part number"] == "STL6P3LLH6"
    assert bom["X3"]["Manufacturer part number"] == "X1E0000210139"
    assert bom["R68"]["Description"] == "91 kΩ"
    assert bom["R68"]["Manufacturer part number"] == "0603WAF9102T5E"
    assert bom["R68"]["LCSC part"] == "C23265"
    _, r68_head, r68_body = cad["Schematic"]["R68"]
    assert attrs(r68_head)["name"] == bom["R68"]["Description"]
    assert [line.split("~")[12] for line in r68_body if line.startswith("T~N~")] == ["91 kΩ"]
    for ref in ("C68", "C69"):
        assert bom[ref]["Description"] == before_bom[ref]["Description"] and "18 pF" in bom[ref]["Description"]
    for ref in cad["PCB"]:
        row = bom[ref]
        mpn = row["Manufacturer part number"]
        if ref.startswith("TP"):
            assert not mpn and row["Population"] == "DNP"
        for group in cad.values():
            attr = attrs(group[ref][1])
            if ref in before_bom:
                assert row["Footprint"] == before_bom[ref]["Footprint"], ref
            assert attr["BOM_Manufacturer Part"] == mpn, (ref, attr["BOM_Manufacturer Part"], mpn)
            if ref in LOCKED:
                assert mpn == before_bom[ref]["Manufacturer part number"], ref
            assert attr.get("BOM_Supplier Part", "") == row["LCSC part"] or row["Population"] == "DNP", ref
    print(f"Schematic, PCB and BOM agree on {len(cad['PCB'])} designators. TP1–TP4 are DNP.")
    print("Panel and battery are external to the CAD refdes sets.")

    needed = {ref for ref, row in bom.items() if row["Population"].startswith("Fit")} - {"LCD1"}
    priced = set()
    total, missing = Decimal(0), []
    cost_rows = rows(HERE / f"{prefix}-BOM-Cost-INR.csv")
    pricing = {}
    external_panel = []
    for row in cost_rows[:-1]:
        designators = refs(row["References"])
        assert len(designators) == int(row["Quantity per board"])
        if designators == ["LCD1"]:
            assert row["Manufacturer part number"] == bom["LCD1"]["Manufacturer part number"]
            assert row["Supplier"] == "External panel" and not row["Extended INR"]
            external_panel.extend(designators)
            continue
        for ref in designators:
            assert ref in needed and ref not in priced, ref
            priced.add(ref)
            pricing[ref] = row
            assert row["Manufacturer part number"] == bom[ref]["Manufacturer part number"], ref
        if row["Unit INR"]:
            assert row["Price source"] and row["Checked IST"] and row["Applied tier"]
            if row["Applied currency"] == "USD":
                assert cents(Decimal(row["Applied unit"]) * Decimal("92.67")) == Decimal(row["Unit INR"])
            else:
                assert row["Applied currency"] == "INR"
                assert cents(row["Applied unit"]) == Decimal(row["Unit INR"])
            extended = Decimal(row["Unit INR"]) * len(designators)
            assert extended == Decimal(row["Extended INR"])
            total += extended
        else:
            assert not row["Extended INR"]
            missing.extend(designators)
    assert priced == needed
    assert external_panel == ["LCD1"]
    tail = cost_rows[-1]
    assert tail["References"] == "TOTAL" and int(tail["Quantity per board"]) == len(needed)
    assert Decimal(tail["Extended INR"]) == total
    bypass = {ref for ref, row in before_bom.items()
              if row["Manufacturer part number"] == "GRM155R71E104KE14D"}
    assert len(bypass) == 32 and bypass <= priced
    print(f"{len(priced)} fitted main-board and cell refs entered once. Itemized price coverage {len(priced)-len(missing)}.")
    print(f"Recomputed priced subtotal INR {total:.2f}. Unpriced refs {', '.join(missing) or 'none'}.")
    print("32 0402 100 nF locations accounted for, including four Ethernet positions.")

    changed = {ref for ref, old in before_bom.items()
               if bom[ref]["Manufacturer part number"] != old["Manufacturer part number"]}
    evidence = {}
    for row in rows(HERE / "tools" / "substitution-evidence.csv"):
        for ref in refs(row["Refs"]):
            assert ref not in evidence
            assert row["Old MPN"] == before_bom[ref]["Manufacturer part number"]
            assert row["New MPN"] == bom[ref]["Manufacturer part number"]
            assert all(row[k] for k in ("Old datasheet", "New datasheet", "Land and pin check", "Ratings checked"))
            evidence[ref] = row
    assert set(evidence) == changed
    print(f"{len(changed)} MPN changes have supplier and engineering evidence.")

    path = HERE / f"{prefix}-Build-Configurator.html"
    html = path.read_text()
    assert HOLD_MARK in html
    embedded, = re.findall(r'<script[^>]+id="pcb-data"[^>]*>(.*?)</script>', html, re.S)
    data = json.loads(embedded)
    assert data["fullMainLow"] == data["fullMainCost"] == int(total * 100)
    hmi = {r["ref"]: r for r in data["parts"] if r["board"] == "HMI"}
    assert hmi["R68"]["description"] == bom["R68"]["Description"]
    for ref in needed:
        assert hmi[ref]["mpn"] == bom[ref]["Manufacturer part number"], ref
        value = pricing[ref]["Unit INR"]
        assert hmi[ref]["cost"] == (int(Decimal(value) * 100) if value else None), ref
    print("Configurator uses the same fitted MPNs, prices and subtotal as the CSVs.")

    with ZipFile(HERE / f"{prefix}-EasyEDA-{HOLD_SUFFIX}.zip") as archive:
        files = {f"{kind}_{prefix}-{HOLD_SUFFIX}.json" for kind in cad}
        assert set(archive.namelist()) == files and archive.testzip() is None
        assert archive.comment.decode("ascii").startswith(HOLD_MARK)
        assert all(archive.read(name) == (HERE / name).read_bytes() for name in files)
        print("ZIP contains the byte-identical schematic and PCB JSONs.")
    original = (BASE / "PCB_Industrial-HMI-RevM-Draft.json").read_bytes()
    print(f"Baseline PCB SHA-256 {hashlib.sha256(original).hexdigest()}")
    print("Offline draft comparisons passed. FABRICATION BLOCKED. Native EasyEDA import, ERC, DRC, CAM and hardware checks remain open.")


if __name__ == "__main__":
    main()
