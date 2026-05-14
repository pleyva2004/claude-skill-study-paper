# study-paper

> A Claude Code skill that turns one AI/ML research paper into five layered artifacts: a 500-word interview-prep doc, a mathematician-grade math deep dive, an opinion-capture template, a publishable GitHub sandbox, and a research-ready LaTeX literature-review entry.

Built for staying current on cutting-edge AI architectures (LLMs, VLMs, multimodal, context/memory, RL algorithms) when you want to actually internalize papers — not just bookmark them.

---

## What it does

Run `/study-paper https://arxiv.org/abs/<id>` inside Claude Code and the skill walks through five stages, pausing for confirmation between each:

| Stage | Output | Format |
|------|--------|--------|
| 0 — Ingest | `source.pdf`, `metadata.json` | Downloads paper, extracts metadata, indexes text |
| 1 — Interview Prep | `01-interview-prep.md` | ~500 words, 5 sections, opinionated talking points |
| 2 — Math Deep Dive | `02-math-deep-dive.md` | Long-form derivations, LaTeX math, load-bearing assumptions |
| 3 — Opinion Capture | `03-opinions.md` | Empty template — **you fill it in**, the skill never fabricates |
| 4 — Sandbox | `sandbox/` → `ai-study-<slug>` GitHub repo | Minimal CPU-runnable PyTorch experiment probing one paper claim |
| 5 — Literature Review (final) | `04-literature-review.tex` + `references.bib` | Standalone-compilable LaTeX, citation-ready, drop-in for a survey paper |

All artifacts land under `~/ai-research-studies/<slug>/`.

## Why these five artifacts

- **Interview prep** is for the moments before you're asked "what's interesting about this paper?" — punchy, opinionated, glance-able.
- **Math deep dive** is for the mathematician in you — derivations, not paraphrase, with explicit "could not derive this" flags.
- **Opinion capture** keeps your voice yours. The skill prompts the right questions and stops; it does not generate opinions on your behalf.
- **Sandbox** turns reading into building — one runnable experiment per paper, published to your GitHub as portfolio.
- **Literature review** is the final research-ready deliverable — pure LaTeX with `\citep`/`\citet`, drop-in suitable for a survey paper, related-work section, or your master lit-review document.

## Install

Clone (or symlink) into your Claude Code skills directory:

```bash
git clone https://github.com/pleyva2004/claude-skill-study-paper.git ~/.claude/skills/study-paper
```

Verify install by listing skills in Claude Code — `/study-paper` should appear.

### Optional dependencies

- **`gh` CLI** (https://cli.github.com) — for Stage 4 to publish sandbox repos automatically. Without `gh`, the skill scaffolds locally and prints the exact command for manual publishing.
- **`pdflatex`** (`sudo apt install texlive-latex-base texlive-fonts-recommended texlive-publishers`) — for Stage 5 to smoke-test the literature-review compile. Without it, the skill skips the test.
- **PyTorch** + **transformers** — only needed if you actually want to run a sandbox experiment on your machine.

## Usage

```
/study-paper https://arxiv.org/abs/2605.06241
```

The skill will:
1. Fetch the paper and metadata
2. Generate the interview prep (≈500 words, 5 sections)
3. Generate the math deep dive (LaTeX, derivations, gaps flagged)
4. Drop the opinion-capture template and **wait** for you
5. Scaffold the sandbox and **confirm** before pushing to GitHub
6. Generate the LaTeX literature review + bibtex, smoke-test compile

Resume an in-progress study with the slug:
```
/study-paper rethinking-rl-llm-reasoning-sparse-policy-selection
```

## Example output

See [pleyva2004/ai-study-rethinking-rl-llm-reasoning](https://github.com/pleyva2004/ai-study-rethinking-rl-llm-reasoning) — the sandbox produced for *Akgül et al. 2026, arxiv:2605.06241* — as a complete reference.

## Repository layout

```
study-paper/
├── SKILL.md                              # activation, persona, routing, workflow
├── stages/
│   ├── 00-ingest.md
│   ├── 01-interview-prep.md
│   ├── 02-math-deep-dive.md
│   ├── 03-opinion-capture.md
│   ├── 04-sandbox.md
│   └── 05-literature-review.md
└── templates/
    ├── 01-interview-prep.md
    ├── 02-math-deep-dive.md
    ├── 03-opinions.md
    ├── 04-literature-review.tex
    ├── references.bib
    └── sandbox-README.md
```

## Customization

- **Sandbox language** — defaults to PyTorch, switches to JAX if the paper uses JAX. Override in `stages/04-sandbox.md`.
- **Math notation** — uses `$...$` LaTeX. Renders in Obsidian, GitHub, and any Markdown viewer with KaTeX/MathJax.
- **Opinion capture template** — edit `templates/03-opinions.md` to add or change the questions you want to be prompted for.
- **Literature review structure** — section list lives in `stages/05-literature-review.md`. Add or reorder sections there.

## Roadmap

- **v2** — `/study-paper --auto`: interest-tag-based arxiv crawl, proposes 3 candidate papers per run.
- **v2** — `/study-link`: cross-link related studies with `\cite{}` peer references.
- **v3** — `/study-update`: re-process older studies if the arxiv paper has been updated.

## License

MIT.

## Acknowledgments

Designed during preparation for the Anthropic RL Research Fellowship. Built with Claude Code.
