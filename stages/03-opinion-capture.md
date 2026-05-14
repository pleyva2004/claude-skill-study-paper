# Stage 3 — Opinion Capture

**Goal:** Drop a structured prompt template into `03-opinions.md` and **stop**. The user fills it in.

## Mandate

**Never invent the user's opinions.** This file is theirs. The skill provides scaffolding (questions); the user provides answers.

## Method

1. Load `templates/03-opinions.md`.
2. Write it to `~/ai-research-studies/<slug>/03-opinions.md` **with all answer slots blank**.
3. Report to user:

```
Wrote: 03-opinions.md (template — empty answers)

Open it and fill in your reactions. Questions cover:
- What surprised you
- Where this would break in practice
- What experiment would falsify the central claim
- What you'd build differently
- Confidence in the central claim (1-10) + why

When done, say "continue" and I'll proceed to Stage 4 (sandbox scaffold).
You can also say "skip opinions" — I'll proceed without them, but the case study will be thinner.
```

4. **Wait.** Do not run Stage 4 without explicit "continue" or "skip".

## Resume Behavior

If `03-opinions.md` exists and is non-empty (user has filled it in some prior session): treat as complete, proceed.

If `03-opinions.md` exists but appears unfilled (template placeholders still present): re-prompt user.
