if __name__ == '__main__': from __init__ import init; init()

from ranger import fsobject
from ranger.fsobject.file import File
from ranger.fsobject.directory import Directory

from os.path import realpath, join, dirname
TESTDIR = realpath(join(dirname(__file__), 'testdir'))
TESTFILE = join(TESTDIR, 'testfile5234148')
NONEXISTANT_DIR = join(TESTDIR, 'nonexistant')

import unittest
class Test1(unittest.TestCase):
	def test_initial_condition(self):
		# Check for the expected initial condition
		dir = Directory(TESTDIR)

		self.assertEqual(dir.path, TESTDIR)
		self.assertFalse(dir.content_loaded)
		self.assertEqual(dir.filenames, None)
		self.assertEqual(dir.files, None)
		self.assertRaises(fsobject.NotLoadedYet, len, dir)
		self.assertRaises(fsobject.NotLoadedYet, dir.__getitem__, 0)

	def test_after_content_loaded(self):
		import os
		# Check whether the directory has the correct list of filenames.
		dir = Directory(TESTDIR)
		dir.load_content()

		self.assertTrue(dir.exists)
		self.assertEqual(type(dir.filenames), list)

		# Get the filenames you expect it to have and sort both before
		# comparing. I don't expect any order after only loading the filenames.
		assumed_filenames = os.listdir(TESTDIR)
		assumed_filenames = list(map(lambda str: os.path.join(TESTDIR, str), assumed_filenames))
		assumed_filenames.sort()
		dir.filenames.sort()

		self.assertTrue(len(dir) > 0)
		self.assertEqual(dir.filenames, assumed_filenames)

		# build a file object for each file in the list assumed_filenames
		# and find exactly one equivalent in dir.files
		for name in assumed_filenames:
			f = File(name)
			f.load()
			equal = 0
			for dirfile in dir.files:
				if (f.__dict__ == dirfile.__dict__):
					equal += 1
			self.assertEqual(equal, 1)

	def test_nonexistant_dir(self):
		dir = Directory(NONEXISTANT_DIR)
		dir.load_content()
		
		self.assertTrue(dir.content_loaded)
		self.assertFalse(dir.exists)
		self.assertFalse(dir.accessible)
		self.assertEqual(dir.filenames, None)
		self.assertRaises(fsobject.NotLoadedYet, len, dir)
		self.assertRaises(fsobject.NotLoadedYet, dir.__getitem__, 0)

	def test_load_if_outdated(self):
		import os
		import time
		# modify the directory. If the time between the last modification
		# was within the filesystems resolution of mtime, we should have a re-load.

		def modify_dir():
			open(TESTFILE, 'w').close()
			os.unlink(TESTFILE)

		def mtime():
			return os.stat(TESTDIR).st_mtime

		dir = Directory(TESTDIR)
		dir.load()

		# If the modification happens to be in the same second as the
		# last modification, it will result in mtime having the same
		# integer value. So we wait until the resolution is exceeded
		# and mtime differs.
		old_mtime = mtime()
		for i in range(50):
			modify_dir()
			if old_mtime != mtime(): break
			time.sleep(0.1)
		else:
			# fail after 5 seconds of trying
			self.fail("Cannot perform test: mtime of TESTDIR is not being updated.")

		self.assertTrue(dir.load_if_outdated())

if __name__ == '__main__':
	unittest.main()

