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
    "BZ1": ("5 V active buzzer", "12 mm 5 V active magnetic buzzer"),
    "C85": ("33 µF 16 V", "47 µF 16 V"),
    "C86": ("33 µF 16 V", "47 µF 16 V"),
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
CHECKPOINT_PCB_SHA256 = "abff5f3eb8ef2f6e672cd597d545dd7fd53c788953bd98c647032aafd008a2a2"
PASSIVE_0402_PACKAGES = {
    "0402", "C0402", "R0402", "GENERIC_CAPC1005X50", "GENERIC_CAPC1005X50_WIDE",
    "GENERIC_RESC1005X35", "SMT-100-nF", "SMT-100-k", "SMT-47-k",
}
PASSIVE_0603_PACKAGES = {"0603", "C0603", "R0603"}
RESTORED_0402 = set("C14 C39 C40 C68 C69 C70 C71 C72 C73 R12 R57 R58 R59 R60 R61 R63".split())
BUZZER_FOOTPRINT = "BUZZER-D12-P7.6-PTH"
BUZZER_FOOTPRINT_FILE = f"Footprint_{BUZZER_FOOTPRINT}.json"
ORIGINAL_BUZZER_FOOTPRINT_ID = "e44ef8f6a948552589cda44d2e5dd065"
FIELD_ZENERS = {"D11", "D14", "D17", "D20"}


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


def geometry(doc, sch, worklist=None):
    specific = {"Title", "Release status"}
    stable = {key: value for key, value in doc.items() if key not in {"head", "shape"}}
    stable["head"] = {**doc["head"], "c_para": {
        key: value for key, value in doc["head"]["c_para"].items() if key not in specific
    }}
    new_shapes = list(doc["shape"])
    for ref, (i, header, body) in components(doc, sch).items():
        attributes = attrs(header)
        if sch and worklist and ref in worklist:
            entry = worklist[ref]
            assert attributes["package"] == entry["New footprint"], ref
            attributes["package"] = entry["Old footprint"]
        if sch and ref == "BZ1" and attributes["package"] == BUZZER_FOOTPRINT:
            attributes["package"] = "PUI-AI-1027-P5.0"
            header[7] = ORIGINAL_BUZZER_FOOTPRINT_ID
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


def verify_buzzer_footprint(cad):
    footprint = json.loads((HERE / BUZZER_FOOTPRINT_FILE).read_bytes())
    head = footprint["head"]
    assert head["docType"] == "4" and head["c_para"]["package"] == BUZZER_FOOTPRINT
    assert head["uuid"] == cad["Schematic"]["BZ1"][1][7]
    pads = {fields[8]: fields for fields in map(lambda s: s.split("~"), footprint["shape"])
            if fields[0] == "PAD"}
    assert pads.keys() == {"1", "2"}
    assert pads["1"][1] == "RECT" and pads["1"][4] == pads["1"][5]
    assert pads["2"][1] == "ELLIPSE" and pads["1"][2] == pads["2"][2]
    scale = Decimal("0.254")
    pitch = abs(Decimal(pads["1"][3]) - Decimal(pads["2"][3])) * scale
    assert cents(pitch) == Decimal("7.60")
    for pad in pads.values():
        assert pad[6] == "11" and pad[15] == "Y"
        assert cents(2 * Decimal(pad[9]) * scale) == Decimal("1.00")
    current_nets = {p[8]: p[7] for p in (s.split("~") for s in cad["PCB"]["BZ1"][2]) if p[0] == "PAD"}
    assert current_nets == {"1": "SYS_5V", "2": "BUZZ_LOW"}
    print("BZ1 editor footprint checks passed. 7.60 mm pitch, 1.00 mm PTH, square positive pad 1 on SYS_5V.")


def verify_purchase(pricing):
    purchase = rows(HERE / "PURCHASE-LIST.csv")
    covered, mpns = set(), set()
    subtotals = {}
    pending = Decimal(0)
    supplier = None
    for row in purchase[:-1]:
        name = row["Supplier"]
        assert name and row["Checked IST"] and row["Source URL"]
        assert supplier is None or name == supplier
        assert name not in subtotals
        if row["Row type"] == "Supplier subtotal":
            assert Decimal(row["Line INR"]) == pending and row["Notes"]
            subtotals[name] = pending
            pending = Decimal(0)
            supplier = None
            continue
        supplier = name
        assert row["Row type"] == "Part" and row["Supplier code"]
        designators = refs(row["References"])
        mpn = row["Manufacturer part number"]
        assert mpn not in mpns and covered.isdisjoint(designators)
        mpns.add(mpn)
        covered.update(designators)
        part = pricing[designators[0]]
        assert all(pricing[ref] == part for ref in designators)
        assert mpn == ("2354" if designators == ["LCD1"] else part["Manufacturer part number"])
        quantity = int(row["Order quantity"])
        stock = int(row["Stock shown"])
        units = len(designators) * 3
        assert int(row["Per board"]) == len(designators) and int(row["Three boards"]) == units
        assert int(row["Minimum spares"]) >= (units + 9) // 10
        assert stock >= quantity >= max(int(row["MOQ"]), units + int(row["Minimum spares"]))
        assert quantity % int(row["Order multiple"]) == 0
        assert row["Currency"] in {"INR", "USD"}
        unit = Decimal(row["Quoted unit"]) * (Decimal("92.67") if row["Currency"] == "USD" else 1)
        if all(re.fullmatch(r"(?:C|R|FB|L)\d+", ref) for ref in designators) and unit < 1:
            assert quantity >= units + 2
        assert cents(unit) == cents(row["Unit INR"])
        subtotal = cents(unit * quantity)
        assert subtotal == Decimal(row["Line INR"])
        pending += subtotal
        if set(designators) == FIELD_ZENERS:
            assert name in {"LCSC", "DigiKey India", "Mouser India"} and stock >= 50
    assert covered == pricing.keys() and supplier is None
    total = sum(subtotals.values())
    assert purchase[-1]["Row type"] == "Overall subtotal" and total == Decimal(purchase[-1]["Line INR"])
    print(f"Purchase list covers {len(mpns)} orderables. MOQ, stock, spares and line totals verified. INR {total:.2f}.")


def main():
    prefix = "Industrial-HMI-RevN"
    worklist_rows = rows(HERE / "0603-WORKLIST.csv")
    worklist = {row["Ref"]: row for row in worklist_rows}
    assert len(worklist_rows) == len(worklist)
    cad = {}
    for kind in ("Schematic", "PCB"):
        before = json.loads((BASE / f"{kind}_Industrial-HMI-RevM-Draft.json").read_bytes())
        after_bytes = (HERE / f"{kind}_{prefix}-{HOLD_SUFFIX}.json").read_bytes()
        after = json.loads(after_bytes)
        is_schematic = kind == "Schematic"
        before_geometry = geometry(before, is_schematic)
        after_geometry = geometry(after, is_schematic, worklist)
        normalize_u1(before_geometry, after_geometry, is_schematic)
        assert before_geometry == after_geometry, kind
        params = after["head"]["c_para"]
        assert params["Title"].startswith(HOLD_MARK) and "Rev N" in params["Title"]
        assert params["Release status"].startswith(HOLD_MARK) and "U1.1" in params["Release status"]
        if is_schematic:
            labels = [s for s in after["shape"] if s.startswith("T~L~")]
            assert sum(f"~{HOLD_MARK} - {SCH_TITLE}~" in s for s in labels) == 1
        else:
            assert hashlib.sha256(after_bytes).hexdigest() == CHECKPOINT_PCB_SHA256
            print(f"PCB is byte-identical to the Rev N checkpoint. SHA-256 {CHECKPOINT_PCB_SHA256}")
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
    assert bom["BZ1"]["Manufacturer part number"] == "TMB12A05"
    assert all(bom[ref]["Manufacturer part number"] == "BZT52B8V2-AQ" for ref in FIELD_ZENERS)
    for ref in ("C85", "C86"):
        assert bom[ref]["Manufacturer part number"] == "CL32A476KOJNNNE"
        assert attrs(cad["Schematic"][ref][1])["name"] == bom[ref]["Description"] == "47 µF 16 V"
    _, r68_head, r68_body = cad["Schematic"]["R68"]
    assert attrs(r68_head)["name"] == bom["R68"]["Description"]
    assert [line.split("~")[12] for line in r68_body if line.startswith("T~N~")] == ["91 kΩ"]
    for ref in ("C68", "C69"):
        assert bom[ref]["Description"] == before_bom[ref]["Description"] and "18 pF" in bom[ref]["Description"]
    mismatched_footprints = set()
    before_sizes, after_sizes = Counter(), Counter()
    for ref in cad["PCB"]:
        row = bom[ref]
        mpn = row["Manufacturer part number"]
        schematic = attrs(cad["Schematic"][ref][1])
        pcb = attrs(cad["PCB"][ref][1])
        before_footprint, after_footprint = pcb["package"], schematic["package"]
        if ref.startswith("TP"):
            assert not mpn and row["Population"] == "DNP"
        if ref in LOCKED:
            assert mpn == before_bom[ref]["Manufacturer part number"], ref
        assert schematic["BOM_Manufacturer Part"] == mpn, ref
        assert schematic.get("BOM_Supplier Part", "") == row["LCSC part"] or row["Population"] == "DNP", ref
        assert after_footprint == row["Footprint"], ref
        if ref in RESTORED_0402:
            assert after_footprint == before_footprint and after_footprint in PASSIVE_0402_PACKAGES, ref
        if before_footprint != after_footprint:
            mismatched_footprints.add(ref)
            if ref == "BZ1":
                assert before_footprint == "PUI-AI-1027-P5.0" and after_footprint == BUZZER_FOOTPRINT
            else:
                assert before_footprint == worklist[ref]["Old footprint"] and before_footprint in PASSIVE_0402_PACKAGES
                assert after_footprint == worklist[ref]["New footprint"] == "0603"
                assert row["Population"].startswith("Fit") and ref.startswith(("R", "C", "FB"))
        if row["Population"].startswith("Fit") and ref.startswith(("R", "C", "FB")):
            for footprint, count in ((before_footprint, before_sizes), (after_footprint, after_sizes)):
                if footprint in PASSIVE_0402_PACKAGES:
                    count["0402"] += 1
                if footprint in PASSIVE_0603_PACKAGES:
                    count["0603"] += 1
        if not ref.startswith(("R", "C", "FB")):
            checkpoint_mpn = ("AI-1027-TWT-5V-R" if ref == "BZ1" else
                              "BZT52H-B8V2-QX" if ref in FIELD_ZENERS else mpn)
            assert pcb["BOM_Manufacturer Part"] == checkpoint_mpn, ref
    assert mismatched_footprints == worklist.keys() | {"BZ1"}
    assert not RESTORED_0402 & worklist.keys()
    print(f"Schematic, PCB and BOM agree on {len(cad['PCB'])} designators. TP1–TP4 are DNP.")
    print(f"{len(worklist)} passive footprint changes in 0603-WORKLIST.csv. BZ1 is listed in the PCB editor tasks.")
    verify_buzzer_footprint(cad)
    print(f"Fitted passive packages 0402 {before_sizes['0402']} → {after_sizes['0402']}, "
          f"0603 {before_sizes['0603']} → {after_sizes['0603']}.")
    print("Panel and battery are external to the CAD refdes sets.")

    needed = {ref for ref, row in bom.items() if row["Population"].startswith("Fit")}
    priced = set()
    total = Decimal(0)
    cost_rows = rows(HERE / f"{prefix}-BOM-Cost-INR.csv")
    retail_status = Counter()
    pricing = {}
    for row in cost_rows[:-1]:
        designators = refs(row["References"])
        assert len(designators) == int(row["Quantity per board"])
        for ref in designators:
            assert row["LCSC part"] == bom[ref]["LCSC part"], ref
            assert bom[ref]["Footprint"] in row["Footprint"].split(" / "), ref
        assert len({bom[ref]["Footprint"] for ref in designators}) == len(row["Footprint"].split(" / "))
        stock, code = row["LCSC retail stock"], row["LCSC part"]
        if stock.isdecimal():
            assert code and row["LCSC stock checked IST"]
            expected = "Meets 1,000" if int(stock) >= 1000 else "Below 1,000"
            if expected == "Below 1,000":
                assert "LCSC below 1,000." in row["Notes"], designators
        else:
            assert not stock
            expected = "Listing unavailable" if code else "No LCSC code"
        assert row["LCSC stock status"] == expected, designators
        retail_status[expected] += 1
        for ref in designators:
            assert ref in needed and ref not in priced, ref
            priced.add(ref)
            pricing[ref] = row
            assert row["Manufacturer part number"] == bom[ref]["Manufacturer part number"], ref
        assert row["Unit INR"] and row["Price source"] and row["Checked IST"] and row["Applied tier"], designators
        if row["Applied currency"] == "USD":
            assert cents(Decimal(row["Applied unit"]) * Decimal("92.67")) == Decimal(row["Unit INR"])
        else:
            assert row["Applied currency"] == "INR"
            assert cents(row["Applied unit"]) == Decimal(row["Unit INR"])
        extended = Decimal(row["Unit INR"]) * len(designators)
        assert extended == Decimal(row["Extended INR"])
        if designators != ["LCD1"]:
            total += extended
        if row["Stock listed"].isdigit() and int(row["Stock listed"]) < 100:
            assert "LOW STOCK" in row["Notes"], designators
    assert priced == needed
    tail = cost_rows[-1]
    assert tail["References"] == "TOTAL" and int(tail["Quantity per board"]) == len(needed) - 1
    assert Decimal(tail["Extended INR"]) == total
    bypass = {ref for ref, row in before_bom.items()
              if row["Manufacturer part number"] == "GRM155R71E104KE14D"}
    assert len(bypass) == 32 and bypass <= priced
    print(f"All {len(priced)} fitted refs priced, including the separately priced LCD.")
    print(f"Recomputed board and cell subtotal INR {total:.2f}.")
    print("LCSC retail line counts " + ", ".join(f"{key} {value}" for key, value in sorted(retail_status.items())) + ".")
    print("32 original 0402 bypass locations accounted for, including four Ethernet positions.")
    verify_purchase(pricing)

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
        field = "panelCost" if ref == "LCD1" else "cost"
        assert hmi[ref][field] == int(Decimal(value) * 100), ref
    print("Configurator uses the same fitted MPNs, prices and subtotal as the CSVs.")

    with ZipFile(HERE / f"{prefix}-EasyEDA-{HOLD_SUFFIX}.zip") as archive:
        files = {f"{kind}_{prefix}-{HOLD_SUFFIX}.json" for kind in cad} | {BUZZER_FOOTPRINT_FILE}
        assert set(archive.namelist()) == files and archive.testzip() is None
        assert archive.comment.decode("ascii").startswith(HOLD_MARK)
        assert all(archive.read(name) == (HERE / name).read_bytes() for name in files)
        print("ZIP contains the exact schematic, PCB and BZ1 footprint JSONs.")
    from fit_0603 import calculate
    assert worklist_rows == [{key: str(value) for key, value in row.items()} for row in calculate()]
    fit_counts = Counter(row["Fit status"] for row in worklist_rows)
    print("0603 screen " + ", ".join(f"{status} {count}" for status, count in sorted(fit_counts.items())) + ".")
    original = (BASE / "PCB_Industrial-HMI-RevM-Draft.json").read_bytes()
    print(f"Baseline PCB SHA-256 {hashlib.sha256(original).hexdigest()}")
    print("Offline draft comparisons passed. FABRICATION BLOCKED. Native EasyEDA import, ERC, DRC, CAM and hardware checks remain open.")


if __name__ == "__main__":
    main()
