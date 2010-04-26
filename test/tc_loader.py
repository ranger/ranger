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

import unittest
import os
from os.path import realpath, join, dirname
from time import time

from test import Fake
from ranger.shared import FileManagerAware, SettingsAware
from ranger.core.loader import Loader
from ranger.fsobject import Directory, File
from ranger.ext.openstruct import OpenStruct

TESTDIR = realpath(join(dirname(__file__), 'testdir'))
#TESTDIR = "/usr/sbin"

def raw_load_content(self):
	"""
	The method which is used in a Directory object to load stuff.
	Keep this up to date!
	"""

	from os.path import join, isdir, basename
	from os import listdir
	import ranger.ext.mount_path

	self.loading = True
	self.load_if_outdated()

	try:
		if self.exists and self.runnable:
			self.mount_path = ranger.ext.mount_path.mount_path(self.path)

			filenames = []
			for fname in listdir(self.path):
				if not self.settings.show_hidden:
					hfilter = self.settings.hidden_filter
					if hfilter:
						if isinstance(hfilter, str) and hfilter in fname:
							continue
						if hasattr(hfilter, 'search') and \
							hfilter.search(fname):
							continue
				if isinstance(self.filter, str) and self.filter \
						and self.filter not in fname:
					continue
				filenames.append(join(self.path, fname))

			self.load_content_mtime = os.stat(self.path).st_mtime

			marked_paths = [obj.path for obj in self.marked_items]

			files = []
			for name in filenames:
				if isdir(name):
					try:
						item = self.fm.env.get_directory(name)
					except:
						item = Directory(name)
				else:
					item = File(name)
				item.load_if_outdated()
				files.append(item)

			self.disk_usage = sum(f.size for f in files if f.is_file)

			self.scroll_offset = 0
			self.filenames = filenames
			self.files = files

			self._clear_marked_items()
			for item in self.files:
				if item.path in marked_paths:
					self.mark_item(item, True)
				else:
					self.mark_item(item, False)

			self.sort()

			if len(self.files) > 0:
				if self.pointed_obj is not None:
					self.sync_index()
				else:
					self.move(to=0)
		else:
			self.filenames = None
			self.files = None

		self.cycle_list = None
		self.content_loaded = True
		self.determine_infostring()
		self.last_update_time = time()
		self.correct_pointer()

	finally:
		self.loading = False


def benchmark_load(n):
	loader = Loader()
	fm = OpenStruct(loader=loader)
	SettingsAware.settings = Fake()
	FileManagerAware.fm = fm
	dir = Directory(TESTDIR)

	t1 = time()
	for _ in range(n):
		dir.load_content(schedule=True)
		while loader.has_work():
			loader.work()
	t2 = time()
	return t2 - t1


def benchmark_raw_load(n):
	SettingsAware.settings = Fake()
	dir = Directory(TESTDIR)
	generator = dir.load_bit_by_bit()
	t1 = time()
	for _ in range(n):
		raw_load_content(dir)
	t2 = time()
	return t2 - t1


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

	def test_get_overhead_of_loader(self):
		N = 5
		tloader = benchmark_load(N)
		traw = benchmark_raw_load(N)
		#traw1k = 250.0
		#traw = traw1k * N / 1000.0
		#print("Loader: {0}s".format(tloader))
		#print("Raw:    {0}s".format(traw))
		self.assertTrue(tloader > traw)
		overhead = tloader * 100 / traw - 100
		self.assertTrue(overhead < 2, "overhead of loader too high: {0}" \
				.format(overhead))
		#print("Overhead: {0:.5}%".format(overhead))


if __name__ == '__main__':
	unittest.main()
