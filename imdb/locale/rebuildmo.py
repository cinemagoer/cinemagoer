# Copyright 2009 H. Turgut Uyar <uyar@tekir.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""
This script builds the .mo files, from the .po files.
"""

import glob
import os

import msgfmt


def rebuildmo():
    cur_dir = os.path.dirname(__file__)
    lang_glob = cur_dir + '/imdbpy-*.po'
    created = []
    for po_file in sorted(glob.glob(lang_glob)):
        lang = os.path.splitext(po_file)[0].split('imdbpy-')[-1]
        mo_dir = os.path.join(cur_dir, lang, 'LC_MESSAGES')
        os.makedirs(mo_dir, exist_ok=True)
        output_file = os.path.join(mo_dir, 'imdbpy.mo')
        msgfmt.make(po_file, output_file)
        created.append(lang)
    return created


if __name__ == '__main__':
    languages = rebuildmo()
    print('Created locale for: %s.' % ' '.join(languages))
