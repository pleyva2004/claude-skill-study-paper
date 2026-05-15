#!/usr/bin/env python3
r"""notation-extractor.py — extract symbols from a .tex/.md file and emit a notation key table.

Scans the input file for LaTeX commands (\foo, \mathbb{X}, \mathcal{X}, etc.) and common
unicode math characters, intersects them with the math-foundations notation glossary
(`notation.json`), and emits either a markdown or LaTeX table to stdout.

Usage:
    python3 notation-extractor.py <input.tex|input.md> [<notation.json>] [--format md|latex]

If `notation.json` is omitted, the script falls back to fetching the canonical copy from:
    https://raw.githubusercontent.com/pleyva2004/math-foundations/main/notation.json

Symbols present in the input but absent from the glossary are emitted with a TODO marker
so the foundations glossary can grow upstream.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

FOUNDATIONS_URL = "https://raw.githubusercontent.com/pleyva2004/math-foundations/main/notation.json"

# LaTeX commands like \alpha, \mathcal, \nabla, plus \mathbb{X}/\mathcal{X} variants.
LATEX_CMD = re.compile(r"\\[a-zA-Z]+(?:\{[A-Za-z]\})?")
# Common unicode math characters worth picking up.
UNICODE_MATH = re.compile(r"[Ͱ-Ͽ℀-⅏←-⋿⟀-⟯⦀-⧿⨀-⫿]")

# Document-structure / packaging commands that are NOT notation. Used to suppress
# the "missing from foundations" output when scanning a .tex file.
STRUCTURAL_DENYLIST = {
    r"\documentclass", r"\usepackage", r"\begin", r"\end", r"\section",
    r"\subsection", r"\subsubsection", r"\paragraph", r"\subparagraph",
    r"\title", r"\author", r"\date", r"\maketitle", r"\abstract",
    r"\bibliography", r"\bibliographystyle", r"\cite", r"\citep", r"\citet",
    r"\label", r"\ref", r"\eqref", r"\pageref", r"\href", r"\url",
    r"\hypersetup", r"\textbf", r"\textit", r"\texttt", r"\emph",
    r"\toprule", r"\midrule", r"\bottomrule", r"\hline", r"\tag",
    r"\item", r"\caption", r"\footnote", r"\verb", r"\noindent",
    r"\par", r"\newpage", r"\clearpage", r"\input", r"\include",
    r"\centering", r"\raggedright", r"\raggedleft",
}


def load_glossary(path: str | None) -> list[dict]:
    if path and os.path.exists(path):
        return json.loads(Path(path).read_text())
    with urllib.request.urlopen(FOUNDATIONS_URL, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def extract_symbols(text: str) -> set[str]:
    cmds = set(LATEX_CMD.findall(text))
    uni = set(UNICODE_MATH.findall(text))
    return cmds | uni


def filter_glossary(glossary: list[dict], found: set[str]) -> list[dict]:
    out = []
    for entry in glossary:
        latex = entry.get("latex", "")
        symbol = entry.get("symbol", "")
        if latex in found or symbol in found or any(latex and latex in tok for tok in found):
            out.append(entry)
    return out


def emit_markdown(rows: list[dict], missing: set[str]) -> str:
    lines = ["| Symbol | Read aloud as | Plain-English meaning |",
             "|--------|---------------|------------------------|"]
    for e in rows:
        sym = f"${e.get('latex', e.get('symbol',''))}$"
        lines.append(f"| {sym} | {e.get('read_aloud','')} | {e.get('meaning','')} |")
    for m in sorted(missing):
        lines.append(f"| `{m}` | ? | ? <!-- TODO add to foundations --> |")
    return "\n".join(lines)


def emit_latex(rows: list[dict], missing: set[str]) -> str:
    lines = [r"\begin{tabular}{lll}", r"\toprule",
             r"Symbol & Read aloud as & Meaning \\", r"\midrule"]
    for e in rows:
        sym = f"${e.get('latex', e.get('symbol',''))}$"
        lines.append(f"{sym} & {e.get('read_aloud','')} & {e.get('meaning','')} \\\\")
    for m in sorted(missing):
        lines.append(f"\\verb|{m}| & ? & ? \\\\  % TODO add to foundations")
    lines += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = [a for a in argv[1:] if a.startswith("--")]
    if not args:
        print(__doc__, file=sys.stderr); return 2
    input_path = args[0]
    glossary_path = args[1] if len(args) > 1 else None
    fmt = "latex" if input_path.endswith(".tex") else "md"
    for f in flags:
        if f.startswith("--format"):
            fmt = f.split("=", 1)[1] if "=" in f else (argv[argv.index(f)+1] if argv.index(f)+1 < len(argv) else fmt)
    text = Path(input_path).read_text()
    glossary = load_glossary(glossary_path)
    found = extract_symbols(text)
    matched = filter_glossary(glossary, found)
    matched_keys = {e.get("latex", "") for e in matched} | {e.get("symbol", "") for e in matched}
    candidate_missing = {
        tok for tok in found
        if tok.startswith("\\") and tok not in matched_keys and tok not in STRUCTURAL_DENYLIST
    }
    out = emit_latex(matched, candidate_missing) if fmt == "latex" else emit_markdown(matched, candidate_missing)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
