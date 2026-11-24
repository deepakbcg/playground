# EasyEDA PCB skill

The [skill](SKILL.md) guides requirements gathering, PCB design, and fabrication review. Its optional local reference library indexes PDFs and other hardware documents and makes cited passages available to Codex over MCP.

## Install the skill in a workspace

Copy `easyeda-pcb/` into the new workspace and run commands from its parent directory. Link the folder into Codex’s workspace skill directory so the scripts and skill instructions share the same copy.

```sh
mkdir -p .agents/skills
ln -s ../../easyeda-pcb .agents/skills/easyeda-pcb
```

If symlinks are unavailable, copy the folder to `.agents/skills/easyeda-pcb`. Open Codex from that workspace and invoke `$easyeda-pcb`. [Codex skill locations](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)

## Test the workflow without EasyEDA

Use the skill to test requirements intake, circuit design and review, stackup planning, and reference retrieval on a machine without the editor. For example, ask “Use `$easyeda-pcb` to lead the intake for a four-layer USB-powered sensor. After we settle the requirements, produce a proposed schematic pin-to-net table and PCB rules for review.” The [editor-independent workflow](references/easyeda-workflow.md#work-without-the-editor) describes the handoff for later native capture and verification.

## Set up the reference library on a new machine

Run these commands from the same parent directory. You need `uv`, internet access for the initial dependency and ebook downloads, and a local Codex CLI or IDE client for MCP. The virtual environment, ebooks, and index are created beside `easyeda-pcb/`. Share the skill directory and keep those three folders local. [Install uv](https://docs.astral.sh/uv/getting-started/installation/)

### 1. Create the Python environment

```sh
uv venv --python 3.13 .pcb-rag-venv
rag_python="$PWD/.pcb-rag-venv/bin/python"
uv pip install --python "$rag_python" 'mcp>=2,<3' pypdf fonttools
```

On Windows PowerShell, use `$rag_python = (Resolve-Path .pcb-rag-venv/Scripts/python.exe).Path` after `uv venv`. Invoke Python with `& $rag_python` and put commands on one line in place of shell `\` continuations.

### 2. Download the ebooks or add your own PDFs

```sh
"$rag_python" -B easyeda-pcb/scripts/hardware_rag.py download-ebooks --output ./pcb-ebooks
```

For the downloaded set, save the following as `pcb-ebooks/sources.json`. For your own PDF, make a manifest with an entry of the same shape and use the actual filename, title, and revision. A `path` is relative to the manifest. The optional `url` records the publisher when a local `path` is supplied. Leave `parts` empty for a general reference.

```json
{
  "sources": [
    {
      "id": "cadence-pcb-design",
      "vendor": "Cadence",
      "title": "PCB Design From Start to Finish",
      "kind": "guide",
      "revision": "2022 ebook",
      "parts": [],
      "path": "cadence-pcb-design-from-start-to-finish.pdf",
      "url": "https://resources.academic.cadence.com/pcb-layout/pcb-design-from-start-to-finish"
    },
    {
      "id": "pfeil-high-speed",
      "vendor": "Printed Circuit Engineering Association",
      "title": "High-Speed Constraint Values and PCB Layout Methods",
      "kind": "guide",
      "revision": "3rd edition, version 3a",
      "parts": [],
      "path": "pfeil-high-speed-constraint-values-3rd-edition.pdf",
      "url": "https://pcea.net/wp-content/uploads/2024/05/High-Speed-Constraint-Values-v3a-Pfeil.pdf"
    },
    {
      "id": "resso-bogatin-si",
      "vendor": "International Engineering Consortium",
      "title": "Signal Integrity Characterization Techniques",
      "kind": "guide",
      "revision": "2nd edition, 2009",
      "parts": [],
      "path": "resso-bogatin-signal-integrity-characterization-techniques-2nd-edition.pdf",
      "url": "https://www.colorado.edu/faculty/bogatin/publications/books-reviews"
    },
    {
      "id": "ti-low-emi",
      "vendor": "Texas Instruments",
      "title": "An Engineer’s Guide to Low EMI in DC/DC Regulators",
      "kind": "guide",
      "revision": "SLYY208, 2021 ebook",
      "parts": [],
      "path": "ti-engineers-guide-to-low-emi-in-dc-dc-regulators.pdf",
      "url": "https://www.ti.com/lit/eb/slyy208/slyy208.pdf"
    }
  ]
}
```

### 3. Build and check the index

```sh
"$rag_python" -B easyeda-pcb/scripts/hardware_rag.py \
  --library ./pcb-reference-library ingest ./pcb-ebooks/sources.json

"$rag_python" -B easyeda-pcb/scripts/hardware_rag.py \
  --library ./pcb-reference-library search 'differential pair stitch vias' \
  --source pfeil-high-speed --content-type text --limit 2
```

Ingestion should report a positive `text_chunks` count for each ebook. Search hits include the source, revision, and PDF page. A scanned PDF needs an OCR text layer. For a private migration of an existing index, copy the complete `pcb-reference-library/` folder while ingestion is idle and continue at step 4.

### 4. Register the MCP server

```sh
codex mcp add easyeda-rag -- "$rag_python" -B \
  "$PWD/easyeda-pcb/scripts/hardware_rag_mcp.py" \
  --library "$PWD/pcb-reference-library"
codex mcp list
```

Use absolute paths in the registration so the server works from other working directories. In the Codex IDE MCP settings, you can enter the same interpreter and arguments as a stdio server. Open a new local session so Codex can launch the server. [Codex MCP setup](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)

Then ask, “Use `easyeda-rag` to find guidance on differential pairs crossing a plane split, with PDF page citations.” The server exposes `list_hardware_sources` and `search_hardware_references`. To add or refresh references, update the manifest and rerun step 3. Subsequent searches use the updated index.

See the [hardware reference workflow](references/hardware-rag.md) for vendor downloads, reference-design ZIPs, source filters, and JSONL export.

## Package the skill

From the authoring workspace that contains `zip_skills.py`, run `python3 zip_skills.py easyeda-pcb`. Share `dist/easyeda-pcb.zip`. The ZIP contains the skill and its supporting files. The command excludes PDFs, the local RAG library, virtual environments, and generated files.
