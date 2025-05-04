.. _webparsers:

Using DOMParserBase and Piculet Rules for IMDb Parsers
======================================================

Overview
--------

The ``DOMParserBase`` class (in ``imdb.parser.http.utils``) provides a flexible foundation for building HTML parsers that extract structured data from IMDb web pages. It leverages the :doc:`piculet <piculet.py>` module, which offers a declarative way to define extraction rules using XPath expressions.

How to Create a Parser
----------------------

1. **Subclass ``DOMParserBase``:**

   - Create a new class inheriting from ``DOMParserBase``.
   - Optionally override ``_init``, ``_reset``, ``preprocess_dom``, ``postprocess_data``, or other hooks for custom behavior.

2. **Define Extraction Rules:**

   - Set the ``rules`` class attribute to a list of Piculet ``Rule`` or ``Rules`` objects.
   - Each ``Rule`` specifies:
     
     - a ``key`` (the name of the extracted field),
     - an ``extractor`` (typically a ``Path`` or nested ``Rules``),
     - optionally, a ``foreach`` XPath to extract multiple items.

3. **Parsing Workflow:**

   - Call ``.parse(html_string)`` on your parser instance.
   - The parser:
     
     - Optionally preprocesses the HTML.
     - Converts it to a DOM tree.
     - Applies the extraction rules to produce a structured dictionary.
     - Optionally gathers references (e.g., to movies or persons).

Piculet Rules Syntax
--------------------

- ``Path(xpath, reduce=None, transform=None, foreach=None)``: Extracts data using an XPath expression.
- ``Rule(key, extractor, foreach=None)``: Associates a key with an extractor, optionally repeating for each match of ``foreach``.
- ``Rules([...], section=None, transform=None, foreach=None)``: Groups multiple rules, optionally scoping to a section or repeating.

**Example:**

.. code-block:: python

    from imdb.parser.http.utils import DOMParserBase
    from imdb.parser.http.piculet import Rule, Path

    class MyTitleParser(DOMParserBase):
        rules = [
            Rule(
                key='title',
                extractor=Path('.//h1/text()')
            ),
            Rule(
                key='year',
                extractor=Path('.//span[@id="titleYear"]/a/text()')
            )
        ]

Adapting to IMDb Page Changes
-----------------------------

When IMDb changes its HTML structure:

- Update the XPath expressions in your rules to match the new DOM.
- Use the Piculet module's flexible extractors to adjust to new layouts.
- Test your parser with real IMDb HTML to ensure correct extraction.

For more advanced needs, override methods like ``preprocess_dom`` or ``postprocess_data`` to handle non-trivial transformations or data normalization.