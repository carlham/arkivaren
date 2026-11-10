---
name: review
description: Get an independent review of the current milestone branch from the reviewer agent. Use after /verify.
argument-hint: [spec file, optional]
---

# Review

1. Find the spec ($ARGUMENTS, or the one with status `pågår`).
2. Hand the review to the `reviewer` agent. Give it the path to the spec and nothing else, so it judges the code without your reasoning from the build.
3. Present its findings to the user, most serious first. Do not soften or drop any.
4. Ask the user which findings to fix. Do not fix anything before they answer. Fixes follow the rules in /build.
