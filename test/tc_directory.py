import unittest
import sys, os, time

sys.path.append(os.path.normpath(os.path.join(os.path.dirname(__file__), '../code')))
import fsobject, file, directory

TESTDIR = os.path.realpath(os.path.join(os.path.dirname(__file__), 'testdir'))
TESTFILE = os.path.join(TESTDIR, 'testfile5234148')
NONEXISTANT_DIR = '/this/directory/will/most/certainly/not/exist'

class Test1(unittest.TestCase):
	def test_initial_condition(self):
		# Check for the expected initial condition
		dir = directory.Directory(TESTDIR)

		self.assertEqual(dir.path, TESTDIR)
		self.assertFalse(dir.content_loaded)
		self.assertEqual(dir.filenames, None)
		self.assertEqual(dir.files, None)
		self.assertRaises(fsobject.NotLoadedYet, len, dir)
		self.assertRaises(fsobject.NotLoadedYet, dir.__getitem__, 0)

	def test_after_content_loaded(self):
		# Check whether the directory has the correct list of filenames.
		dir = directory.Directory(TESTDIR)
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
			f = file.File(name)
			f.load()
			equal = 0
			for dirfile in dir.files:
				if (f.__dict__ == dirfile.__dict__):
					equal += 1
			self.assertEqual(equal, 1)

	def test_nonexistant_dir(self):
		dir = directory.Directory(NONEXISTANT_DIR)
		dir.load_content()
		
		self.assertTrue(dir.content_loaded)
		self.assertFalse(dir.exists)
		self.assertFalse(dir.accessible)
		self.assertEqual(dir.filenames, None)
		self.assertRaises(fsobject.NotLoadedYet, len, dir)
		self.assertRaises(fsobject.NotLoadedYet, dir.__getitem__, 0)

	def test_modify_frozen_clone(self):
		dir = directory.Directory(TESTDIR)
		clone = dir.frozen_clone()

		# assert that their attributes are equal, except for frozen, which
		# should be true for the clone.
		self.assertTrue(clone.frozen)
		clone.frozen = False
		self.assertEqual(dir.__dict__, clone.__dict__)
		clone.frozen = True

		# check for inequality after loading filenames with one object
		self.assertEqual(dir.filenames, clone.filenames)
		dir.load_content()
		self.assertNotEqual(dir.filenames, clone.filenames)

		self.assertRaises(fsobject.FrozenException, clone.load_content)

	def test_load_if_outdated(self):
		# modify the directory. If the time between the last modification
		# was within the filesystems resolution of mtime, we should have a re-load.

		def modify_dir():
			open(TESTFILE, 'w').close()
			os.unlink(TESTFILE)

		def mtime():
			return os.stat(TESTDIR).st_mtime

		dir = directory.Directory(TESTDIR)
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

