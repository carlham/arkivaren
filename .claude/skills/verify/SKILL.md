---
name: verify
description: Check every "ferdig når" point in the current spec with real evidence. Use after /build, or when the user asks whether a milestone is done.
argument-hint: [spec file, optional]
---

# Verify

1. Find the spec ($ARGUMENTS, or the one with status `pågår`).
2. Run the full test suite with the command from CLAUDE.md.
3. Run any eval script in evals/ that the milestone touches.
4. Go through each point under "Ferdig når" and check it. Record the evidence, meaning the command you ran and the relevant lines of output. A point is only passed when you have evidence. "It should work" is not evidence.
5. Points that need a manual check by the user go under "Du må sjekke selv", with exact steps.
6. Tick the points that passed in the spec.

## Output

A table with one row per point.

| Punkt | Status | Bevis |
|---|---|---|
| ... | ✅ / ❌ / venter på deg | command and output excerpt |

Do not fix failures in this step. Report them and suggest going back to /build.
