# Stage 4 — Sandbox Scaffold

**Goal:** Generate a minimal runnable experiment probing one claim from the paper. **Local scaffold only — no git operations.** Publishing happens in Stage 6.

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
```

Use `templates/sandbox-README.md` as the sub-README template — it now positions the sandbox as a subdirectory of the larger study repo (not a standalone repo).

Defaults:
- **PyTorch** unless paper uses JAX.
- **CPU-runnable** — small enough to finish in <60 seconds on a laptop. If a GPU is required for the experiment to make sense, document the GPU run command and provide a CPU smoke-test fallback.
- **Single command to run**: `python experiment.py` should work after `pip install -r requirements.txt`.
- README states: paper title + arxiv link, the specific claim being probed, the experiment design, expected output, "what would falsify the claim".

## Step C: Show

Show the user the file tree of `sandbox/` and the diff/preview of each file. **No confirmation needed at this stage** — nothing is being published yet. Publishing to GitHub is Stage 6's responsibility, after the literature review is also generated.

## Output

```
Sandbox scaffolded: ~/ai-research-studies/<slug>/sandbox/
Files: README.md, experiment.py, requirements.txt, utils.py (if needed)
Ready for Stage 5 (literature review). Continue?
```
