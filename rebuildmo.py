# Copyright 2022 H. Turgut Uyar <uyar@tekir.org>
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
import os.path
import sys
from subprocess import check_call


def rebuildmo():
    created = []
    locale_dir = os.path.join("imdb", "locale")
    po_files = os.path.join(locale_dir, "imdbpy-*.po")
    for po_file in sorted(glob.glob(po_files)):
        lang = os.path.basename(po_file)[7:-3]
        lang_dir = os.path.join(locale_dir, lang)
        mo_dir = os.path.join(lang_dir, "LC_MESSAGES")
        mo_file = os.path.join(mo_dir, "imdbpy.mo")
        if os.path.exists(mo_file) and (os.stat(po_file).st_mtime < os.stat(mo_file).st_mtime):
            continue
        if not os.path.exists(mo_dir):
            os.makedirs(mo_dir)
        check_call([sys.executable, "msgfmt.py", "-o", mo_file, po_file])
        created.append(lang)
    return created


if __name__ == '__main__':
    languages = rebuildmo()
    if len(languages) > 0:
        print('Created locale for: %s.' % ' '.join(languages))
