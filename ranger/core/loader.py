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

from collections import deque
from time import time, sleep
from subprocess import Popen, PIPE
import math
import os
import select

from ranger.shared import FileManagerAware

def status_generator():
	"""Generate a rotating line which can be used as a throbber"""
	while True:
		yield '/'
		yield '-'
		yield '\\'
		yield '|'


class Loadable(object):
	paused = False
	def __init__(self, gen, descr):
		self.load_generator = gen
		self.description = descr

	def get_description(self):
		return self.description

	def pause(self):
		self.paused = True

	def unpause(self):
		try:
			del self.paused
		except:
			pass

	def destroy(self):
		pass


class CommandLoader(Loadable, FileManagerAware):
	"""
	Run an external command with the loader.

	Output from stderr will be reported.  Ensure that the process doesn't
	ever ask for input, otherwise the loader will be blocked until this
	object is removed from the queue (type ^C in ranger)
	"""
	finished = False
	def __init__(self, args, descr, begin_hook=None, end_hook=None):
		Loadable.__init__(self, self.generate(), descr)
		self.args = args
		self.begin_hook = begin_hook
		self.end_hook = end_hook

	def generate(self):
		self.process = process = Popen(self.args,
				stdout=open(os.devnull, 'w'),
				stderr=PIPE)
		if self.begin_hook:
			self.begin_hook(process)
		while process.poll() is None:
			rd, _, __ = select.select(
					[process.stderr], [], [], 0.05)
			if rd:
				error = process.stderr.readline().decode('utf-8')
				self.fm.notify(error, bad=True)
			sleep(0.02)
			yield
		self.finished = True
		if self.end_hook:
			self.end_hook(process)

	def pause(self):
		if not self.finished and not self.paused:
			self.process.send_signal(20)
		Loadable.pause(self)

	def unpause(self):
		if not self.finished and self.paused:
			self.process.send_signal(18)
		Loadable.unpause(self)

	def destroy(self):
		if self.process:
			self.process.kill()


class Loader(FileManagerAware):
	seconds_of_work_time = 0.03

	def __init__(self):
		self.queue = deque()
		self.item = None
		self.load_generator = None
		self.status_generator = status_generator()
		self.rotate()
		self.old_item = None

	def rotate(self):
		"""Rotate the throbber"""
		# TODO: move all throbber logic to UI
		self.status = next(self.status_generator)

	def add(self, obj):
		"""
		Add an object to the queue.
		It should have a load_generator method.
		"""
		while obj in self.queue:
			self.queue.remove(obj)
		self.queue.appendleft(obj)

	def move(self, _from, to):
		try:
			item = self.queue[_from]
		except IndexError:
			return

		del self.queue[_from]

		if to == 0:
			self.queue.appendleft(item)
			if _from != 0:
				self.queue[1].pause()
		elif to == -1:
			self.queue.append(item)
		else:
			raise NotImplementedError

	def remove(self, item=None, index=None):
		if item is not None and index is None:
			for i, test in enumerate(self.queue):
				if test == item:
					index = i 
					break
			else:
				return

		if index is not None:
			if item is None:
				item = self.queue[index]
			if hasattr(item, 'unload'):
				item.unload()
			item.destroy()
			del self.queue[index]

	def work(self):
		"""
		Load items from the queue if there are any.
		Stop after approximately self.seconds_of_work_time.
		"""
		while True:
			# get the first item with a proper load_generator
			try:
				item = self.queue[0]
				if item.load_generator is None:
					self.queue.popleft()
				else:
					break
			except IndexError:
				return

		self.rotate()
		if item != self.old_item:
			if self.old_item:
				self.old_item.pause()
			self.old_item = item
		item.unpause()

		end_time = time() + self.seconds_of_work_time

		try:
			while time() < end_time:
				next(item.load_generator)
		except StopIteration:
			item.load_generator = None
			self.queue.remove(item)
		except Exception as err:
			self.fm.notify(err)

	def has_work(self):
		"""Is there anything to load?"""
		return bool(self.queue)

	def destroy(self):
		while self.queue:
			self.queue.pop().destroy()
