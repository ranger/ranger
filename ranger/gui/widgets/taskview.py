# Copyright (C) 2009, 2010, 2011  Roman Zimbelmann <romanz@lavabit.com>
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
The TaskView allows you to modify what the loader is doing.
"""

from . import Widget
from ranger.ext.accumulator import Accumulator

class TaskView(Widget, Accumulator):
	old_lst = None

	def __init__(self, win):
		Widget.__init__(self, win)
		Accumulator.__init__(self)
		self.scroll_begin = 0

	def draw(self):
		base_clr = []
		base_clr.append('in_taskview')
		lst = self.get_list()

		if self.old_lst != lst:
			self.old_lst = lst
			self.need_redraw = True

		if self.need_redraw:
			self.win.erase()
			if not self.pointer_is_synced():
				self.sync_index()

			if self.hei <= 0:
				return

			self.addstr(0, 0, "Task View")
			self.color_at(0, 0, self.wid, tuple(base_clr), 'title')

			if lst:
				for i in range(self.hei - 1):
					i += self.scroll_begin
					try:
						obj = lst[i]
					except IndexError:
						break

					y = i + 1
					clr = list(base_clr)

					if self.pointer == i:
						clr.append('selected')

					descr = obj.get_description()
					self.addstr(y, 0, descr, self.wid)
					self.color_at(y, 0, self.wid, tuple(clr))

			else:
				if self.hei > 1:
					self.addstr(1, 0, "No task in the queue.")
					self.color_at(1, 0, self.wid, tuple(base_clr), 'error')

			self.color_reset()

	def finalize(self):
		y = self.y + 1 + self.pointer - self.scroll_begin
		self.fm.ui.win.move(y, self.x)


	def task_remove(self, i=None):
		if i is None:
			i = self.pointer

		if self.fm.loader.queue:
			self.fm.loader.remove(index=i)

	def task_move(self, to, i=None):
		if i is None:
			i = self.pointer

		self.fm.loader.move(_from=i, to=to)

	def press(self, key):
		self.env.keymaps.use_keymap('taskview')
		self.fm.ui.press(key)

	def get_list(self):
		return self.fm.loader.queue
