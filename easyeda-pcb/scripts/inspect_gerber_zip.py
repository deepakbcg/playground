#!/usr/bin/env python3
"""Check the filename inventory of an EasyEDA Gerber ZIP without extracting it."""

import argparse
from collections import defaultdict
from pathlib import PurePosixPath
import re
import sys
from zipfile import BadZipFile, ZipFile


NATIVE_FILES = {
    "gerber_boardoutline.gko": "outline",
    "gerber_toplayer.gtl": "top-copper",
    "gerber_bottomlayer.gbl": "bottom-copper",
    "gerber_topsoldermasklayer.gts": "top-mask",
    "gerber_bottomsoldermasklayer.gbs": "bottom-mask",
    "gerber_topsilklayer.gto": "top-silk",
    "gerber_bottomsilklayer.gbo": "bottom-silk",
    "gerber_toppastemasklayer.gtp": "top-paste",
    "gerber_bottompastemasklayer.gbp": "bottom-paste",
    "drill_pth_through.drl": "pth",
    "drill_pth_through_via.drl": "via-pth",
    "drill_npth_through.drl": "npth",
}
EXTRA_REQUIREMENTS = (
    "top-mask", "bottom-mask", "top-silk", "bottom-silk",
    "top-paste", "bottom-paste", "pth", "npth",
)
INNER_LAYER = re.compile(r"gerber_innerlayer([1-9][0-9]*)\.gp?\1")


def file_role(filename):
    """Match documented native names, including legacy GP inner-layer suffixes."""
    name = PurePosixPath(filename).name.lower()
    inner = INNER_LAYER.fullmatch(name)
    if inner:
        return f"inner-{inner[1]}"
    return NATIVE_FILES.get(name)


def read_inventory(path):
    files_by_role = defaultdict(list)
    unclassified = []
    with ZipFile(path) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            role = file_role(member.filename)
            if role is None:
                unclassified.append(member.filename)
                continue
            files_by_role[role].append(member)
    return files_by_role, unclassified


def inventory_problems(files_by_role, layers, requirements):
    inner_layers = {f"inner-{number}" for number in range(1, layers - 1)}
    required = {"outline", "top-copper", "bottom-copper"} | inner_layers
    required.update(requirements)
    available = set(files_by_role)
    if "via-pth" in available:
        available.add("pth")

    for role in sorted(required - available):
        yield f"Missing required role {role}"
    for role in sorted(files_by_role):
        entries = files_by_role[role]
        if role.startswith("inner-") and role not in inner_layers:
            yield f"Unexpected copper role {role} for a {layers}-layer board"
        if len(entries) > 1:
            yield f"Multiple files for role {role}"
        for entry in entries:
            if entry.file_size == 0:
                yield f"Empty file for role {role}: {entry.filename!r}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", help="EasyEDA Gerber ZIP")
    parser.add_argument("--layers", type=int, choices=(2, 4, 6), required=True,
                        help="expected number of physical copper layers")
    parser.add_argument("--require", choices=EXTRA_REQUIREMENTS, action="append", default=[],
                        help="require an additional native file role (repeatable)")
    args = parser.parse_args()

    try:
        files_by_role, unclassified = read_inventory(args.archive)
    except (BadZipFile, OSError, UnicodeError) as error:
        print(f"Cannot read ZIP {args.archive!r}: {error}", file=sys.stderr)
        return 2

    for role, entries in sorted(files_by_role.items()):
        for entry in entries:
            print(f"{role}: {entry.filename!r} ({entry.file_size} bytes)")
    for name in sorted(unclassified):
        print(f"Unclassified, review if relevant: {name!r}")

    problems = list(inventory_problems(files_by_role, args.layers, args.require))
    if problems:
        for problem in problems:
            print(f"Inventory problem: {problem}")
        return 1

    print(f"Expected native filename roles present for {args.layers} copper layers.")
    print("Inspect file contents and layer mapping in a CAM viewer before release.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
