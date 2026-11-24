#!/usr/bin/env python3
"""Build one distributable ZIP per skill in this workspace."""

import argparse
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile


WORKSPACE = Path(__file__).resolve().parent
SKILL_DIRECTORIES = {"agents", "assets", "references", "scripts"}
SKILL_FILES = {"skill.md", "readme.md", "license", "notice", "copying"}
LOCAL_DIRECTORIES = {
    "__macosx", "__pycache__", "artifacts", "build", "dist", "downloads", "node_modules",
    "pcb-ebooks", "pcb-reference-library", "tests", "venv",
}
LOCAL_SUFFIXES = (
    ".pdf", ".epub", ".mobi", ".pyc", ".pyo", ".db", ".db-wal", ".db-shm",
    ".sqlite", ".sqlite-wal", ".sqlite-shm", ".sqlite3", ".sqlite3-wal", ".sqlite3-shm",
    ".jsonl", ".log", ".zip", ".tar", ".tar.gz", ".tgz", ".7z", ".rar",
)


def is_skill(path):
    manifest = path / "SKILL.md"
    return (not path.name.startswith(".") and not path.is_symlink()
            and manifest.is_file() and not manifest.is_symlink())


def skill_files(skill):
    for directory, folders, files in os.walk(skill):
        folder = Path(directory)
        folders[:] = sorted(name for name in folders if not name.startswith(".")
                            and name.lower() not in LOCAL_DIRECTORIES
                            and not (folder / name).is_symlink()
                            and (folder != skill or name in SKILL_DIRECTORIES))
        for name in sorted(files):
            path = folder / name
            lower = name.lower()
            if name.startswith(".") or lower.endswith(LOCAL_SUFFIXES) or path.is_symlink():
                continue
            if folder == skill and lower not in SKILL_FILES and not lower.startswith("license."):
                continue
            if path.is_file():
                yield path


def zip_skill(skill, output):
    destination = output / f"{skill.name}.zip"
    with NamedTemporaryFile(dir=output, prefix=".skill-zip-", delete=False) as temporary:
        staging = Path(temporary.name)
    try:
        with ZipFile(staging, "w", compression=ZIP_DEFLATED) as archive:
            for file in skill_files(skill):
                archive.write(file, file.relative_to(skill.parent).as_posix())
        staging.replace(destination)
    finally:
        staging.unlink(missing_ok=True)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skills", nargs="*", help="skill folder names (default: all workspace skills)")
    parser.add_argument("--output-dir", type=Path, default=WORKSPACE / "dist", help="ZIP destination")
    args = parser.parse_args()
    names = args.skills or sorted(path.name for path in WORKSPACE.iterdir() if is_skill(path))
    if not names:
        parser.error("no workspace skills found")
    for name in names:
        if Path(name).name != name or not is_skill(WORKSPACE / name):
            parser.error(f"not a workspace skill: {name}")

    output = args.output_dir.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    for name in dict.fromkeys(names):
        print(zip_skill(WORKSPACE / name, output))


if __name__ == "__main__":
    main()
