import unittest
import sys, os
sys.path.append('../code')
import directory

TESTDIR = os.path.realpath(os.path.join(os.path.dirname(sys.argv[0]), 'testdir'))
NONEXISTANT_DIR = '/this/directory/will/most/certainly/not/exist'

class Test1(unittest.TestCase):
	def testInitialCondition(self):
		# Check for the expected initial condition
		dir = directory.Directory(TESTDIR)

		self.assertEqual(dir.path, TESTDIR)
		self.assertFalse(dir.files_loaded)
		self.assertEqual(dir.files, None)
		self.assertRaises(directory.NotLoadedYet, len, dir)
		self.assertRaises(directory.NotLoadedYet, dir.__getitem__, 0)

	def testAfterFilesLoaded(self):
		# Check whether the directory has the correct list of files.
		dir = directory.Directory(TESTDIR)
		dir.load_files()

		self.assertTrue(dir.exists)
		self.assertEqual(type(dir.files), list)

		# Get the files you expect it to have and sort both before
		# comparing. I don't expect any order after only loading the files.
		assumed_files = os.listdir(TESTDIR)
		assumed_files.sort()
		dir.files.sort()

		self.assertTrue(len(dir) > 0)
		self.assertEqual(dir.files, assumed_files)

	def testNonexistantDir(self):
		dir = directory.Directory(NONEXISTANT_DIR)
		dir.load_files()
		
		self.assertTrue(dir.files_loaded)
		self.assertFalse(dir.exists)
		self.assertFalse(dir.accessible)
		self.assertEqual(dir.files, None)
		self.assertRaises(directory.NotLoadedYet, len, dir)
		self.assertRaises(directory.NotLoadedYet, dir.__getitem__, 0)

	def testModifyFrozenClone(self):
		dir = directory.Directory(TESTDIR)
		clone = dir.frozenClone()

		# assert that their attributes are equal, except for frozen, which
		# should be true for the clone.
		self.assertTrue(clone.frozen)
		clone.frozen = False
		self.assertEqual(dir.__dict__, clone.__dict__)
		clone.frozen = True

		# check for inequality after loading files with one object
		self.assertEqual(dir.files, clone.files)
		dir.load_files()
		self.assertNotEqual(dir.files, clone.files)

		self.assertRaises(directory.FrozenException, clone.load_files)

unittest.main()

