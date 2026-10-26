# Beslutninger

## Milepæl 1 — skjelett

- **`pgvector/pgvector:pg16` som database-image** i stedet for `postgres:16` + manuell installasjon av pgvector. Bildet har extensionen ferdig kompilert inn, og vi trenger den uansett fra milepæl 4.
- **psycopg v3, synkron modus** som Postgres-driver, ikke async. Enklere å forklare og lese, og ingen av de tidlige milepælene har ytelseskrav som trenger async. Kan revurderes hvis det blir en flaskehals senere.
- **n8n med eget SQLite-volum**, ikke koblet til applikasjonens Postgres-database. Holder n8n sitt interne skjema (workflows, kjøringshistorikk) separat fra våre data.
- **Python 3.12**, ikke 3.14. Brukeren har 3.14 lokalt installert, men siden alt kjører i Docker er det ikke noe krav om at lokal og container-versjon matcher. 3.12 har bedre støtte i økosystemet (ferdigbygde wheels for psycopg og pydantic-core).
- **requirements.txt med pinnede versjoner**, ikke Poetry/uv. Enklest å lese og forklare, ingen ekstra verktøy å installere.
- Første Alembic-migrasjon gjør kun `CREATE EXTENSION IF NOT EXISTS vector` — ingen tabeller ennå, siden milepæl 1 bare krever en tom database med migrasjonsinfrastruktur på plass.

## Milepæl 2 — Elverum-adapter

### robots.txt på www.elverum.kommune.no

```
User-agent: *
Disallow:   /Innsyn.aspx
Disallow:   /innsyn.aspx
Disallow:   /Innsyn6
Disallow:   /innsyn6
Disallow:   /Innsyn5
Disallow:   /innsyn5
Disallow:   /Innsyn
Disallow:   /innsyn
... (en rekke admin-/skjema-/maler-stier, ikke relevante her)
```

**Vurdering:** `/Innsyn` og `/innsyn` (med varianter `Innsyn5`/`Innsyn6`) er disallowed. Dette er de gamle ASPX-sidene fra en tidligere utgave av løsningen (Acos sitt eldre innsynsprodukt). Det politiske møteplan-widgetet som faktisk vises på siden i dag (`/vare-tjenester/politikk-planer-og-organisasjon/politikk/politisk-moteplan/`) er en nyere React-komponent («nye-innsyn») som henter data fra et JSON-API under `/api/presentation/v2/nye-innsyn/...`. Denne stien starter ikke med `/innsyn` eller `/Innsyn` og treffer ikke noen disallow-regel i robots.txt (reglene matcher på prefiks av path, ikke på at «innsyn» forekommer et sted i stien).

**Konklusjon: adapteren kan bruke `/api/presentation/v2/nye-innsyn/...`-API-et.** Det er det samme API-et den vanlige nettsiden bruker for alle besøkende, ikke en skjult eller autentisert bakvei, og det ligger utenfor robots.txt-sperren. De gamle `/Innsyn*.aspx`-sidene rører vi ikke.

Dette er et grensetilfelle jeg vil at du bekrefter eksplisitt før vi skriver kode, siden CLAUDE.md sier «hent aldri automatisk fra en kilde som blokkerer det i robots.txt» — konklusjonen her er at kilden *ikke* blokkerer dette spesifikke API-et, men regelen er skrevet med den gamle løsningen i tankene.

**Godkjent av brukeren.** Brukeren har også sendt e-post til Elverum kommune og bedt om tillatelse — hvis kommunen svarer, oppdater dette avsnittet med svaret. Adapteren bruker `/api/presentation/v2/nye-innsyn/...` under disse betingelsene:

- **Maks én forespørsel hvert tiende sekund** (rate-limit i adapteren, ikke bare "vær rask"). Skjerpet fra 2 til 10 sekunder siden vi ennå ikke har fått svar fra kommunen.
- **Aldri hente samme dokument to ganger** — sjekk stabil ID/fil-nøkkel mot databasen før nedlasting.
- **Tydelig User-Agent** med prosjektnavn og kontakt-e-post, slik CLAUDE.md allerede krever generelt.
- **Ikke publiser PDF-ene selv** — lagre dem lokalt for tekstuttrekk/indeksering, men svar fra systemet skal lenke til kommunens egen kilde (møteplan-siden), ikke til en kopi vi hoster.
- **Stopp umiddelbart** hvis kommunen ber om det, uavhengig av hva robots.txt sier på det tidspunktet.
- **Kun en håndfull dokumenter i den første reelle kjøringen.** Vi har ikke fått skriftlig tillatelse fra kommunen ennå (e-post sendt, ikke besvart). CLI-et har derfor en `--limit`-flagg (antall møter, ikke antall dokumenter) som standard er lav, slik at den første kjøringen mot det ekte API-et er en liten stikkprøve, ikke et fullt årshentingsforsøk. Hev grensen når kommunen har svart.

### Systemet

Elverum bruker **Acos** som totalleverandør (bekreftet i footer og i stier som `/Maler/`, `/.AcosOppgradering`). Den politiske møteplanen er en innebygd React-widget («nye-innsyn») på den vanlige kommune-siden, ikke et eget nettsted. Det finnes også en «Politikerportalen» på `elverum.acossky.no/moteportal`, men den er innloggingsbeskyttet (BFF-login) og ser ut til å være for politikere/ansatte, ikke offentlig innsyn — ikke relevant for oss.

To datakilder (kalt `Datasource` i API-et), velges i UI med en radioknapp:
- `585964d3-63d8-44c9-9f12-de294f9152c7` — «Arkiv fra april 2024» (nåværende system)
- `38efd16c-5bbb-4e5a-9dde-9fbbfa15fa2f` — «Historisk arkiv 2007-2024» (gammelt system, egen kildekode)

Milepæl 2 fokuserer på den nåværende kilden (2024→). Historisk arkiv kan bli en egen, senere oppgave siden datastrukturen kan avvike.

### API-endepunkter (alle under `https://www.elverum.kommune.no/api/presentation/v2/nye-innsyn/`)

Alle kall er `POST` med JSON-body `{"type": 1, "keyValues": [{"key": ..., "value": ...}, ...]}`, selv der det egentlig er et GET-aktig oppslag.

**Rettelse (funnet først når vi faktisk kjørte adapteren mot det ekte API-et):** Det stemmer *ikke* at ingen autentisering kreves. Et rent HTTP-kall mot `overview` uten noen forhistorie ble avvist (401/tilkoblingen ble brutt). Årsaken er at nettleseren alltid har lastet en vanlig HTML-side på samme domene først, noe som setter en sesjon-cookie (ASP.NET/Acos-infrastruktur) — uten den cookien nekter serveren API-kall. Bekreftet med `curl`: samme POST uten cookie → ingen respons (tilkobling brutt), samme POST med en cookie hentet fra et vanlig sidebesøk først → 200 OK. Adapteren besøker derfor møteplan-siden én gang per klient (gjennom samme rate-begrensede HTTP-klient, så det teller som et av kallene) før den gjør noen API-kall, og gjenbruker cookien httpx lagrer automatisk resten av sesjonen. Dette er fortsatt det samme en anonym nettleserbesøkende opplever — ingen pålogging, ingen hemmelig nøkkel — bare at vi må besøke en side før API-et, akkurat som nettleseren gjør.

- **`POST overview`** — søk/liste over møter. `keyValues` som brukes:
  - `Datasource` → tenant-GUID (se over)
  - `UtvalgID` → utvalgets ID (format `u-<tenant-guid>-<tall>!<hash>`), hentes fra `searchOptions.searchFilters` i responsen (se under) — ikke noe vi gjetter eller hardkoder
  - `Dato` (tre ganger i rekkefølge: FromDate, ToDate, modus) — modus er `ComingMeetings`, `HeldMeetings` eller `Other` (fri periode). Eksempel for et helt år: `{"key":"Dato","value":"2026-01-01"}, {"key":"Dato","value":"2026-12-31"}, {"key":"Dato","value":"Other"}`
  - `page`, `pageSize` for paginering
  - Responsen inneholder `content.searchItems.items[]` (møter, `type: "Mote"`, med `identifier`, `title` = utvalgsnavn, `properties.dato/tid/sted`) og `content.searchOptions.searchFilters[]` — sistnevnte gir **hele lista over utvalg med stabile ID-er** (`identifier` på feltet under filteret med `identifier: "UtvalgID"`). Dette betyr at vi kan hente utvalgslisten dynamisk i stedet for å hardkode den.
  - Testet: samme kall uten `UtvalgID`/med tom body gir et bredere postliste-søk (arkivsaker, inngående dokumenter) — samme bakenforliggende søkemotor som brukes på «Søk etter saker og dokumenter»-siden.

- **`POST mote/{moteId}`** — møtedetaljer: saksliste (saksnummer, antall dokumenter per sak) og lenker til møtedokumenter (innkalling, protokoll, møtebok som pdf), samt deltakerliste.
- **`POST mote/fremmote/{moteId}`** — fremmøte/deltakerliste for møtet (egen kall, ikke i hoveddetaljen).
- **`POST mote/saksfremlegg/{sakId}`** — sak-detaljer, inkl. lenker til saksframlegg-dokumenter for den enkelte saken.
- **`GET filer/{fileKey}?pid=1`** — selve PDF-filen. `fileKey` er en lang signert streng vi får fra de andre kallene, ikke noe vi konstruerer selv.

Alle disse ID-ene (`moteId`, `sakId`, `fileKey`, `UtvalgID`) er signerte/hash-suffikser (`!<hash>`) som kommer fra API-et selv — adapteren må alltid gå via `overview` → `mote` → `saksfremlegg`/`filer` i den rekkefølgen, aldri konstruere ID-er selv.

### Faktisk JSON-skjema (verifisert med ekte kall, ikke gjettet)

**Paginering er ikke pålitelig styrt av `pageSize` vi sender.** Testet med `pageSize=2` og `pageSize=3` — serveren returnerte likevel 10 treff på side 1 (ser ut som en server-side nedre grense). `page` fungerer derimot korrekt (side 2 ga resten). Adapteren ber om en stor `pageSize` (f.eks. 100) og looper på `page` basert på **responsens** `content.searchItems.pageSize`/antall returnerte elementer, ikke det vi selv ba om.

**`mote/{moteId}`** returnerer en generisk tre-struktur, ikke flate felt:
```
content: { title, identifier, props, b: [...] }
```
`b[]`-noder har `{key?, title, type, url?, identifier?, b?}`. De to vi bruker:
- `type: "FileListButton"`, `key: "MEETING_FILES"` → møtedokumenter. Barn har `type: "Text"` og `key` ∈ {`MEETING_FILES_SUMMON` (innkalling), `MEETING_FILES_PROTOCOL` (protokoll)}, eller ingen `key` for møtebok. Et barn uten `url` betyr "ikke publisert enda" — hoppes over.
- `type: "DocumentList"`, `key: "MEETING_CASES"` → saksliste. Barn har `type: "AsyncDocument"`, `identifier` = sakId (brukes mot `saksfremlegg`), `title` = sakstittel, og et nestet `type: "PropertyList"`-barn med `Property`-rader `{title: "Saksnummer", text: "001/26"}` og `{title: "Antall dokumenter", text: "1"}`.

**`mote/saksfremlegg/{sakId}`** er flatere:
```
content: { title, identifier, b: [...], props: {saksnummer, "antall dokumenter", sakstype} }
```
Dokumentene ligger under barnet med `type: "FileList"`, `key: "MEETING_CASE_FILES"` — hver fil har `{identifier, title, url, type: "Text"}`.

Alle filer (møtedokumenter og saksframlegg) har en ferdig `url`-sti (`/api/presentation/v2/nye-innsyn/filer/...?pid=1`) — adapteren bruker denne direkte i stedet for å bygge den selv.

**`kilde_url` vi lagrer per dokument** peker til den offentlige møtesiden: `https://www.elverum.kommune.no/vare-tjenester/politikk-planer-og-organisasjon/politikk/politisk-moteplan/#/details/{moteId}` — samme lenke for alle dokumenter tilhørende det møtet (inkludert saksframlegg), siden det er her et menneske faktisk kan se og laste ned dokumentet selv.

**Deltakerliste/fremmøte hoppes over.** Det finnes et eget endepunkt (`mote/fremmote/{moteId}`), men CLAUDE.md sitt fellesformat for møtedokumenter har ikke noe deltakerfelt, så vi henter det ikke — unngår kode vi ikke har bruk for ennå.

**Antakelse verifisert:** `identifier`/fil-URL-ene er stabile mellom kjøringer, ikke bare innen én sesjon. Bekreftet ved å kjøre CLI-et mot det ekte API-et to ganger (egne prosesser) for Kommunestyret 28.01.2026: første kjøring ga 19 nye dokumenter, andre kjøring ga 0 nye / 19 allerede hentet — samme radantall i `documents`-tabellen etterpå.

### Avsluttende valg for milepæl 2

- **Flat `documents`-tabell** (`api/app/models.py`), ikke egne "meetings"/"documents"-tabeller. CLAUDE.md sitt fellesformat beskriver ett møtedokument som enheten, og vi trenger ikke den ekstra abstraksjonen før et nytt mønster faktisk krever det.
- **CLI-først, ikke HTTP-endepunkt.** `docker compose exec api python -m app.ingest.elverum_cli --utvalg <navn> --year <år> --limit <n>`. Milepæl 8 (n8n → `/ingest`) kan wrappe `app.ingest.elverum.run(...)` i et FastAPI-endepunkt senere uten omskriving.
- **Ingen ny docker-compose-volum for PDF-ene.** `./api:/app`-mountet i `docker-compose.yml` dekker allerede `api/data/elverum/` — filene overlever container-restart uten endringer i compose-filen. La til `api/data/` i `.gitignore` i stedet.
- **Historisk arkiv (2007–2024) og de andre utvalgene er ikke hentet.** Bare Kommunestyret, kun 2026, kun 19 dokumenter fra ett møte — i tråd med at vi ikke har fått bekreftet tillatelse fra kommunen ennå.
