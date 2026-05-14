# Stage 0 — Ingest

**Goal:** Resolve user input into a normalized study directory and a readable PDF, with metadata captured.

## Input Resolution

Branch on input shape:

### Arxiv URL (e.g. `https://arxiv.org/abs/2407.08608`)
1. Normalize: strip version suffix (`v1`, `v2`), strip trailing slash, ensure `abs/` form.
2. Extract arxiv ID (e.g. `2407.08608`).
3. Fetch the abstract page via `mcp__plugin_context-mode_context-mode__ctx_fetch_and_index` (URL = the abs page). Search the indexed source for `title`, `authors`, `abstract`, `submitted`.
4. Derive slug: kebab-case of title, max 60 chars, ASCII-only. Fallback: `arxiv-<id>`.
5. PDF URL = `https://arxiv.org/pdf/<id>.pdf`.

### Local PDF path
1. Verify file exists and is readable.
2. Derive slug from filename (strip extension, kebab-case). If filename is uninformative (`paper.pdf`, `download.pdf`), read the PDF first page via `ctx_execute_file` and slugify the first heading.
3. Title/authors/date → leave blank in metadata if unknown; user can edit.

### Bare slug (resume)
1. Check `~/ai-research-studies/<slug>/` exists. If not, error and ask whether user meant a new study.
2. List existing artifacts. Report state. Ask which stages to run.

## Directory Setup

```
mkdir -p ~/ai-research-studies/<slug>
```

Write `metadata.json`:
```json
{
  "slug": "<slug>",
  "title": "<title>",
  "authors": ["..."],
  "arxiv_id": "<id-or-null>",
  "source_url": "<arxiv-abs-or-null>",
  "pdf_path": "~/ai-research-studies/<slug>/source.pdf",
  "started": "<YYYY-MM-DD>",
  "stages_completed": []
}
```

## PDF Acquisition

For arxiv: download via `ctx_execute` with `curl -L -o ~/ai-research-studies/<slug>/source.pdf <pdf-url>`. Confirm size <50MB before proceeding.

For local: copy or symlink into the study dir as `source.pdf`.

## PDF → Text for Downstream Stages

Use `mcp__plugin_context-mode_context-mode__ctx_execute_file` with `path: ~/ai-research-studies/<slug>/source.pdf` to read paper text in the sandbox **without flooding context**. The PDF text becomes available to subsequent stages via the indexed source — they can `ctx_search` it.

For PDF parsing inside the sandbox use `pdftotext` (poppler-utils) if available, else `pypdf` via Python. Prefer:
```python
import subprocess
text = subprocess.check_output(['pdftotext', '-layout', PDF_PATH, '-']).decode()
print(text[:200])  # only print preview to context
```

Then `ctx_index` the full text file for later search.

## Output

Report to user:
```
Ingested: <title>
Slug: <slug>
Dir: ~/ai-research-studies/<slug>/
PDF: source.pdf (<size>)
Ready for Stage 1 (interview prep). Continue?
```

Wait for confirmation before proceeding to Stage 1.
