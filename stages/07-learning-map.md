# Stage 7 — Interactive Learning Map

**Goal:** Build a three-graph learning map for the study: `paper/` graph (concepts from the paper itself), `improvements/` graph (concepts from the proposed extensions), and cross-links into the shared foundations graph at [`pleyva2004/math-foundations`](https://github.com/pleyva2004/math-foundations).

Every concept in every graph (paper, improvements, foundations) **must have a runnable `.py` code analog**. No exceptions. For abstract concepts, the `.py` is a finite/discrete witness.

## Mandate

This is the educational/portfolio surface. A reader at any skill level — total novice to senior researcher — must be able to enter at their level and walk the dependency graph forward to the paper and into the improvements. The forcing function: explain the paper "from first principles" as a literal dependency DAG of mathematical objects, each with prose + formal math + runnable code.

## Inputs

- `02-math-deep-dive.md` — primary source for paper-graph concept identification. Every defined symbol, lemma, or theorem is a candidate concept node.
- `04-literature-review.tex` + `references.bib` — paper-graph concepts cite related works by `\citep` key.
- `05-improvements.tex` — primary source for improvements-graph concept identification. Each proposal yields ≥1 new concept node.
- `improvements/*.py` (Stage 6 prototypes) — improvements-graph concept-level `.py` files reuse functions/patterns from these.
- `sandbox/experiment.py` — paper-graph concept-level `.py` files reuse functions from here.
- `~/.claude/math-foundations/manifest.json` — list of available foundation concepts to cross-link by URL.

## Method

### Step A — Paper graph (`learning-map/paper/`)

1. Read the math deep dive's "Setup & Notation", "Central Object", and each math section. For each named mathematical object or named operation, create a paper-graph node.
2. For each node, identify prereqs:
   - Local prereqs (other paper-graph nodes) — same file.
   - Foundation prereqs (concepts in `pleyva2004/math-foundations`) — link by stable URL `https://github.com/pleyva2004/math-foundations/blob/main/concepts/<NN>-<slug>.md`.
3. Write `learning-map/paper/manifest.json` listing all nodes + edges (local + cross-graph).
4. For each node, write `learning-map/paper/concepts/<NN>-<slug>.md` using `templates/concept.md`. Each concept .md is ≤300 words plus formal LaTeX definition.
5. For each node, write `learning-map/paper/code/<NN>-<slug>.py` using `templates/concept-code.py`. CPU-runnable in <30 s, ≤80 lines.
6. Write `learning-map/paper/README.md` with mermaid DAG (use the generator pattern from math-foundations).
7. Write `learning-map/paper/tours/quick-tour.md` (~30-min walk through paper concepts) and `tours/deep-dive.md` (~3-hour walk with foundation refresh).

### Step B — Improvements graph (`learning-map/improvements/`)

Same structure as Step A but rooted at the extension proposals. Each improvement concept typically prereqs ≥1 paper-graph node (the thing being extended) plus ≥1 foundation node.

**Hard rule:** every improvement concept gets its own `.py` file. If the corresponding Stage 6 full prototype (e.g. `improvements/cfg-schedule.py`) is too large to use directly, the learning-map .py is a minimal extract — the smallest runnable witness of the concept's idea.

### Step B.5 — Per-concept "Symbols you'll see" prelude

Every paper-graph and improvements-graph concept `.md` (under `learning-map/paper/concepts/` and `learning-map/improvements/concepts/`) **inherits the same "Symbols you'll see" pattern** used by foundation concepts in `pleyva2004/math-foundations`. After the concept's intro paragraph and before the formal definition, insert a small markdown table:

```markdown
## Symbols you'll see

| Symbol | Read aloud as | Meaning |
|--------|---------------|---------|
| ... | ... | ... |
```

Generation:
- Run `python3 templates/notation-extractor.py learning-map/paper/concepts/<NN>-<slug>.md notation.json` against each concept body. Pipe stdout into the `## Symbols you'll see` section.
- For symbols missing from the foundations glossary, the extractor emits a `<!-- TODO add to foundations -->` comment on that row — leave it in place so it surfaces during foundations growth (see "Foundations growth" below).
- For improvements-graph concepts, run the same extractor on each `learning-map/improvements/concepts/<NN>-<slug>.md`.

This keeps every node's notation discoverable without forcing the reader to leave the page, while still pointing at the foundations glossary as the canonical reference.

### Step C — Cross-cutting top-level (`learning-map/`)

1. `learning-map/README.md` — combined mermaid (foundations → paper → improvements) with `click` directives. Skill-level entry-point table at top. Links to all three sub-graphs.
2. `learning-map/manifest.json` — union manifest with explicit `graph` tag per node ("foundations" / "paper" / "improvements").
3. `learning-map/notebook/paper-learning.ipynb` — generated mechanically by concatenating paper-graph concept .md and code .py in topological order.
4. `learning-map/notebook/improvements-learning.ipynb` — same, for improvements graph.
5. `learning-map/notebook/combined.ipynb` — paper + improvements in topological order, one document.
6. `learning-map/html/{index.html,data.json,styles.css}` — D3 force graph. Use the same template as `math-foundations/html/`.

### Step D — Update the top-level study README

Add a `learning-map/` row to the study's top-level `README.md` artifact table, with a "How to navigate" link to `learning-map/README.md`.

### Step F — Build the tour and improvement validation files

After the paper-graph and improvements-graph are written, generate a per-paper **tour** in three forms and per-improvement **validation files** (proof OR measurement) that round out the study.

#### F.1 — The tour (`learning-map/tour.{md,tex,ipynb}`)

Generate three forms of the same content from three data spines: the **paper manifest** (`learning-map/paper/manifest.json`), the **improvements manifest** (`learning-map/improvements/manifest.json`), and the **math deep dive** (`02-math-deep-dive.md`) plus the foundations URL (`https://github.com/pleyva2004/math-foundations`).

All three forms share the same five-section structure:

1. **Reader's contract** — three concrete learning outcomes; prereq topics with refresh links; explicit out-of-scope items.
2. **Foundations walk** — table with one row per foundation node referenced by the paper. Columns: concept, why-it-matters-here, link to the canonical foundation page.
3. **Paper concepts walk** — table over the paper-graph nodes in topological order. Columns: concept, role-in-the-paper, files (`learning-map/paper/concepts/<NN>-<slug>.md` + `code/<NN>-<slug>.py`). Closes with a one-paragraph "how the pieces fit" narrative.
4. **Improvements walk** — one entry per row in `05-improvements.tex`. Each entry names the improvement, its mode (PROOF / MEASUREMENT / link-only), and the file path of its validation artifact. See F.2 for mode selection.
5. **What to do next** — five concrete next actions: reproduce sandbox, run a measurement, audit a proof, fill in opinions, extend the foundations graph.

Generation steps:

- Render `learning-map/tour.md` from `templates/tour.md`. Substitute Mustache placeholders (`{{paper_title}}`, `{{foundations_walk_table}}`, `{{paper_concepts_walk_table}}`, `{{improvements_walk}}`, etc.) with per-paper content.
- Render `learning-map/tour.tex` from `templates/tour.tex`. Same content, write-latex compliant (no `fontspec`, `\section*` defaults, comments inside `\iffalse...\fi`). Uses `longtable` + `hyperref` for the foundations walk table.
- Render `learning-map/tour.ipynb` from `templates/tour.ipynb`. Generate via Python `json` module — must be valid JSON. ~6-8 cells: section headers as markdown cells; one code cell that loads `notation.json` and prints a quick summary; one placeholder code cell per MEASUREMENT-mode improvement (commented `from improvements.<slug> import measure; measure()`).

#### F.2 — Per-improvement validation files

For each entry in `05-improvements.tex`, pick **exactly one** of {PROOF, MEASUREMENT} per the heuristic:

| Improvement section | Default mode | Override condition |
|---|---|---|
| Mathematical Improvements | PROOF | MEASUREMENT if it is a tighter empirical bound |
| Implementation/Code Improvements | MEASUREMENT | PROOF if it is a complexity-class statement |
| Experimental Extensions | MEASUREMENT | — |
| Theoretical/Conceptual Connections | PROOF | "link only" if just citing existing literature |

**PROOF mode** — write `proofs/<slug>.tex` from `templates/proof.tex`:
- Standalone, ~2-3 page LaTeX, write-latex compliant.
- `\section*{Theorem}` with a precise `\begin{theorem}...\end{theorem}` statement.
- `\section*{Proof}` with a `\begin{proof}...\end{proof}` complete proof. **No "obvious", no "left as exercise", no "by standard arguments".**
- `\section*{Discussion}` — what the proof gives us, what it does not, where it would break.

**MEASUREMENT mode** — extend `improvements/<slug>.py` (already drafted in Stage 6):
- Add `def measure() -> dict` returning a quantitative comparison (baseline vs proposal across the metrics that matter for this proposal).
- Modify `main()` to call `measure()` and print a comparison table.
- Ensure determinism: fixed seed at module top (e.g. `SEED = 0; random.seed(SEED); torch.manual_seed(SEED); np.random.seed(SEED)`).
- Keep CPU-runnable in <2 minutes.

**link-only mode** — for Theoretical/Conceptual Connections that are pure citations, write neither file. The improvements walk in §4 of the tour notes the citation key and links into `references.bib`.

Validation:
- Every non-link-only improvement has exactly one of `proofs/<slug>.tex` or an extended `improvements/<slug>.py` with `measure()` — never both, never neither.
- `tour.ipynb` parses as JSON.
- `tour.tex` and every `proofs/<slug>.tex` compile cleanly under `pdflatex` if placeholders are stub-filled.

### Step E — Update the render workflow

`.github/workflows/render.yml` already exists for LaTeX rendering. Extend it (or add a sibling workflow) to:
- Validate `learning-map/manifest.json` JSON.
- Verify every node has both a `.md` and `.py` file.
- Smoke-parse every `learning-map/**/*.py`.
- (Optional) `nbconvert --to html` the notebooks and commit `built/*.html`.

## Concept identification heuristic

A new concept node is warranted iff:
- The paper or improvements doc names it explicitly (e.g. "decision point set", "velocity field", "scheduled CFG").
- It has a precise mathematical definition.
- It is not already covered by an existing foundation concept (else link out by URL).
- A finite/discrete demonstration is plausible (else flag it as `# TODO needs cluster prototype` in the .py).

Typical counts:
- Paper graph: 10-20 nodes for a typical ML paper.
- Improvements graph: 5-15 nodes (one per proposal + supporting concepts).

## Foundations growth

If the math deep dive uses a mathematical object NOT present in `~/.claude/math-foundations/manifest.json`, Stage 7 also:
- Adds a new entry to the foundations manifest.
- Generates the skeleton concept .md + .py via the foundations generator.
- Commits + pushes the foundations repo as part of the same Stage 7 work.

This keeps the foundations graph growing organically with each new paper.

## Output

```
Wrote: learning-map/
  paper/
    manifest.json (<N> nodes, <M> edges)
    concepts/ (<N> files)
    code/ (<N> files — every node has a .py)
    README.md (mermaid DAG)
    tours/quick-tour.md, tours/deep-dive.md
  improvements/
    manifest.json (<I> nodes, <J> edges)
    concepts/ (<I> files)
    code/ (<I> files — every node has a .py)
    README.md (mermaid DAG)
    tours/proposal-walkthrough.md
  manifest.json (union)
  notebook/{paper-learning,improvements-learning,combined}.ipynb
  html/{index.html, data.json, styles.css}
  README.md (combined view, skill-level entry table)
  tour.md, tour.tex, tour.ipynb (per-paper tour, three forms)
proofs/
  <slug>.tex (one per PROOF-mode improvement)
improvements/
  <slug>.py (extended with measure() for each MEASUREMENT-mode improvement)

Validation:
  - .py count matches node count in every graph: PASS
  - All cross-graph URLs HTTP 200: <CHECKED|SKIPPED-OFFLINE>
  - Notebook valid JSON: PASS
  - tour.ipynb valid JSON: PASS
  - HTML structurally valid: PASS
  - Every non-link-only improvement has exactly one validation file: PASS
```

Ready for Stage 8 (publish). Continue?
