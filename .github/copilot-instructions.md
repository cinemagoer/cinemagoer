# GitHub Copilot Personal Instructions for IMDb Parsers

- **Always use the `DOMParserBase` class as the base for new IMDb HTML parsers.**
- **Define extraction logic using Piculet rules (`Rule`, `Path`, `Rules`) and XPath expressions.**
- **When asked to fix bugs, update existing parsers or introduce new parsers:**
  - Analyze the current parser to identify which information are collected and how they are structured.
  - Inspect the HTML structure to identify the wanted information.
  - Update the XPath expressions in the parser's `rules` to match the new elements or attributes.
  - Prefer robust, specific XPaths that are less likely to break with minor layout changes.
  - Use Piculet's `foreach` for lists or repeated elements.
  - If data is nested or requires transformation, use `transform` or override `postprocess_data`.
  - If the information is no longer present in the HTML, notify me and remove the related rule from the parser.
- **Test the parser with provided HTML to verify extraction accuracy.**
- **Avoid hardcoding data outside of rules; keep logic modular and reusable.**
- **Document any complex extraction logic or workarounds in the parser class.**