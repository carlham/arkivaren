# Plan

Én milepæl per økt. Hver milepæl har et «ferdig når» som må være oppfylt før vi går videre.

## 1. Skjelett — ✅ ferdig
Docker Compose med PostgreSQL (pgvector), FastAPI og n8n. Tom database med migrasjoner (Alembic).
Ferdig når `docker compose up` starter alt og `GET /health` svarer at databasen er tilgjengelig.
Gjenstår: ingenting innenfor omfanget. `.env` bruker et placeholder-passord lokalt — bytt det ut når vi deployer (milepæl 10).

## 2. Elverum-adapter
Undersøk hvordan Elverums innsynsløsning lister utvalg, møter og dokumenter. Skriv ned funnene i docs/decisions.md før koden skrives. Hent møter for ett utvalg og én periode, lagre PDF-ene lokalt og metadata i databasen.
Ferdig når en kommando henter kommunestyrets møter for 2026 uten duplikater ved ny kjøring, og testene dekker parsing av svarene.

## 3. Tekstuttrekk og chunking
Trekk ut tekst per side fra PDF-ene. Del opp i biter med sidetall bevart. Prøv å dele på saksgrenser i protokoller i stedet for fast lengde.
Ferdig når hver bit i databasen kan spores tilbake til dokument og side.

## 4. Embeddings
Lag embeddings med BGE-M3 og lagre dem i pgvector.
Ferdig når alle biter har en embedding og nye dokumenter får det automatisk.

## 5. Søk
Endepunkt som kombinerer vektorsøk og fulltekstsøk, med filter på kommune, utvalg og dato.
Ferdig når `GET /search` returnerer relevante biter med kilde, og jeg har skrevet deler av dette selv.

## 6. Svar
Endepunkt som henter relevante biter, sender dem til Claude og returnerer svar med kildehenvisninger. Svarer «fant ikke dette i dokumentene» når grunnlaget mangler.
Ferdig når hver påstand i svaret kan kobles til en kilde.

## 7. Evaluering
Skript som kjører evals/questions.yaml og måler om riktig dokument er blant de fem første treffene, og om svaret dekker fasiten. Resultatene lagres slik at endringer kan sammenlignes.
Ferdig når én kommando gir en tabell med tall jeg kan sammenligne før og etter en endring.

## 8. n8n
Nattlig flyt som kaller `/ingest` for nye dokumenter. Flyten eksporteres til n8n/ slik at den ligger i git.
Ferdig når nye dokumenter dukker opp uten at jeg gjør noe.

## 9. Frontend
Enkel React-side med søkefelt, svar og klikkbare kilder som åpner riktig side i PDF-en.

## 10. Deploy
Kjør det på en server, med README som forklarer arkitekturen, resultatene fra evalueringen og hva jeg lærte.

## Senere
- Adaptere for Løten og Hamar (venter på svar på e-post)
- Agentisk søk der modellen selv velger filtre
- Transkribering av KommuneTV-opptak med lenke til tidspunkt
