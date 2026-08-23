How to make a release
=====================

**During development**

*Version files*

    Keep the project version aligned in these sources:

    - ``imdb/version.py`` (``__version__``)
    - ``pyproject.toml`` (``[project].version``)

    After changing them, run ``uv lock`` to refresh the local project entry in
    ``uv.lock``. Sphinx reads its ``version`` and ``release`` values from the
    installed distribution metadata, so ``docs/conf.py`` has no separate
    version string to update.

*CHANGELOG.txt*

    When a major fix or feature is committed, the changelog must be updated.


**When a new release is planned**

*CHANGELOG.txt*

    The date of the release has to be added.

*Version files*

    Update ``imdb/version.py`` and ``pyproject.toml`` to the new version, then
    run ``uv lock`` so ``uv.lock`` is refreshed.

*Translations*

    Compile the locale catalogs before tests and documentation checks::

      uv run python rebuildmo.py

    Generated ``.mo`` files are ignored and should not be committed. The PEP
    517 build compiles the shipped ``.po`` sources into each wheel.

*Checks and artifacts*

    Run the required quality checks and build both the source distribution and
    wheels from the repository and from that source distribution::

      uv run tox
      uv build --sdist --out-dir dist
      uv build --wheel --out-dir dist/direct .
      uv build --wheel --out-dir dist/from-sdist dist/*.tar.gz
      uv run --no-project python tools/verify_distributions.py \
          --sdist dist/*.tar.gz \
          --wheel dist/direct/*.whl \
          --wheel dist/from-sdist/*.whl

    Start with an empty ``dist`` directory so stale artifacts cannot satisfy a
    wildcard. The verifier checks sdist contents, compiled translations,
    metadata and dependency boundaries, the installed CLI, and a native SQLite
    query. See :doc:`packaging` for downstream packaging details.


**How to release**

- Commit the above changes.

- Add an annotated tag like *year.month.day*; e.g.: ``git tag -a 2020.09.25``
  (the commit message is not important).

- Build and verify the artifacts using the commands above.

- ``git push``

- ``git push --tags``

- Don't forget to push both sources and tags to both the GitHub and Bitbucket
  repositories (they are kept in sync).

- Upload to pypi: ``python3 -m twine upload dist/cinemagoer-*`` (you probably need
  a recent version of twine and the appropriate ~/.pypi file)

- The new tar.gz must also be uploaded
  to https://sourceforge.net/projects/cinemagoer/ (along with a new "news").

- Create a new release on GitHub, including the changelog and the whl and tar.gz files.
  https://github.com/cinemagoer/cinemagoer/releases/new


**communication**

- update the *content/news* section of https://github.com/cinemagoer/website

- add a news on https://sourceforge.net/p/cinemagoer/news/new

**After the release**

*CHANGELOG.txt*

    Add a new section for the next release, on top.

After that, you can commit the above changes with a message like "version bump"
