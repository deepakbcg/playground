#!/usr/bin/env python3
"""Serve a local EasyEDA hardware reference index over MCP stdio."""

import argparse
from contextlib import closing
import os
from pathlib import Path
import sqlite3
from typing import Annotated, Literal

from mcp.server import MCPServer
from mcp.types import ToolAnnotations
from pydantic import Field

from hardware_rag import json_rows, open_index, passages


def create_server(library):
    server = MCPServer("EasyEDA Hardware RAG")
    read_only = ToolAnnotations(readOnlyHint=True, openWorldHint=False)

    @server.tool(annotations=read_only, structured_output=True)
    def list_hardware_sources(source: str | None = None) -> dict[str, list[dict]]:
        """List indexed PCB sources with revisions, part tags, local artifacts, and warnings."""
        with closing(open_index(library)) as db:
            rows = db.execute(
                "SELECT id AS source_id, vendor, title, kind, revision, parts, url, "
                "artifact, sha256, warnings FROM sources WHERE (? IS NULL OR id = ?) ORDER BY id",
                (source, source),
            )
            return {"sources": list(json_rows(rows))}

    @server.tool(annotations=read_only, structured_output=True)
    def search_hardware_references(
        query: Annotated[str, Field(min_length=1, max_length=2048)],
        part: str | None = None,
        source: str | None = None,
        vendor: str | None = None,
        kind: Literal["guide", "datasheet", "errata", "reference-design"] | None = None,
        content_type: Literal["text", "inventory", "metadata"] = "text",
        limit: Annotated[int, Field(ge=1, le=20)] = 6,
    ) -> dict[str, list[dict]]:
        """Search PCB references by keyword and exact metadata. Cite the result's revision and locator."""
        if not any(character.isalnum() for character in query):
            raise ValueError("query must contain letters or digits")
        with closing(open_index(library)) as db:
            hits = list(passages(db, query=query, part=part, source=source, vendor=vendor,
                                 kind=kind, content_type=content_type, limit=limit))
        return {"hits": hits}

    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, default=os.environ.get("EASYEDA_RAG_DIR"),
                        help="local library directory, or set EASYEDA_RAG_DIR")
    args = parser.parse_args()
    if args.library is None:
        parser.error("set --library or EASYEDA_RAG_DIR")
    library = args.library.expanduser().resolve()
    try:
        with closing(open_index(library)):
            pass
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.error(str(error))
    create_server(library).run(transport="stdio")


if __name__ == "__main__":
    main()
