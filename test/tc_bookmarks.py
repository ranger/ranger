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

if __name__ == '__main__': from __init__ import init; init()

from os.path import realpath, join, dirname
import unittest
import os
import time

from ranger.container.bookmarks import Bookmarks

TESTDIR = realpath(join(dirname(__file__), 'testdir'))
BMFILE = join(TESTDIR, 'bookmarks')

class TestDisplayable(unittest.TestCase):
	def setUp(self):
		try:
			os.remove(BMFILE)
		except:
			pass

	def tearDown(self):
		try:
			os.remove(BMFILE)
		except:
			pass
	
	def test_adding_bookmarks(self):
		bm = Bookmarks(BMFILE, str, autosave=False)
		bm.load()
		bm['a'] = 'fooo'
		self.assertEqual(bm['a'], 'fooo')

	def test_sharing_bookmarks_between_instances(self):
		bm = Bookmarks(BMFILE, str, autosave=True)
		bm2 = Bookmarks(BMFILE, str, autosave=True)

		bm.load()
		bm2.load()
		bm['a'] = 'fooo'
		self.assertRaises(KeyError, bm2.__getitem__, 'a')

		bm.save()
		bm2.load()
		self.assertEqual(bm['a'], bm2['a'])

		bm2['a'] = 'bar'

		bm.save()
		bm2.save()
		bm.load()
		bm2.load()

		self.assertEqual(bm['a'], bm2['a'])
	
	def test_messing_around(self):
		bm = Bookmarks(BMFILE, str, autosave=False)
		bm2 = Bookmarks(BMFILE, str, autosave=False)

		bm.load()
		bm['a'] = 'car'

		bm2.load()
		self.assertRaises(KeyError, bm2.__getitem__, 'a')

		bm2.save()
		bm.update()
		bm.save()
		bm.load()
		bm2.load()

		self.assertEqual(bm['a'], bm2['a'])

if __name__ == '__main__':
	unittest.main()
