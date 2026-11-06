# buscador-pisos

Sistema que encuentra el mejor alquiler en CABA para Marcos, al mejor precio.
Captura avisos de portales, inmobiliarias y fuentes informales, los valora contra el mercado y avisa por Telegram.
Especificación completa: `docs/SPEC.md`. Decisiones tomadas y pendientes: `docs/DECISIONES.md`.

## Personas

- **Gabi**: dueño del repo. Revisa y acepta los PRs. Vive en A Coruña (hora de Madrid).
- **Marcos**: el que se muda. Recibe alertas y hace las visitas. Vive en Buenos Aires.
- Fecha objetivo: contrato nuevo con entrada el 1 de mayo de 2027.

## Cómo se trabaja en este repo

- Las tareas son issues de GitHub. Tomalas con la skill `/siguiente-tarea`.
- Una tarea = una rama = un PR. Nombre de rama: `tarea/<id>-<slug>`, por ejemplo `tarea/c05-scraper-portales`.
- Solo tomá issues con etiqueta `tipo:claude` y sin dependencias abiertas.
- Las etiquetas `tipo:gabi` y `tipo:marcos` son trabajo humano. Nunca las cierres vos.
- Cada PR cumple el criterio de aceptación del issue. Pegá en el PR la salida del comando que lo demuestra.
- Cada PR deja tests. Un adaptador sin fixture HTML no se acepta.
- El PR dice `Closes #N`. Si el alcance cambió, explicalo en el PR, no lo amplíes en silencio.
- Si falta una decisión, pará y comentá en el issue. No inventes valores de negocio (tope, barrios, pesos).

## Stack

| Pieza | Tecnología | Dónde corre |
| --- | --- | --- |
| Base de datos | Supabase (Postgres + PostGIS), plan gratis | Nube |
| Funciones | Supabase Edge Functions (Deno/TypeScript) | Nube |
| Scrapers y lotes | Python 3.12 con `uv`, Playwright | PC de Windows de Gabi (IP residencial) y GitHub Actions |
| IA por lotes | `claude -p` con modelo Haiku y salida JSON | PC de Windows, franja 02:00–08:00 Madrid |
| Lector de alertas | Google Apps Script | Gmail exclusivo de alertas |
| Bot | Telegram Bot API vía Edge Function `telegram` | Nube |
| Web privada | HTML + JS estático, Leaflet, Supabase Auth | Firebase Hosting |
| Tareas programadas | GitHub Actions, Programador de tareas de Windows, pg_cron | Varias |

**No usar n8n.** El único n8n disponible es de la empresa de Gabi y no se puede usar para este proyecto.
**Costo objetivo: US$0.** La única API paga permitida es una clave opcional con tope de US$5/mes para visión (ver `docs/DECISIONES.md`).

## Estructura

```
scrapers/        Python: portales, inmobiliarias, ficha, runner
  portales/      zonaprop, argenprop, properati
  inmobiliarias/ adaptadores por plataforma (tokko, ...)
  fixtures/      HTML y emails reales para tests
enrich/          Python: lotes de IA, deduplicado, modelo de precios
supabase/
  migrations/    SQL versionado
  functions/     ingest, ml-sync, telegram, notify
apps-script/     lector de Gmail
web/             página estática
config/          busqueda.yaml (filtros, barrios, pesos)
.claude/         skills, agentes, hooks
docs/            SPEC.md, DECISIONES.md
legacy/          scraper original (cacho-se-muda), solo lectura
```

## Comandos

```
uv sync                        # dependencias Python
uv run pytest                  # tests Python
uv run ruff check . && uv run ruff format --check .
supabase start                 # stack local
supabase db reset              # aplica migraciones en local
supabase functions serve       # funciones en local
deno test supabase/functions   # tests de funciones
```

## Reglas de scraping

- Máximo 1 página cada 5–10 segundos por portal, con espera aleatoria.
- Bajá cada ficha una sola vez. El listado solo detecta altas, bajas y cambios de precio.
- Zonaprop y Argenprop corren desde la PC (IP residencial). Nunca desde GitHub Actions.
- Guardá el HTML crudo comprimido (gzip) solo de avisos dentro de los barrios objetivo.
- Uso privado. Nunca redistribuyas datos de los portales.

## Secretos

- Nunca escribas claves en archivos versionados. Usá `.env` local (ignorado), GitHub Secrets y Supabase Vault.
- `.env.example` lista los nombres, sin valores.

## Convenciones

- Código y nombres en inglés. Textos para Marcos y Gabi en español rioplatense.
- Montos en pesos argentinos como enteros. Moneda siempre explícita en el esquema.
- Fechas en UTC en la base. Mostrá hora de Buenos Aires a Marcos y hora de Madrid a Gabi.
- Python: tipado, `ruff`, funciones chicas. TypeScript: `deno fmt` y `deno lint`.
- Migraciones nuevas, nunca editar una ya aplicada.
- RLS activado en todas las tablas. La web lee solo vistas permitidas a los 2 usuarios.
