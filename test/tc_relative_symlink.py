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

import os.path
import sys
rangerpath = os.path.join(os.path.dirname(__file__), '..')
if sys.path[1] != rangerpath:
	sys.path[1:1] = [rangerpath]

import unittest
from ranger.ext.relative_symlink import *
rel = get_relative_source_file

class Test(unittest.TestCase):
	def test_foo(self):
		self.assertEqual('../foo', rel('/foo', '/x/bar'))
		self.assertEqual('../../foo', rel('/foo', '/x/y/bar'))
		self.assertEqual('../../a/b/foo', rel('/a/b/foo', '/x/y/bar'))
		self.assertEqual('../../x/b/foo', rel('/x/b/foo', '/x/y/bar',
			common_base='/'))
		self.assertEqual('../b/foo', rel('/x/b/foo', '/x/y/bar'))
		self.assertEqual('../b/foo', rel('/x/b/foo', '/x/y/bar'))

	def test_get_common_base(self):
		self.assertEqual('/', get_common_base('', ''))
		self.assertEqual('/', get_common_base('', '/'))
		self.assertEqual('/', get_common_base('/', ''))
		self.assertEqual('/', get_common_base('/', '/'))
		self.assertEqual('/', get_common_base('/bla/bar/x', '/foo/bar/a'))
		self.assertEqual('/foo/bar/', get_common_base('/foo/bar/x', '/foo/bar/a'))
		self.assertEqual('/foo/', get_common_base('/foo/bar/x', '/foo/baz/a'))
		self.assertEqual('/foo/', get_common_base('/foo/bar/x', '/foo/baz/a'))
		self.assertEqual('/', get_common_base('//foo/bar/x', '/foo/baz/a'))

if __name__ == '__main__': unittest.main()
