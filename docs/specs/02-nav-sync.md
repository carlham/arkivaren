# M2 Synkronisering mot NAV

Status: pågår
Branch: m02-nav-sync

## Mål
Hente stillingsannonser fra NAVs pam-stilling-feed side for side, huske hvor vi slapp, og lagre dem uten kontaktinfo. Nye annonser legges til, endrede oppdateres og inaktive skjules med en gang.

## Ferdig når
- [x] Første synk mot ekte feed (siste 7 dager) fyller `job_ad`-tabellen (manuell sjekk: kjør `python -m app.nav.sync --since-days 7`, `SELECT count(*)` gir flere tusen rader og loggen viser antall).
- [x] Detaljkall hoppes over for inaktive og uendrede oppføringer (test: fixture med én ny, én uendret, én endret og én inaktiv gir to detaljkall).
- [x] Ny synk rett etterpå gir ingen duplikater (test: samme fixture synkes to ganger, antall rader er uendret).
- [x] Endret annonse oppdateres (test: fixture med endret tittel/tekst gir oppdatert rad).
- [x] Inaktiv annonse er skjult fra alle resultater (test: spørringen som brukes til lesing returnerer ikke inaktive).
- [x] Ingen kontaktpersoner eller kontaktinfo i databasen (test: lagret rad fra fixture med kontaktfelt inneholder ingen av verdiene; manuell sjekk: grep i `pg_dump`).
- [x] E-post og telefonnummer i annonseteksten er erstattet med `[fjernet]` (test: fixture med begge deler i teksten, lagret tekst inneholder ingen av dem).
- [x] Søknadsfrist tolkes riktig (test: «2026-12-01T23:59:59+01:00» og «01.12.2026» gir dato, «Snarest» gir tom dato, og originalteksten lagres alltid).
- [x] Kontaktinfo fjernes også fra tittel, søknadsfrist-tekst og søknadslenke (test: `mailto:`-lenke blir tom, e-post og telefon i tittel og fristtekst blir `[fjernet]`, datoer beholdes).
- [x] Midlertidige feil mot NAV prøves på nytt, og synken stopper uten å miste annonser (test: 503, 429 og nettverksfeil gir nye forsøk, etter fire forsøk stopper synken, 404 behandles som inaktiv, 304 gir tom synk).
- [x] Synken fortsetter fra sist lagrede posisjon (test: avbrutt synk starter på riktig side neste gang).
- [x] Token og base-URL leses fra `.env` via `Settings` (test: klienten sender token fra settings).
- [x] Ingen tester kaller NAV (alle bruker lagrede eksempelsvar i `api/tests/fixtures/`).
- [x] Logg per kjøring: antall sider, nye, endrede og inaktive annonser.

## Utenfor scope
- Forfilter og AI-uttrekk (M3 og M4).
- Embeddings og søk (M5).
- Planlegging av synk i n8n (M10).
- API-endepunkt for å lese annonser (kommer i M5). Skjuling av inaktive gjøres nå som en gjenbrukbar spørring/visning.

## Oppgaver
- [x] 1. Lagre noen ekte svar fra feeden som fixtures (liste og enkeltannonse), uten kontaktinfo der vi kan.
- [x] 2. Legg `NAV_FEED_BASE_URL` og `NAV_FEED_TOKEN` i `Settings`.
- [x] 3. Modeller `job_ad`, `employer` og `sync_state` + migrasjon `0002`.
- [x] 4. NAV-klient i `api/app/nav/client.py` som leser en side av gangen.
- [x] 5. Mapping fra feed-oppføring til `job_ad` som dropper kontaktfelt.
- [x] 6. Synk-logikk: ny, endret, inaktiv, og lagring av posisjon.
- [x] 7. CLI-inngang i `nav/sync.py` (`python -m app.nav.sync`).
- [x] 8. Oppdater decisions.md.

## Beslutninger
- Vi lagrer utvalgte kolonner per annonse (uuid, tittel, renset tekst, arbeidsgiver, sted, omfang, sektor, `application_deadline`, søknadslenke, status, tidsstempler), ikke rå JSON. Kontaktfelt droppes. Kan justeres senere hvis andre data trengs. Hvorfor: rå JSON ville tatt med kontaktinfo, og kolonner er enklere å forklare.

- NAVs `occupationCategories` lagres uendret som JSON i kolonnen `occupation_categories` på `job_ad`, uten egen tabell. Hvorfor: M3 skal bruke NAVs yrkeskategorier i forfilteret, og uten kolonnen måtte alle annonser hentes på nytt.
- E-postadresser og telefonnumre i annonseteksten fjernes med regex før lagring og erstattes med `[fjernet]`. Det samme gjelder tittelen og søknadsfristen (når den ikke er en dato), og en søknadslenke som er en e-postadresse (`mailto:` eller med `@`) lagres ikke. Navn i fritekst fjernes ikke (kan ikke gjøres pålitelig uten AI). Dette er en kjent begrensning og føres i decisions.md. Hvis kontaktinfo trengs, hentes den på nytt via søknadslenken.

- Synken startes med CLI: `docker compose exec api python -m app.nav.sync`. Logikken ligger i en funksjon i `nav/sync.py` som tar en database-sesjon og en klient, slik at et endepunkt kan kalle den samme i M10. Hvorfor: minst kode nå, endepunkt trengs først når n8n kommer inn.

- Inaktive annonser: `status = 'inactive'`, annonseteksten tømmes, de andre kolonnene beholdes for statistikk. Alle lesespørringer går via én felles `active_job_ads()`. Hvorfor: vilkårene krever at de forsvinner fra resultater, teksten kan inneholde personopplysninger, og decisions.md sier at strukturerte felt beholdes.
- Første synk starter 7 dager bak i tid med `If-Modified-Since` (valgfritt `--since-days`), og valgfri `--max-pages` for utvikling. Posisjonen lagres etter hver side. Hvorfor: NAV har ca. 600 nye annonser om dagen (4332 siste uke, målt av deg 2026-11-10), så 7 dager er rundt 3600 detaljkall, omtrent 35 minutter. Hele feeden inneholder historikk vi ikke trenger.
- Detaljkall gjøres bare for nye eller endrede aktive oppføringer. Inaktive oppføringer og aktive med samme `uuid` og `sistEndret` som i databasen hoppes over (inaktive som finnes fra før markeres og tømmes). Hvorfor: færre kall mot en gratis tjeneste, og senere synker henter bare det nye.
- Vi er greie mot NAV: 0,5 sekunder pause mellom kall (konstant i koden) og `HTTP_USER_AGENT` fra `.env` på alle kall.
- Feil mot NAV: 429, 5xx og nettverksfeil prøves på nytt opptil fire ganger med økende pause. Feiler det fortsatt, stopper synken, og det som er lagret blir stående. Vi hopper ikke over annonsen, for vi husker bare siste side og ville mistet den. En annonse som gir 404 er borte hos NAV og behandles som inaktiv. Svarer NAV 304 på første side, er synken tom. Hvorfor: en synk tar over en time, og én feil skal ikke kaste bort arbeidet eller miste annonser stille.
- Alle yrker hentes i M2. Filtrering til IT skjer i M3, før AI-uttrekk.
- Token-endepunktet `/api/publicToken` returnerer en tekstlinje foran selve tokenen. Tokenen limes inn i `.env` for hånd, klienten henter den ikke selv.

- Feedformat (bekreftet mot ekte svar 2026-11-10, se fixtures i `api/tests/fixtures/nav/`):
  - Auth: `Authorization: Bearer <token>`. Den offentlige tokenen hentes fra `/api/publicToken` (svaret har en tekstlinje foran tokenen) og roterer uregelmessig, så den limes inn i `.env` for hånd.
  - `GET /api/v1/feed` gir en side med opptil 1000 `items` og `next_url`. Hver oppføring har `_feed_entry` med `uuid`, `status` (`ACTIVE`/`INACTIVE`) og `sistEndret`. Detaljene hentes fra `url` i oppføringen (relativ, `/api/v1/feedentry/{uuid}`).
  - Detaljsvaret har `uuid`, `status`, `sistEndret` og `ad_content` (ikke `json`). For inaktive annonser mangler `ad_content`.
  - Hver endring gir en ny oppføring i feeden, så samme `uuid` kan dukke opp flere ganger. Siste oppføring gjelder.
  - Slutt på feeden: `next_url` er `null`. Posisjonen vi husker er `feed_url` til siste side vi leste, siden siste side ikke har noen `next_url`. Neste synk leser den siden på nytt, og det er ufarlig fordi uendrede annonser hoppes over.
  - Kontaktfelt: `ad_content.contactList[]` (navn, e-post, telefon, rolle, tittel). Droppes. `employer.description` lagres heller ikke.
  - `applicationDue` er fritekst, ikke alltid en dato (for eksempel «We are evaluating candidates continuously!»).
- Søknadsfrist lagres i to kolonner: `application_deadline_text` med originalteksten og `application_deadline` som dato. Datoen fylles bare ut når teksten er en dato (ISO, dd.mm.åååå eller dd-mm-åååå), ellers er den tom. Hvorfor: teksten som ikke er en dato går ikke tapt, og M5 kan filtrere på datoen.

## Åpne spørsmål
-

## Logg
- 2026-11-10: Etter oppgave 1 ble feedformatet bekreftet mot ekte svar. Rettet `json` til `ad_content`, la til sidestørrelse 1000, og la til `application_deadline_text` ved siden av `application_deadline` fordi `applicationDue` er fritekst. Nytt ferdig-når-punkt for tolking av søknadsfrist. Godkjent av deg med «go».
- 2026-11-10: La til `occupation_categories` (JSON) på `job_ad`, fordi M3 trenger NAVs yrkeskategorier. Godkjent av deg i chatten.
- 2026-11-10: Etter `/review` rettet jeg at spesifikasjonen sa at vi husker `next_url` / `next_id`. Koden lagrer `feed_url` til siste leste side, fordi siste side har `next_url = null`. Dessuten: kontaktinfo fjernes også fra tittel, fristtekst og søknadslenke, `dd-mm-åååå` leses som dato, og feil mot NAV (retry, 404, 304) er beskrevet. Godkjent av deg med «Ta 1-5».
