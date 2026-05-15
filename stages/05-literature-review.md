# Stage 5 — Literature Review (LaTeX, research-ready)

**Goal:** Produce `04-literature-review.tex` (and `references.bib` if not already present) — a publication-quality LaTeX literature-review entry suitable for inclusion in an actual research document.

This is the **final deliverable** of the workflow. It is not a blog post or case study. It is written to land verbatim in a survey paper, a related-work section, or a personal master literature-review document.

## Inputs

- `01-interview-prep.md` — for framing and headline contribution
- `02-math-deep-dive.md` — for the technical core (definitions, equations, derivations)
- `03-opinions.md` — for the discussion / critique paragraphs (used verbatim or paraphrased; if empty, the discussion section gets a `% TODO` marker rather than fabrication)
- `metadata.json` — for arxiv ID, authors, year, title, github links

## LaTeX Conventions

The `.tex` output **must follow the [`write-latex`](../../write-latex/SKILL.md) skill's rules**: `pdflatex`-clean, no `fontspec`, `\section*` by default (no numbering unless requested), comments only inside `\iffalse ... \fi`, no output other than valid LaTeX. The bundled template (`templates/04-literature-review.tex`) already conforms; preserve those conventions when filling it in.

## Notation prelude (mandatory)

The `.tex` output **must** include a `\section*{Notation}` block placed **between** `\end{abstract}` and `\section{Background and Motivation}`. This block is a small `longtable` (or `tabular` if the symbol list is short) listing every symbol the paper uses, sourced from the foundations glossary.

Rules:
- The block must include an `\href` reference to the canonical PDF:
  `\href{https://github.com/pleyva2004/math-foundations/blob/main/notation.pdf}{Foundations Glossary}`
- Pull rows from `notation.json` — do **not** redefine symbols inline. Symbols missing from the glossary go in the table with a `% TODO add to foundations` comment on that row so the gap is visible upstream.
- Generation is automated: run
  `python3 templates/notation-extractor.py 04-literature-review.tex notation.json --format latex`
  and paste the resulting `tabular`/`longtable` block into the `Notation` section.
- Keep this in sync with the `## Notation key` subsection emitted by Stage 2 — both are derived from the same `notation.json` and should agree symbol-for-symbol.

If `longtable` is used, ensure `\usepackage{longtable}` is in the preamble (the bundled template already loads it via the standard amsmath stack; add it if missing).

## Method

1. Load `templates/04-literature-review.tex`.
2. Read all four prior artifacts via `ctx_execute_file` (they may be long).
3. Generate the LaTeX document **per write-latex rules**. Populate every section. Replace every placeholder.
4. Generate or augment `references.bib` with the entries cited (the paper itself + 5–10 most-relevant prior works the paper engages with — drawn from the math deep dive's "Connections" section).
5. Write `~/ai-research-studies/<slug>/04-literature-review.tex` and `~/ai-research-studies/<slug>/references.bib`.
6. Smoke-test compile if `pdflatex` is available: `pdflatex -interaction=nonstopmode 04-literature-review.tex` (in sandbox via `ctx_execute`). Report compile errors but do not fail the stage on them.

## Required Sections in the .tex Output

| Section | Content |
|---|---|
| Abstract / Summary | One paragraph: paper's claim and the contribution to the literature |
| Background and Motivation | What gap the paper addresses; what came before |
| Technical Approach | Definitions, central equation(s), method walk-through with real LaTeX math |
| Key Results | Empirical findings, what was tested, what was shown |
| Position in the Literature | How this paper sits relative to specific prior works (cited via `\citep` / `\citet`) |
| Limitations and Open Questions | Honest critique — drawn from `03-opinions.md` if present, otherwise the gaps flagged in the math deep dive |
| (Optional) Sandbox Probe | One-paragraph mention of any sandbox experiment built around the paper |

## Style Rules

- Pure LaTeX, compilable standalone (article class, amsmath, amssymb, natbib, hyperref).
- Every equation in a `\begin{equation}` or `$$ ... $$` environment. Number equations referenced more than once.
- Citations via `\citep{key}` (parenthetical) and `\citet{key}` (inline). Never bare-name cite; always use the bibtex key.
- No first-person narration unless the discussion is genuinely the user's voice (then frame as "We argue that…" — first-person plural is acceptable in a survey).
- No filler phrases ("This paper presents an interesting approach to…"). Open with the substantive claim.
- No emoji. No markdown formatting (no `**bold**`, no bullets — use LaTeX `\textbf{}` and `itemize` instead).
- Length target: 800–2000 words of body text plus the equations.

## Bib Hygiene

`references.bib` entries must include: `@article` or `@inproceedings`, with `author`, `title`, `journal`/`booktitle`, `year`, and either `archivePrefix={arXiv}, eprint={...}` or a venue. Use lowercase-hyphen keys derived from first-author-lastname + year (e.g. `akgul2026`, `rafailov2023`).

## Output

```
Wrote: 04-literature-review.tex (~<word count> words, <equation count> equations, <citation count> citations)
Wrote: references.bib (<n> entries)
Compile check: <PASS|FAIL — see error log>
Study complete:
  ~/ai-research-studies/<slug>/
    01-interview-prep.md
    02-math-deep-dive.md
    03-opinions.md
    04-literature-review.tex   ← final deliverable
    references.bib
    sandbox/  → <github url>
```
