#!/usr/bin/env python
# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
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
import pithy

distutils.core.setup(
	name='pithy',
	description='Vim-like file manager',
	version=pithy.__version__,
	author=pithy.__author__,
	author_email=pithy.__email__,
	license=pithy.__license__,
	url='http://savannah.nongnu.org/projects/ranger',
	scripts=['scripts/pithy'],
	data_files=[('share/man/man1', ['doc/pithy.1'])],
	package_data={'pithy': ['data/*']},
	packages=('pithy',
	          'pithy.api',
	          'pithy.colorschemes',
	          'pithy.container',
	          'pithy.core',
	          'pithy.defaults',
	          'pithy.ext',
	          'pithy.fsobject',
	          'pithy.gui',
	          'pithy.gui.widgets',
	          'pithy.help',
	          'pithy.shared'))
