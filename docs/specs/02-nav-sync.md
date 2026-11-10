# M2 Synkronisering mot NAV

Status: pågår
Branch: m02-nav-sync

## Mål
Hente stillingsannonser fra NAVs pam-stilling-feed side for side, huske hvor vi slapp, og lagre dem uten kontaktinfo. Nye annonser legges til, endrede oppdateres og inaktive skjules med en gang.

## Ferdig når
- [ ] Første synk mot ekte feed (siste 7 dager) fyller `job_ad`-tabellen (manuell sjekk: kjør `python -m app.nav.sync --since-days 7`, `SELECT count(*)` gir flere tusen rader og loggen viser antall).
- [ ] Detaljkall hoppes over for inaktive og uendrede oppføringer (test: fixture med én ny, én uendret, én endret og én inaktiv gir to detaljkall).
- [ ] Ny synk rett etterpå gir ingen duplikater (test: samme fixture synkes to ganger, antall rader er uendret).
- [ ] Endret annonse oppdateres (test: fixture med endret tittel/tekst gir oppdatert rad).
- [ ] Inaktiv annonse er skjult fra alle resultater (test: spørringen som brukes til lesing returnerer ikke inaktive).
- [ ] Ingen kontaktpersoner eller kontaktinfo i databasen (test: lagret rad fra fixture med kontaktfelt inneholder ingen av verdiene; manuell sjekk: grep i `pg_dump`).
- [ ] E-post og telefonnummer i annonseteksten er erstattet med `[fjernet]` (test: fixture med begge deler i teksten, lagret tekst inneholder ingen av dem).
- [ ] Synken fortsetter fra sist lagrede posisjon (test: avbrutt synk starter på riktig side neste gang).
- [ ] Token og base-URL leses fra `.env` via `Settings` (test: klienten sender token fra settings).
- [ ] Ingen tester kaller NAV (alle bruker lagrede eksempelsvar i `api/tests/fixtures/`).
- [ ] Logg per kjøring: antall sider, nye, endrede og inaktive annonser.

## Utenfor scope
- Forfilter og AI-uttrekk (M3 og M4).
- Embeddings og søk (M5).
- Planlegging av synk i n8n (M10).
- API-endepunkt for å lese annonser (kommer i M5). Skjuling av inaktive gjøres nå som en gjenbrukbar spørring/visning.

## Oppgaver
- [x] 1. Lagre noen ekte svar fra feeden som fixtures (liste og enkeltannonse), uten kontaktinfo der vi kan.
- [ ] 2. Legg `NAV_FEED_BASE_URL` og `NAV_FEED_TOKEN` i `Settings`.
- [ ] 3. Modeller `job_ad`, `employer` og `sync_state` + migrasjon `0002`.
- [ ] 4. NAV-klient i `api/app/nav/client.py` som leser en side av gangen.
- [ ] 5. Mapping fra feed-oppføring til `job_ad` som dropper kontaktfelt.
- [ ] 6. Synk-logikk: ny, endret, inaktiv, og lagring av posisjon.
- [ ] 7. CLI-inngang i `nav/sync.py` (`python -m app.nav.sync`).
- [ ] 8. Oppdater decisions.md.

## Beslutninger
- Vi lagrer utvalgte kolonner per annonse (uuid, tittel, renset tekst, arbeidsgiver, sted, omfang, sektor, `application_deadline`, søknadslenke, status, tidsstempler), ikke rå JSON. Kontaktfelt droppes. Kan justeres senere hvis andre data trengs. Hvorfor: rå JSON ville tatt med kontaktinfo, og kolonner er enklere å forklare.

- E-postadresser og telefonnumre i annonseteksten fjernes med regex før lagring og erstattes med `[fjernet]`. Navn i fritekst fjernes ikke (kan ikke gjøres pålitelig uten AI). Dette er en kjent begrensning og føres i decisions.md. Hvis kontaktinfo trengs, hentes den på nytt via søknadslenken.

- Synken startes med CLI: `docker compose exec api python -m app.nav.sync`. Logikken ligger i en funksjon i `nav/sync.py` som tar en database-sesjon og en klient, slik at et endepunkt kan kalle den samme i M10. Hvorfor: minst kode nå, endepunkt trengs først når n8n kommer inn.

- Inaktive annonser: `status = 'inactive'`, annonseteksten tømmes, de andre kolonnene beholdes for statistikk. Alle lesespørringer går via én felles `active_job_ads()`. Hvorfor: vilkårene krever at de forsvinner fra resultater, teksten kan inneholde personopplysninger, og decisions.md sier at strukturerte felt beholdes.
- Første synk starter 7 dager bak i tid med `If-Modified-Since` (valgfritt `--since-days`), og valgfri `--max-pages` for utvikling. Posisjonen lagres etter hver side. Hvorfor: NAV har ca. 600 nye annonser om dagen (4332 siste uke, målt av deg 2026-11-10), så 7 dager er rundt 3600 detaljkall, omtrent 35 minutter. Hele feeden inneholder historikk vi ikke trenger.
- Detaljkall gjøres bare for nye eller endrede aktive oppføringer. Inaktive oppføringer og aktive med samme `uuid` og `sistEndret` som i databasen hoppes over (inaktive som finnes fra før markeres og tømmes). Hvorfor: færre kall mot en gratis tjeneste, og senere synker henter bare det nye.
- Vi er greie mot NAV: 0,5 sekunder pause mellom kall (konstant i koden) og `HTTP_USER_AGENT` fra `.env` på alle kall.
- Alle yrker hentes i M2. Filtrering til IT skjer i M3, før AI-uttrekk.
- Token-endepunktet `/api/publicToken` returnerer en tekstlinje foran selve tokenen. Tokenen limes inn i `.env` for hånd, klienten henter den ikke selv.

- Feedformat (fra NAVs dokumentasjon, må bekreftes mot ekte svar i oppgave 1):
  - Auth: `Authorization: Bearer <token>`. Den offentlige tokenen hentes fra `/api/publicToken` og roterer uregelmessig, så den limes inn i `.env` for hånd.
  - `GET /api/v1/feed` gir en side med `items` og `next_url`. Hver oppføring har `_feed_entry` med `uuid`, `status` (`ACTIVE`/`INACTIVE`) og `sistEndret`. Detaljene hentes fra `url` i oppføringen.
  - Hver endring gir en ny oppføring i feeden, så samme `uuid` kan dukke opp flere ganger. Siste oppføring gjelder.
  - Slutt på feeden: `next_url` er `null`. Posisjonen vi husker er siste `next_url` / `next_id`.
  - Kontaktfelt: `json.contactList[]` (navn, e-post, telefon, rolle, tittel). Droppes.
  - Stoppede annonser kan ha tittel, arbeidsgiver og kontaktinfo maskert. Vi leser ikke detaljer for inaktive annonser.

## Åpne spørsmål
-

## Logg
-
