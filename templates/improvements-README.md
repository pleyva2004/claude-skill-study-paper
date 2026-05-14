# improvements/

> Runnable Python prototypes for the proposals in [`../05-improvements.tex`](../05-improvements.tex).

Each file in this directory implements one specific subsection of `05-improvements.tex` (Implementation / Code Improvements section). Cross-references are listed below.

---

## Prototypes

| File | Implements (§ in 05-improvements.tex) | One-line description |
|------|---------------------------------------|----------------------|
| `{{slug_1}}.py` | §{{section_ref_1}} | {{one_line_1}} |
| `{{slug_2}}.py` | §{{section_ref_2}} | {{one_line_2}} |

## Run

```bash
pip install -r requirements.txt
python {{slug_1}}.py
python {{slug_2}}.py
```

Each script runs on CPU in <60s and prints a numerical comparison against the baseline it proposes to improve.

## Notes

These are prototypes, not production code. They demonstrate the *direction* of the proposed improvement on a small, transparent example — not the SOTA result. Production-grade re-implementations would belong in a separate repo.
