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
import os
from os.path import realpath, join, dirname

from testlib import Fake
from ranger.core.shared import FileManagerAware, SettingsAware
from ranger.core.loader import Loader
from ranger.fsobject import Directory, File
from ranger.ext.openstruct import OpenStruct

TESTDIR = realpath(join(dirname(__file__), 'testdir'))
#TESTDIR = "/usr/sbin"

class Test1(unittest.TestCase):
	def test_loader(self):
		loader = Loader()
		fm = OpenStruct(loader=loader)
		SettingsAware.settings = Fake()
		FileManagerAware.fm = fm

		# initially, the loader has nothing to do
		self.assertFalse(loader.has_work())

		dir = Directory(TESTDIR)
		self.assertEqual(None, dir.files)
		self.assertFalse(loader.has_work())

		# Calling load_content() will enqueue the loading operation.
		# dir is not loaded yet, but the loader has work
		dir.load_content(schedule=True)
		self.assertEqual(None, dir.files)
		self.assertTrue(loader.has_work())

		iterations = 0
		while loader.has_work():
			iterations += 1
			loader.work()
		#print(iterations)
		self.assertNotEqual(None, dir.files)
		self.assertFalse(loader.has_work())
#
#	def test_get_overhead_of_loader(self):
#		N = 5
#		tloader = benchmark_load(N)
#		traw = benchmark_raw_load(N)
#		#traw1k = 250.0
#		#traw = traw1k * N / 1000.0
#		#print("Loader: {0}s".format(tloader))
#		#print("Raw:    {0}s".format(traw))
#		self.assertTrue(tloader > traw)
#		overhead = tloader * 100 / traw - 100
#		self.assertTrue(overhead < 2, "overhead of loader too high: {0}" \
#				.format(overhead))
#		#print("Overhead: {0:.5}%".format(overhead))


if __name__ == '__main__':
	unittest.main()
