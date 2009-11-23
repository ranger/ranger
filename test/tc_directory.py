import unittest
import sys, os
sys.path.append('../code')
import directory, fsobject, file

TESTDIR = os.path.realpath(os.path.join(os.path.dirname(sys.argv[0]), 'testdir'))
TESTFILE = os.path.join(TESTDIR, 'testfile5234148')
NONEXISTANT_DIR = '/this/directory/will/most/certainly/not/exist'

class Test1(unittest.TestCase):
	def testInitialCondition(self):
		# Check for the expected initial condition
		dir = directory.Directory(TESTDIR)

		self.assertEqual(dir.path, TESTDIR)
		self.assertFalse(dir.content_loaded)
		self.assertEqual(dir.filenames, None)
		self.assertEqual(dir.files, None)
		self.assertRaises(fsobject.NotLoadedYet, len, dir)
		self.assertRaises(fsobject.NotLoadedYet, dir.__getitem__, 0)

	def testAfterContentLoaded(self):
		# Check whether the directory has the correct list of filenames.
		dir = directory.Directory(TESTDIR)
		dir.load_content()

		self.assertTrue(dir.exists)
		self.assertEqual(type(dir.filenames), list)

		# Get the filenames you expect it to have and sort both before
		# comparing. I don't expect any order after only loading the filenames.
		assumed_filenames = os.listdir(TESTDIR)
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

	def testNonexistantDir(self):
		dir = directory.Directory(NONEXISTANT_DIR)
		dir.load_content()
		
		self.assertTrue(dir.content_loaded)
		self.assertFalse(dir.exists)
		self.assertFalse(dir.accessible)
		self.assertEqual(dir.filenames, None)
		self.assertRaises(fsobject.NotLoadedYet, len, dir)
		self.assertRaises(fsobject.NotLoadedYet, dir.__getitem__, 0)

	def testModifyFrozenClone(self):
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
		if os.path.exists(TESTFILE): os.unlink(TESTFILE)
		dir = directory.Directory(TESTDIR)
		dir.load()

		open(TESTFILE, 'w').close()

		self.assertTrue(dir.load_if_outdated())

		os.unlink(TESTFILE)

unittest.main()

