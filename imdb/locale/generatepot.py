#!/usr/bin/env python

import re
import sys

from datetime import datetime as dt

DEFAULT_MESSAGES = { }

ELEMENT_PATTERN = r"""<!ELEMENT\s+([^\s]+)"""
re_element = re.compile(ELEMENT_PATTERN)

POT_HEADER_TEMPLATE = r"""# Gettext message file for imdbpy
msgid ""
msgstr ""
"Project-Id-Version: imdbpy\n"
"POT-Creation-Date: %(now)s\n"
"PO-Revision-Date: YYYY-MM-DD HH:MM+0000\n"
"Last-Translator: YOUR NAME <YOUR@EMAIL>\n"
"Language-Team: TEAM NAME <TEAM@EMAIL>\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Plural-Forms: nplurals=1; plural=0;\n"
"Language-Code: en\n"
"Language-Name: English\n"
"Preferred-Encodings: utf-8\n"
"Domain: imdbpy\n"
"""

if len(sys.argv) != 2:
    print "Usage: %s dtd_file" % sys.argv[0]
    sys.exit()

dtdfilename = sys.argv[1]
dtd = open(dtdfilename).read()
elements = re_element.findall(dtd)
uniq = set(elements)
elements = list(uniq)

print POT_HEADER_TEMPLATE % {
    'now': dt.strftime(dt.now(), "%Y-%m-%d %H:%M+0000")
}
for element in sorted(elements):
    if element in DEFAULT_MESSAGES:
        print '# Default: %s' % DEFAULT_MESSAGES[element]
    else:
        print '# Default: %s' % element.replace('-', ' ').capitalize()
    print 'msgid "%s"' % element
    print 'msgstr ""'
    print

