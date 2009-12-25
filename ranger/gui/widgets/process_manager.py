"""
The process manager allows you to modify what the loader is doing.
"""

import curses

from . import Widget
from ranger.ext.accumulator import Accumulator
from ranger import log
from ranger.container import CommandList
from collections import deque

class DummyLoadObject(object):
	def __init__(self, txt):
		self.get_description = lambda: txt
		self.load_generator = range(100)


class DummyLoader(object):
	def __init__(self):
		self.queue = deque()
		self.queue.append(DummyLoadObject("blub"))
		self.queue.append(DummyLoadObject("foo"))
		self.queue.append(DummyLoadObject("asfkljflk"))
		self.queue.append(DummyLoadObject("g$%GKSERJgsldflj"))


class ProcessManager(Widget, Accumulator):
	def __init__(self, win):
		Widget.__init__(self, win)
		Accumulator.__init__(self)
		self.scroll_begin = 0
		self.commandlist = CommandList()
		self.settings.keys.initialize_process_manager_commands( \
				self.commandlist)

		# ---- dummy loader for testing purposes
		self.loader = DummyLoader()
	
	def draw(self):
		base_clr = deque()
		base_clr.append('in_pman')
		lst = self.get_list()

		if not self.pointer_is_synced():
			self.sync_index()

		self.win.addnstr(self.y, self.x, "  Process Manager", self.wid)
		self.color_at(self.y, self.x, self.wid, base_clr, 'title')

		if lst:
			for i in range(self.hei - 1):
				i += self.scroll_begin
				try:
					obj = lst[i]
				except IndexError:
					break
				y, x = self.y + i + 1, self.x
				clr = deque(base_clr)

				if self.pointer == i:
					clr.append('selected')

				descr = obj.get_description()
				self.win.addnstr(y, x, descr, self.wid)
				self.color_at(y, x, self.wid, clr)

		else:
			if self.hei > 1:
				self.win.addnstr(self.y + 1, self.x,\
						"No processes running", self.wid)
				self.color_at(self.y + 1, self.x, self.wid, base_clr, 'error')

		self.color_reset()

	def process_remove(self, i=None):
		if i is None:
			i = self.pointer

		self.fm.loader.remove(index=i)
	
	def process_move(self, absolute, i=None):
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
				cmd.execute(self, self.env.keybuffer.number)
				self.env.key_clear()
	
	def get_list(self):
		return self.fm.loader.queue
		return self.loader.queue


class KeyWrapper(object):
	@staticmethod
	def move(relative=0, absolute=None):
		if absolute is None:
			def fnc(wdg, n):
				if n is not None:
					if relative >= 0:
						wdg.move(relative=n)
					else:
						wdg.move(relative=-n)
				else:
					wdg.move(relative=relative)
		else:
			def fnc(wdg, n):
				if n is not None:
					wdg.move(absolute=n, relative=relative)
				else:
					wdg.move(absolute=absolute, relative=relative)
		return fnc
