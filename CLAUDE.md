# kommune-rag (arbeidsnavn)

## Om prosjektet

En tjeneste der man kan stille spørsmål om politiske saker og vedtak i norske kommuner og få svar med lenke til dokumentet og siden svaret kommer fra. Første kilde er Elverum kommune. Flere kommuner og fylker skal kunne legges til senere via adaptere.

Dette er et soloprosjekt for porteføljen min. Koden skal være lett å lese og lett å forklare i et intervju. Velg det enkle fremfor det smarte.

## Stack

- Python 3.12 og FastAPI
- PostgreSQL 16 med pgvector (vektorsøk) og innebygd fulltekstsøk med norsk konfigurasjon
- n8n for planlagte jobber (daglig henting)
- Docker Compose for alle tjenester
- BGE-M3 for embeddings, kjøres lokalt
- Claude API for å formulere svar
- React for frontend (senere milepæl)

## Kommandoer

```
docker compose up -d          # start alt
docker compose exec api pytest # kjør tester
docker compose logs -f api    # følg loggen til API-et
```

## Struktur

```
api/
  app/
    adapters/   # én adapter per kildesystem, f.eks. elverum_innsyn.py
    ingest/     # tekstuttrekk, chunking, embeddings
    search/     # hybrid søk
    answer/     # promptbygging og kall mot Claude
  tests/
evals/          # spørsmålssett og evalueringsskript
n8n/            # eksporterte n8n-flyter
docs/
  plan.md       # milepæler
  decisions.md  # beslutningslogg
```

## Felles dataformat

Alle adaptere returnerer det samme formatet, slik at resten av systemet ikke vet hvor dataene kom fra. Et møtedokument har kommune, utvalg, møtedato, dokumenttype (innkalling, saksframlegg, protokoll), tittel, saksnummer hvis det finnes, kilde-URL og en stabil ID som brukes for å unngå duplikater.

## Regler for Claude

- Jobb med én milepæl om gangen fra docs/plan.md. Legg frem en plan og vent på godkjenning før du gjør større endringer.
- Hold endringene små. Ikke lag abstraksjoner før det samme mønsteret trengs to steder.
- Skriv tester for ny logikk med pytest, og kjør dem før du sier at noe er ferdig.
- Spør før du legger til nye avhengigheter.
- Hemmeligheter ligger i .env og skal aldri committes. Oppdater .env.example når nye variabler kommer til.
- Vær snill mot kildene. Hent med lav frekvens, bruk en tydelig User-Agent med kontaktinfo, og hent aldri automatisk fra en kilde som blokkerer det i robots.txt med mindre docs/decisions.md sier at vi har fått tillatelse.
- Ikke endre evals/questions.yaml. Den skriver jeg selv.
- Når du tar et valg som er verdt å forklare (bibliotek, modell, parameter, struktur), legg til en kort oppføring i docs/decisions.md med hva som ble valgt og hvorfor.
- Avslutt hver oppgave med en kort oppsummering av hva som er endret og hva jeg bør teste selv.
- Kode, variabelnavn og commit-meldinger på engelsk. Dokumentasjon på norsk.
