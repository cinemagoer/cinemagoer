#!/usr/bin/env python

import glob
import msgfmt
import os

#LOCALE_DIR = os.path.dirname(__file__)

def rebuildmo():
    lang_glob = 'imdbpy-*.po'
    for input_file in glob.glob(lang_glob):
        lang = input_file[7:-3]
        if not os.path.exists(lang):
            os.mkdir(lang)
        mo_dir = os.path.join(lang, 'LC_MESSAGES')
        if not os.path.exists(mo_dir):
            os.mkdir(mo_dir)
        output_file = os.path.join(mo_dir, 'imdbpy.mo')
        msgfmt.make(input_file, output_file)


if __name__ == '__main__':
    rebuildmo()

