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
