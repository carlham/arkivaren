# Beslutningslogg

Nyeste øverst. Hver oppføring sier hva som ble bestemt og hvorfor.

---

### Synken startes fra kommandolinjen (2026-11-10)

`docker compose exec api python -m app.nav.sync` starter synken, med `--since-days` (hvor langt tilbake første synk går, som standard 7) og `--max-pages` (for utvikling). Logikken ligger i `sync()` i `nav/sync.py`, som tar en database-sesjon og en klient, slik at et endepunkt kan kalle samme funksjon i milepæl 10.

Tokenen leses fra `NAV_FEED_TOKEN` i `.env`. Den offentlige tokenen hentes fra `/api/publicToken` (svaret har en tekstlinje foran selve tokenen), roterer uregelmessig og limes inn for hånd. Klienten henter den ikke selv, slik at den kan byttes med en fast token senere uten kodeendring.

**Hvorfor** Minst mulig kode nå. Et endepunkt trengs først når n8n skal starte synken, og da kan det kalle den samme funksjonen.

---

### Hvordan synken leser feeden (2026-11-10)

Første synk starter 7 dager bak i tid (`--since-days`), siden NAV har rundt 600 nye annonser per dag. Etter det starter hver synk på siste side vi leste. Posisjonen er `feed_url` til den siden, ikke `next_url`, fordi siste side har `next_url = null`. Å lese siste side på nytt er ufarlig.

Detaljkall (ett per annonse) gjøres bare for nye eller endrede aktive annonser. Inaktive oppføringer og aktive med samme `sistEndret` som sist hoppes over. Vi sammenligner mot `sistEndret` i listeoppføringen, ikke den i detaljsvaret, for de to er ikke like. Det er en pause på 0,5 sekunder mellom kall, og `HTTP_USER_AGENT` sendes med.

Alle yrker hentes. Filtreringen til IT hører til forfilteret i milepæl 3.

Feil mot NAV: 429, 5xx og nettverksfeil prøves på nytt opptil fire ganger med økende pause (5, 10 og 15 sekunder). Feiler det fortsatt, stopper synken og det som er lagret blir stående. Vi hopper ikke over en annonse som feiler, fordi vi bare husker siste side vi leste, og en annonse på en tidligere side ville blitt borte. En annonse som gir 404 er fjernet hos NAV og behandles som inaktiv. Svarer NAV 304 på første forespørsel, er synken tom.

**Hvorfor** NAV-feeden er gratis, så vi skal være greie mot den. Ved å huske posisjonen og hoppe over det som ikke er endret henter senere synker bare det som er nytt.

---

### Hva vi lagrer fra annonsene (2026-11-10)

Utvalgte kolonner i `job_ad`, ikke rå JSON, pluss `employer` i egen tabell. Det som lagres: uuid, tittel, tekst, sted (kommune og fylke), omfang, sektor, søknadslenke, søknadsfrist, NAVs yrkeskategorier (`occupation_categories`, som JSON) og tidsstempler.

- **Kontaktinfo.** `contactList` og arbeidsgiverbeskrivelsen kopieres ikke. E-postadresser og telefonnumre i annonseteksten, tittelen og søknadsfristen byttes med `[fjernet]` (regex). Fristteksten røres bare når den ikke er en dato, siden en dato som `15-12-2026` ellers ligner på et telefonnummer. Søknadslenker som er e-postadresser (`mailto:` eller med `@`) lagres ikke. Punktum fungerer som skilletegn bare i formen `22.33.44.55`, slik at datoer som `01.12.2026` ikke fjernes. Navn i fritekst fjernes ikke, siden det ikke kan gjøres pålitelig uten AI. Dette er en kjent begrensning. Trengs kontaktinfo, hentes den på nytt via søknadslenken. Regexen for telefon kan også fjerne åtte siffer som ikke er telefon, for eksempel «2026 2027». Det er bevisst, fordi det er tryggere å fjerne for mye enn for lite.
- **Søknadsfrist.** `applicationDue` er fritekst («We are evaluating candidates continuously!»). Vi lagrer originalteksten i `application_deadline_text`, og en dato i `application_deadline` bare når teksten er en dato (ISO eller dd.mm.åååå).
- **Inaktive annonser.** Raden beholdes for statistikk, men status settes til `inactive` og teksten fjernes. All lesing av annonser skal gå gjennom `active_job_ads()`, slik at inaktive aldri havner i resultater.
- **Yrkeskategorier.** `occupationCategories` lagres uendret, fordi forfilteret i milepæl 3 skal bruke dem. Uten dem måtte alle annonser hentes på nytt.

**Hvorfor** Rå JSON ville tatt med kontaktpersoner, som vilkårene ikke tillater at vi lagrer. Kolonner er også enklere å lese og forklare. Feltene fra AI-uttrekket i milepæl 4 lagres separat.

---

### Kommunekoden er slettet (2026-10-30)

Adaptere, innlesing, tester, `documents`-tabellen og migrasjonen fra kommuneprosjektet er fjernet. Det samme gjelder innstillingen for pause mellom forespørsler. Skjelettet (Docker, Postgres, FastAPI, Alembic, n8n) er beholdt. `.env.example` har fått `DATABASE_URL`, og `CONTACT_EMAIL` er erstattet av `HTTP_USER_AGENT`, som config.py allerede krevde.

**Hvorfor** Milepæl 1 skal være et rent skjelett uten rester fra kommuneprosjektet. Koden ligger i git-historikken (commit 72163bf) hvis noe trengs senere.

---

### Uttrekksskjema, første utkast (2026-10-30)

Feltene AI-uttrekket skal fylle ut for hver annonse. Justeres når vi ser ekte data.

- `job_category`, én av frontend, backend, fullstack, mobil, devops og plattform, data og AI, IT-drift og support, test og kvalitet, design og UX, ledelse og prosjekt, annen IT, ikke IT
- `skills_required`, ferdigheter som står som krav, normalisert (for eksempel «React.js» og «ReactJS» blir «React»)
- `skills_preferred`, ferdigheter som står som ønsket eller en fordel
- `years_experience_min`, laveste antall års erfaring som kreves, tomt hvis det ikke står
- `education_requirement`, krav til utdanning med egne ord fra annonsen
- `junior_friendly`, ja, nei eller uklart, med en kort begrunnelse fra teksten
- `remote`, på stedet, hybrid, hjemmekontor eller uklart
- `language_requirements`, for eksempel norsk eller engelsk

Felt som NAV allerede leverer strukturert (sted, omfang, sektor, søknadsfrist, arbeidsgiver) hentes fra feeden og skal ikke trekkes ut med AI.

**Hvorfor** Bare felt som er nyttige for filtrering, matching eller statistikk er med. «Uklart» er et gyldig svar, slik at modellen ikke gjetter.

---

### Profilen min holdes utenfor git (2026-10-30)

CV, ferdigheter og ønsker ligger i profile/ og er lagt i .gitignore. Den offentlige demoen bruker en egen demoprofil.

**Hvorfor** Profilen inneholder personopplysninger om meg som ikke skal ligge åpent på GitHub.

---

### Forfilter før AI-uttrekk (2026-10-30)

Bare IT-relaterte annonser sendes til AI-uttrekk. Hvordan filteret lages avgjøres i milepæl 3.

**Hvorfor** Feeden inneholder mange tusen annonser. Å kjøre AI på alle ville kostet unødvendig mye og gitt mest støy.

---

### Datakilde er NAVs stillingsfeed (2026-10-30)

Vi bruker pam-stilling-feed fra NAV. Den er gratis, åpen for alle og laget for gjenbruk. Den offentlige tokenen brukes til utforsking, og fast token er søkt om på e-post til nav.team.arbeidsplassen@nav.no.

Vilkårene (https://arbeidsplassen.nav.no/vilkar-api) gir disse reglene for prosjektet.
- Annonser som blir inaktive eller slettes hos NAV skal straks fjernes fra resultatlisten.
- Annonser som endres skal oppdateres.
- Søknadsknappen skal lenke direkte til arbeidsgiverens søknadsfunksjon.
- Vi er selvstendig behandlingsansvarlig for personopplysninger i annonsene. Derfor lagres ikke kontaktpersoner eller annen kontaktinfo.
- Statistikk og analyse er eksplisitt tillatt.

Inaktive annonser skjules fra alle søk og matcher med en gang. De strukturerte feltene uten personopplysninger beholdes for statistikk over tid.

**Hvorfor** Etter erfaringen med kommuneprosjektet ville jeg ha en kilde som er publisert for gjenbruk, med tydelige vilkår og uten behov for manuell innsamling.

---

### Byttet fra kommuneprosjekt til jobbradar (2026-10-30)

Prosjektet startet som en RAG-tjeneste over politiske møtedokumenter fra kommunene rundt meg. Jeg spurte kommunene om tillatelse før jeg hentet noe. Løten svarte at manuell henting var greit, men ikke automatisk. Flere av de andre kommunene blokkerte automatisk henting i robots.txt. Manuell innsamling ville tatt mer tid enn prosjektet var verdt.

**Hvorfor** Dataene var flaskehalsen, ikke teknologien. Skjelettet fra milepæl 1 (Docker, Postgres med pgvector, FastAPI, n8n) ble tatt med videre uendret.
