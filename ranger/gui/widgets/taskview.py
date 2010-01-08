# Copyright (c) 2009, 2010 hut <hut@lavabit.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""
The TaskView allows you to modify what the loader is doing.
"""

import curses

from . import Widget
from ranger.ext.accumulator import Accumulator
from ranger.container import CommandList
from collections import deque

class TaskView(Widget, Accumulator):
	old_lst = None
	
	def __init__(self, win):
		Widget.__init__(self, win)
		Accumulator.__init__(self)
		self.scroll_begin = 0
		self.commandlist = CommandList()
		self.settings.keys.initialize_taskview_commands(self.commandlist)

	def draw(self):
		base_clr = deque()
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
			self.color_at(0, 0, self.wid, base_clr, 'title')

			if lst:
				for i in range(self.hei - 1):
					i += self.scroll_begin
					try:
						obj = lst[i]
					except IndexError:
						break

					y = i + 1
					clr = deque(base_clr)

					if self.pointer == i:
						clr.append('selected')

					descr = obj.get_description()
					self.addstr(y, 0, descr, self.wid)
					self.color_at(y, 0, self.wid, clr)

			else:
				if self.hei > 1:
					self.addstr(1, 0, "No task in the queue.")
					self.color_at(1, 0, self.wid, base_clr, 'error')

			self.color_reset()

	def task_remove(self, i=None):
		if i is None:
			i = self.pointer

		self.fm.loader.remove(index=i)
	
	def task_move(self, absolute, i=None):
		if i is None:
			i = self.pointer

		self.fm.loader.move(_from=i, to=absolute)

	def press(self, key):
		try:
			tup = self.env.keybuffer.tuple_without_numbers()
			if tup:
				cmd = self.commandlist[tup]
			else:
				return
				
		except KeyError:
			self.env.key_clear()
		else:
			if hasattr(cmd, 'execute'):
				cmd.execute_wrap(self)
				self.env.key_clear()
	
	def get_list(self):
		return self.fm.loader.queue
