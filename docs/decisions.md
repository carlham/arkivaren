# Beslutningslogg

Nyeste øverst. Hver oppføring sier hva som ble bestemt og hvorfor.

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
