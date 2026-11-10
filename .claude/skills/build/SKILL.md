---
name: build
description: Implement an approved spec from docs/specs/ one task at a time. Use after /spec has been approved.
argument-hint: [spec file, optional]
disable-model-invocation: true
---

# Build

## Before starting

1. Find the spec. Use $ARGUMENTS if given, otherwise the spec in docs/specs/ with status `godkjent` or `pågår`.
2. If the status is `utkast`, stop and tell the user to finish /spec first.
3. Make sure you are on the branch named in the spec. Set the status to `pågår`.

## For each unchecked task, in order

1. Make the smallest change that completes the task.
2. Write or update tests as CLAUDE.md describes.
3. Run the test suite with the command from CLAUDE.md. Do not move on while tests fail.
4. Tick the task in the spec.
5. Commit on the milestone branch with a short English message. One commit per task: code, tests and the tick in the spec go in the same commit. Never merge to main and never push.

## When the spec is wrong

If a task turns out to be wrong, missing or bigger than expected, stop. Explain what you found, propose a change to the spec, and wait for an explicit go. Then update the spec and add a line under Logg. Do not work around the spec on your own.

## Scope

Only do what the spec says. If you notice other problems along the way, list them at the end under "Ting jeg la merke til" instead of fixing them.

## When all tasks are done

Give a short summary and tell the user to run /verify. Do not call the milestone finished.
