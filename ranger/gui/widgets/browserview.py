"""The BrowserView manages a set of BrowserColumns."""
from . import Widget
from .browsercolumn import BrowserColumn
from .pager import Pager
from ..displayable import DisplayableContainer

class BrowserView(Widget, DisplayableContainer):
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

		if len(self.ratios) >= 2:
			self.stretch_ratios = self.ratios[:-2] + \
					((self.ratios[-2] + self.ratios[-1] * 0.9), \
					(self.ratios[-1] * 0.1))
		
		offset = 1 - len(ratios)
		if preview: offset += 1

		for level in range(len(ratios)):
			fl = BrowserColumn(self.win, level + offset)
			self.add_child(fl)

		try:
			self.main_column = self.container[preview and -2 or -1]
		except IndexError:
			self.main_column = None
		else:
			self.main_column.display_infostring = True
			self.main_column.main_display = True

		self.pager = Pager(self.win, embedded=True)
		self.add_child(self.pager)
	
	def resize(self, y, x, hei, wid):
		"""Resize all the columns according to the given ratio"""
		DisplayableContainer.resize(self, y, x, hei, wid)
		left = 0

		cut_off_last = self.preview and not self.preview_available \
				and self.stretch_ratios

		if cut_off_last:
			generator = zip(self.stretch_ratios, range(len(self.ratios)))
		else:
			generator = zip(self.ratios, range(len(self.ratios)))

		last_i = len(self.ratios) - 1

		for ratio, i in generator:
			wid = int(ratio * self.wid)

			if i == last_i:
				wid = int(self.wid - left + 1)

			if i == last_i - 1:
				self.pager.resize(0, left, hei, max(1, self.wid - left))

			try:
				self.container[i].resize(0, left, hei, max(1, wid-1))
			except KeyError:
				pass

			left += wid
	
	def click(self, event):
		n = event.ctrl() and 1 or 3
		if event.pressed(4):
			self.fm.scroll(relative = -n)
		elif event.pressed(2) or event.key_invalid():
			self.fm.scroll(relative = n)
		else:
			DisplayableContainer.click(self, event)
	
	def open_pager(self):
		self.pager.visible = True
		self.pager.focused = True
		self.pager.open()
		try:
			self.container[-2].visible = False
			self.container[-3].visible = False
		except IndexError:
			pass
	
	def close_pager(self):
		self.pager.visible = False
		self.pager.focused = False
		self.pager.close()
		try:
			self.container[-2].visible = True
			self.container[-3].visible = True
		except IndexError:
			pass
	
	def poke(self):
		DisplayableContainer.poke(self)
		if self.settings.collapse_preview and self.preview:
			has_preview = self.container[-2].has_preview()
			if self.preview_available != has_preview:
				self.preview_available = has_preview
				self.resize(self.y, self.x, self.hei, self.wid)
