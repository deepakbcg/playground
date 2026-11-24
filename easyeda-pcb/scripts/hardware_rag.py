#!/usr/bin/env python3
"""Download selected hardware references and retrieve cited passages from a local index."""

import argparse
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
from http.client import HTTPException
from io import BytesIO
import json
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import sys
from tempfile import NamedTemporaryFile
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from zipfile import BadZipFile, ZipFile
from zlib import error as ZipCompressionError


MIB = 1024 * 1024
DOWNLOAD_LIMIT = 128 * MIB
ZIP_MEMBER_LIMIT = 24 * MIB
ZIP_TEXT_LIMIT = 96 * MIB
ZIP_ENTRY_LIMIT = 10000
FORMATS = {"pdf", "zip", "html", "text", "artifact"}
KINDS = ("guide", "datasheet", "errata", "reference-design")
SUFFIX_FORMAT = {
    ".pdf": "pdf", ".zip": "zip", ".html": "html", ".htm": "html",
    ".txt": "text", ".md": "text", ".rst": "text", ".csv": "text",
}
BLOB_SUFFIX = {"pdf": ".pdf", "zip": ".zip", "html": ".html", "text": ".txt", "artifact": ".bin"}
EBOOKS = {
    "cadence": (
        "cadence-pcb-design-from-start-to-finish.pdf",
        "https://content.cdntwrk.com/files/"
        "aT0xNDc2NTEwJnY9MSZpc3N1ZU5hbWU9cGNiLWRlc2lnbi1mcm9tLXN0YXJ0LXRvLWZpbmlzaCZjbWQ9"
        "ZCZzaWc9MjYxMGE4NjM2N2JkNThmYTE1NjFhYjY0NDhmNTU2MTI%253D",
    ),
    "pfeil": (
        "pfeil-high-speed-constraint-values-3rd-edition.pdf",
        "https://pcea.net/wp-content/uploads/2024/05/High-Speed-Constraint-Values-v3a-Pfeil.pdf",
    ),
    "resso-bogatin": (
        "resso-bogatin-signal-integrity-characterization-techniques-2nd-edition.pdf",
        "https://drive.usercontent.google.com/download"
        "?id=1t1JiVT42vBhY9fld_-bUXY9wzxis-Ov3&export=download&confirm=t",
    ),
    "ti-emi": (
        "ti-engineers-guide-to-low-emi-in-dc-dc-regulators.pdf",
        "https://www.ti.com/lit/eb/slyy208/slyy208.pdf",
    ),
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    vendor TEXT NOT NULL,
    title TEXT NOT NULL,
    kind TEXT NOT NULL,
    revision TEXT NOT NULL,
    parts TEXT NOT NULL,
    url TEXT,
    resolved_url TEXT,
    original_name TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    artifact TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    assets TEXT NOT NULL,
    warnings TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS sources_vendor ON sources(vendor, kind);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(
    title, parts, text, source_id UNINDEXED, locator UNINDEXED, content_type UNINDEXED
);
"""

RESULT_FIELDS = """
sources.id AS source_id, sources.vendor, sources.title, sources.kind, sources.revision,
sources.parts, sources.url, sources.resolved_url, sources.original_name, sources.artifact,
sources.sha256, sources.ingested_at, chunks.locator, chunks.content_type, chunks.text
"""


@dataclass(frozen=True)
class Source:
    id: str
    vendor: str
    title: str
    kind: str
    revision: str
    parts: list
    url: str = ""
    path: str = ""
    format: str = ""
    sha256: str = ""


@dataclass(frozen=True)
class Chunk:
    locator: str
    text: str
    content_type: str = "text"


def check_url(url):
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username is not None
            or parsed.password is not None):
        raise ValueError("source URLs must use HTTPS and contain no credentials")
    return url


class HTTPSRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return super().redirect_request(req, fp, code, msg, headers, check_url(newurl))


def read_limited(stream, limit):
    data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"file exceeds the {limit // MIB} MiB limit")
    if not data:
        raise ValueError("file is empty")
    return data


def download(url, limit=DOWNLOAD_LIMIT):
    request = Request(check_url(url), headers={"User-Agent": "EasyEDA-Hardware-Reference/1.0"})
    with build_opener(HTTPSRedirects()).open(request, timeout=45) as response:
        data = read_limited(response, limit)
        return data, response.geturl(), response.headers.get_content_type()


class PageParser(HTMLParser):
    omitted = {"script", "style", "nav", "header", "footer", "noscript", "template", "svg", "head"}
    blocks = {"p", "li", "div", "section", "tr", "td", "th", "br", "h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = []
        self.text = []
        self.links = []
        self.anchor = None

    def handle_starttag(self, tag, attrs):
        if tag in self.omitted:
            self.skip.append(tag)
        if self.skip:
            return
        if tag in self.blocks:
            self.text.append("\n")
        if tag == "a":
            self.anchor = (dict(attrs).get("href"), [])

    def handle_endtag(self, tag):
        if self.skip:
            if tag == self.skip[-1]:
                self.skip.pop()
            return
        if tag in self.blocks:
            self.text.append("\n")
        if tag == "a" and self.anchor is not None:
            href, label = self.anchor
            if href:
                self.links.append((href, " ".join("".join(label).split())))
            self.anchor = None

    def handle_data(self, data):
        if not self.skip:
            self.text.append(data)
            if self.anchor is not None:
                self.anchor[1].append(data)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)


def parse_html(data):
    parser = PageParser()
    parser.feed(data.decode("utf-8-sig", errors="replace"))
    parser.close()
    return parser


def suffix_format(name):
    return SUFFIX_FORMAT.get(PurePosixPath(name).suffix.lower())


def detect_format(data, name, mime, expected):
    start = data[:4096].removeprefix(b"\xef\xbb\xbf").lstrip()
    if data.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
        detected = "zip"
    elif start.startswith(b"%PDF-"):
        detected = "pdf"
    elif mime in {"text/html", "application/xhtml+xml"} or re.match(
        rb"(?is)(?:<!--.*?-->\s*)*(?:<!doctype\s+html\b|<(?:html|head|body)\b)", start
    ):
        detected = "html"
    elif mime.startswith("text/") or expected == "text" or suffix_format(name) == "text":
        if b"\0" in start:
            raise ValueError("the selected text file contains binary data")
        detected = "text"
    else:
        detected = "artifact"
    if expected and detected != expected:
        raise ValueError(f"expected {expected}, received {detected}. Check the publisher URL or local file")
    return detected


def text_chunks(text, locator, content_type="text"):
    words = list(re.finditer(r"\S+", text))
    for start in range(0, len(words), 220):
        end = min(start + 260, len(words))
        position = f"{locator}, passage {start // 220 + 1}" if len(words) > 260 else locator
        yield Chunk(position, text[words[start].start():words[end - 1].end()], content_type)
        if end == len(words):
            break


def document_chunks(data, file_format, locator, warnings):
    if file_format == "pdf":
        try:
            from pypdf import PdfReader
            from pypdf.errors import PyPdfError
        except ImportError:
            warnings.append(f"{locator}: install pypdf and re-ingest to index PDF text")
            return
        try:
            reader = PdfReader(BytesIO(data))
            if reader.is_encrypted:
                warnings.append(f"{locator}: PDF is encrypted")
                return
            found = False
            for page_number, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                if text.strip():
                    found = True
                    yield from text_chunks(text, f"{locator}, PDF page {page_number}")
            if not found:
                warnings.append(f"{locator}: PDF has no extractable text. Supply an OCR text layer or notes")
        except (PyPdfError, ValueError, OSError, NotImplementedError) as error:
            warnings.append(f"{locator}: PDF text extraction stopped ({error})")
        return

    text = "".join(parse_html(data).text) if file_format == "html" else data.decode(
        "utf-8-sig", errors="replace"
    )
    if text.strip():
        yield from text_chunks(text, locator)
    else:
        warnings.append(f"{locator}: no extractable text")


def zip_chunks(data, warnings):
    assets = []
    chunks = []
    remaining = ZIP_TEXT_LIMIT
    with ZipFile(BytesIO(data)) as archive:
        entries = archive.infolist()
        if len(entries) > ZIP_ENTRY_LIMIT:
            raise ValueError(f"ZIP exceeds the {ZIP_ENTRY_LIMIT} member limit")
        for entry in entries:
            member = PurePosixPath(entry.filename)
            if entry.is_dir() or "__MACOSX" in member.parts or member.name.startswith("._"):
                continue
            assets.append({"name": entry.filename, "bytes": entry.file_size})
            member_format = suffix_format(entry.filename)
            if member_format not in {"pdf", "html", "text"} or not entry.file_size:
                continue
            if entry.file_size > min(remaining, ZIP_MEMBER_LIMIT):
                warnings.append(f"{entry.filename}: exceeds the ZIP text inspection budget")
                continue
            # Read members into memory using ZipInfo. No member paths are written to disk.
            remaining -= entry.file_size
            try:
                with archive.open(entry) as stream:
                    member_data = read_limited(stream, ZIP_MEMBER_LIMIT)
                actual = detect_format(member_data, entry.filename, "", member_format)
                chunks.extend(document_chunks(member_data, actual, entry.filename, warnings))
            except (BadZipFile, RuntimeError, ValueError, OSError, ZipCompressionError) as error:
                warnings.append(f"{entry.filename}: skipped ({error})")
    manifests = "\n".join(asset["name"] for asset in assets)
    chunks.extend(text_chunks(manifests, "ZIP member inventory", "inventory"))
    return assets, chunks


def load_manifest(path):
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or not isinstance(manifest.get("sources"), list):
        raise ValueError("manifest must contain a sources array")
    sources = []
    ids = set()
    for item in manifest["sources"]:
        try:
            source = Source(**item)
        except TypeError as error:
            raise ValueError(f"invalid source entry: {error}") from error
        for field in ("id", "vendor", "title", "kind", "revision"):
            value = getattr(source, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"source {field} must be a nonempty string")
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,100}", source.id) or source.id in ids:
            raise ValueError(f"invalid or duplicate source id {source.id!r}")
        if source.kind not in KINDS:
            raise ValueError(f"{source.id}: unsupported source kind {source.kind!r}")
        if not isinstance(source.parts, list) or not all(
            isinstance(part, str) and part.strip() for part in source.parts
        ):
            raise ValueError(f"{source.id}: parts must be an array of nonempty strings")
        if not all(isinstance(getattr(source, field), str) for field in ("path", "url", "format", "sha256")):
            raise ValueError(f"{source.id}: path, url, format and sha256 must be strings")
        if source.format and source.format not in FORMATS:
            raise ValueError(f"{source.id}: unsupported file format {source.format!r}")
        if source.sha256 and not re.fullmatch(r"[0-9a-fA-F]{64}", source.sha256):
            raise ValueError(f"{source.id}: sha256 must contain 64 hexadecimal characters")
        if source.url:
            check_url(source.url)
        elif not source.path:
            raise ValueError(f"{source.id}: supply a URL or a local path")
        if not source.path and not source.format and not suffix_format(urlsplit(source.url).path):
            raise ValueError(f"{source.id}: set format for extensionless or unrecognized download URLs")
        sources.append(source)
        ids.add(source.id)
    if not sources:
        raise ValueError("manifest contains no sources")
    return sources


def write_file(target, data, *, replace=False):
    with NamedTemporaryFile(dir=target.parent, delete=False) as staging:
        staged = Path(staging.name)
        try:
            staging.write(data)
            staging.close()
            if replace:
                staged.replace(target)
            else:
                # Publish the complete file without replacing a destination created concurrently.
                os.link(staged, target)
        finally:
            staged.unlink(missing_ok=True)


def save_blob(library, data, digest, file_format):
    path = Path("artifacts") / (digest + BLOB_SUFFIX[file_format])
    target = library / path
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        write_file(target, data, replace=True)
    return path.as_posix()


def ingest_source(db, library, source, manifest_dir):
    if source.path:
        local = manifest_dir / source.path
        original_name, resolved, mime = local.name, None, ""
        with local.open("rb") as stream:
            data = read_limited(stream, DOWNLOAD_LIMIT)
    else:
        data, resolved, mime = download(source.url)
        original_name = PurePosixPath(urlsplit(resolved).path).name or source.id
    expected = source.format or suffix_format(source.path or urlsplit(source.url).path)
    file_format = detect_format(data, original_name, mime, expected)
    digest = sha256(data).hexdigest()
    if source.sha256 and digest != source.sha256.lower():
        raise ValueError(f"source checksum mismatch. Received SHA-256 {digest}")
    warnings = []
    assets = []
    if file_format == "zip":
        assets, chunks = zip_chunks(data, warnings)
    elif file_format == "artifact":
        chunks = []
    else:
        chunks = list(document_chunks(data, file_format, original_name, warnings))

    text_count = sum(chunk.content_type == "text" for chunk in chunks)
    if not text_count:
        warnings.append("No document text indexed. The original and any inventory are available for inspection")
    chunks.insert(0, Chunk(
        "Source metadata", f"{source.title}\n{original_name}\n{source.revision}", "metadata"
    ))
    with db:
        db.execute("BEGIN IMMEDIATE")
        if not text_count and db.execute(
            "SELECT 1 FROM chunks WHERE source_id = ? AND content_type = 'text' LIMIT 1",
            (source.id,),
        ).fetchone():
            raise ValueError("update has no extractable text. The previous indexed source was retained")
        artifact = save_blob(library, data, digest, file_format)
        db.execute("DELETE FROM chunks WHERE source_id = ?", (source.id,))
        db.execute(
            "INSERT OR REPLACE INTO sources VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (source.id, source.vendor, source.title, source.kind, source.revision,
             json.dumps(source.parts), source.url or None, resolved, original_name, digest, artifact,
             datetime.now(timezone.utc).isoformat(), json.dumps(assets), json.dumps(warnings)),
        )
        db.executemany(
            "INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?)",
            ((source.title, " ".join(source.parts), chunk.text, source.id,
              chunk.locator, chunk.content_type) for chunk in chunks),
        )
    return {"source_id": source.id, "sha256": digest, "artifact": artifact,
            "text_chunks": text_count,
            "asset_count": len(assets), "warnings": warnings}


def json_rows(rows):
    for row in rows:
        record = dict(row)
        for field in ("parts", "assets", "warnings"):
            if field in record:
                record[field] = json.loads(record[field])
        if "locator" in record:
            key = [record[field] for field in ("source_id", "sha256", "locator", "text")]
            record["passage_id"] = sha256(json.dumps(key).encode()).hexdigest()
        yield record


def open_index(library):
    database = library / "index.sqlite3"
    if not database.is_file():
        raise ValueError("no index found. Ingest a source manifest first")
    db = sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    return db


def passages(db, *, query="", source=None, vendor=None, kind=None, part=None,
             content_type=None, limit=None):
    filters = []
    params = []
    keywords = re.findall(r"[^\W_]+", query.casefold())
    if keywords:
        # Quote user terms so raw FTS operators never become part of the expression.
        filters.append("chunks MATCH ?")
        params.append(" OR ".join(f'"{term}"' for term in dict.fromkeys(keywords)))
    if source:
        filters.append("sources.id = ?")
        params.append(source)
    if vendor:
        filters.append("lower(sources.vendor) = lower(?)")
        params.append(vendor)
    if kind:
        filters.append("sources.kind = ?")
        params.append(kind)
    if part:
        filters.append("EXISTS (SELECT 1 FROM json_each(sources.parts) WHERE lower(value) = lower(?))")
        params.append(part)
    if content_type:
        filters.append("chunks.content_type = ?")
        params.append(content_type)

    query = f"SELECT {RESULT_FIELDS} FROM chunks JOIN sources ON chunks.source_id = sources.id"
    if filters:
        query += " WHERE " + " AND ".join(filters)
    if keywords:
        query += " ORDER BY bm25(chunks, 1.0, 1.5, 4.0), chunks.rowid"
    else:
        query += " ORDER BY sources.id, chunks.rowid"
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
    return json_rows(db.execute(query, params))


def discover_links(url):
    data, resolved, mime = download(url, 8 * MIB)
    if detect_format(data, resolved, mime, "") != "html":
        raise ValueError("links expects a publisher HTML page")
    found = {}
    for href, label in parse_html(data).links:
        link = urljoin(resolved, href)
        try:
            check_url(link)
        except ValueError:
            continue
        file_format = suffix_format(urlsplit(link).path)
        if file_format in {"pdf", "zip"} or re.search(
            r"(?i)datasheet|data sheet|design files|schematics?|reference design|hardware (?:design |development )?guide",
            label,
        ):
            found[link] = {"url": link, "label": label, "format": file_format}
    return list(found.values())


def show_json(record):
    print(json.dumps(record, ensure_ascii=False, indent=2))


def verify_ebook_pdf(stream):
    header = stream.read(5)
    size = stream.seek(0, os.SEEK_END)
    stream.seek(max(0, size - 2048))
    if header != b"%PDF-" or b"%%EOF" not in stream.read():
        raise ValueError("expected a PDF with a complete file header and trailer")


def download_ebooks(output, books):
    output = output.expanduser().resolve()
    if output.is_relative_to(Path(__file__).resolve().parents[1]):
        raise ValueError("choose an ebook output directory outside the distributable skill")
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for book in dict.fromkeys(books or EBOOKS):
        filename, url = EBOOKS[book]
        target = output / filename
        result = {"book": book, "path": str(target)}
        try:
            if not target.exists() and not target.is_symlink():
                data, _, _ = download(url)
                verify_ebook_pdf(BytesIO(data))
                try:
                    write_file(target, data)
                except FileExistsError:
                    pass
                else:
                    results.append(dict(result, status="downloaded"))
                    continue
            if target.is_symlink() or not target.is_file():
                raise ValueError("ebook destination must be a regular PDF file")
            with target.open("rb") as stream:
                verify_ebook_pdf(stream)
            results.append(dict(result, status="already present"))
        except (OSError, ValueError, HTTPException) as error:
            results.append(dict(result, error=str(error)))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", help="corpus storage directory, or set EASYEDA_RAG_DIR",
                        default=os.environ.get("EASYEDA_RAG_DIR"))
    commands = parser.add_subparsers(dest="action", required=True)
    links = commands.add_parser("links", help="find candidate links on one publisher page")
    links.add_argument("url")
    ebooks = commands.add_parser("download-ebooks", help="download the free PCB ebooks to a separate folder")
    ebooks.add_argument("--output", required=True, type=Path, help="directory outside the skill")
    ebooks.add_argument("--book", action="append", choices=tuple(EBOOKS), help="select a title (repeatable)")
    ingest = commands.add_parser("ingest", help="ingest selected URLs or local files from a JSON manifest")
    ingest.add_argument("manifest", type=Path)
    inventory = commands.add_parser("list", help="list the active sources, assets and indexing warnings")
    inventory.add_argument("--source", help="show one manifest source ID")
    search = commands.add_parser("search", help="retrieve passages with source citations")
    search.add_argument("query", nargs="?", default="", help="plain-language search terms")
    search.add_argument("--source", help="filter by manifest source ID")
    search.add_argument("--vendor", help="filter by the exact vendor field")
    search.add_argument("--part", help="filter by an exact manifest part or family tag")
    search.add_argument("--kind", choices=KINDS)
    search.add_argument("--content-type", choices=("text", "inventory", "metadata"))
    search.add_argument("--limit", type=int, default=8)
    export = commands.add_parser("export", help="emit all active retrieval records as JSON Lines")
    export.add_argument("--source", help="export one manifest source ID")
    args = parser.parse_args()
    if args.action not in {"links", "download-ebooks"} and not args.library:
        parser.error("set --library or EASYEDA_RAG_DIR")
    if args.action == "search":
        if not 1 <= args.limit <= 1000:
            parser.error("--limit must be between 1 and 1000")
        if args.query and not re.search(r"[^\W_]", args.query):
            parser.error("query must contain letters or digits")

    try:
        if args.action == "links":
            show_json(discover_links(args.url))
            return 0
        if args.action == "download-ebooks":
            results = download_ebooks(args.output, args.book)
            show_json(results)
            return int(any("error" in result for result in results))
        library = Path(args.library).expanduser().resolve()
        database = library / "index.sqlite3"
        if args.action == "ingest":
            sources = load_manifest(args.manifest)
            library.mkdir(parents=True, exist_ok=True)
            outcomes = []
            failures = 0
            with closing(sqlite3.connect(database, timeout=30)) as db:
                db.executescript(SCHEMA)
                for source in sources:
                    try:
                        outcomes.append(ingest_source(db, library, source, args.manifest.parent))
                    except (BadZipFile, OSError, ValueError, sqlite3.Error, HTTPException) as error:
                        failures += 1
                        outcomes.append({"source_id": source.id, "error": str(error)})
            show_json(outcomes)
            return int(bool(failures))

        with closing(open_index(library)) as db:
            if args.action == "list":
                rows = db.execute(
                    "SELECT * FROM sources WHERE (? IS NULL OR id = ?) ORDER BY id",
                    (args.source, args.source),
                )
                show_json(list(json_rows(rows)))
            elif args.action == "search":
                show_json(list(passages(db, query=args.query, source=args.source, vendor=args.vendor,
                                        kind=args.kind, part=args.part, content_type=args.content_type,
                                        limit=args.limit)))
            else:
                for record in passages(db, source=args.source):
                    print(json.dumps(record, ensure_ascii=False))
    except (BadZipFile, OSError, ValueError, sqlite3.Error, HTTPException) as error:
        print(f"Hardware RAG: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
