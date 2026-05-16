#!/usr/bin/env python3
"""
sandbox-torch-skeleton.py — Level-2 torch + MPS/CUDA sandbox skeleton.

This is a GENERIC skeleton that the per-study Stage 4 sandbox-build agent
copies and specializes for the paper at hand. It is intentionally
study-agnostic; the agent replaces:

  - `train_step(...)` body with the paper's training loss / update rule.
  - `TinyGPTConfig` defaults if the paper's regime differs.
  - data loading (`load_corpus`, `make_data`) with the paper's dataset.

Default architecture: ~30M-param decoder-only GPT in PyTorch, trained on
a small text corpus.

    Layers=6, d_model=384, heads=6, d_k=64, d_ff=1536, ctx=256.
    Tokenizer: tiktoken gpt2 (50257) if available, char-level fallback.
    Optim:     AdamW + linear warmup -> cosine decay, grad-clip 1.0.
    Devices:   MPS > CUDA > CPU.

IMPORTANT — Linux parse-safety contract
---------------------------------------
This file is *importable* on any platform. If torch is not installed, the
script prints a clear install message and exits 0. This lets a Stage-4
sandbox subagent smoke-test the file with `python3 file.py --steps 1`
even on a Linux box without GPU dependencies.

CLI
---
    python3 sandbox-torch-skeleton.py --steps 5    # smoke test (CPU OK)
    python3 sandbox-torch-skeleton.py --train      # full ~3000-step run
    python3 sandbox-torch-skeleton.py --sample     # generate from checkpoint
"""
from __future__ import annotations

import argparse
import math
import os
import sys
import time
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# 1. Soft imports — parse cleanly even without torch installed.
# ---------------------------------------------------------------------------

_MISSING: list[str] = []
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
except Exception:  # pragma: no cover — exercised on Linux without torch
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]
    F = None  # type: ignore[assignment]
    _MISSING.append("torch>=2.4")


def _print_install_message_and_exit() -> None:
    msg = (
        "sandbox-torch-skeleton.py: required packages not installed: "
        + ", ".join(_MISSING)
        + "\n\n"
        "Install (Apple Silicon recommended):\n"
        "    pip install torch\n\n"
        "Or run on a GPU host (CUDA or MPS). Exiting cleanly (0)."
    )
    print(msg)
    sys.exit(0)


def pick_device() -> str:
    """MPS > CUDA > CPU. Caller has already verified torch is importable."""
    assert torch is not None
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


# ---------------------------------------------------------------------------
# 2. Config
# ---------------------------------------------------------------------------

@dataclass
class TinyGPTConfig:
    """~30M-param decoder-only transformer config."""
    vocab_size: int = 50257
    n_layer: int = 6
    n_head: int = 6
    d_model: int = 384
    d_ff: int = 1536
    ctx_len: int = 256
    dropout: float = 0.0


# ---------------------------------------------------------------------------
# 3. Tokenizer (tiktoken if available, char-level fallback)
# ---------------------------------------------------------------------------

class CharTokenizer:
    """Fallback tokenizer when tiktoken is unavailable."""

    def __init__(self, text: str):
        chars = sorted(set(text)) if text else list("abcdefghijklmnopqrstuvwxyz \n")
        self.stoi = {c: i for i, c in enumerate(chars)}
        self.itos = {i: c for i, c in enumerate(chars)}
        self.vocab_size = len(chars)

    def encode(self, s: str):
        return [self.stoi[c] for c in s if c in self.stoi]

    def decode(self, ids):
        return "".join(self.itos.get(int(i), "") for i in ids)


def build_tokenizer(text_for_fallback: str):
    try:
        import tiktoken
        enc = tiktoken.get_encoding("gpt2")

        class _Tik:
            vocab_size = enc.n_vocab

            def encode(self, s: str):
                return enc.encode_ordinary(s)

            def decode(self, ids):
                return enc.decode(list(ids))

        return _Tik()
    except Exception:
        return CharTokenizer(text_for_fallback)


# ---------------------------------------------------------------------------
# 4. Model — only defined if torch imported successfully.
# ---------------------------------------------------------------------------

if torch is not None:

    class CausalSelfAttention(nn.Module):
        def __init__(self, cfg: TinyGPTConfig):
            super().__init__()
            assert cfg.d_model % cfg.n_head == 0
            self.n_head = cfg.n_head
            self.d_head = cfg.d_model // cfg.n_head
            self.qkv = nn.Linear(cfg.d_model, 3 * cfg.d_model, bias=False)
            self.proj = nn.Linear(cfg.d_model, cfg.d_model, bias=False)
            self.dropout = cfg.dropout
            mask = torch.tril(torch.ones(cfg.ctx_len, cfg.ctx_len)).view(
                1, 1, cfg.ctx_len, cfg.ctx_len
            )
            self.register_buffer("mask", mask, persistent=False)

        def forward(self, x):
            B, T, C = x.shape
            qkv = self.qkv(x).view(B, T, 3, self.n_head, self.d_head)
            q, k, v = qkv.unbind(dim=2)
            q = q.transpose(1, 2)
            k = k.transpose(1, 2)
            v = v.transpose(1, 2)
            att = (q @ k.transpose(-2, -1)) / math.sqrt(self.d_head)
            att = att.masked_fill(self.mask[:, :, :T, :T] == 0, float("-inf"))
            att = F.softmax(att, dim=-1)
            if self.training and self.dropout > 0:
                att = F.dropout(att, p=self.dropout)
            y = att @ v
            y = y.transpose(1, 2).contiguous().view(B, T, C)
            return self.proj(y)

    class Block(nn.Module):
        def __init__(self, cfg: TinyGPTConfig):
            super().__init__()
            self.ln1 = nn.LayerNorm(cfg.d_model)
            self.attn = CausalSelfAttention(cfg)
            self.ln2 = nn.LayerNorm(cfg.d_model)
            self.mlp = nn.Sequential(
                nn.Linear(cfg.d_model, cfg.d_ff, bias=False),
                nn.GELU(),
                nn.Linear(cfg.d_ff, cfg.d_model, bias=False),
            )

        def forward(self, x):
            x = x + self.attn(self.ln1(x))
            x = x + self.mlp(self.ln2(x))
            return x

    class TinyGPT(nn.Module):
        def __init__(self, cfg: TinyGPTConfig):
            super().__init__()
            self.cfg = cfg
            self.tok_emb = nn.Embedding(cfg.vocab_size, cfg.d_model)
            self.pos_emb = nn.Embedding(cfg.ctx_len, cfg.d_model)
            self.blocks = nn.ModuleList([Block(cfg) for _ in range(cfg.n_layer)])
            self.ln_f = nn.LayerNorm(cfg.d_model)
            self.head = nn.Linear(cfg.d_model, cfg.vocab_size, bias=False)
            # Tie weights.
            self.head.weight = self.tok_emb.weight

        def forward(self, idx, targets=None):
            B, T = idx.shape
            assert T <= self.cfg.ctx_len
            pos = torch.arange(T, device=idx.device).unsqueeze(0)
            x = self.tok_emb(idx) + self.pos_emb(pos)
            for blk in self.blocks:
                x = blk(x)
            x = self.ln_f(x)
            logits = self.head(x)
            loss = None
            if targets is not None:
                loss = F.cross_entropy(
                    logits.view(-1, logits.size(-1)), targets.view(-1)
                )
            return logits, loss

        @torch.no_grad()
        def generate(self, idx, max_new_tokens: int, temperature: float = 1.0):
            for _ in range(max_new_tokens):
                idx_cond = idx[:, -self.cfg.ctx_len :]
                logits, _ = self(idx_cond)
                logits = logits[:, -1, :] / max(temperature, 1e-8)
                probs = F.softmax(logits, dim=-1)
                nxt = torch.multinomial(probs, num_samples=1)
                idx = torch.cat([idx, nxt], dim=1)
            return idx


# ---------------------------------------------------------------------------
# 5. Data
# ---------------------------------------------------------------------------

def load_corpus(max_chars: int = 200_000) -> str:
    """Per-study agent: replace with the paper's dataset.

    Default: a tiny synthetic corpus so the skeleton runs end-to-end
    without external downloads.
    """
    return ("once upon a time there was a tiny model that wanted to learn. "
            "the end. " * 5000)[:max_chars]


def make_data(tokens, ctx_len: int, batch_size: int, device: str):
    assert torch is not None
    data = torch.tensor(tokens, dtype=torch.long)
    n = data.numel() - ctx_len - 1
    if n <= 0:
        raise ValueError("Corpus too small for ctx_len.")
    ix = torch.randint(0, n, (batch_size,))
    x = torch.stack([data[i : i + ctx_len] for i in ix]).to(device)
    y = torch.stack([data[i + 1 : i + 1 + ctx_len] for i in ix]).to(device)
    return x, y


# ---------------------------------------------------------------------------
# 6. Train step — per-study agent replaces this body with the paper's loss.
# ---------------------------------------------------------------------------

def train_step(model, optimizer, batch, *, step: int, total_steps: int):
    """Generic supervised-CE step. The per-study agent overwrites this.

    For RL papers: compute log-probs of the rollout actions, multiply by
    advantages, add KL-to-reference, etc.

    For architecture papers: this is fine as-is.
    """
    assert torch is not None
    x, y = batch
    _, loss = model(x, targets=y)
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    optimizer.step()
    return float(loss.item())


# ---------------------------------------------------------------------------
# 7. Driver
# ---------------------------------------------------------------------------

def train(steps: int, full: bool) -> None:
    device = pick_device()
    print(f"[device] {device}")

    text = load_corpus()
    tok = build_tokenizer(text)
    cfg = TinyGPTConfig(vocab_size=tok.vocab_size, ctx_len=128)
    model = TinyGPT(cfg).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"[model ] TinyGPT params={n_params/1e6:.2f}M ctx={cfg.ctx_len}")

    tokens = tok.encode(text)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, betas=(0.9, 0.95))

    target_steps = 3000 if full else steps
    t0 = time.time()
    for step in range(1, target_steps + 1):
        batch = make_data(tokens, cfg.ctx_len, batch_size=8, device=device)
        loss = train_step(model, optimizer, batch, step=step, total_steps=target_steps)
        if step == 1 or step % max(1, target_steps // 10) == 0:
            print(f"[train ] step={step:4d}/{target_steps} loss={loss:.4f}")
    dt = time.time() - t0
    print(f"[done  ] {target_steps} steps in {dt:.1f}s")

    ckpt = os.path.join(os.path.dirname(__file__) or ".", "tinygpt.pt")
    torch.save({"model": model.state_dict(), "cfg": cfg.__dict__}, ckpt)
    print(f"[save  ] {ckpt}")


def sample_from_ckpt(prompt: str = "once upon a time", n_new: int = 100) -> None:
    device = pick_device()
    ckpt_path = os.path.join(os.path.dirname(__file__) or ".", "tinygpt.pt")
    if not os.path.exists(ckpt_path):
        print(f"[sample] no checkpoint at {ckpt_path}; run --train first.")
        return
    blob = torch.load(ckpt_path, map_location=device)
    cfg = TinyGPTConfig(**blob["cfg"])
    model = TinyGPT(cfg).to(device)
    model.load_state_dict(blob["model"])
    model.eval()

    text = load_corpus()
    tok = build_tokenizer(text)
    ids = torch.tensor([tok.encode(prompt)], dtype=torch.long, device=device)
    out = model.generate(ids, max_new_tokens=n_new, temperature=0.9)
    print(tok.decode(out[0].tolist()))


def main() -> None:
    if _MISSING:
        _print_install_message_and_exit()

    p = argparse.ArgumentParser()
    p.add_argument("--steps", type=int, default=10, help="smoke-test steps")
    p.add_argument("--train", action="store_true", help="full ~3000-step run")
    p.add_argument("--sample", action="store_true", help="load ckpt + generate")
    args = p.parse_args()

    if args.sample:
        sample_from_ckpt()
        return
    train(steps=args.steps, full=args.train)


if __name__ == "__main__":
    main()
