#!/usr/bin/env python3
"""
sandbox-real-lm-skeleton.py — Level-2 LoRA-on-real-LM sandbox skeleton.

The full-fat companion to the numpy + torch sandboxes. Mirrors the algorithm
from the paper, but wired into a real Hugging Face transformer using LoRA so
the whole thing fits on a single Apple Silicon laptop (M4 Pro, 48 GB unified)
or a mid-range CUDA GPU.

This is a GENERIC skeleton that the per-study Stage 4 sandbox-build agent
copies and specializes. The agent replaces:

  - `MODEL_ID` if the paper's regime needs a different base model.
  - `build_episodes(...)` with the paper-specific dataset / task.
  - `compute_loss(...)` with the paper's actual loss (PPO-clipped surrogate,
    DPO logit difference, GRPO with KL, RFT cross-entropy, etc.).
  - the reward function if RL.

Hardware
--------
This file is *importable* on any platform: if torch / transformers / peft
are missing it prints a clear install message and exits 0. Real training
needs Apple Silicon MPS or a CUDA GPU.

Memory hints
------------
- bf16 by default (Apple MPS supports it via autocast; CUDA fp16/bf16).
- No gradient checkpointing initially — turn on if OOM at >3B base.
- 1.5B-3B base models fit comfortably in 48 GB unified memory with LoRA
  rank 16. Bump to 7-13B on a 24 GB+ CUDA card.

CLI
---
    python3 sandbox-real-lm-skeleton.py --steps 1   # smoke (~10 min on MPS)
    python3 sandbox-real-lm-skeleton.py --train     # full run (~3-4 hr)
    python3 sandbox-real-lm-skeleton.py --eval      # load adapter, run eval
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# 1. Soft imports + device detection
# ---------------------------------------------------------------------------

_MISSING: list[str] = []
try:
    import torch
    import torch.nn.functional as F
except Exception:  # pragma: no cover — exercised on Linux without torch
    torch = None  # type: ignore[assignment]
    F = None  # type: ignore[assignment]
    _MISSING.append("torch>=2.4")

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
except Exception:  # pragma: no cover
    AutoModelForCausalLM = None  # type: ignore[assignment]
    AutoTokenizer = None  # type: ignore[assignment]
    _MISSING.append("transformers>=4.45")

try:
    from peft import LoraConfig, PeftModel, get_peft_model
except Exception:  # pragma: no cover
    LoraConfig = None  # type: ignore[assignment]
    PeftModel = None  # type: ignore[assignment]
    get_peft_model = None  # type: ignore[assignment]
    _MISSING.append("peft>=0.12")

try:
    import accelerate  # noqa: F401 — used implicitly by transformers
except Exception:  # pragma: no cover
    _MISSING.append("accelerate>=0.34")


def _print_install_message_and_exit() -> None:
    msg = (
        "sandbox-real-lm-skeleton.py: required packages not installed: "
        + ", ".join(_MISSING)
        + "\n\n"
        "Install (Apple Silicon recommended):\n"
        "    pip install torch transformers peft accelerate\n\n"
        "Or run on a GPU host (CUDA or MPS). Exiting cleanly (0)."
    )
    print(msg)
    sys.exit(0)


def detect_device() -> str:
    """MPS > CUDA > CPU. Caller has already verified torch is importable."""
    assert torch is not None
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


# ---------------------------------------------------------------------------
# 2. Constants — per-study agent overrides
# ---------------------------------------------------------------------------

MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"  # tier_mid_gpu default

# LoRA targets q/k/v/o projections — works for most modern decoder-only LMs.
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
LORA_TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj"]

CKPT_DIR = Path(__file__).parent / "lora_ckpt"


# ---------------------------------------------------------------------------
# 3. Episode / data types — per-study agent overrides
# ---------------------------------------------------------------------------

@dataclass
class Episode:
    """Generic episode. Per-study agent extends with task-specific fields."""

    prompt: str
    gold: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


def build_episodes(seed: int = 0, n: int = 16) -> list[Episode]:
    """Per-study agent: replace with paper's dataset / task.

    Default: a trivial copy-the-keyword task so the skeleton runs without
    external downloads.
    """
    rng = random.Random(seed)
    bank = ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot",
            "golf", "hotel", "india", "juliet"]
    episodes = []
    for _ in range(n):
        kw = rng.choice(bank)
        episodes.append(Episode(prompt=f"Repeat the keyword: {kw}\nAnswer:", gold=kw))
    return episodes


# ---------------------------------------------------------------------------
# 4. Model load
# ---------------------------------------------------------------------------

def load_model_and_tokenizer(device: str):
    """Load base model in bf16, attach LoRA, return (model, tokenizer)."""
    assert torch is not None
    print(f"[load ] base model {MODEL_ID}")
    dtype = torch.bfloat16
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    base = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=dtype,
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    )

    lora_cfg = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=LORA_TARGETS,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(base, lora_cfg)
    model.to(device)

    # Trainable-param count.
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(
        f"[lora ] r={LORA_R} alpha={LORA_ALPHA} dropout={LORA_DROPOUT}"
        f" targets={LORA_TARGETS}"
    )
    print(
        f"[params] trainable={trainable/1e6:.2f}M / total={total/1e9:.2f}B"
        f" ({100*trainable/total:.3f}%)"
    )
    return model, tokenizer


# ---------------------------------------------------------------------------
# 5. Loss — per-study agent replaces this body with the paper's actual loss.
# ---------------------------------------------------------------------------

def compute_loss(model, tokenizer, episode: Episode, device: str):
    """Generic supervised next-token CE loss on (prompt + gold).

    Per-study agent overrides for:
      - PPO/GRPO: compute log-probs of rollout actions, multiply by advantages.
      - DPO: log-sigmoid of (preferred - rejected) log-prob delta.
      - RFT: filter on reward then standard CE.
      - KL-regularized: add beta * KL(policy || ref).
    """
    assert torch is not None
    text = episode.prompt + " " + episode.gold
    enc = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    input_ids = enc["input_ids"].to(device)
    attn = enc["attention_mask"].to(device)
    labels = input_ids.clone()
    out = model(input_ids=input_ids, attention_mask=attn, labels=labels)
    return out.loss


# ---------------------------------------------------------------------------
# 6. Train / eval drivers
# ---------------------------------------------------------------------------

def train(steps: int, log_every: int = 1) -> None:
    device = detect_device()
    print(f"[device] {device}")
    model, tokenizer = load_model_and_tokenizer(device)
    optimizer = torch.optim.AdamW(
        (p for p in model.parameters() if p.requires_grad),
        lr=1e-4, betas=(0.9, 0.95),
    )

    episodes = build_episodes(seed=0, n=max(steps * 2, 16))
    rng = random.Random(0)
    t0 = time.time()
    for step in range(1, steps + 1):
        ep = rng.choice(episodes)
        loss = compute_loss(model, tokenizer, ep, device)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(
            [p for p in model.parameters() if p.requires_grad], 1.0
        )
        optimizer.step()
        if step == 1 or step % max(1, log_every) == 0:
            print(f"[train ] step={step:4d}/{steps} loss={float(loss.item()):.4f}")
    dt = time.time() - t0
    print(f"[done  ] {steps} steps in {dt:.1f}s")

    CKPT_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(CKPT_DIR))
    tokenizer.save_pretrained(str(CKPT_DIR))
    print(f"[save  ] adapter -> {CKPT_DIR}")


def evaluate() -> None:
    device = detect_device()
    print(f"[device] {device}")
    if not CKPT_DIR.exists():
        print(f"[eval  ] no adapter at {CKPT_DIR}; run --train first.")
        return
    tokenizer = AutoTokenizer.from_pretrained(str(CKPT_DIR), trust_remote_code=True)
    base = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, torch_dtype=torch.bfloat16, trust_remote_code=True,
    )
    model = PeftModel.from_pretrained(base, str(CKPT_DIR))
    model.to(device)
    model.eval()

    episodes = build_episodes(seed=42, n=8)
    correct = 0
    for ep in episodes:
        enc = tokenizer(ep.prompt, return_tensors="pt").to(device)
        with torch.no_grad():
            out = model.generate(**enc, max_new_tokens=8, do_sample=False)
        decoded = tokenizer.decode(out[0], skip_special_tokens=True)
        ok = ep.gold.lower() in decoded.lower()
        correct += int(ok)
        print(f"[eval  ] gold={ep.gold!r:12s} ok={ok} :: {decoded!r}")
    print(f"[eval  ] {correct}/{len(episodes)} correct")


# ---------------------------------------------------------------------------
# 7. CLI
# ---------------------------------------------------------------------------

def main() -> None:
    if _MISSING:
        _print_install_message_and_exit()

    p = argparse.ArgumentParser()
    p.add_argument("--steps", type=int, default=1, help="smoke-test steps")
    p.add_argument("--train", action="store_true", help="full LoRA fine-tune")
    p.add_argument("--eval", action="store_true", help="load adapter + eval")
    args = p.parse_args()

    if args.eval:
        evaluate()
        return
    n_steps = 200 if args.train else args.steps
    train(steps=n_steps, log_every=max(1, n_steps // 20))


if __name__ == "__main__":
    main()
