# Jobbradar

## Om prosjektet

En jobbsøkerassistent bygget på NAVs åpne stillingsfeed. Systemet henter nye stillingsannonser hver dag, bruker AI til å trekke ut strukturert informasjon fra annonsetekstene (kategori, ferdigheter, krav til erfaring, om stillingen passer for nyutdannede), og matcher annonsene mot profilen min (CV, ferdigheter, prosjekter). Jeg skal kunne filtrere på type jobb, se hvorfor en stilling passer eller ikke, se statistikk over hva markedet etterspør, og spørre en assistent som «hva slags jobber passer meg?».

Dette er et soloprosjekt for porteføljen min. Koden skal være lett å lese og lett å forklare i et intervju. Velg det enkle fremfor det smarte.

## Stack

- Python 3.12 og FastAPI
- PostgreSQL 16 med pgvector og innebygd fulltekstsøk med norsk konfigurasjon
- n8n for planlagte jobber og e-postvarsling
- Docker Compose for alle tjenester
- BGE-M3 for embeddings, kjøres lokalt
- Claude API, en rimelig modell for uttrekk av annonser og en sterkere modell for matching og assistent
- React og TypeScript for frontend

## Kommandoer

```
docker compose up -d           # start alt
docker compose exec api pytest # kjør tester
docker compose logs -f api     # følg loggen til API-et
```

## Struktur

```
api/
  app/
    nav/          # klient og synkronisering mot NAVs stillingsfeed
    extraction/   # AI-uttrekk av strukturerte felt fra annonser
    profile/      # innlesing av profilen min
    search/       # hybrid søk med filtre
    matching/     # matching mellom annonser og profil
    assistant/    # assistent med verktøy
    stats/        # markedsinnsikt
  tests/
web/              # React-frontend
evals/            # evalueringssett og skript
n8n/              # eksporterte n8n-flyter
profile/          # min CV og profil, ligger IKKE i git (se profile/README.md)
docs/
  plan.md         # milepæler
  decisions.md    # beslutningslogg
```

## Ordliste

Bruk de engelske navnene i koden.

| Norsk | I koden |
|---|---|
| stillingsannonse | `job_ad` |
| arbeidsgiver | `employer` |
| krav | `requirement` |
| ferdighet | `skill` |
| stillingskategori | `job_category` |
| profil | `profile` |
| match | `match` |
| søknadsfrist | `application_deadline` |

## Regler for Claude

- Jobb med én milepæl om gangen fra docs/plan.md. Legg frem en plan og vent på godkjenning før større endringer.
- Hold endringene små. Ikke lag abstraksjoner før det samme mønsteret trengs to steder.
- Skriv tester for ny logikk med pytest, og kjør dem før du sier at noe er ferdig. Tester skal ikke kalle NAV eller Claude API, bruk lagrede eksempelsvar.
- Spør før du legger til nye avhengigheter.
- Hemmeligheter ligger i .env og skal aldri committes. Oppdater .env.example når nye variabler kommer til.
- Mappen profile/ inneholder personopplysninger om meg og skal aldri committes, bortsett fra README.md og eksempelfiler.
- Følg NAVs vilkår (se docs/decisions.md). Inaktive annonser skal straks fjernes fra alle resultater. Kontaktpersoner og annen kontaktinfo fra annonsene skal ikke lagres.
- Tenk på kostnad. AI-uttrekk skal bare kjøres på annonser som er nye eller har endret tekst, og bare på annonser som passerer forfilteret. Logg antall kall og tokens per kjøring.
- Ikke endre filer i evals/ som ender på `labels.yaml`. Dem skriver jeg selv.
- Når du tar et valg som er verdt å forklare (bibliotek, modell, prompt, parameter, struktur), legg til en kort oppføring i docs/decisions.md med hva som ble valgt og hvorfor.
- Avslutt hver oppgave med en kort oppsummering av hva som er endret og hva jeg bør teste selv.
- Kode, variabelnavn og commit-meldinger på engelsk. Dokumentasjon på norsk.
