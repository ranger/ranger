"""Notify is a bar which displays messages."""

from . import Widget
from time import time
from collections import deque

class Notify(Widget):
	requested_height = 1
	max_size = 5
	textcontainer = None

	def __init__(self, win):
		Widget.__init__(self, win)
		self.textcontainer = deque(maxlen=self.max_size)

	def poke(self):
		for i in reversed(range(len(self.textcontainer))):
			msg = self.textcontainer[i]
			if msg.elapse and time() > msg.elapse:
				msg.alive = False
				del self.textcontainer[i]
		self.requested_height = len(self.textcontainer) + 1

	def draw(self):
		import curses, socket, os

		i = 0
		for msg in self.textcontainer:
			if i >= self.hei - 1:
				break

			how = msg.bad and 'bad' or 'good'
			self.color_at(i, 0, self.wid,\
					'in_notify', 'background', how)
			self.color('in_notify', 'message', how)
			self.win.addnstr(i, 0, msg.text, self.wid)
			i += 1

		self.color_reset()
	
	def display(self, text, duration=4, bad=False):
		msg = Message(self.textcontainer, text, duration, bad)
		self.textcontainer.append(msg)
		return msg

class Message(object):
	elapse = None
	text = None
	bad = False
	alive = True
	container = None

	def __init__(self, container, text, duration, bad):
		self.text = text
		self.bad = bad
		self.container = container
		self.set_duration(duration)
	
	def set_duration(self, n=4):
		if n:
			self.elapse = time() + n
		else:
			self.elapse = None

	def delete(self):
		self.alive = False
		try:
			self.container.remove(self)
		except ValueError:
			pass
