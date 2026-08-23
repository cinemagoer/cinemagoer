# Copyright 2026 Davide Alberani <da@mimante.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

"""Setuptools commands used while building Cinemagoer distributions."""

import importlib.util
from pathlib import Path

from setuptools.command.build_py import build_py


def _load_rebuildmo():
    script = Path(__file__).with_name('rebuildmo.py')
    spec = importlib.util.spec_from_file_location(
        '_cinemagoer_rebuildmo', script
    )
    if spec is None or spec.loader is None:
        raise RuntimeError('unable to load %s' % script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.rebuildmo


class BuildPy(build_py):
    """Build Python modules and compile translation catalogs."""

    def run(self):
        super().run()
        locale_dir = Path(self.build_lib, 'imdb', 'locale')
        _load_rebuildmo()(locale_dir=locale_dir, force=True)
