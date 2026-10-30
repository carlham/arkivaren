# Plan

Én milepæl per økt. Hver milepæl har et «ferdig når» som må være oppfylt før vi går videre.

## 1. Skjelett ✅
Docker Compose med PostgreSQL (pgvector), FastAPI og n8n. Ferdig fra forrige prosjekt, men prosjektnavn og eventuelle kommunerester skal ryddes bort.

## 2. Synkronisering mot NAV
Klient mot pam-stilling-feed som leser feeden side for side og husker hvor den slapp. Lagre annonsene uten kontaktinfo. Nye annonser legges til, endrede oppdateres og inaktive markeres slik at de forsvinner fra alle resultater med en gang. Token leses fra .env, slik at den offentlige tokenen kan byttes med en fast senere.
Ferdig når en første synk og en ny synk etterpå fungerer, ingen annonser dupliseres, inaktive annonser er skjult, og ingen kontaktpersoner ligger i databasen.

## 3. Forfilter
Finn ut hvilke felt i annonsene som kan brukes for å plukke ut IT-relaterte stillinger (NAVs egne yrkeskategorier, tittel, nøkkelord). Skriv funnene i decisions.md. Bare annonser som passerer går videre til AI-uttrekk.
Ferdig når filteret er testet på et utvalg annonser og jeg har sett gjennom hva som ble tatt med og hva som falt utenfor.

## 4. AI-uttrekk
La en rimelig Claude-modell lese annonseteksten og returnere strukturerte felt etter skjemaet i decisions.md. Lagre resultatet sammen med en hash av teksten, slik at uttrekket bare kjøres på nytt når teksten endres. Lag samtidig evals/extraction_eval.py som sammenligner uttrekket med mine håndmerkede annonser.
Ferdig når alle annonser som passerer forfilteret har strukturerte felt, og evalueringen gir treffsikkerhet per felt.

## 5. Søk og filtre
Embeddings av annonsene med BGE-M3. Endepunkt som kombinerer vektorsøk, fulltekstsøk og filtre på kategori, sted, omfang, hjemmekontor, junior og søknadsfrist.
Ferdig når `GET /jobs` gir relevante treff for både fritekst og filtre, og jeg har skrevet deler av søkelogikken selv.

## 6. Profil
Les inn filene i profile/ (CV, ferdigheter, prosjekter, ønsker), del dem opp og lag embeddings. Profilen skal kunne oppdateres ved å endre filene og kjøre innlesingen på nytt.
Ferdig når hver bit av profilen kan hentes med søk og spores tilbake til filen den kom fra.

## 7. Matching
To steg. Først et raskt utvalg med vektorsøk og filtre ut fra ønskene mine. Deretter vurderer Claude de beste kandidatene og svarer med en vurdering (passer godt, delvis, dårlig), hvilke krav jeg dekker med henvisning til profilen, og hvilke krav jeg mangler. Resultatet lagres, så samme annonse ikke vurderes to ganger uten endring.
Ferdig når evals/match_eval.py viser hvor ofte systemets vurdering stemmer med mine egne merkelapper.

## 8. Assistent
Et chat-endepunkt der Claude har verktøy for å søke i annonser, hente en annonse, hente bevis fra profilen og hente statistikk. Den skal kunne svare på «hva slags jobber passer meg?» med konkrete annonser, lenker og begrunnelse. Den skal aldri finne opp annonser og skal si fra når den ikke finner noe. Svarene strømmes til klienten.
Ferdig når spørsmålene i evals/assistant_questions.yaml er kjørt og jeg har gått gjennom svarene.

## 9. Markedsinnsikt
Endepunkter for statistikk. Mest etterspurte ferdigheter per kategori og region, utvikling over tid, andel stillinger som passer for nyutdannede, og hvor mange «junior»-stillinger som likevel krever flere års erfaring.
Ferdig når tallene stemmer med en manuell sjekk på et lite utvalg.

## 10. n8n
Daglig flyt som kjører synk, uttrekk og matching i rekkefølge, og en morgenflyt som sender meg e-post med nye stillinger som passer godt. Flytene eksporteres til n8n/.
Ferdig når e-posten kommer uten at jeg gjør noe, og en feil i ett steg gir varsel i stedet for å stoppe stille.

## 11. Frontend
React med stillingsliste og filtre, annonsevisning med matchvurdering, dashboard med statistikk og en chat med assistenten. Universell utforming fra start, med tastaturnavigasjon, skjermleserstøtte og god kontrast.

## 12. Deploy
Kjør det på en server. Den offentlige versjonen bruker en demoprofil, slik at CV-en min ikke ligger åpent. README forklarer arkitekturen, viser resultatene fra evalueringene og hva jeg lærte.

## Senere
- Varsling på flere kanaler enn e-post
- Følge med på enkeltarbeidsgivere
- Sammenligne utviklingen i markedet måned for måned
