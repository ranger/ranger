"""The FileListContainer manages a set of FileLists."""
from . import Widget
from .filelist import FileList
from ..displayable import DisplayableContainer

class FileListContainer(Widget, DisplayableContainer):
	ratios = None
	preview = True

	def __init__(self, win, ratios, preview = True):
		DisplayableContainer.__init__(self, win)
		from functools import reduce
		self.ratios = ratios
		# normalize ratios:
		ratio_sum = float(reduce(lambda x,y: x + y, ratios))
		self.ratios = tuple(map(lambda x: x / ratio_sum, ratios))
		
		offset = 1 - len(ratios)
		if preview: offset += 1

		for level in range(len(ratios)):
			self.add_obj(FileList(win, level + offset))

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
		left = self.y
		for ratio, i in zip(self.ratios, range(len(self.ratios))):
			wid = int(ratio * self.wid)
			try:
				self.container[i].resize(self.y, left, hei, max(1, wid-1))
			except KeyError:
				pass
			left += wid
