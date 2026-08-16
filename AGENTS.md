# Repository guidance

## Scope and generated files

- These instructions apply to the whole repository.
- Do not inspect, search, edit, or report findings from `build/`,
  `cinemagoer.egg-info/`, `.cache/`, `.pytest_cache/`, or `.ruff_cache/`
  directories (including nested instances such as `tests/.cache/`).
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
- `imdb/parser/s3/`: SQLAlchemy queries, dataset-to-public-field transforms,
  soundex matching, and search ranking.
- `imdb/cli.py`: the installed `cinemagoer` command.
- `bin/`: dataset download, reduction, and database import tools.
- `tests/partial.db`: checked-in, deterministic SQLite fixture used by tests.
- `docs/`: Sphinx documentation written in reStructuredText.

## Environment and commands

`pyproject.toml` and `uv.lock` are the source of truth for supported Python
versions, dependencies, Ruff, pytest, coverage, tox, and Sphinx configuration.
Some prose in `docs/devel/test.rst` still describes older Makefile/tox setups;
do not copy those stale commands into new guidance.

Set up the locked development environment with:

```bash
uv sync --group dev
```

Run the narrowest useful checks while iterating, then the relevant broader
checks before handing off:

```bash
uv run pytest tests/test_search_get.py
uv run pytest
uv run pytest --cov
uv run ruff check --preview imdb tests
uv run sphinx-build -b html docs docs/_build
uv run tox
```

Ruff uses a 79-character project line length; tests override it to 119 via
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
- Keep generic access orchestration in `IMDbBase` and dataset/SQLAlchemy details
  in `IMDbS3AccessSystem`. Use SQLAlchemy statements and short-lived connection
  contexts consistently with the existing backend.
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
- When `CINEMAGOER_S3_URI` is set, tests target that external SQLAlchemy URI.
  Mention this explicitly when reporting results obtained from a non-default
  database.
- Do not run `s32cinemagoer.py` against an existing database without explicit
  user authorization: importing rebuilds (and therefore drops) its tables.
- Avoid tests that require network access or the live IMDb website. The library
  is designed around already-downloaded datasets.
- Match tests to the change: core containers/XML in `test_in_operator.py` and
  `test_xml.py`; backend retrieval in `test_search_get.py`; ranking in
  `test_search_ranking.py`; CLI output in `test_cli.py`.

## Documentation and releases

- Keep README and docs examples dataset-backed: create a database with
  `s32cinemagoer.py`, then connect with
  `Cinemagoer('s3', uri='sqlite:///...')`.
- Use valid reStructuredText, keep toctrees accurate, and build Sphinx after
  changing docs or public docstrings. Update documentation with user-visible
  API or CLI changes.
- Add meaningful user-visible fixes and features to `CHANGELOG.txt` when the
  task calls for release-facing documentation.
- For a version change, keep `imdb/version.py`, `pyproject.toml`, and
  `docs/conf.py` aligned, then run `uv lock` so the local project entry in
  `uv.lock` is refreshed. Do not perform tagging, publishing, uploads, or other
  release actions unless explicitly requested.
