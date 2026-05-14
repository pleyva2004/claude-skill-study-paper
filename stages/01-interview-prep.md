# Stage 1 — Interview Prep

**Goal:** Produce `01-interview-prep.md` — a ~500-word, opinionated talking-points doc optimized for the 15-min research brainstorm interview.

## Inputs

- Indexed paper text from Stage 0
- Title, authors, arxiv ID from `metadata.json`

## Method

1. `ctx_search` the indexed paper for: introduction, contributions, method, results, limitations, related work.
2. Load `templates/01-interview-prep.md`.
3. Generate the doc — populate every section. Write `~/ai-research-studies/<slug>/01-interview-prep.md`.

## Section Requirements

| Section | Length | Tone |
|---------|--------|------|
| **One-sentence elevator** | 1 sentence | Crisp; what the paper actually does |
| **What's novel** | 2–4 bullets | Specific — name the technique, not the topic |
| **What's mathematically clever** | 2–3 bullets | Point at the actual derivation/identity that makes it work; brief LaTeX OK |
| **What I'd push back on** | 2–4 bullets | Real critiques: assumptions, missing baselines, scope of claim, suspicious experimental choices |
| **Open questions** | 2–3 bullets | What you'd ask the authors; what the next paper should answer |

## Style Rules

- Opinionated, not encyclopedic. If you'd say "this is just X with Y bolted on", say it.
- No padding ("This paper presents an interesting approach to…"). Cut to the substance.
- Citation-light — name 1–2 prior works max.
- ~500 words total. Hard cap 700.
- LaTeX in `$...$` for any math.

## Output

After writing, report:
```
Wrote: 01-interview-prep.md (~<word count> words)
Preview: <one-sentence elevator>
Ready for Stage 2 (math deep dive). Continue?
```
