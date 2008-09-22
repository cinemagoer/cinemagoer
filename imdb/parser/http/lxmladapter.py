"""
parser.http.lxmladapter module (imdb.parser.http package).

This module adapts the lxml xpath support to the internal mechanism.

Copyright 2008 H. Turgut Uyar <uyar@tekir.org>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

from lxml import html


def fromstring(html_string):
    """Return a DOM representation of the string.
    """
    return html.fromstring(html_string)


def tostring(element):
    """Return a unicode representation of an element.
    """
    if isinstance(element, (unicode, str)):
        return element
    return html.tostring(element, encoding=unicode)


def fix_rowspans(html_string):
    """Repeat td elements according to their rowspan attributes in subsequent
    tr elements.
    """
    dom = fromstring(html_string)
    cols = dom.xpath("//td[@rowspan]")
    for col in cols:
        span = int(col.get('rowspan'))
        position = len(col.xpath("./preceding-sibling::td"))
        row = col.getparent()
        next = row
        for i in xrange(span-1):
            next = next.xpath("./following-sibling::tr[1]")[0]
            # if not cloned, child will be moved to new parent
            clone = fromstring(tostring(col))
            next.insert(position, clone)
    return tostring(dom)


def apply_xpath(element, path):
    """Apply an xpath expression to a node. Return a list of nodes.

    Make sure to use unicode elements instead of string.
    """
    result = []
    items = element.xpath(path)
    for item in items:
        if isinstance(item, str):
            item = unicode(item)
        result.append(item)
    return result
