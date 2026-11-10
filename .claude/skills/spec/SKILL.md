---
name: spec
description: Turn a milestone from docs/plan.md into an approved spec file by interviewing the user ("the grill"). Use when starting a new milestone.
argument-hint: [milestone number]
disable-model-invocation: true
---

# Spec (the grill)

Goal: produce `docs/specs/NN-short-name.md` for milestone $ARGUMENTS and get the user's explicit approval. Write no code in this step.

## Steps

1. Read CLAUDE.md, the milestone in docs/plan.md, docs/decisions.md and the code the milestone will touch. Use the Explore agent for broad searches so the main context stays clean.
2. Draft the spec from the template below with status `utkast`. Fill in what you can and put everything uncertain under Åpne spørsmål.
3. Interview the user, one question at a time. Give your recommended answer and the reason with each question, so the user can simply agree or correct you. Ask the questions that change the design first.
4. Push back on vague "ferdig når" points until each one can be checked by a test, a command, or a specific manual check the user does.
5. Update the spec file after each answer. Stop when Åpne spørsmål is empty or the user says the rest can wait.
6. Show a short summary of the spec and ask for approval.

## Gate

Only an explicit go ("go", "godkjent", "kjør") approves the spec. A question, a comment or "ok, does this cover X?" is not approval. Answer it and ask again.

When approved, set status to `godkjent`, create the branch `mNN-short-name` from main, and tell the user to run /build.

## Template

Written in Norwegian, as CLAUDE.md asks for documentation.

```markdown
# MNN Navn

Status: utkast
Branch: mNN-short-name

## Mål
En eller to setninger.

## Ferdig når
- [ ] Hvert punkt kan sjekkes. Skriv hvordan (navn på test, kommando, eller manuell sjekk jeg gjør selv).

## Utenfor scope
- Det vi bevisst ikke gjør nå.

## Oppgaver
- [ ] 1. Små oppgaver i rekkefølge. Testene skal være grønne etter hver.

## Beslutninger
- Valg tatt underveis. Kopieres til docs/decisions.md ved /ship.

## Åpne spørsmål
-

## Logg
- Dato og kort notat når spesifikasjonen endres etter godkjenning, og hvorfor.
```
