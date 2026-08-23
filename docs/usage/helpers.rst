Compatibility helpers
=====================

The :mod:`imdb.helpers` and :mod:`imdb.utils` modules contain a mixture of
dataset-aware conveniences and general operations for Cinemagoer's
dictionary-like containers. They remain supported when they operate on the
current S3 backend, serialized containers, or data supplied by the caller.

Current dataset helpers
-----------------------

These helpers operate directly on data returned by the S3 backend:

- :func:`imdb.helpers.get_byURL` extracts a movie or person IMDb ID and
  retrieves it from the configured dataset database. Character and company
  URLs are rejected because the backend does not implement standalone
  character or company retrieval.
- :func:`imdb.helpers.sortedSeasons` and
  :func:`imdb.helpers.sortedEpisodes` order the episode structure returned by
  the ``episodes`` infoset.
- :func:`imdb.helpers.akasLanguages`,
  :func:`imdb.helpers.sortAKAsBySimilarity`, and
  :func:`imdb.helpers.getAKAsInLanguage` support the structured AKA records
  returned by S3 as well as legacy string records.

Container and caller-data helpers
---------------------------------

The following helpers do not depend on a data access system and remain useful
for applications:

- ``makeObject2Txt``, ``makeTextNotes``, ``makeCgiPrintEncoding``, and
  ``cgiPrint`` format containers or caller-provided values.
- ``makeModCGILinks``, ``modHtmlLinks``, and ``modHtmlLinksASCII`` transform
  explicit title/name/character reference maps. S3 does not populate the old
  web-parser reference maps, but callers and deserialized objects can provide
  them.
- ``keyToXML``, ``translateKey``, ``tagToKey``, ``parseTags``, and ``parseXML``
  support XML and localized data keys. ``parseXML`` uses only the Python
  standard library.
- ``resizeImage`` transforms a compatible image URL supplied by the caller.
  IMDb's downloadable datasets do not provide cover or headshot URLs.

The public analysis/building utilities in :mod:`imdb.utils` are also retained:
name, title, and company analyzers/builders; ``is_series_episode``; container
comparators; ``modNull`` and the ``modClear*Refs`` functions;
``modifyStrings``; ``date_and_notes``; ``RolesList``; ``escape4xml``; and
``flatten``. They operate on strings or containers and do not parse IMDb web
pages.

Character and company containers
--------------------------------

:class:`imdb.Character.Character` and :class:`imdb.Company.Company` remain
supported as dictionary-like compatibility containers. Character objects are
used for role data and both types can occur in manually constructed or
deserialized object graphs. The S3 backend does not provide standalone
character/company search or retrieval; retaining the containers does not imply
that backend capability.

Removed web-parser helper
-------------------------

``fullSizeCoverURL`` was removed. It was an obsolete wrapper around
cover/headshot fields supplied by the retired web-page parsers. Applications
that already have an image URL can continue to use ``resizeImage`` or the
container's computed full-size image key.
