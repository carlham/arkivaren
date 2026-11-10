# M2 Synkronisering mot NAV: lesehjelp

Synken henter stillingsannonser fra NAVs feed side for side, lagrer dem uten kontaktinfo, og skjuler de som blir inaktive. Rundt 500 linjer produksjonskode i fem filer. Resten er tester, fixtures og dokumentasjon.

Linjenumrene gjelder da M2 ble ferdig. ★ betyr at du bør lese delen selv og kunne forklare den i et intervju.

## Leserekkefølge

| # | Fil | Hva den gjør | Viktigst |
|---|---|---|---|
| 1 | `docs/specs/02-nav-sync.md` | Hvorfor alt er som det er. Les **Beslutninger**. | ★ |
| 2 | `api/app/models.py` | Tabellene. `JobAd` (`:18`) har `status`, og teksten tømmes når annonsen blir inaktiv. `active_job_ads()` (`:50`) er den eneste veien til lesing av annonser. `SyncState` (`:55`) husker siste leste side. | `:18`, `:50` |
| 3 | `api/app/nav/client.py` | Snakker med NAV. `get_page` (`:40`) gir `None` ved 304. `_get` (`:60`) prøver på nytt ved 429 og 5xx (`RETRY_STATUSES :14`, `MAX_ATTEMPTS :15`). | `:60` |
| 4 | `api/app/nav/mapping.py` | Gjør et NAV-svar om til kolonner. `map_ad` (`:56`) velger feltene og dropper `contactList`. `remove_contact_info` (`:20`) bruker `EMAIL` (`:7`) og `PHONE` (`:10`). `parse_deadline` (`:39`) tolker frist, `clean_url` (`:32`) dropper e-postlenker. | ★ `:56`, `:20` |
| 5 | `api/app/nav/sync.py` | Selve synken. `sync` (`:21`) starter fra `since` første gang og fra lagret side etterpå. `sync_page` (`:57`) tar siste oppføring per annonse (`:59`) og har tre grener: inaktiv (`:69`), uendret (`:73`) og hent detaljer (`:77`). `mark_inactive` (`:95`), `save_ad` (`:102`). | ★ `:21`, `:57` |
| 6 | `api/tests/test_nav_sync.py`, `test_nav_mapping.py`, `test_nav_client.py` | Viser forventet oppførsel med anonymiserte NAV-svar. Test-navnene leses som en liste over hva koden skal gjøre. | skim |
| 7 | `api/tests/conftest.py` | `db`-fixturen: hver test kjører i en transaksjon som rulles tilbake, så ekte data blir urørt. | skim |

Hopp over, med mindre du er nysgjerrig: `api/migrations/versions/0002_job_ad_tables.py` (følger modellene), `api/tests/fixtures/nav/` (anonymiserte svar), `main()` og `parse_args()` i `sync.py` (kommandolinjen).

## Du bør kunne forklare
1. **Hvorfor vi lagrer `feed_url` til siste side og ikke `next_url`.** Siste side har `next_url = null`, så vi ville ikke hatt noe sted å starte. Å lese siste side på nytt er ufarlig.
2. **Hvorfor vi hopper over detaljkall for uendrede og inaktive annonser**, og hvorfor `sistEndret` sammenlignes mot verdien i listen (ikke i detaljsvaret, de er ikke like).
3. **Hvorfor synken stopper ved feil i stedet for å hoppe over annonsen.** Vi husker bare siste side, så en annonse på en tidligere side ville blitt borte for godt.
4. **Hvordan kontaktinfo fjernes, og hva som ikke fanges.** E-post og telefon fjernes med regex. Navn i fritekst fjernes ikke.

## Tips
- `git show <commit>` viser én commit. `git diff main...m02-nav-sync -- api/app/nav/sync.py` viser én fil.
- `/explain api/app/nav/sync.py::sync_page` forklarer en funksjon steg for steg.
