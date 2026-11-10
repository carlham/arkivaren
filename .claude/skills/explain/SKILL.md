---
name: explain
description: Explain a file, a function or a part of the code in plain Norwegian, so the user can explain it in an interview. Use when the user asks what some code does or why it is built that way.
argument-hint: [file, file::function, or a short description]
---

# Explain

Read-only. Do not change any files.

1. Find the code in $ARGUMENTS. It can be a path, `path::function`, or a description such as "how the sync remembers its position". If more than one place fits, ask which one.
2. Read the code and what surrounds it: who calls it, what it calls, its tests, and the entry in docs/specs/ or docs/decisions.md that explains why it exists.
3. Answer in Norwegian, in this order, and keep each part short:
   - **Hva det gjør**, in one sentence.
   - **Hvorfor det finnes**, with a link to the spec or decision.
   - **Steg for steg**, following the code in reading order, with `file:line`.
   - **Hvordan det henger sammen**, meaning who calls it and what it depends on.
   - **Valg og avveininger**, meaning what was chosen, what the alternative was, and what you would say if asked in an interview.
   - **Hva testene viser**, with test names.
   - **Begrensninger**, if any are known.
4. Explain terms the first time they are used. Choose the simple wording over the precise one.
5. End with two or three questions an interviewer could ask about this code. Do not answer them.
