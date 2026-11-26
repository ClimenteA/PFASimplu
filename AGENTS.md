# AGENTS.md

PFASimplu is an accounting app for Romanian PFA/freelancers (partida simpla).
Stack: **Python 3.12 + Django 5.2 + SQLite**, server-rendered templates with
**Pico CSS + Alpine.js**. No frontend build step, no SPA, no REST API for the UI.

Run all commands from the repository root. Django code lives in `src/`
(`manage.py` is `src/manage.py`).

## Guiding principle

Keep it simple. Use Django and the standard library before writing anything new.
Do not add a library, abstraction, base class or helper for something that
already exists, and do not recreate existing project helpers.

- Prefer small, direct changes over refactors. No new layer or pattern for a
  one-off feature.
- No new dependencies, no JS build step or asset pipeline, no async/Celery/signals,
  no DRF or custom auth models. Use what is already in `pyproject.toml`.
- Prefer the ORM (`Q`, `F`, `annotate`, `aggregate`, `Subquery`) over raw SQL.
- Use `logging`, never `print()`. Use `timezone.now()`, never naive `datetime.now()`.

## Do not touch

- `appdata/` (runtime DB, uploads, logs) and `staticfiles/` (generated)
- Applied migrations. Add a new one instead (one migration per change; no
  squashing or regenerating).
- `.env`, DB files, generated media: never commit them.
- `appdata/db/stocare.db` from tests. Tests use the isolated DB only.

## Stop and ask

Fiscal logic is high-stakes and Romanian thresholds change yearly. If a task
needs a tax, VAT or deductibility rule that is not already implemented in the
files under "Where logic lives", **stop and ask**. Never guess a rate,
threshold, ceiling or deadline, and never hardcode one outside the central
files.

## Where logic lives

| What | Where |
|---|---|
| Taxes / impozite | `utils/calcule.py` |
| Deductibility, depreciation, fixed assets | `cheltuieli/calcul.py` |
| Reverse-charge VAT, D301, D390 | `utils/tva.py`, `utils/tva_documente.py` |
| Exchange rates | `utils/cursuri` (`CursBnr`), `utils/valuta` (`to_ron`, `ron_to_eur`) |
| Money rounding and formatting | `utils/decimale`, template filter `suma2` |
| Pagination, edit form, delete, CSV/XLSX export | `utils/views.py` |
| Per-user scoping | `utils/models.py`, `utils/multiuser.py` |
| File paths and serving | `utils/files.py` |

Apps whose purpose is not obvious from the name: `setari` (PFA data, bank
accounts, MCP API keys), `registre` (dashboards, mandatory registers, exports),
`utils` (shared code), `mcp_server` (FastMCP, read + add only).

Do not copy or invent fiscal formulas. Do not call exchange-rate APIs from views.

## Money rules

- Always `Decimal`, never `float`. Convert with `D(value)`.
- `rotund4` for intermediate steps, `rotund2` for final amounts (`ROUND_HALF_UP`).
- `suma(...)` for exact totals; `format_suma(...)` or `|suma2` for display.

## Models and data

- All user data models inherit `UserOwnedModel`. Its `UserScopedManager` filters
  by the current user; do not bypass it in user-facing code.
- One `SetariModel` per user: `SetariModel.objects.first()`.
- Store only facts the user entered. RON amounts, deductions, depreciation and
  invoice totals (`total_de_plata`) are `@property` values or `calcul.py`
  functions, never columns.
- `TextChoices` for enums, `gettext_lazy` for labels, `UniqueConstraint` for
  uniqueness. Date facts are `DateField`. `USE_TZ=True`, `Europe/Bucharest`.
- Files: `FileField(upload_to=get_save_path)`. Generated files go under
  `get_media_path()` / `get_extracts_path()`, never directly in `MEDIA_ROOT`.
- Invoice files are generated in `facturi/generare.py` after save, not in
  `save()`. PDF parsing happens in `documente/services.py`, not as a model
  side effect.
- Domain names are Romanian (`suma`, `incasari`, `deducere`); generic plumbing
  may be English. Match the language and style of the surrounding file for
  comments and user-facing text (user-facing text is Romanian).

## Adding a feature (CRUD pattern)

Copy the structure of **`<REFERENCE_APP>/views.py`** and
**`templates/<REFERENCE_TEMPLATE>.html`**, then adapt:

1. Model inherits `UserOwnedModel`; the form excludes `user`.
2. `ModelForm` with explicit widgets for dates and uploads.
3. Class-based `View`:
   - `get`: `handle_delete_id_query_param(...)`, then
     `get_page_items(request, Form, Model)`, then `render`.
   - `post`: validate; on success add a message and `redirect`; on failure
     re-render the bound form.
4. URL names are lowercase Romanian (`facturi`, `descarca-incasari`).
5. Template extends `base.html`; fields rendered manually
   (`{{ form.field }}` + `{{ form.field.errors }}`); POST forms keep CSRF tokens.

Messages use `extra_tags="✅ Succes!"`, `"🟥 Eroare!"` or `"🟥 Date necompletate!"`.

## Frontend

- `templates/base.html` is the only shell. Keep navigation, the message modal and
  the delete-confirm modal (`open-confirm` event) working.
- Pico classes first (`grid`, `container`, `article`, `striped`, `outline`);
  reuse `styles.css`, do not add a second CSS system.
- Alpine.js for local state; plain JS only when Alpine cannot do it.
- Assets are vendored in `src/static/`; no CDN at runtime (except the exported
  `SUMAR.html`).
- Keep element IDs and button labels stable. Playwright tests depend on them.

## Security

- Every page except login, registration and static requires authentication.
- Never expose another user's data. Rely on the scoped manager and the
  `user_<id>/` media prefix.
- Settings come from `PFASIMPLU_*` env vars (see `.env.example`).

## MCP server

`src/mcp_server/` exposes read tools plus `add_incasare` / `add_cheltuiala`.
It uses the same forms and `user_context()` so the scoped manager applies, and
intentionally has no delete tools. New write tools must copy
**`<REFERENCE_MCP_TOOL>`** and must not bypass form validation.

## Commands

```bash
uv sync                          # install dependencies
make dev                         # migrate + runserver on :8990
make dev-superuser               # admin account for /admin/
make ruff                        # format + fix
make check                       # format check + lint (CI)
make test-e2e                    # Playwright suite (isolated DB)
uv run src/manage.py test conturi documente   # Django TestCase tests
make migrate-all                 # makemigrations + migrate
make dist                        # wheel + PyCrucible executable in dist/
```

First run of the e2e suite may need browsers: `uv run playwright install chromium`.

## Tests

- Fiscal or money change → add/adjust a Django test in `src/<app>/tests.py` with
  a concrete numeric example. Assert exact `Decimal` values (e.g.
  `Decimal("1234.50")`), never approximate comparisons.
- UI or text change → update the Playwright assertions in `src/tests/`
  (helpers in `src/tests/helpers.py`, Faker for data).
- E2E follows the real workflow: Setari → Facturi → Incasari → Cheltuieli → Registre.

## Workflow and definition of done

- Run `make ruff` before finishing. Do not leave the dev server running.
- Do not commit unless asked. If asked, use short imperative commit messages.
- Done means: the change is small and uses existing helpers; `make check`
  passes; the relevant Django and/or e2e tests pass; no floats for money, no new
  dependencies, no edits to `appdata/`, `staticfiles/` or applied migrations.
  