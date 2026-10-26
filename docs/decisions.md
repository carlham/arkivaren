# Beslutninger

## Milepæl 1 — skjelett

- **`pgvector/pgvector:pg16` som database-image** i stedet for `postgres:16` + manuell installasjon av pgvector. Bildet har extensionen ferdig kompilert inn, og vi trenger den uansett fra milepæl 4.
- **psycopg v3, synkron modus** som Postgres-driver, ikke async. Enklere å forklare og lese, og ingen av de tidlige milepælene har ytelseskrav som trenger async. Kan revurderes hvis det blir en flaskehals senere.
- **n8n med eget SQLite-volum**, ikke koblet til applikasjonens Postgres-database. Holder n8n sitt interne skjema (workflows, kjøringshistorikk) separat fra våre data.
- **Python 3.12**, ikke 3.14. Brukeren har 3.14 lokalt installert, men siden alt kjører i Docker er det ikke noe krav om at lokal og container-versjon matcher. 3.12 har bedre støtte i økosystemet (ferdigbygde wheels for psycopg og pydantic-core).
- **requirements.txt med pinnede versjoner**, ikke Poetry/uv. Enklest å lese og forklare, ingen ekstra verktøy å installere.
- Første Alembic-migrasjon gjør kun `CREATE EXTENSION IF NOT EXISTS vector` — ingen tabeller ennå, siden milepæl 1 bare krever en tom database med migrasjonsinfrastruktur på plass.
