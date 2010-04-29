from ranger.core.loader import Loader
from ranger.fsobject import Directory, File
from ranger.ext.openstruct import OpenStruct
import os
from ranger.shared import FileManagerAware, SettingsAware
from test import Fake
from os.path import realpath, join, dirname
TESTDIR = realpath(join(dirname(__file__), '/usr/include'))

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
