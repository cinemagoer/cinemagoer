# Copyright (C) 2014-2025 H. Turgut Uyar <uyar@tekir.org>
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

For more information, please refer to the documentation:
https://piculet.readthedocs.io/
"""

import re
from functools import partial
from operator import itemgetter
from types import MappingProxyType

import lxml.html
from lxml import etree as ElementTree

from . import jsel

__version__ = '1.2b2'


###########################################################
# DATA EXTRACTION OPERATIONS
###########################################################


XPath = ElementTree.XPath
xpath = ElementTree._Element.xpath


_EMPTY = MappingProxyType({})  # empty result singleton


class Extractor:
    """Abstract base extractor for getting data out of an XML element."""

    def __init__(self, transform=None, foreach=None):
        """Initialize this extractor.

        :param transform: Function to transform the extracted value.
        :param foreach: Path to apply for generating a collection of values.
        """
        self.transform = transform
        """Function to transform the extracted value."""

        self.foreach = XPath(foreach) if foreach is not None else None
        """Path to apply for generating a collection of values."""

    def apply(self, element):
        """Get the raw data from an element using this extractor.

        :param element: Element to apply this extractor to.
        :return: Extracted raw data.
        """
        raise NotImplementedError('Concrete extractors must implement this method')

    def extract(self, element, transform=True):
        """Get the processed data from an element using this extractor.

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

        :param path: Path to apply to get the data.
        :param reduce: Function to reduce selected texts into a single string.
        :param transform: Function to transform extracted value.
        :param foreach: Path to apply for generating a collection of data.
        """
        super().__init__(transform=transform, foreach=foreach)

        self.path = XPath(path)
        """XPath evaluator to apply to get the data."""

        if reduce is None:
            reduce = reducers.concat

        self.reduce = reduce
        """Function to reduce selected texts into a single string."""

    def apply(self, element):
        """Apply this extractor to an element.

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

        :param rules: Rules for generating the data items.
        :param section: Path for setting the root of this section.
        :param transform: Function to transform extracted value.
        :param foreach: Path for generating multiple items.
        """
        super().__init__(transform=transform, foreach=foreach)

        self.rules = rules
        """Rules for generating the data items."""

        self.section = XPath(section) if section is not None else None
        """XPath expression for selecting a subroot for this section."""

    def apply(self, element):
        """Apply this extractor to an element.

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

        :param key: Name to distinguish this data item.
        :param extractor: Extractor that will generate this data item.
        :param foreach: Path for generating multiple items.
        """
        self.key = key
        """Name to distinguish this data item."""

        self.extractor = extractor
        """Extractor that will generate this data item."""

        self.foreach = XPath(foreach) if foreach is not None else None
        """XPath evaluator for generating multiple items."""

        self.json_extractor = None
        """JSON extractor for further parsing of the obtained data."""

    @staticmethod
    def from_map(item):
        """Generate a rule from a description map.

        :param item: Item description.
        :return: Rule object.
        """
        item_key = item['key']
        key = item_key if isinstance(item_key, str) else Extractor.from_map(item_key)
        value = Extractor.from_map(item['value'])
        return Rule(key=key, extractor=value, foreach=item.get('foreach'))

    def extract(self, element):
        """Extract data out of an element using this rule.

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
                if self.json_extractor and isinstance(value, str):
                    value = jsel.select(value, self.json_extractor)
                if (value is None) or (value is _EMPTY):
                    continue
                data[key] = value
            else:
                # don't try to transform list items by default, it might waste a lot of time
                raw_values = [self.extractor.extract(r, transform=False)
                              for r in self.extractor.foreach(subroot)]
                values = [v for v in raw_values if (v is not None) and (v is not _EMPTY)]
                if self.json_extractor:
                    values = [jsel.select(v, self.json_extractor) for v in values]
                if len(values) == 0:
                    continue
                data[key] = values if self.extractor.transform is None else \
                    list(map(self.extractor.transform, values))
        return data


def remove_elements(root, path):
    """Remove selected elements from the tree.

    :param root: Root element of the tree.
    :param path: XPath to select the elements to remove.
    """
    elements = XPath(path)(root)
    if len(elements) > 0:
        for element in elements:
            # XXX: could this be hazardous? parent removed in earlier iteration?
            element.getparent().remove(element)


def set_element_attr(root, path, name, value):
    """Set an attribute for selected elements.

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

    :param document: XML document to build the tree from.
    :param force_html: Force to parse from HTML without converting.
    :return: Root element of the XML tree.
    """
    if force_html:
        return lxml.html.fromstring(document)
    return ElementTree.fromstring(document)


class Registry:
    """A simple, attribute-based namespace."""

    def __init__(self, entries):
        """Initialize this registry.

        :param entries: Entries to add to this registry.
        """
        self.__dict__.update(entries)

    def get(self, item):
        """Get the value of an entry from this registry.

        :param item: Entry to get the value for.
        :return: Value of entry.
        """
        return self.__dict__.get(item)

    def register(self, key, value):
        """Register a new entry in this registry.

        :param key: Key to search the entry in this registry.
        :param value: Value to store for the entry.
        """
        self.__dict__[key] = value


_PREPROCESSORS = {
    'remove': remove_elements,
    'set_attr': set_element_attr,
    'set_text': set_element_text
}

preprocessors = Registry(_PREPROCESSORS)
"""Predefined preprocessors."""


_REDUCERS = {
    'first': itemgetter(0),
    'concat': partial(str.join, ''),
    'join': partial(str.join, ' '),
    'pipe_join': partial(str.join, '|'),
    'clean': lambda xs: re.sub(r'\s+', ' ', ''.join(xs).replace('\xa0', ' ')).strip(),
    'normalize': lambda xs: re.sub('[^a-z0-9_]', '', ''.join(xs).lower().replace(' ', '_'))
}

reducers = Registry(_REDUCERS)
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

transformers = Registry(_TRANSFORMERS)
"""Predefined transformers."""


def preprocess(root, pre):
    """Process a tree before starting extraction.

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

    :param element: Element to extract the data from.
    :param items: Descriptions for extracting items.
    :param section: Path to select the root element for these items.
    :return: Extracted data.
    """
    rules = Rules([Rule.from_map(item) for item in items], section=section)
    return rules.extract(element)


def scrape(document, spec):
    """Extract data from a document after optionally preprocessing it.

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
