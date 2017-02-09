#!/usr/bin/env python
# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)

import distutils.core  # pylint: disable=import-error,no-name-in-module
import os
import shutil

import ranger


def _findall(directory):
    return [os.path.join(directory, f) for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f))]


def _script(src_path, name):
    if not os.path.exists('build/scripts'):
        os.makedirs('build/scripts')
    dest_path = os.path.join('build/scripts', name)
    shutil.copy(src_path, dest_path)
    return dest_path


if __name__ == '__main__':
    distutils.core.setup(  # pylint: disable=no-member
        name='ranger',
        description='Vim-like file manager',
        long_description=ranger.__doc__,
        version=ranger.__version__,
        author=ranger.__author__,
        author_email=ranger.__email__,
        license=ranger.__license__,
        url='http://ranger.nongnu.org',
        scripts=[
            _script('ranger.py', 'ranger'),
            _script('ranger/ext/rifle.py', 'rifle'),
        ],
        data_files=[
            ('share/applications', [
                'doc/ranger.desktop',
            ]),
            ('share/man/man1', [
                'doc/ranger.1',
                'doc/rifle.1',
            ]),
            ('share/doc/ranger', [
                'doc/colorschemes.txt',
                'CHANGELOG.md',
                'HACKING.md',
                'README.md',
            ]),
            ('share/doc/ranger/config', _findall('doc/config')),
            ('share/doc/ranger/config/colorschemes', _findall('doc/config/colorschemes')),
            ('share/doc/ranger/examples', _findall('examples')),
            ('share/doc/ranger/tools', _findall('doc/tools')),
        ],
        package_data={
            'ranger': [
                'data/*',
                'config/rc.conf',
                'config/rifle.conf',
            ],
        },
        packages=(
            'ranger',
            'ranger.api',
            'ranger.colorschemes',
            'ranger.config',
            'ranger.container',
            'ranger.core',
            'ranger.ext',
            'ranger.ext.vcs',
            'ranger.gui',
            'ranger.gui.widgets',
        ),
    )
