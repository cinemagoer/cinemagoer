How to make a release
=====================

**During development**

*setup.cfg*

    The ``egg_info`` section must include the lines below::

      [egg_info]
      tag_build = dev
      tag_date = true

*imdb.version*

    Be sure that the ``__version__`` variable is up-to-date.

*docs/Changelog.rst*

    When a major fix or feature is committed, the changelog must be updated.


**When a new release is planned**

*setup.cfg*

    In the ``egg_info`` section, the lines mentioned above must be
    commented out.

*setup.py*

    Not touched.

*docs/Changelog.rst*

    The date of the release has to be added.


**How to release**

- Commit the above changes.

- Add an annotated tag like *major.minor*; e.g.: ``git tag -a 6.3``
  (the commit message is not important).

- ``python3 setup.py sdist``

- ``python3 setup.py bdist_wheel``

- ``git push``

- ``git push --tags``

- Don't forget to push both sources and tags to both the GitHub and Bitbucket
  repositories (they are kept in sync).

- Upload to pypi: ``twine upload dist/IMDbPY-*`` (you probably need a recent
  version of twine and the appropriate ~/.pypi file)

- The new tar.gz must also be uploaded
  to https://sourceforge.net/projects/imdbpy/ (along with a new "news").


**communication**

- access the web site with: `sftp ${your-sourceforge-username}@frs.sourceforge.net` and move to the *imdbpy_web/htdocs/*

- download *index.html* and add an *article* section, removing the one or more of the old ones

- upload the page

- add a news on https://sourceforge.net/p/imdbpy/news/new

- send an email to imdbpy-devel@lists.sourceforge.net and imdbpy-help@lists.sourceforge.net


**After the release**

*setup.cfg*

    Uncomment the two lines again.


*docs/Changelog.rst*

    Add a new section for the next release, on top.

After that, you can commit the above changes with a message like "version bump"
