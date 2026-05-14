# Stage 6 — Suggest Improvements

**Goal:** Generate `05-improvements.tex` (standalone LaTeX) + `improvements/` (runnable Python prototypes) — a forward-thinking artifact that turns each studied paper into a launchpad for follow-on work rather than a closed reading.

## Mandate

This is the **only artifact Claude is allowed to draft on the user's behalf as a substantive proposal**. It is the deliberate forcing function for a forward-looking, research-brainstorm mindset.

The skill writes both:
1. A **standalone LaTeX document** (`05-improvements.tex`) with four `\section*` blocks covering all proposal categories. Conforms to the [`write-latex`](../../write-latex/SKILL.md) skill rules.
2. A **directory of runnable Python prototypes** (`improvements/`) implementing any code-level proposal that is feasible at sandbox scale (CPU-runnable in <60s).

The user reviews and refines both before Stage 7 publishes. Stage 7's commit list will include both artifacts.

## Inputs

- `01-interview-prep.md` — "What I'd push back on" and "Open questions" sections seed proposal candidates
- `02-math-deep-dive.md` — the "Gaps Flagged" / "could not derive this" section is gold; each item becomes a candidate mathematical improvement
- `03-opinions.md` — user's verbatim opinions (if filled) point at proposals worth pursuing
- `04-literature-review.tex` + `references.bib` — every proposal `\citep{}`s related work from the same bib
- `source.pdf` — for fact-checking specific claims when drafting proposals

## Method

1. Load all five inputs via `ctx_execute_file` if any are large.
2. Load `templates/05-improvements.tex` and `templates/improvements-README.md`.
3. For each of the four categories, draft 1–3 concrete proposals. Each proposal must:
   - State the proposal precisely (math, code change, experiment design, or conceptual link)
   - `\citep{}` related work from `references.bib`
   - State the test — a derivation, an experiment, a benchmark
   - Flag whether a prototype lives in `improvements/`
4. For each Implementation/Code Improvement that is feasible to prototype (CPU, <60s, single .py file): write a runnable Python file to `improvements/<proposal-slug>.py`.
5. Write `improvements/README.md` indexing the prototypes, and `improvements/requirements.txt`.
6. Smoke-test compile (`pdflatex 05-improvements.tex`) if `pdflatex` is available; lint syntax otherwise.

## Required Sections in the .tex Output

| Section | Content |
|---|---|
| Abstract | One paragraph: framing as "proposals built on top of [paper]" — what gaps the proposals address |
| Mathematical Improvements | Tighter assumptions, alternative formulations, generalizations, proof improvements, derivations the paper hand-waves |
| Implementation / Code Improvements | Better algorithms, efficiency wins, refactors. **Each entry cross-references a file in `improvements/`** when a prototype exists |
| Experimental Extensions | Controls the paper missed, falsification experiments, scale tests, out-of-distribution probes |
| Theoretical / Conceptual Connections | Links to other research lines, applications to new domains, hybrid methods |
| Closing | One paragraph: which proposal the user finds most personally promising (left blank as `% TODO author pick` if `03-opinions.md` is empty) |

## Code Prototype Rules

For each prototype written to `improvements/`:

- **Filename:** kebab-case proposal slug + `.py` (e.g. `adaptive-tau.py`, `streaming-entropy.py`)
- **Docstring at top:** brief description + the exact subsection of `05-improvements.tex` it implements (e.g. "Implements §2.1 of 05-improvements.tex")
- **CPU-runnable in <60s.** Same constraint as the sandbox.
- **Self-contained.** Imports stdlib + PyTorch/numpy only; no project-internal imports.
- **Prints a comparison.** Time, accuracy, memory, or qualitative diff between the proposed change and the baseline.

Skip prototypes whose feasibility window is too wide (e.g. requires multi-GPU training). Document as `% TODO prototype needs cluster` in the .tex.

## Style Rules (LaTeX)

Inherited from [`write-latex`](../../write-latex/SKILL.md) skill:

- `\section*` and `\subsection*` by default (no numbering)
- Preamble identical to `04-literature-review.tex` (article class, amsmath, natbib, hyperref, xcolor)
- Citations via `\citep{key}` / `\citet{key}` against the same `references.bib`
- No `fontspec`; no markdown contamination
- Comments only inside `\iffalse ... \fi` blocks
- Length target: 1500–3000 words (similar to lit review)

## Output

```
Wrote: 05-improvements.tex (~<word count> words, <subsection count> proposals, <citation count> cites)
Wrote: improvements/ (<n> prototypes + README + requirements.txt)
Compile check: <PASS|FAIL|SKIPPED — pdflatex not found>
Ready for Stage 7 (publish). Continue?
```

## Edge Cases

- **No opinions filled** → still proceed, but draw proposal candidates only from the math deep-dive's flagged gaps and the interview prep's pushback section. Closing paragraph gets `% TODO author pick` placeholder.
- **Theory-only paper (no code release)** → Implementation/Code Improvements section can be lighter; bias proposals toward Experimental Extensions instead.
- **No feasible CPU prototypes** → `improvements/` still gets created with just a README explaining why the proposals need cluster-scale prototypes.
- **User skips this stage** → Stage 7 publishes without `05-improvements.tex` / `improvements/`. The render workflow's `if hashFiles('05-improvements.tex') != ''` guard prevents CI failure.
