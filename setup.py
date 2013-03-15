#!/usr/bin/env python
# Copyright (C) 2009-2013  Roman Zimbelmann <hut@lavabit.com>
# This software is distributed under the terms of the GNU GPL version 3.

import distutils.core
import os.path
import ranger

def _findall(directory):
    return [os.path.join(directory, f) for f in os.listdir(directory) \
            if os.path.isfile(os.path.join(directory, f))]

if __name__ == '__main__':
    distutils.core.setup(
        name='ranger',
        description='Vim-like file manager',
        long_description=ranger.__doc__,
        version=ranger.__version__,
        author=ranger.__author__,
        author_email=ranger.__email__,
        license=ranger.__license__,
        url='http://ranger.nongnu.org',
        scripts=['scripts/ranger', 'scripts/rifle'],
        data_files=[
            ('share/man/man1',
                ['doc/ranger.1',
                 'doc/rifle.1']),
            ('share/doc/ranger',
                ['README',
                 'CHANGELOG',
                 'doc/HACKING',
                 'doc/colorschemes.txt']),
            ('share/doc/ranger/config/colorschemes',
                _findall('doc/config/colorschemes')),
            ('share/doc/ranger/config', _findall('doc/config')),
            ('share/doc/ranger/tools', _findall('doc/tools')),
            ('share/doc/ranger/examples', _findall('doc/examples')),
        ],
        package_data={'ranger': ['data/*', 'config/rc.conf',
            'config/rifle.conf']},
        packages=('ranger',
                  'ranger.api',
                  'ranger.colorschemes',
                  'ranger.container',
                  'ranger.core',
                  'ranger.config',
                  'ranger.ext',
                  'ranger.gui',
                  'ranger.gui.widgets',
                  'ranger.ext.vcs'))
