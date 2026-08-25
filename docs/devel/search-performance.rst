Bounded search benchmark
========================

Movie and person searches first generate candidates with indexed soundex
queries and then apply the existing Ratcliff-Obershelp relevance ranking in
Python.  Candidate generation is bounded per source so common soundex values
cannot materialize an entire collision group in application memory.

The default pool contains 1,000 candidates.  It grows by 20 candidates for
each requested result up to 10,000, and is always at least as large as the
requested result count.  Exact primary titles, AKA titles, and normal or
canonical name variants are selected before the rest of the pool.  Exact
title/year behavior, filters, reversed-name matching, Python ranking, and the
caller's final result limit are therefore retained.  Searches without a usable
soundex retain their separate 100-row exact-match limit.

The relevance scorer itself is unchanged.  For a soundex collision group
larger than its pool, fuzzy rows beyond the bounded database prefix are no
longer scored; exact variants are selected separately so they cannot be hidden
in that tail.

SQLAlchemy reflects tables only when a query first needs them.  The resulting
``Table`` objects and their stable schema metadata are cached in the adapter's
``MetaData`` for the lifetime of its engine.

Reproducing the benchmark
-------------------------

Run the fixed-query benchmark against an already imported SQLite database; it
opens the file read-only and never imports or changes data::

   python tools/benchmark_search.py /path/to/cinemagoer.db --repeat 3

To exercise the optional adapter as well::

   python tools/benchmark_search.py /path/to/cinemagoer.db \
       --adapter sqlalchemy --repeat 3

The JSON output records the snapshot path and size, row and raw candidate
counts, query plans, configured candidate limit, timings, peak traced Python
memory, top public results, and the SQLAlchemy tables reflected by the fixed
queries.  Keep the database file unchanged when comparing revisions.

The implementation baseline used the 2026-08-25 snapshot, a 21,294,022,656
byte SQLite file containing 12,741,362 title rows, 59,072,799 AKA rows, and
15,601,022 person rows.  ``Love`` produced 2,721 primary-title and 6,702 AKA
candidates.  ``Li`` and ``John Smith`` produced 105,207 and 133,004 person
candidates respectively.  ``EXPLAIN QUERY PLAN`` selected the existing
single-column soundex indexes in every case, including SQLite's multi-index
``OR`` plan for people, so the measurements did not support adding speculative
composite or covering indexes.

On that snapshot, a warm native ``Li`` search retained the same top five IDs
while reducing the Python-ranked pool from 105,207 rows to 1,000.  A direct
before/after run reduced elapsed time from 2.39 to 0.62 seconds and peak RSS
from approximately 148 MB to 30 MB.  Treat timings as machine-specific; use
the benchmark's candidate counts, plans, result IDs, and memory measurements
when comparing another implementation on the same snapshot.

This change does not alter the stored schema, and existing databases need no
reimport.  Rolling back the application code is sufficient; there is no data
migration to reverse.
