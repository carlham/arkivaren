# Jobbradar

En jobbsøkerassistent bygget på NAVs åpne stillingsfeed. Systemet henter nye stillingsannonser hver dag, bruker AI til å trekke ut strukturert informasjon fra annonsetekstene (kategori, ferdigheter, krav til erfaring, om stillingen passer for nyutdannede), og matcher annonsene mot en profil (CV, ferdigheter, prosjekter).

Målet er at man skal kunne:

- filtrere på type jobb, sted, omfang og om stillingen passer for nyutdannede
- se hvorfor en stilling passer eller ikke, med henvisning til profilen
- se statistikk over hva markedet etterspør
- spørre en assistent som «hva slags jobber passer meg?» og få svar med konkrete annonser

Mer kommer.

Dette er et soloprosjekt for porteføljen min.

## Status

**Prosjektet er under bygging.** Det er delt i 12 milepæler (se [docs/plan.md](docs/plan.md)). Hver milepæl har en egen spesifikasjon og et «ferdig når» som må være oppfylt før neste starter.

| # | Milepæl | Status |
|---|---|---|
| 1 | Skjelett: Docker Compose, PostgreSQL, FastAPI | ✅ Ferdig |
| 2 | Synkronisering mot NAVs stillingsfeed | ✅ Ferdig |
| 3 | Forfilter for IT-stillinger | Neste |
| 4 | AI-uttrekk av strukturerte felt | Ikke startet |
| 5 | Søk og filtre (BGE-M3, fulltekst og vektor) | Ikke startet |
| 6 | Profil | Ikke startet |
| 7 | Matching | Ikke startet |
| 8 | Assistent med verktøy | Ikke startet |
| 9 | Markedsinnsikt | Ikke startet |
| 10 | n8n: daglige flyter og e-postvarsling | Ikke startet |
| 11 | Frontend (React, universell utforming) | Ikke startet |
| 12 | Deploy med demoprofil | Ikke startet |

### Det som fungerer nå

- Klient mot NAVs `pam-stilling-feed` som leser feeden side for side og husker hvor den slapp.
- Nye annonser legges til, endrede oppdateres, og inaktive markeres og skjules fra alle resultater med en gang.
- Kontaktpersoner og annen kontaktinfo lagres ikke, slik NAVs vilkår krever. E-post og telefonnummer i annonseteksten fjernes før lagring.
- Databaseskjema med migrasjoner (Alembic) og tester med lagrede eksempelsvar, uten kall mot NAV.

Det er **ikke** noe brukergrensesnitt ennå, og AI-uttrekk, søk, matching og assistent er ikke bygget.

## Teknologi

- Python 3.12 og FastAPI
- PostgreSQL 16 med pgvector og fulltekstsøk med norsk konfigurasjon
- n8n for planlagte jobber og e-postvarsling
- Docker Compose for alle tjenester
- BGE-M3 for embeddings, kjøres lokalt
- Claude API: en rimelig modell for uttrekk av annonser og en sterkere modell for matching og assistent
- React og TypeScript for frontend

Stacken for uttrekk, søk, matching og frontend er planlagt, men ikke tatt i bruk ennå.

## Struktur

```
api/
  app/
    nav/          # klient og synkronisering mot NAVs stillingsfeed (M2, ferdig)
    extraction/   # AI-uttrekk av strukturerte felt (planlagt)
    profile/      # innlesing av profilen (planlagt)
    search/       # hybrid søk med filtre (planlagt)
    matching/     # matching mellom annonser og profil (planlagt)
    assistant/    # assistent med verktøy (planlagt)
    stats/        # markedsinnsikt (planlagt)
  migrations/     # Alembic-migrasjoner
  tests/
web/              # React-frontend (planlagt)
evals/            # evalueringssett og skript
n8n/              # eksporterte n8n-flyter (planlagt)
profile/          # min CV og profil, ligger ikke i git
docs/
  plan.md         # milepæler
  specs/          # én spesifikasjon per milepæl
  decisions.md    # beslutningslogg
```

Mapper merket «planlagt» finnes ikke i repoet ennå.

## Kom i gang

Krever Docker. Kopier `.env.example` til `.env` og fyll inn verdiene. NAVs offentlige token hentes fra `/api/publicToken` og limes inn i `NAV_FEED_TOKEN`.

```
docker compose up -d                        # start alt
docker compose exec api pytest              # kjør tester
docker compose exec api python -m app.nav.sync --max-pages 2   # hent annonser fra NAV
docker compose logs -f api                  # følg loggen til API-et
```

## Personvern og vilkår

- Jobbradar bruker NAVs åpne stillingsfeed og følger vilkårene for den. Inaktive annonser fjernes fra resultatene straks, og kontaktinfo fra annonsene lagres ikke.
- Mappen `profile/` inneholder personopplysninger om meg og er ikke i git. Den offentlige versjonen vil bruke en oppdiktet demoprofil.
- Hemmeligheter ligger i `.env`, som aldri committes.

## Lisens

Ingen lisens er valgt ennå. Koden er lagt ut for å vise hva jeg har bygget.
