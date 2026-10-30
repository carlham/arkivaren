# Evaluering

Tre sett som måler hver sin del av systemet. Filene som ender på `labels.yaml` skriver jeg selv. Claude skal ikke endre dem.

Hvert skript lagrer resultatet i `evals/results/` med dato, slik at jeg kan sammenligne før og etter en endring.

## 1. Uttrekk (`extraction_labels.yaml`)

Rundt 30 annonser der jeg har lest teksten og fylt inn feltene selv. Skriptet sammenligner med AI-uttrekket og viser treffsikkerhet per felt. Velg annonser med variasjon, både tydelige og rotete, både junior og senior, og noen som ikke er IT.

```yaml
- ad_id: <uuid fra NAV>
  job_category: frontend
  skills_required: [React, TypeScript]
  skills_preferred: [Next.js]
  years_experience_min: null
  junior_friendly: ja
  remote: hybrid
```

## 2. Matching (`match_labels.yaml`)

Rundt 30 annonser der jeg har vurdert selv om de passer meg. Skriptet måler hvor ofte systemets vurdering stemmer med min.

```yaml
- ad_id: <uuid fra NAV>
  fit: godt        # godt, delvis eller dårlig
  note: Krever React og WCAG, som jeg har. Ingen krav til erfaring.
```

## 3. Assistent (`assistant_questions.yaml`)

Spørsmål med forventet oppførsel i stedet for fasitsvar, siden svarene endrer seg når nye annonser kommer inn.

```yaml
- id: a001
  question: Hva slags jobber passer meg?
  expect:
    - Viser bare aktive annonser
    - Lenker til hver annonse den nevner
    - Begrunner med konkrete ting fra profilen
- id: a002
  question: Finnes det frontendjobber i Innlandet som passer for nyutdannede?
  expect:
    - Bruker filtrene kategori, region og junior
    - Sier tydelig fra hvis det ikke finnes noen
- id: a003
  question: Hvilke ferdigheter burde jeg lære for å få flere treff?
  expect:
    - Bygger på statistikk fra annonsene, ikke generelle råd
- id: a004
  question: Finn en jobb som kokk i Tromsø
  expect:
    - Sier at systemet bare dekker IT-stillinger
```
