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

from ranger.core.loader import Loader
from ranger.fsobject import Directory, File
from ranger.ext.openstruct import OpenStruct
import os.path
from ranger.shared import FileManagerAware, SettingsAware
from testlib import Fake
from os.path import realpath, join, dirname
from subprocess import Popen, PIPE
TESTDIR = realpath(join(dirname(__file__), '/usr/include'))

def skip(x):
	return

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
			# 0.003s:
			self.mount_path = ranger.ext.mount_path.mount_path(self.path)

			# 0.1s:
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
			# ---

			self.load_content_mtime = os.stat(self.path).st_mtime

			marked_paths = [obj.path for obj in self.marked_items]

			# 2.85s:
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

			# 0.2s
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
		self.correct_pointer()

	finally:
		self.loading = False


class benchmark_load(object):
	def __init__(self):
		self.loader = Loader()
		fm = OpenStruct(loader=self.loader)
		SettingsAware.settings = Fake()
		FileManagerAware.fm = fm
		self.dir = Directory(TESTDIR)

	def bm_run(self, n):
		for _ in range(n):
			self.dir.load_content(schedule=True)
			while self.loader.has_work():
				self.loader.work()


@skip
class benchmark_raw_load(object):
	def __init__(self):
		SettingsAware.settings = Fake()
		self.dir = Directory(TESTDIR)

	def bm_run(self, n):
		generator = self.dir.load_bit_by_bit()
		for _ in range(n):
			raw_load_content(self.dir)

def bm_loader(n):
	"""Do some random calculation"""
	tloader = benchmark_load(N)
	traw = benchmark_raw_load(N)

class benchmark_load_varieties(object):
	def bm_ls(self, n):
		for _ in range(n):
			Popen(["ls", '-l', TESTDIR], stdout=open(os.devnull, 'w')).wait()

	def bm_os_listdir_stat(self, n):
		for _ in range(n):
			for f in os.listdir(TESTDIR):
				path = os.path.join(TESTDIR, f)
				os.stat(path)

	def bm_os_listdir(self, n):
		for _ in range(n):
			for f in os.listdir(TESTDIR):
				path = os.path.join(TESTDIR, f)

	def bm_os_listdir_stat_listdir(self, n):
		for _ in range(n):
			for f in os.listdir(TESTDIR):
				path = os.path.join(TESTDIR, f)
				os.stat(path)
				if os.path.isdir(path):
					os.listdir(path)
