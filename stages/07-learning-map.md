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

### Step C — Cross-cutting top-level (`learning-map/`)

1. `learning-map/README.md` — combined mermaid (foundations → paper → improvements) with `click` directives. Skill-level entry-point table at top. Links to all three sub-graphs.
2. `learning-map/manifest.json` — union manifest with explicit `graph` tag per node ("foundations" / "paper" / "improvements").
3. `learning-map/notebook/paper-learning.ipynb` — generated mechanically by concatenating paper-graph concept .md and code .py in topological order.
4. `learning-map/notebook/improvements-learning.ipynb` — same, for improvements graph.
5. `learning-map/notebook/combined.ipynb` — paper + improvements in topological order, one document.
6. `learning-map/html/{index.html,data.json,styles.css}` — D3 force graph. Use the same template as `math-foundations/html/`.

### Step D — Update the top-level study README

Add a `learning-map/` row to the study's top-level `README.md` artifact table, with a "How to navigate" link to `learning-map/README.md`.

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

Validation:
  - .py count matches node count in every graph: PASS
  - All cross-graph URLs HTTP 200: <CHECKED|SKIPPED-OFFLINE>
  - Notebook valid JSON: PASS
  - HTML structurally valid: PASS
```

Ready for Stage 8 (publish). Continue?
