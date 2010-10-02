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
from time import time
from ranger.core.shared import FileManagerAware
import math

def status_generator():
	"""Generate a rotating line which can be used as a throbber"""
	while True:
		yield '/'
		yield '-'
		yield '\\'
		yield '|'

class LoadableObject(object):
	def __init__(self, gen, descr):
		self.load_generator = gen
		self.description = descr

	def get_description(self):
		return self.description


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
			self.old_item = item

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
