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

"""
The titlebar is the widget at the top, giving you broad orientation.

It displays the current path among other things.
"""

from math import floor

from . import Widget
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

	def click(self, event):
		"""Handle a MouseEvent"""
		if not event.pressed(1) or not self.result:
			return False

		pos = 0
		for i, part in enumerate(self.result):
			pos += len(part.string)
			if event.x < pos:
				if i < 2:
					self.fm.enter_dir("~")
				elif i == 2:
					self.fm.enter_dir("/")
				else:
					try:
						self.fm.env.enter_dir(self.env.pathway[(i-3)/2])
					except:
						pass
				return False

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
		if self.env.username == 'root':
			clr = 'bad'
		else:
			clr = 'good'

		bar.add(self.env.username, 'hostname', clr, fixedsize=True)
		bar.add('@', 'hostname', clr, fixedsize=True)
		bar.add(self.env.hostname, 'hostname', clr, fixedsize=True)

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
