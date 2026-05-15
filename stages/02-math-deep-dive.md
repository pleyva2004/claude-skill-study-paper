# Stage 2 — Math Deep Dive

**Goal:** Produce `02-math-deep-dive.md` — long-form, mathematician-grade derivation of the paper's core technical content.

## Mandate

**Derive, do not paraphrase.** If the paper writes "we minimize the KL divergence", you write the KL definition, the gradient, the assumption that makes the gradient unbiased, and where it stops being unbiased. If the paper writes "by standard arguments", you supply the standard argument or flag that you couldn't reconstruct it.

The user identifies as a pure mathematician. Treat them as one.

## Notation prelude (mandatory)

The math deep dive output **must** begin — immediately after the "Setup & Notation" section — with a `## Notation key` subsection. This subsection is a small markdown table listing every symbol the paper uses, sourced from the foundations glossary at:

> https://github.com/pleyva2004/math-foundations/blob/main/NOTATION.md
> (canonical JSON: `notation.json`; PDF: `notation.pdf`)

Rules:
- The foundations glossary is the **source of truth**. Reuse the `latex`, `read_aloud`, and `meaning` fields verbatim — never fabricate a duplicate inline definition.
- Symbols **not yet** in the foundations glossary must be included in the table AND flagged with an HTML comment so they propagate upstream:
  `| $\mathcal{X}$ | "cal X" | Decision-point set <!-- TODO add to foundations --> |`
- Generation is automated: run `templates/notation-extractor.py <path-to-02-math-deep-dive.md> notation.json` and paste the resulting markdown table into the `## Notation key` subsection.
- The subsection must include a one-liner linking back to the glossary so readers can find the full reference.

The literature-review stage (Stage 5) ships an analogous LaTeX prelude — keep the two in sync.

## Method

1. `ctx_search` the indexed paper for: equations, theorems, lemmas, proofs, algorithms, definitions.
2. Load `templates/02-math-deep-dive.md`.
3. Walk the paper's central technical contribution top-to-bottom. For each equation/claim:
   - State it precisely (LaTeX, `$$...$$` for display).
   - Define every symbol on first use.
   - Derive it or cite where it comes from.
   - Note the assumptions it requires.
   - Flag any step you cannot reconstruct ("hand-wavy in the paper" or "I cannot derive this from what's given").
4. Add an "alternative formulations" section if relevant (e.g. dual problem, equivalent loss, relationship to prior algorithm).
5. Add a "load-bearing assumptions" section: list the assumptions whose violation would break the central claim.

## Length

No cap. Be as long as the math demands. Bias toward thoroughness over brevity. If a paper is 30 pages of math, this doc is allowed to be long.

## Style Rules

- LaTeX everywhere math appears. `$inline$` and `$$display$$`.
- Numbered equations for anything referenced more than once: `$$ \mathcal{L}(\theta) = \mathbb{E}_{x \sim p}[\ell(x; \theta)] \tag{1} $$`
- Do not skip steps that would be skipped in a conference paper but are non-obvious to a first reader.
- Honest about unknowns: "I'm not sure why the authors choose this normalization" beats fabricated justification.

## Output

```
Wrote: 02-math-deep-dive.md (~<word count> words, <equation count> equations)
Coverage: <list of paper sections covered>
Gaps flagged: <count of "could not derive" notes>
Ready for Stage 3 (opinion capture). Continue?
```
