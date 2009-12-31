"""
The titlebar is the widget at the top, giving you broad orientation.

It displays the current path among other things.
"""

from . import Widget
from math import floor
from ranger.gui.bar import Bar

class TitleBar(Widget):
	old_cf = None
	old_keybuffer = None
	old_wid = None
	result = None
	throbber = ' '

	def draw(self):
		if self.env.cf != self.old_cf or\
				str(self.env.keybuffer) != str(self.old_keybuffer) or\
				self.wid != self.old_wid:
			self.old_wid = self.wid
			self.old_cf = self.env.cf
			self._calc_bar()
		self._print_result(self.result)
		if self.wid > 2:
			self.color('in_titlebar', 'throbber')
			self.win.addnstr(self.y, self.wid - 2, self.throbber, 1)

	def _calc_bar(self):
		bar = Bar('in_titlebar')
		self._get_left_part(bar)
		self._get_right_part(bar)
		try:
			bar.shrink_by_cutting(self.wid)
		except ValueError:
			bar.shrink_by_removing(self.wid)
		self.result = bar.combine()
	
	def _get_left_part(self, bar):
		import socket, os
		
		bar.add(os.getenv('LOGNAME'), 'hostname', fixedsize=True)
		bar.add('@', 'hostname', fixedsize=True)
		bar.add(socket.gethostname(), 'hostname', fixedsize=True)

		for path in self.env.pathway:
			if path.islink:
				clr = 'link'
			else:
				clr = 'directory'

			bar.add(path.basename, clr)
			bar.add('/', clr, fixedsize=True)

		if self.env.cf is not None:
			bar.add(self.env.cf.basename, 'file', fixedsize=True)

	def _get_right_part(self, bar):
		kb = str(self.env.keybuffer)
		self.old_keybuffer = kb
		bar.addright(kb, 'keybuffer', fixedsize=True)
		bar.addright('  ', 'space', fixedsize=True)

	def _print_result(self, result):
		import _curses
		self.win.move(0, 0)
		for part in result:
			self.color(*part.lst)
			self.addstr(part.string)
		self.color_reset()
