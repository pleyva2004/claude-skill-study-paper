# Stage 4 — Sandbox Scaffold

**Goal:** Generate a minimal runnable experiment probing one claim from the paper, then publish to GitHub as `ai-study-<slug>`.

## Step A: Categorize

Determine paper category from `01-interview-prep.md` and metadata. Map to sandbox archetype:

| Paper category | Sandbox archetype |
|----------------|-------------------|
| Attention/architecture (e.g. Flash Attention, Mamba, MoE) | Tiny PyTorch implementation + benchmark vs reference impl on small input |
| RL algorithm (PPO, GRPO, DPO, RLHF variants) | Minimal Gym/MiniGrid harness running the algorithm; log return curves |
| Training technique (curriculum, distillation, scaling) | Small-scale ablation: with vs without the technique on a tiny task |
| Evaluation/benchmark | Reproduce one row of the benchmark table on one model |
| Memory/context (attention sinks, RoPE variants, retrieval) | Toy reproduction of the proposed property on synthetic data |
| Theory-only (no experiments) | Numerical verification of one theorem on a small case |

If the paper doesn't fit, ask the user which claim they most want to probe.

## Step B: Scaffold

Create `~/ai-research-studies/<slug>/sandbox/`:

```
sandbox/
  README.md           # what the experiment probes, how to run, expected output
  requirements.txt    # PyTorch by default; JAX only if paper uses JAX
  experiment.py       # main script — runnable end-to-end
  utils.py            # helpers if needed
  .gitignore          # standard Python ignores + checkpoints
```

Defaults:
- **PyTorch** unless paper uses JAX.
- **CPU-runnable** — small enough to finish in <60 seconds on a laptop. If a GPU is required for the experiment to make sense, document the GPU run command and provide a CPU smoke-test fallback.
- **Single command to run**: `python experiment.py` should work after `pip install -r requirements.txt`.
- README states: paper title + arxiv link, the specific claim being probed, the experiment design, expected output, "what would falsify the claim".

Use `templates/sandbox-README.md` as the README template.

## Step C: Show + Confirm

Show the user:
- File tree of `sandbox/`
- Diff/preview of each file
- The exact `gh repo create` command that will run

**Wait for explicit confirmation** before publishing. Do not auto-push.

## Step D: Publish

On confirmation, run from inside `sandbox/`:
```
git init -b main
git add .
git commit -m "Initial scaffold for ai-study-<slug>"
gh repo create ai-study-<slug> --public --source=. --push --description "Sandbox study of: <paper title>"
```

If `gh` is not authenticated, do NOT attempt the push. Print the exact command for the user to run manually.

Update `metadata.json` with `"github_url": "<url>"`.

## Output

```
Sandbox: ~/ai-research-studies/<slug>/sandbox/
Published: https://github.com/<user>/ai-study-<slug>
Ready for Stage 5 (case study). Continue?
```
