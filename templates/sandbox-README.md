# ai-study-{{slug}}

> Sandbox study of **{{title}}** ({{arxiv_url}}).

This repo is part of an ongoing series of paper studies. Each repo isolates one claim from a paper and probes it with a minimal, self-contained experiment.

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
- `utils.py` — helpers
- `requirements.txt` — pinned deps

---

## Notes

This is sandbox-grade code: optimized for clarity over performance, single-purpose, not production-ready.

Full study notes (math deep dive + case study) live in my private research notes.
