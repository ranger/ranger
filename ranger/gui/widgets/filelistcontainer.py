"""The FileListContainer manages a set of FileLists."""
from . import Widget
from .filelist import FileList
from ..displayable import DisplayableContainer
from ranger import log

class FileListContainer(Widget, DisplayableContainer):
	ratios = None
	preview = True
	preview_available = True
	stretch_ratios = None

	def __init__(self, win, ratios, preview = True):
		DisplayableContainer.__init__(self, win)
		from functools import reduce
		self.ratios = ratios
		self.preview = preview

		# normalize ratios:
		ratio_sum = float(reduce(lambda x,y: x + y, ratios))
		self.ratios = tuple(map(lambda x: x / ratio_sum, ratios))

		if self.ratios >= 2:
			self.stretch_ratios = self.ratios[:-2] + \
					((self.ratios[-2] + self.ratios[-1] * 0.9), \
					(self.ratios[-1] * 0.1))
		
		offset = 1 - len(ratios)
		if preview: offset += 1

		for level in range(len(ratios)):
			fl = FileList(win, level + offset)
			self.add_obj(fl)

		try:
			self.main_filelist = self.container[preview and -2 or -1]
		except IndexError:
			self.main_filelist = None
		else:
			self.main_filelist.display_infostring = True
			self.main_filelist.main_display = True
	
	def resize(self, y, x, hei, wid):
		"""Resize all the filelists according to the given ratio"""
		DisplayableContainer.resize(self, y, x, hei, wid)
		left = self.x

		cut_off_last = self.preview and not self.preview_available \
				and self.stretch_ratios

		if cut_off_last:
			generator = zip(self.stretch_ratios, range(len(self.ratios)))
		else:
			generator = zip(self.ratios, range(len(self.ratios)))

		for ratio, i in generator:
			wid = int(ratio * self.wid)

			if i == len(self.ratios) - 1:
				wid = int(self.wid - left + 1)

			try:
				self.container[i].resize(self.y, left, hei, max(1, wid-1))
			except KeyError:
				pass

			left += wid
	
	def poke(self):
		DisplayableContainer.poke(self)
		if self.settings.collapse_preview and self.preview:
			has_preview = self.container[-1].has_preview()
			if self.preview_available != has_preview:
				self.preview_available = has_preview
				self.resize(self.y, self.x, self.hei, self.wid)
