# Stage 4 — Sandbox Scaffold

**Goal:** Generate a minimal runnable experiment probing one claim from the paper. **Local scaffold only — no git operations.** Publishing happens in Stage 6.

## Step 0: Read the hardware tier

Load `~/ai-research-studies/<slug>/metadata.json` and read `hardware_tier`, `hardware_tier_description`, `hardware_recommendations`. These come from the pre-stage 00.0 hardware detection (see `stages/00-ingest.md`).

**Size every sandbox experiment to the tier.** The `recommendations` block tells you the ceiling: `max_model_params`, `max_lora_base_params`, `training_budget_minutes`, and `recommended_frameworks`. Do not exceed these. The orchestrator should bake these constraints into any subagent prompts that scaffold the sandbox.

Concrete tier-to-sandbox mapping:

| Tier | Sandbox model size | Frameworks | Training budget |
|------|--------------------|------------|-----------------|
| `tier_cpu_only`  | ≤100 K params, numpy only | numpy | ~5 min |
| `tier_mid_cpu`   | ≤1 M params | numpy + torch CPU | ~30 min |
| `tier_low_gpu`   | ≤5 M params from scratch; LoRA on <500 M | torch (MPS/CUDA) + numpy fallback | ~1 hr |
| `tier_mid_gpu`   | ≤50 M params from scratch (TinyStories class); LoRA on 1.5-3 B | torch (MPS/CUDA) + MLX (Apple) + numpy fallback | ~4 hr |
| `tier_high_gpu`  | ≤300 M params from scratch; LoRA on 7-13 B; int4 inference on 70 B | torch + MLX + transformers + peft | ~8 hr |
| `tier_extreme`   | 1-3 B from scratch; LoRA on 30-70 B | torch + accelerate + multi-GPU | days |

**Always include a numpy fallback** for the math-clean version of any experiment, even at higher tiers — keeps the sandbox runnable on any reader's laptop. At higher tiers, the numpy demo coexists with a "real" PyTorch/MLX/transformers script that exercises the actual hardware.

If the paper category in Step A would naturally need more compute than the tier allows (e.g. RLHF on a 7 B model when tier is `tier_low_gpu`), pick a smaller proxy that demonstrates the same algorithmic claim and clearly note the simplification in `sandbox/README.md`.

## Step 0.5: Plan the two-level sandbox (MANDATORY)

Every Stage 4 sandbox must produce **two levels**:

- **Level 1 (CPU baseline)** — pure numpy, runs anywhere, fast (<5 min total). Always present, regardless of tier. Files use the prefixes `toy_*.py` (tabular MDP demos) and `tiny_*.py` (numpy tiny-GPT demos).
- **Level 2 (hardware-upsized)** — sized to the detected tier (per the table below). Demonstrates the SAME algorithm at a scale where qualitative results match what would happen with a frontier model. Files use the prefixes `torch_*.py` (torch + MPS/CUDA), `mlx_*.py` (optional Mac-native), `real_*.py` (LoRA on a real LM via transformers + peft).

### Naming conventions

| Prefix | Level | Purpose |
|--------|-------|---------|
| `toy_*.py` | 1 (CPU) | Tabular MDP toys; pure numpy; <30s. |
| `tiny_*.py` | 1 (CPU) | Numpy tiny-GPT-class demos; <300s. |
| `torch_*.py` | 2 (upsized) | torch + MPS/CUDA; tier-appropriate model size. |
| `mlx_*.py` | 2 (Mac-native, optional) | MLX-native parallel cell for Apple silicon. |
| `real_*.py` | 2 (highest tiers) | LoRA on a real LM (transformers + peft); needs real weights. |

### Per-tier script mandate

| Tier | Level 1 (always) | Level 2 (when tier supports) |
|------|------------------|------------------------------|
| `tier_cpu_only`  | `toy_*.py` + `tiny_*.py` | (none — Level 1 IS the only level) |
| `tier_mid_cpu`   | `toy_*.py` + `tiny_*.py` | (none — Level 1 only) |
| `tier_low_gpu`   | `toy_*.py` + `tiny_*.py` | `torch_*.py` (≤5M params) |
| `tier_mid_gpu`   | `toy_*.py` + `tiny_*.py` | `torch_*.py` (~30M) + `real_*.py` (LoRA on ≤3B) |
| `tier_high_gpu`  | `toy_*.py` + `tiny_*.py` | `torch_*.py` (~100M) + `mlx_*.py` + `real_*.py` (LoRA on 7-13B) |
| `tier_extreme`   | `toy_*.py` + `tiny_*.py` | All Level-2 forms, multi-GPU options |

### Smoke-test contract for Level 2

Subagents in any given Stage 4 dispatch cannot reliably exercise the GPU (Linux box, no Mac access). So:
- **Level 1 scripts MUST run end-to-end during the agent's smoke-test.**
- **Level 2 scripts MUST parse cleanly (`ast.parse`) and either run with `--steps 1` successfully OR print a clear "install X / run on a GPU host" message and exit 0.** They are NOT required to train during agent runtime — the user runs them on their primary device.

### Skeletons available

Subagents can copy from `~/.claude/skills/study-paper/templates/sandbox-torch-skeleton.py` (torch + MPS/CUDA + numpy fallback) and `~/.claude/skills/study-paper/templates/sandbox-real-lm-skeleton.py` (LoRA on real LM via transformers + peft). Both wrap heavy imports in try/except so they parse on Linux without GPU deps.

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
