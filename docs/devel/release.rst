How to make a release
=====================

**During development**

*Version files*

    Keep the project version aligned in these files:

    - ``imdb/version.py`` (``__version__``)
    - ``pyproject.toml`` (``[project].version``)
    - ``uv.lock`` (regenerate with ``uv lock`` after changing the version)

*CHANGELOG.txt*

    When a major fix or feature is committed, the changelog must be updated.


**When a new release is planned**

*CHANGELOG.txt*

    The date of the release has to be added.

*Version files*

    Update ``imdb/version.py`` and ``pyproject.toml`` to the new version, then
    run ``uv lock`` so ``uv.lock`` is refreshed.


**How to release**

- Commit the above changes.

- Add an annotated tag like *year.month.day*; e.g.: ``git tag -a 2020.09.25``
  (the commit message is not important).

- ``python3 -m build``

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

- send an email to imdbpy-devel@lists.sourceforge.net and imdbpy-help@lists.sourceforge.net


**After the release**

*CHANGELOG.txt*

    Add a new section for the next release, on top.

After that, you can commit the above changes with a message like "version bump"
