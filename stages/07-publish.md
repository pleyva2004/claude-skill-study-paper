# Stage 7 — Publish (whole study to GitHub)

**Goal:** Publish the entire study directory to GitHub as `<slug>` — including interview prep, math deep dive, opinion capture, lit review, improvements + prototypes, references, source PDF, and sandbox subdir. **The repo is the study, not just the sandbox.**

## Mandate

This stage runs **after** Stage 5 (literature review) so the published repo contains the complete artifact set. Force-push and destructive operations require explicit user confirmation.

## Inputs

- Everything in `~/ai-research-studies/<slug>/` produced by Stages 0-5
- User's GitHub username (read from `~/.config/study-paper/config.json` if present, else prompt and persist)

## Step A: Top-level README + .gitignore + CI render workflow

Write `~/ai-research-studies/<slug>/README.md` using `templates/study-README.md`. This README frames the study as a coherent published artifact — links to all sub-files, explains the paper, gives build instructions for the lit review (`pdflatex`) and sandbox (`pip install + python`), and notes the dual license (paper = CC BY 4.0 if applicable, rest = MIT). Include the **Render LaTeX** build status badge and PDF links — these light up once the workflow runs on first push.

Copy `templates/render-workflow.yml` to `~/ai-research-studies/<slug>/.github/workflows/render.yml`. On every push that touches `.tex` or `.bib` files, this workflow compiles them with `pdflatex` via the `xu-cheng/latex-action` GitHub Action and auto-commits the resulting PDFs to `pdfs/` with a `[skip ci]` marker.

Write `~/ai-research-studies/<slug>/.gitignore`:
```
# Python
__pycache__/
*.pyc
.venv/
venv/
.cache/
*.pt
*.bin

# OS
.DS_Store

# LaTeX byproducts (keep source.pdf — that's the paper, not a build artifact)
*.aux
*.log
*.bbl
*.blg
*.out
*.toc
*.fls
*.fdb_latexmk
*.synctex.gz
04-literature-review.pdf
```

## Step B: Git init + commit

```shell
cd ~/ai-research-studies/<slug>/
git init -b main
git add 01-interview-prep.md 02-math-deep-dive.md 03-opinions.md \
        04-literature-review.tex 05-improvements.tex references.bib metadata.json \
        source.pdf README.md .gitignore \
        .github/workflows/render.yml \
        sandbox/README.md sandbox/experiment.py sandbox/requirements.txt \
        improvements/README.md improvements/requirements.txt improvements/*.py
git commit -m "Initial commit: full study artifacts for arxiv:<id>"
```

Note: explicit file list (not `git add .`) avoids accidentally committing `__pycache__`, downloaded model weights, or compile byproducts.

## Step C: Create the GitHub repo + push

Two paths depending on environment:

### Path 1 — `gh` CLI available + authenticated

```shell
gh auth status >/dev/null 2>&1 && \
gh repo create <slug> --public --source=. --push \
  --description "Layered study of: <paper title> (arxiv:<id>)"
```

**Confirm before this command runs.** Public publish is hard to reverse.

### Path 2 — `gh` not available, SSH push

If `gh` is missing or unauthed, fall back to SSH:

1. Print the pre-filled GitHub "new repo" URL:
   ```
   https://github.com/new?name=<slug>&description=Layered+study+of+arxiv+<id>&visibility=public
   ```
   Tell the user: open this URL, click "Create repository", **leave "Add a README" / `.gitignore` / license unchecked**, then say "go".

2. After confirmation, push via SSH (no PAT needed if SSH key is registered with GitHub):
   ```shell
   git remote add origin git@github.com:<user>/<slug>.git
   git push -u origin main
   ```

3. If push is rejected with "fetch first" (user accidentally let GitHub auto-create a README), confirm with user, then `git push --force origin main`.

## Step D: Update metadata + report

Update `metadata.json` with `"github_url": "https://github.com/<user>/<slug>"`. Edit `04-literature-review.tex` to replace any `<user>` placeholder in the Sandbox Probe section with the real username, then commit + push the fix.

Output:
```
Published: https://github.com/<user>/<slug>
Files in repo: <count>
Total size: <size>
Study fully complete.
```

## Configuration

GitHub username persists across runs at `~/.config/study-paper/config.json`:
```json
{
  "github_username": "<user>",
  "default_visibility": "public",
  "prefer_ssh": true
}
```

First run prompts and writes this; subsequent runs read it.

## Edge Cases

- **`git` not installed** → abort, ask user to install
- **No SSH key registered with GitHub and no `gh`** → tell user to either run `ssh-keygen + paste pubkey to github.com/settings/keys`, or install `gh`
- **Repo already exists on GitHub from a prior study** → ask whether to force-push (overwrite) or skip publish
- **User wants private** → toggle `--visibility private` in gh path, or `?visibility=private` in URL fallback
