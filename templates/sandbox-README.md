# Sandbox: {{slug}}

> Minimal runnable experiment probing one claim from **{{title}}** ({{arxiv_url}}).

This is a subdirectory of the larger study repo — see [`../README.md`](../README.md) for the full artifact set (interview prep, math deep dive, lit review, references).

---

## The claim being probed

{{specific_claim}}

## Experiment design

{{experiment_design}}

## Expected output

{{expected_output}}

## What would falsify the claim

{{falsification_condition}}

---

## Run

```bash
pip install -r requirements.txt
python experiment.py
```

Runs on CPU in <60s by default. {{gpu_note_if_any}}

## Files

- `experiment.py` — main script
- `requirements.txt` — pinned deps
- `utils.py` — helpers (if any)

---

## Notes

This is sandbox-grade code: optimized for clarity over performance, single-purpose, not production-ready.
