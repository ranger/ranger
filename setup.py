#!/usr/bin/env python
# Copyright (C) 2009, 2010, 2011  Roman Zimbelmann <romanz@lavabit.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import distutils.core
import ranger

if __name__ == '__main__':
	distutils.core.setup(
		name='ranger',
		description='Vim-like file manager',
		long_description=ranger.__doc__,
		version=ranger.__version__,
		author=ranger.__author__,
		author_email=ranger.__email__,
		license=ranger.__license__,
		url='http://savannah.nongnu.org/projects/ranger',
		scripts=['ranger/data/ranger'],
		data_files=[('share/man/man1', ['doc/ranger.1'])],
		package_data={'ranger': ['data/*', 'defaults/rc.conf']},
		packages=('ranger',
		          'ranger.api',
		          'ranger.colorschemes',
		          'ranger.container',
		          'ranger.core',
		          'ranger.defaults',
		          'ranger.ext',
		          'ranger.fsobject',
		          'ranger.gui',
		          'ranger.gui.widgets'))
