# Copyright (C) 2014-2022 H. Turgut Uyar <uyar@tekir.org>
#
# Piculet is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Piculet is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Piculet.  If not, see <http://www.gnu.org/licenses/>.

"""Piculet is a module for scraping XML and HTML documents using XPath queries.

It consists of this single source file with no dependencies other than
the standard library, which makes it very easy to integrate into applications.
It has been tested with Python 2.7, Python 3.4+, PyPy2 5.7+, and PyPy3 5.7+.

For more information, please refer to the documentation:
https://piculet.readthedocs.io/
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import json
import re
import sys
from argparse import ArgumentParser
from collections import deque
from functools import partial
from operator import itemgetter
from pkgutil import find_loader

__version__ = '1.2b1'

PY2 = sys.version_info < (3, 0)

if PY2:
    str, bytes = unicode, str

if PY2:
    from cgi import escape as html_escape
    from htmlentitydefs import name2codepoint  # noqa: I003
    from HTMLParser import HTMLParser
    from StringIO import StringIO
else:
    from html import escape as html_escape
    from html.parser import HTMLParser
    from io import StringIO
    from types import MappingProxyType


if PY2:
    from contextlib import contextmanager

    @contextmanager
    def redirect_stdout(new_stdout):
        """Context manager for temporarily redirecting stdout."""
        old_stdout, sys.stdout = sys.stdout, new_stdout
        try:
            yield new_stdout
        finally:
            sys.stdout = old_stdout
else:
    from contextlib import redirect_stdout


###########################################################
# HTML OPERATIONS
###########################################################


class HTMLNormalizer(HTMLParser):
    """HTML cleaner and XHTML convertor.

    DOCTYPE declarations and comments are removed.
    """

    SELF_CLOSING_TAGS = {'br', 'hr', 'img', 'input', 'link', 'meta'}
    """Tags to handle as self-closing."""

    def __init__(self, omit_tags=None, omit_attrs=None):
        """Initialize this normalizer.

        :sig: (Optional[Iterable[str]], Optional[Iterable[str]]) -> None
        :param omit_tags: Tags to remove, along with all their content.
        :param omit_attrs: Attributes to remove.
        """
        if PY2:
            HTMLParser.__init__(self)
        else:
            super().__init__(convert_charrefs=True)

        self.omit_tags = set(omit_tags) if omit_tags is not None else set()     # sig: Set[str]
        self.omit_attrs = set(omit_attrs) if omit_attrs is not None else set()  # sig: Set[str]

        # stacks used during normalization
        self._open_tags = deque()
        self._open_omitted_tags = deque()

    def handle_starttag(self, tag, attrs):
        if tag in self.omit_tags:
            self._open_omitted_tags.append(tag)
        if not self._open_omitted_tags:
            # stack empty -> not in omit mode
            if '@' in tag:
                # email address in angular brackets
                print('&lt;%s&gt;' % tag, end='')
                return
            if (tag == 'li') and (self._open_tags[-1] == 'li'):
                self.handle_endtag('li')
            attributes = []
            for attr_name, attr_value in attrs:
                if attr_name in self.omit_attrs:
                    continue
                if attr_value is None:
                    attr_value = ''
                markup = '%(name)s="%(value)s"' % {
                    'name': attr_name,
                    'value': html_escape(attr_value, quote=True)
                }
                attributes.append(markup)
            line = '<%(tag)s%(attrs)s%(slash)s>' % {
                'tag': tag,
                'attrs': (' ' + ' '.join(attributes)) if len(attributes) > 0 else '',
                'slash': ' /' if tag in self.SELF_CLOSING_TAGS else ''
            }
            print(line, end='')
            if tag not in self.SELF_CLOSING_TAGS:
                self._open_tags.append(tag)

    def handle_endtag(self, tag):
        if not self._open_omitted_tags:
            # stack empty -> not in omit mode
            if tag not in self.SELF_CLOSING_TAGS:
                last = self._open_tags[-1]
                if (tag == 'ul') and (last == 'li'):
                    self.handle_endtag('li')
                if tag == last:
                    # expected end tag
                    print('</%(tag)s>' % {'tag': tag}, end='')
                    self._open_tags.pop()
                elif tag not in self._open_tags:
                    # XXX: for <a><b></a></b>, this case gets invoked after the case below
                    pass
                elif tag == self._open_tags[-2]:
                    print('</%(tag)s>' % {'tag': last}, end='')
                    print('</%(tag)s>' % {'tag': tag}, end='')
                    self._open_tags.pop()
                    self._open_tags.pop()
        elif (tag in self.omit_tags) and (tag == self._open_omitted_tags[-1]):
            # end of expected omitted tag
            self._open_omitted_tags.pop()

    def handle_data(self, data):
        if not self._open_omitted_tags:
            # stack empty -> not in omit mode
            line = html_escape(data)
            print(line.decode('utf-8') if PY2 and isinstance(line, bytes) else line, end='')

    def handle_entityref(self, name):
        # XXX: doesn't get called if convert_charrefs=True
        num = name2codepoint.get(name)  # we are sure we're on PY2 here
        if num is not None:
            print('&#%(ref)d;' % {'ref': num}, end='')

    def handle_charref(self, name):
        # XXX: doesn't get called if convert_charrefs=True
        print('&#%(ref)s;' % {'ref': name}, end='')

    # def feed(self, data):
        # super().feed(data)
        # # close all remaining open tags
        # for tag in reversed(self._open_tags):
        #     print('</%(tag)s>' % {'tag': tag}, end='')


def html_to_xhtml(document, omit_tags=None, omit_attrs=None):
    """Clean HTML and convert to XHTML.

    :sig: (str, Optional[Iterable[str]], Optional[Iterable[str]]) -> str
    :param document: HTML document to clean and convert.
    :param omit_tags: Tags to exclude from the output.
    :param omit_attrs: Attributes to exclude from the output.
    :return: Normalized XHTML content.
    """
    out = StringIO()
    normalizer = HTMLNormalizer(omit_tags=omit_tags, omit_attrs=omit_attrs)
    with redirect_stdout(out):
        normalizer.feed(document)
    return out.getvalue()


###########################################################
# DATA EXTRACTION OPERATIONS
###########################################################


# sigalias: XPathResult = Union[Sequence[str], Sequence[Element]]


_USE_LXML = find_loader('lxml') is not None
if _USE_LXML:
    from lxml import etree as ElementTree
    from lxml.etree import Element

    XPath = ElementTree.XPath
    xpath = ElementTree._Element.xpath
else:
    from xml.etree import ElementTree
    from xml.etree.ElementTree import Element

    class XPath:
        """An XPath expression evaluator.

        This class is mainly needed to compensate for the lack of ``text()``
        and ``@attr`` axis queries in ElementTree XPath support.
        """

        def __init__(self, path):
            """Initialize this evaluator.

            :sig: (str) -> None
            :param path: XPath expression to evaluate.
            """
            def descendant(element):
                # strip trailing '//text()'
                return [t for e in element.findall(path[:-8]) for t in e.itertext() if t]

            def child(element):
                # strip trailing '/text()'
                return [t for e in element.findall(path[:-7])
                        for t in ([e.text] + [c.tail if c.tail else '' for c in e]) if t]

            def attribute(element, subpath, attr):
                result = [e.attrib.get(attr) for e in element.findall(subpath)]
                return [r for r in result if r is not None]

            if path[0] == '/':
                # ElementTree doesn't support absolute paths
                # TODO: handle this properly, find root of tree
                path = '.' + path

            if path.endswith('//text()'):
                _apply = descendant
            elif path.endswith('/text()'):
                _apply = child
            else:
                steps = path.split('/')
                front, last = steps[:-1], steps[-1]
                # after dropping PY2: *front, last = path.split('/')
                if last.startswith('@'):
                    _apply = partial(attribute, subpath='/'.join(front), attr=last[1:])
                else:
                    _apply = partial(Element.findall, path=path)

            self._apply = _apply    # sig: Callable[[Element], XPathResult]

        def __call__(self, element):
            """Apply this evaluator to an element.

            :sig: (Element) -> XPathResult
            :param element: Element to apply this expression to.
            :return: Elements or strings resulting from the query.
            """
            return self._apply(element)

    xpath = lambda e, p: XPath(p)(e)


_EMPTY = {} if PY2 else MappingProxyType({})  # empty result singleton


# sigalias: Reducer = Callable[[Sequence[str]], str]
# sigalias: PathTransformer = Callable[[str], Any]
# sigalias: MapTransformer = Callable[[Mapping[str, Any]], Any]
# sigalias: Transformer = Union[PathTransformer, MapTransformer]
# sigalias: ExtractedItem = Union[str, Mapping[str, Any]]


class Extractor:
    """Abstract base extractor for getting data out of an XML element."""

    def __init__(self, transform=None, foreach=None):
        """Initialize this extractor.

        :sig: (Optional[Transformer], Optional[str]) -> None
        :param transform: Function to transform the extracted value.
        :param foreach: Path to apply for generating a collection of values.
        """
        self.transform = transform  # sig: Optional[Transformer]
        """Function to transform the extracted value."""

        self.foreach = XPath(foreach) if foreach is not None else None  # sig: Optional[XPath]
        """Path to apply for generating a collection of values."""

    def apply(self, element):
        """Get the raw data from an element using this extractor.

        :sig: (Element) -> ExtractedItem
        :param element: Element to apply this extractor to.
        :return: Extracted raw data.
        """
        raise NotImplementedError('Concrete extractors must implement this method')

    def extract(self, element, transform=True):
        """Get the processed data from an element using this extractor.

        :sig: (Element, Optional[bool]) -> Any
        :param element: Element to extract the data from.
        :param transform: Whether the transformation will be applied or not.
        :return: Extracted and optionally transformed data.
        """
        value = self.apply(element)
        if (value is None) or (value is _EMPTY) or (not transform):
            return value
        return value if self.transform is None else self.transform(value)

    @staticmethod
    def from_map(item):
        """Generate an extractor from a description map.

        :sig: (Mapping[str, Any]) -> Extractor
        :param item: Extractor description.
        :return: Extractor object.
        :raise ValueError: When reducer or transformer names are unknown.
        """
        transformer = item.get('transform')
        if transformer is None:
            transform = None
        else:
            transform = transformers.get(transformer)
            if transform is None:
                raise ValueError('Unknown transformer')

        foreach = item.get('foreach')

        path = item.get('path')
        if path is not None:
            reducer = item.get('reduce')
            if reducer is None:
                reduce = None
            else:
                reduce = reducers.get(reducer)
                if reduce is None:
                    raise ValueError('Unknown reducer')
            extractor = Path(path, reduce, transform=transform, foreach=foreach)
        else:
            items = item.get('items')
            # TODO: check for None
            rules = [Rule.from_map(i) for i in items]
            extractor = Rules(rules, section=item.get('section'),
                              transform=transform, foreach=foreach)

        return extractor


class Path(Extractor):
    """An extractor for getting text out of an XML element."""

    def __init__(self, path, reduce=None, transform=None, foreach=None):
        """Initialize this extractor.

        :sig: (
                str,
                Optional[Reducer],
                Optional[PathTransformer],
                Optional[str]
            ) -> None
        :param path: Path to apply to get the data.
        :param reduce: Function to reduce selected texts into a single string.
        :param transform: Function to transform extracted value.
        :param foreach: Path to apply for generating a collection of data.
        """
        if PY2:
            Extractor.__init__(self, transform=transform, foreach=foreach)
        else:
            super().__init__(transform=transform, foreach=foreach)

        self.path = XPath(path)     # sig: XPath
        """XPath evaluator to apply to get the data."""

        if reduce is None:
            reduce = reducers.concat

        self.reduce = reduce        # sig: Reducer
        """Function to reduce selected texts into a single string."""

    def apply(self, element):
        """Apply this extractor to an element.

        :sig: (Element) -> str
        :param element: Element to apply this extractor to.
        :return: Extracted text.
        """
        selected = self.path(element)
        if len(selected) == 0:
            value = None
        else:
            value = self.reduce(selected)
        return value


class Rules(Extractor):
    """An extractor for getting data items out of an XML element."""

    def __init__(self, rules, section=None, transform=None, foreach=None):
        """Initialize this extractor.

        :sig:
            (
                Sequence[Rule],
                str,
                Optional[MapTransformer],
                Optional[str]
            ) -> None
        :param rules: Rules for generating the data items.
        :param section: Path for setting the root of this section.
        :param transform: Function to transform extracted value.
        :param foreach: Path for generating multiple items.
        """
        if PY2:
            Extractor.__init__(self, transform=transform, foreach=foreach)
        else:
            super().__init__(transform=transform, foreach=foreach)

        self.rules = rules  # sig: Sequence[Rule]
        """Rules for generating the data items."""

        self.section = XPath(section) if section is not None else None  # sig: Optional[XPath]
        """XPath expression for selecting a subroot for this section."""

    def apply(self, element):
        """Apply this extractor to an element.

        :sig: (Element) -> Mapping[str, Any]
        :param element: Element to apply the extractor to.
        :return: Extracted mapping.
        """
        if self.section is None:
            subroot = element
        else:
            subroots = self.section(element)
            if len(subroots) == 0:
                return _EMPTY
            if len(subroots) > 1:
                raise ValueError('Section path should select exactly one element')
            subroot = subroots[0]

        data = {}
        for rule in self.rules:
            extracted = rule.extract(subroot)
            data.update(extracted)
        return data if len(data) > 0 else _EMPTY


class Rule:
    """A rule describing how to get a data item out of an XML element."""

    def __init__(self, key, extractor, foreach=None):
        """Initialize this rule.

        :sig: (Union[str, Extractor], Extractor, Optional[str]) -> None
        :param key: Name to distinguish this data item.
        :param extractor: Extractor that will generate this data item.
        :param foreach: Path for generating multiple items.
        """
        self.key = key              # sig: Union[str, Extractor]
        """Name to distinguish this data item."""

        self.extractor = extractor  # sig: Extractor
        """Extractor that will generate this data item."""

        self.foreach = XPath(foreach) if foreach is not None else None  # sig: Optional[XPath]
        """XPath evaluator for generating multiple items."""

    @staticmethod
    def from_map(item):
        """Generate a rule from a description map.

        :sig: (Mapping[str, Any]) -> Rule
        :param item: Item description.
        :return: Rule object.
        """
        item_key = item['key']
        key = item_key if isinstance(item_key, str) else Extractor.from_map(item_key)
        value = Extractor.from_map(item['value'])
        return Rule(key=key, extractor=value, foreach=item.get('foreach'))

    def extract(self, element):
        """Extract data out of an element using this rule.

        :sig: (Element) -> Mapping[str, Any]
        :param element: Element to extract the data from.
        :return: Extracted data.
        """
        data = {}
        subroots = [element] if self.foreach is None else self.foreach(element)
        for subroot in subroots:
            key = self.key if isinstance(self.key, str) else self.key.extract(subroot)
            if key is None:
                continue
            if self.extractor.foreach is None:
                value = self.extractor.extract(subroot)
                if (value is None) or (value is _EMPTY):
                    continue
                data[key] = value
            else:
                # don't try to transform list items by default, it might waste a lot of time
                raw_values = [self.extractor.extract(r, transform=False)
                              for r in self.extractor.foreach(subroot)]
                values = [v for v in raw_values if (v is not None) and (v is not _EMPTY)]
                if len(values) == 0:
                    continue
                data[key] = values if self.extractor.transform is None else \
                    list(map(self.extractor.transform, values))
        return data


def remove_elements(root, path):
    """Remove selected elements from the tree.

    :sig: (Element, str) -> None
    :param root: Root element of the tree.
    :param path: XPath to select the elements to remove.
    """
    if _USE_LXML:
        get_parent = ElementTree._Element.getparent
    else:
        # ElementTree doesn't support parent queries, so we'll build a map for it
        get_parent = root.attrib.get('_get_parent')
        if get_parent is None:
            get_parent = {e: p for p in root.iter() for e in p}.get
            root.attrib['_get_parent'] = get_parent
    elements = XPath(path)(root)
    if len(elements) > 0:
        for element in elements:
            # XXX: could this be hazardous? parent removed in earlier iteration?
            get_parent(element).remove(element)


def set_element_attr(root, path, name, value):
    """Set an attribute for selected elements.

    :sig:
        (
            Element,
            str,
            Union[str, Mapping[str, Any]],
            Union[str, Mapping[str, Any]]
        ) -> None
    :param root: Root element of the tree.
    :param path: XPath to select the elements to set attributes for.
    :param name: Description for name generation.
    :param value: Description for value generation.
    """
    elements = XPath(path)(root)
    for element in elements:
        attr_name = name if isinstance(name, str) else \
            Extractor.from_map(name).extract(element)
        if attr_name is None:
            continue

        attr_value = value if isinstance(value, str) else \
            Extractor.from_map(value).extract(element)
        if attr_value is None:
            continue

        element.attrib[attr_name] = attr_value


def set_element_text(root, path, text):
    """Set the text for selected elements.

    :sig: (Element, str, Union[str, Mapping[str, Any]]) -> None
    :param root: Root element of the tree.
    :param path: XPath to select the elements to set attributes for.
    :param text: Description for text generation.
    """
    elements = XPath(path)(root)
    for element in elements:
        element_text = text if isinstance(text, str) else \
            Extractor.from_map(text).extract(element)
        # note that the text can be None in which case the existing text will be cleared
        element.text = element_text


def build_tree(document, force_html=False):
    """Build a tree from an XML document.

    :sig: (str, Optional[bool]) -> Element
    :param document: XML document to build the tree from.
    :param force_html: Force to parse from HTML without converting.
    :return: Root element of the XML tree.
    """
    content = document.encode('utf-8') if PY2 else document
    if _USE_LXML and force_html:
        import lxml.html
        return lxml.html.fromstring(content)
    return ElementTree.fromstring(content)


class Registry:
    """A simple, attribute-based namespace."""

    def __init__(self, entries):
        """Initialize this registry.

        :sig: (Mapping[str, Any]) -> None
        :param entries: Entries to add to this registry.
        """
        self.__dict__.update(entries)

    def get(self, item):
        """Get the value of an entry from this registry.

        :sig: (str) -> Any
        :param item: Entry to get the value for.
        :return: Value of entry.
        """
        return self.__dict__.get(item)

    def register(self, key, value):
        """Register a new entry in this registry.

        :sig: (str, Any) -> None
        :param key: Key to search the entry in this registry.
        :param value: Value to store for the entry.
        """
        self.__dict__[key] = value


_PREPROCESSORS = {
    'remove': remove_elements,
    'set_attr': set_element_attr,
    'set_text': set_element_text
}

preprocessors = Registry(_PREPROCESSORS)    # sig: Registry
"""Predefined preprocessors."""


_REDUCERS = {
    'first': itemgetter(0),
    'concat': partial(str.join, ''),
    'clean': lambda xs: re.sub(r'\s+', ' ', ''.join(xs).replace('\xa0', ' ')).strip(),
    'normalize': lambda xs: re.sub('[^a-z0-9_]', '', ''.join(xs).lower().replace(' ', '_'))
}

reducers = Registry(_REDUCERS)              # sig: Registry
"""Predefined reducers."""


_TRANSFORMERS = {
    'int': int,
    'float': float,
    'bool': bool,
    'len': len,
    'lower': str.lower,
    'upper': str.upper,
    'capitalize': str.capitalize,
    'lstrip': str.lstrip,
    'rstrip': str.rstrip,
    'strip': str.strip
}

transformers = Registry(_TRANSFORMERS)      # sig: Registry
"""Predefined transformers."""


def preprocess(root, pre):
    """Process a tree before starting extraction.

    :sig: (Element, Sequence[Mapping[str, Any]]) -> None
    :param root: Root of tree to process.
    :param pre: Descriptions for processing operations.
    """
    for step in pre:
        op = step['op']
        if op == 'remove':
            remove_elements(root, step['path'])
        elif op == 'set_attr':
            set_element_attr(root, step['path'], name=step['name'], value=step['value'])
        elif op == 'set_text':
            set_element_text(root, step['path'], text=step['text'])
        else:
            raise ValueError('Unknown preprocessing operation')


def extract(element, items, section=None):
    """Extract data from an XML element.

    :sig:
        (
            Element,
            Sequence[Mapping[str, Any]],
            Optional[str]
        ) -> Mapping[str, Any]
    :param element: Element to extract the data from.
    :param items: Descriptions for extracting items.
    :param section: Path to select the root element for these items.
    :return: Extracted data.
    """
    rules = Rules([Rule.from_map(item) for item in items], section=section)
    return rules.extract(element)


def scrape(document, spec):
    """Extract data from a document after optionally preprocessing it.

    :sig: (str, Mapping[str, Any]) -> Mapping[str, Any]
    :param document: Document to scrape.
    :param spec: Extraction specification.
    :return: Extracted data.
    """
    root = build_tree(document)
    pre = spec.get('pre')
    if pre is not None:
        preprocess(root, pre)
    data = extract(root, spec.get('items'), section=spec.get('section'))
    return data


###########################################################
# COMMAND-LINE INTERFACE
###########################################################


def main():
    parser = ArgumentParser(description="extract data from XML/HTML")
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('--html', action='store_true', help='document is in HTML format')
    parser.add_argument('-s', '--spec', required=True, help='spec file')
    arguments = parser.parse_args()

    content = sys.stdin.read()
    if arguments.html:
        content = html_to_xhtml(content)

    with open(arguments.spec) as f:
        spec_content = f.read()
    spec = json.loads(spec_content)

    data = scrape(content, spec)
    print(json.dumps(data, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
