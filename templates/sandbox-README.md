# Sandbox: {{slug}}

> Minimal runnable experiment probing one claim from **{{title}}** ({{arxiv_url}}).

This is a subdirectory of the larger study repo — see [`../README.md`](../README.md) for the full artifact set (interview prep, math deep dive, lit review, references).

This sandbox demonstrates the paper's claims at **two levels**.

---

## The claim being probed

{{specific_claim}}

## Experiment design

{{experiment_design}}

## What would falsify the claim

{{falsification_condition}}

---

## Level 1: CPU baseline (runs anywhere)

Pure numpy, no GPU required, fast (<5 min total). Sufficient to verify the *algorithmic* claims of the paper.

| Script | Demonstrates | Runtime (CPU) |
|--------|--------------|---------------|
| `toy_{{claim_slug}}.py` | {{claim_restated}} | {{toy_runtime}} |
| `tiny_{{claim_slug}}_lm.py` | {{claim_on_tiny_lm}} | {{tiny_runtime}} |

Install + run:

```bash
pip install -r requirements.txt
python3 toy_{{claim_slug}}.py
python3 tiny_{{claim_slug}}_lm.py
```

## Level 2: Hardware-upsized (`tier_{{your_tier}}`)

Sized to the detected hardware tier (recorded in `metadata.json` → `hardware_tier`). Demonstrates the same claims at a scale where qualitative results match what would happen with a frontier model.

| Script | Demonstrates | Runtime (estimate) | Needs |
|--------|--------------|--------------------|-----|
| `torch_{{claim_slug}}.py` | {{claim_larger_model}} | ~30-60 min on MPS/CUDA | torch + MPS/CUDA |
| `real_{{claim_slug}}_lora.py` | {{claim_on_real_lm}} | ~3-4 hr on M4 Pro | torch + transformers + peft + GPU |

Install + run:

```bash
pip install -r requirements.txt
python3 torch_{{claim_slug}}.py --train      # tier-appropriate scale
python3 real_{{claim_slug}}_lora.py --train  # full LoRA fine-tune (slow; needs GPU)
```

---

## What gets measured at each level

- **Level 1** verifies the *structural* properties of the algorithm (reward shape, KL bound, sensitivity curves). These reproduce deterministically with `np.random.seed(0)`.
- **Level 2** verifies that the algorithm *transfers* to a setting closer to the paper's actual experimental regime. Numbers there will differ from Level 1 — the question is whether the qualitative shape (reward improvement, KL bound, etc.) holds.

See `findings.md` (at study repo root) for measured numbers at each level.

---

## Hardware tier note

This study's `metadata.json` lists `hardware_tier = "tier_{{your_tier}}"` from the v4.0 study-paper hardware-detection feature. Re-run with:

```bash
python3 ~/.claude/skills/study-paper/templates/detect-hardware.py --force --summary
```

to refresh.

---

## Notes

This is sandbox-grade code: optimized for clarity over performance, single-purpose, not production-ready. Level 1 prioritizes inspectability; Level 2 prioritizes fidelity to the paper's regime.
