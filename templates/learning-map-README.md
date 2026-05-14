# Learning Map — {{paper_title}}

> Three-graph interactive learning surface for [arxiv:{{arxiv_id}}]({{arxiv_url}}).

Anyone — total math novice to senior researcher — can enter at their skill level and walk the dependency graph forward to the paper and into the proposed extensions. Every concept has prose + formal math + runnable code.

## Pick your entry point

| Skill level | Start here |
|-------------|------------|
| Total beginner (no math) | [Foundations: novice tour](https://github.com/{{github_username}}/math-foundations/blob/main/tours/novice.md) |
| Calc + linear algebra | [Foundations: CS undergrad tour](https://github.com/{{github_username}}/math-foundations/blob/main/tours/cs-undergrad.md) |
| Measure theory | [Foundations: math grad tour](https://github.com/{{github_username}}/math-foundations/blob/main/tours/math-grad.md) |
| Domain researcher | [Paper graph](./paper/README.md) |
| Reviewer / brainstorm partner | [Improvements graph](./improvements/README.md) |

## Combined graph

```mermaid
{{combined_mermaid_DAG}}
```

Grey nodes = foundations (clicks out to the shared foundations repo).
Blue nodes = paper-specific (this study).
Orange nodes = proposed extensions (this study).

## Sub-graphs

- [Paper graph](./paper/README.md) — concepts the paper itself defines or uses
- [Improvements graph](./improvements/README.md) — concepts from the proposed extensions
- [Foundations graph (shared)](https://github.com/{{github_username}}/math-foundations) — prerequisites referenced by stable URL

## Interactive views

- **Mermaid** (this README) — clickable in GitHub's browse view.
- **Jupyter notebook** — [`notebook/combined.ipynb`](./notebook/combined.ipynb) — runnable cells.
- **HTML force graph** — [`html/index.html`](./html/index.html) — drag, zoom, filter by level.

## Code-in-line guarantee

Every concept node — in every graph — has an aligned `.py` file in `code/<NN>-<slug>.py`. No exceptions, including abstract concepts (which get a finite/discrete witness).
