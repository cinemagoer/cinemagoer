JSON Extraction Utilities
=========================

Since some time some IMDb web pages contains a `<script id="__NEXT_DATA__">` tag
with a JSON object containing extended information.

For example, parsing the HTML of the "top 250 movies" page will result in
just 25 items, while the JSON object contains 250 items.

We have introduced the `jsel` and `jextr` modules, which provide utilities for extracting and selecting information from that JSON data.

jsel module
-----------

The `jsel` module implements a lightweight JSON selector utility, inspired by JQ-like syntax. It allows you to extract specific fields or elements from a JSON object using a concise selector string. Supported selectors include:

- `.key` — select a field from an object
- `.key1.key2` — select nested fields
- `.key[]` — select all elements in a list under a key
- `.key[N]` — select the N-th element in a list under a key
- `.[N]` — select the N-th element from the root array
- `.` — select the entire object

Example usage::

    from imdb.parser.http import jsel
    data = {"foo": {"bar": [1, 2, 3]}}
    result = jsel.select(data, ".foo.bar[1]")  # result == 2

jextr module
------------

The `jextr` module provides functions to extract and normalize movie data from IMDb JSON objects. It is designed to work with the data structures found in the `__NEXT_DATA__` JSON payloads on IMDb pages.

The main function, `movie_data(obj)`, takes a JSON object and returns a dictionary with normalized movie information.

See also
--------
- :doc:`extend` for information on extending data access systems.
