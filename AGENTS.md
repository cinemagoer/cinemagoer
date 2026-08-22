<!-- CODEGRAPH_START -->
## CodeGraph

This repository is indexed in `.codegraph/`. Before using text search or
opening source files to locate or understand code, run:

```bash
codegraph explore "<symbols or question>"
```

Prefer the equivalent `codegraph_explore` MCP tool when it is available. Its
output includes current, line-numbered source and call paths, including dynamic
dispatch that text search can miss. Use `rg` or direct file reads afterward for
configuration, prose, data files, or details CodeGraph did not return.
<!-- CODEGRAPH_END -->

# Repository guidance

## Scope and generated files

- These instructions apply to the whole repository.
- Do not inspect, search, edit, or report findings from `build/`, `dist/`,
  `cinemagoer.egg-info/`, `.cache/`, `.pytest_cache/`, `.ruff_cache/`, `.tox/`,
  `.venv/`, or `__pycache__/` directories (including nested instances such as
  `tests/.cache/`). Treat `.coverage` as generated as well.
- Treat `docs/_build/` and compiled locale files (`*.mo`) as generated output.
  Change their sources instead.
- Preserve unrelated worktree changes. Check `git status --short` before editing
  and keep the final diff limited to the requested work.

## Project overview

Cinemagoer is a Python 3.10+ library and CLI for querying a local SQL database
populated from IMDb's non-commercial downloadable datasets. The supported data
access system is the dataset-backed `s3` backend; do not reintroduce assumptions
about the retired IMDb web-page parsers.

Important areas:

- `imdb/__init__.py`: public factory (`IMDb`/`Cinemagoer`) and shared access
  system behavior.
- `imdb/Movie.py`, `Person.py`, `Character.py`, `Company.py`, and `utils.py`:
  dictionary-like public data containers and compatibility helpers.
- `imdb/parser/s3/`: native SQLite and optional SQLAlchemy adapters,
  dataset importing, dataset-to-public-field transforms, soundex matching,
  and search ranking. `adapters.py` owns canonical `sqlite:` access,
  `sqlalchemy_adapter.py` owns optional dialect support, and `importer.py`
  mirrors that split for database creation.
- `imdb/cli.py`: the installed `cinemagoer` command.
- `bin/`: dataset download, reduction, and database import tools.
- `tests/partial.db`: checked-in, deterministic SQLite fixture used by tests.
- `docs/`: Sphinx documentation written in reStructuredText.

## Environment and commands

`pyproject.toml` and `uv.lock` are the source of truth for supported Python
versions, dependencies, Ruff, pytest, coverage, and tox. Sphinx dependencies
and its tox command are declared there; project-specific Sphinx settings live
in `docs/conf.py`. The GitHub Actions workflow is the source of truth for what
CI actually runs. Some prose in `docs/devel/test.rst` still describes older
Makefile/tox setups; do not copy those stale commands into new guidance.

Set up the locked development environment with:

```bash
uv sync --locked --group dev
```

CI compiles locale catalogs before running tests. On a clean checkout, or
after changing a `.po` file, generate the ignored `*.mo` outputs with:

```bash
uv run python rebuildmo.py
```

Run the narrowest useful checks while iterating, then the relevant broader
checks before handing off:

```bash
uv run pytest tests/test_search_get.py
uv run pytest tests/test_s3_optional_sqlalchemy.py
uv run pytest
uv run pytest --cov
uv run ruff check --preview imdb tests
uv run sphinx-build -b html docs docs/_build
uv run tox
uv build
```

The current CI test matrix covers Python 3.10 through 3.14. The tox environment
list in `pyproject.toml` covers Python 3.10 through 3.13 plus style and docs, so
tox is not a substitute for checking the Python 3.14 CI job. Ruff uses a
79-character project line length; tests override it to 119 via
`tests/ruff.toml`. Do not perform broad formatting or modernization unrelated
to the task.

## Implementation conventions

- Preserve the public import surface and legacy names under the `imdb` package;
  `Cinemagoer` is an alias of `IMDb`, and `s3` has several documented aliases.
- `Movie`, `Person`, `Character`, and `Company` are dictionary-like containers,
  not dataclasses. Preserve their key aliases, computed keys, comparison and
  containment behavior, reference handling, XML serialization, `current_info`,
  and `infoset2keys` semantics.
- Dataset column-to-API mappings belong in `DB_TRANSFORM` in
  `imdb/parser/s3/utils.py`. Public data keys normally use lowercase words with
  spaces; avoid leaking raw TSV or SQL column names through the API.
- Keep generic access orchestration in `IMDbBase` and dataset/database details
  in `IMDbS3AccessSystem` and its adapters. Canonical `sqlite:` URIs must stay
  on the standard-library `sqlite3` path without importing SQLAlchemy;
  `sqlite+pysqlite:` and non-SQLite dialects use the optional SQLAlchemy path.
  Preserve lazy loading of the optional dependency. Use parameterized native
  SQL in `SQLiteAdapter`, and SQLAlchemy statements and short-lived connection
  contexts in `SQLAlchemyAdapter`.
- Preserve import/query adapter parity. Canonical `sqlite:` imports use
  `SQLiteImporter`; explicitly selected and non-SQLite dialects use
  `SQLAlchemyImporter`. Imported dataset years are exposed as strings.
- Search changes should retain exact-title/year, AKA, reversed-name, filtering,
  ranking, and result-limit behavior. Add targeted regression tests for ranking
  or normalization changes.
- The current backend only implements movie and person search/get. Standalone
  character behavior is intentionally documented by an `xfail`; do not turn
  that into a silent pass or broaden backend scope accidentally.
- Follow the existing GPL v2-or-later licensing and copyright-header style in
  new source modules.

## Testing and data safety

- Tests use `tests/partial.db` unless `CINEMAGOER_S3_URI` is set. Prefer the
  bundled fixture for reproducible tests, and add data to it only when a test
  cannot be expressed with existing rows or isolated unit inputs.
- When `CINEMAGOER_S3_URI` is set, tests target that external database URI.
  A canonical `sqlite:` value still selects the native adapter; other dialects
  select SQLAlchemy. Mention the URI/dialect and adapter when reporting results
  obtained from a non-default database.
- The `dev` dependency group installs SQLAlchemy, so its missing-extra test is
  skipped in the normal development environment. Validate the base package in
  an isolated environment with SQLAlchemy absent when changing dependency
  boundaries or adapter selection; also exercise a real non-SQLite dialect
  with its DBAPI driver when changing SQLAlchemy support.
- Do not run `s32cinemagoer.py` against an existing database without explicit
  user authorization: importing rebuilds (and therefore drops) its tables.
- Avoid tests that require network access or the live IMDb website. The library
  is designed around already-downloaded datasets.
- Match tests to the change: container behavior in `test_in_operator.py` and
  `test_container_comparison.py`; XML in `test_xml.py`; person helpers in
  `test_person.py`; backend retrieval in `test_search_get.py`; episodes in
  `test_s3_episodes.py`; ranking in `test_search_ranking.py`; adapter/importer
  boundaries in `test_s3_optional_sqlalchemy.py`; locale behavior in
  `test_locale.py`; and CLI output in `test_cli.py`.

## Documentation and releases

- Keep README and docs examples dataset-backed: create a database with
  `s32cinemagoer.py`, then connect with
  `Cinemagoer('s3', uri='sqlite:///...')`.
- Document SQLite as a base-package capability. Non-SQLite databases require
  the `sqlalchemy` extra plus a separately selected DBAPI driver; keep both the
  user path in `docs/usage/s3.rst` and downstream implications in
  `docs/devel/packaging.rst` accurate when this boundary changes.
- Use valid reStructuredText, keep toctrees accurate, and build Sphinx after
  changing docs or public docstrings. Update documentation with user-visible
  API or CLI changes.
- Treat packaging checks as clean-artifact checks: build both wheel and sdist,
  verify required compiled translations and test fixtures are present where
  intended, and smoke-test the installed artifact rather than relying only on
  the source checkout.
- Add meaningful user-visible fixes and features to `CHANGELOG.txt` when the
  task calls for release-facing documentation.
- For a version change, keep `imdb/version.py`, `pyproject.toml`, and
  `docs/conf.py` aligned, then run `uv lock` so the local project entry in
  `uv.lock` is refreshed. Do not perform tagging, publishing, uploads, or other
  release actions unless explicitly requested.
