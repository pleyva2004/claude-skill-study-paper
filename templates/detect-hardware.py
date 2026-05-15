#!/usr/bin/env python3
"""
detect-hardware.py — detect available compute and cache a sizing tier so the
study-paper skill's Stage 4 (sandbox) can size experiments to the user's machine.

Cache: ~/.claude/skills/study-paper/cache/hardware.json
TTL:   30 days (re-run with --force to refresh sooner)

Tiers:
  tier_cpu_only   no GPU, low RAM
  tier_mid_cpu    no GPU but >=64 GB RAM
  tier_low_gpu    NVIDIA <8 GB VRAM, or Apple Silicon <16 GB unified
  tier_mid_gpu    NVIDIA 8-23 GB, or Apple Silicon 16-47 GB unified
  tier_high_gpu   NVIDIA 24-47 GB, or Apple Silicon 48-95 GB unified
  tier_extreme    NVIDIA multi-GPU, or 96+ GB unified

Each tier carries concrete recommendations (max model params, frameworks,
training-budget minutes) that Stage 4 reads to scaffold experiments.

CLI:
    python3 detect-hardware.py                # use cache if fresh, else detect
    python3 detect-hardware.py --force        # always re-detect
    python3 detect-hardware.py --summary      # short human-readable output
    python3 detect-hardware.py --print-only   # detect + print, do not write cache
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

CACHE_PATH = Path.home() / ".claude" / "skills" / "study-paper" / "cache" / "hardware.json"
CACHE_TTL_DAYS = 30


def _run(cmd: list[str], timeout: float = 8.0) -> str | None:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout if r.returncode == 0 else None
    except Exception:
        return None


def detect_os() -> dict[str, Any]:
    release = platform.release().lower()
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "is_wsl": "microsoft" in release or "wsl" in release,
        "is_mac": platform.system() == "Darwin",
        "is_linux": platform.system() == "Linux",
    }


def detect_cpu() -> dict[str, Any]:
    info: dict[str, Any] = {
        "logical_cores": os.cpu_count(),
        "physical_cores": None,
        "model": None,
    }
    if platform.system() == "Darwin":
        out = _run(["sysctl", "-n", "hw.physicalcpu"])
        if out and out.strip().isdigit():
            info["physical_cores"] = int(out.strip())
        brand = _run(["sysctl", "-n", "machdep.cpu.brand_string"])
        if brand:
            info["model"] = brand.strip()
    elif platform.system() == "Linux":
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.startswith("model name"):
                        info["model"] = line.split(":", 1)[1].strip()
                        break
        except Exception:
            pass
    return info


def detect_ram() -> dict[str, Any]:
    if platform.system() == "Darwin":
        total = _run(["sysctl", "-n", "hw.memsize"])
        if total and total.strip().isdigit():
            t = int(total.strip()) / (1024 ** 3)
            return {"total_gb": round(t, 1), "available_gb": None}
    elif platform.system() == "Linux":
        try:
            with open("/proc/meminfo") as f:
                fields = {}
                for line in f:
                    name = line.split(":", 1)[0]
                    if name in ("MemTotal", "MemAvailable"):
                        fields[name] = int(line.split()[1])  # kB
            return {
                "total_gb": round(fields.get("MemTotal", 0) / (1024 ** 2), 1),
                "available_gb": round(fields.get("MemAvailable", 0) / (1024 ** 2), 1) if "MemAvailable" in fields else None,
            }
        except Exception:
            pass
    return {"total_gb": None, "available_gb": None}


def _detect_nvidia() -> dict[str, Any] | None:
    out = _run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"])
    if not out or not out.strip():
        return None
    lines = [ln for ln in out.strip().splitlines() if ln.strip()]
    parts = [p.strip() for p in lines[0].split(",")]
    if len(parts) < 2 or not parts[1].isdigit():
        return None
    return {
        "vendor": "NVIDIA",
        "name": parts[0],
        "vram_mb": int(parts[1]),
        "vram_gb": round(int(parts[1]) / 1024, 1),
        "is_unified": False,
        "gpu_count": len(lines),
    }


def _detect_apple_silicon(ram: dict[str, Any]) -> dict[str, Any] | None:
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        return None
    chip = _run(["sysctl", "-n", "machdep.cpu.brand_string"])
    gpu_cores = None
    sys_prof = _run(["system_profiler", "SPDisplaysDataType", "-detailLevel", "mini"])
    if sys_prof:
        for line in sys_prof.splitlines():
            if "Total Number of Cores" in line:
                try:
                    gpu_cores = int(line.split(":")[-1].strip())
                except Exception:
                    pass
                break
    return {
        "vendor": "Apple",
        "name": chip.strip() if chip else "Apple Silicon",
        "gpu_cores": gpu_cores,
        "vram_gb": ram.get("total_gb"),  # unified memory == RAM
        "is_unified": True,
        "gpu_count": 1,
    }


def detect_gpu(ram: dict[str, Any]) -> dict[str, Any]:
    """Priority: NVIDIA > Apple Silicon > none."""
    nv = _detect_nvidia()
    if nv:
        return nv
    apple = _detect_apple_silicon(ram)
    if apple:
        return apple
    return {"vendor": "none", "name": None, "vram_gb": 0, "is_unified": False, "gpu_count": 0}


def detect_disk() -> dict[str, Any]:
    try:
        total, _, free = shutil.disk_usage(str(Path.home()))
        return {
            "free_gb": round(free / (1024 ** 3), 1),
            "total_gb": round(total / (1024 ** 3), 1),
        }
    except Exception:
        return {"free_gb": None, "total_gb": None}


def detect_ml_libs() -> dict[str, Any]:
    libs: dict[str, Any] = {}
    for canonical, import_name in [
        ("torch", "torch"),
        ("mlx", "mlx.core"),
        ("transformers", "transformers"),
        ("peft", "peft"),
        ("accelerate", "accelerate"),
        ("jax", "jax"),
        ("tensorflow", "tensorflow"),
        ("tiktoken", "tiktoken"),
    ]:
        try:
            __import__(import_name)
            libs[canonical] = True
        except Exception:
            libs[canonical] = False
    if libs.get("torch"):
        try:
            import torch
            libs["torch_version"] = torch.__version__
            libs["torch_cuda_available"] = bool(torch.cuda.is_available())
            mps = getattr(torch.backends, "mps", None)
            libs["torch_mps_available"] = bool(mps and mps.is_available())
        except Exception:
            pass
    return libs


# ---------------------------------------------------------------- tier logic --

TIER_RECS = {
    "tier_cpu_only": {
        "max_model_params": 100_000,
        "max_lora_base_params": 0,
        "training_budget_minutes": 5,
        "recommended_frameworks": ["numpy"],
        "guidance": (
            "Use numpy-only toy MDPs and tiny GPTs (<100K params). No LoRA "
            "fine-tuning is feasible. Cap training at ~5 min runs."
        ),
    },
    "tier_mid_cpu": {
        "max_model_params": 1_000_000,
        "max_lora_base_params": 0,
        "training_budget_minutes": 30,
        "recommended_frameworks": ["numpy", "torch (CPU)"],
        "guidance": (
            "Toy MDPs, numpy GPTs up to ~1M params, torch CPU for small models. "
            "No LoRA. Training caps at ~30 min."
        ),
    },
    "tier_low_gpu": {
        "max_model_params": 5_000_000,
        "max_lora_base_params": 500_000_000,
        "training_budget_minutes": 60,
        "recommended_frameworks": ["torch (MPS/CUDA)", "numpy fallback"],
        "guidance": (
            "GPTs up to ~5M params from scratch; LoRA on <500M models. "
            "Training caps at ~1 hour."
        ),
    },
    "tier_mid_gpu": {
        "max_model_params": 50_000_000,
        "max_lora_base_params": 3_000_000_000,
        "training_budget_minutes": 240,
        "recommended_frameworks": ["torch (MPS/CUDA)", "MLX (Apple)", "numpy fallback"],
        "guidance": (
            "GPTs up to ~50M params from scratch (TinyStories class). "
            "LoRA on 1.5B-3B base models. Training up to ~4 hours."
        ),
    },
    "tier_high_gpu": {
        "max_model_params": 300_000_000,
        "max_lora_base_params": 13_000_000_000,
        "training_budget_minutes": 480,
        "recommended_frameworks": ["torch (MPS/CUDA)", "MLX (Apple)", "transformers + peft"],
        "guidance": (
            "GPTs up to ~300M params from scratch. LoRA on 7B-13B base models. "
            "Int4 inference on 70B feasible. Training up to ~8 hours."
        ),
    },
    "tier_extreme": {
        "max_model_params": 3_000_000_000,
        "max_lora_base_params": 70_000_000_000,
        "training_budget_minutes": 2880,
        "recommended_frameworks": ["torch (multi-GPU)", "MLX", "transformers + peft + accelerate"],
        "guidance": (
            "Pre-training of 1-3B models from scratch. LoRA on 30B-70B base "
            "models. Full multi-day training runs."
        ),
    },
}


def classify_tier(gpu: dict[str, Any], ram: dict[str, Any]) -> tuple[str, str]:
    vram = gpu.get("vram_gb") or 0
    if gpu["vendor"] == "none":
        ram_total = ram.get("total_gb") or 0
        if ram_total >= 64:
            return "tier_mid_cpu", f"CPU-only with {ram_total} GB RAM"
        return "tier_cpu_only", f"CPU-only ({ram_total} GB RAM)"
    if gpu["is_unified"]:
        if vram >= 96:
            return "tier_extreme", f"Apple Silicon, {vram} GB unified"
        if vram >= 48:
            return "tier_high_gpu", f"Apple Silicon, {vram} GB unified"
        if vram >= 16:
            return "tier_mid_gpu", f"Apple Silicon, {vram} GB unified"
        return "tier_low_gpu", f"Apple Silicon, {vram} GB unified"
    if gpu.get("gpu_count", 1) > 1:
        return "tier_extreme", f"Multi-GPU ({gpu['gpu_count']}x {gpu.get('name', '?')})"
    if vram >= 24:
        return "tier_high_gpu", f"Discrete GPU 24+ GB ({gpu.get('name', '?')})"
    if vram >= 8:
        return "tier_mid_gpu", f"Discrete GPU 8-23 GB ({gpu.get('name', '?')})"
    if vram > 0:
        return "tier_low_gpu", f"Discrete GPU <8 GB ({gpu.get('name', '?')})"
    return "tier_cpu_only", "Discrete GPU detected but VRAM unknown"


def detect_all() -> dict[str, Any]:
    os_info = detect_os()
    cpu = detect_cpu()
    ram = detect_ram()
    gpu = detect_gpu(ram)
    disk = detect_disk()
    ml = detect_ml_libs()
    tier, tier_desc = classify_tier(gpu, ram)
    return {
        "schema_version": 1,
        "detected_at": datetime.now(timezone.utc).isoformat(),
        "os": os_info,
        "cpu": cpu,
        "ram": ram,
        "gpu": gpu,
        "disk": disk,
        "ml_libs": ml,
        "tier": tier,
        "tier_description": tier_desc,
        "recommendations": TIER_RECS[tier],
    }


def _cache_is_fresh(cache: Path) -> tuple[bool, dict[str, Any] | None]:
    if not cache.exists():
        return False, None
    try:
        d = json.loads(cache.read_text())
        detected = datetime.fromisoformat(d["detected_at"])
        if datetime.now(timezone.utc) - detected < timedelta(days=CACHE_TTL_DAYS):
            return True, d
    except Exception:
        return False, None
    return False, None


def _print_summary(d: dict[str, Any]) -> None:
    gpu_desc = d["gpu"].get("name") or "none"
    vram = d["gpu"].get("vram_gb") or 0
    print(f"OS:    {d['os']['system']} {d['os']['machine']}{'  (WSL)' if d['os'].get('is_wsl') else ''}")
    print(f"CPU:   {d['cpu'].get('model') or 'unknown'} ({d['cpu']['logical_cores']} cores)")
    print(f"RAM:   {d['ram']['total_gb']} GB")
    print(f"GPU:   {gpu_desc} ({vram} GB{' unified' if d['gpu'].get('is_unified') else ''})")
    print(f"Disk:  {d['disk'].get('free_gb')} GB free")
    print(f"Tier:  {d['tier']}  ({d['tier_description']})")
    print(f"Guidance: {d['recommendations']['guidance']}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--force", action="store_true", help="Re-detect even if cache is fresh")
    p.add_argument("--cache-path", default=str(CACHE_PATH), help=f"Cache file path (default: {CACHE_PATH})")
    p.add_argument("--print-only", action="store_true", help="Detect and print; do not write cache")
    p.add_argument("--summary", action="store_true", help="Print short summary instead of full JSON")
    args = p.parse_args()
    cache = Path(args.cache_path)

    if not args.force and not args.print_only:
        fresh, cached = _cache_is_fresh(cache)
        if fresh and cached is not None:
            if args.summary:
                _print_summary(cached)
                print(f"(cached; age "
                      f"{(datetime.now(timezone.utc) - datetime.fromisoformat(cached['detected_at'])).days}d)")
            else:
                print(json.dumps(cached, indent=2))
            return 0

    result = detect_all()

    if not args.print_only:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(result, indent=2) + "\n")

    if args.summary:
        _print_summary(result)
    else:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
