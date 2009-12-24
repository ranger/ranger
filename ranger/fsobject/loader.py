from collections import deque
from time import time
from ranger import log
import math

def status_generator():
	"""Generate a rotating line which can be used as a throbber"""
	while True:
		yield '/'
		yield '-'
		yield '\\'
		yield '|'

class Loader(object):
	seconds_of_work_time = 0.05

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
			self.queue.popleft()
	
	def has_work(self):
		"""Is there anything to load?"""
		return bool(self.queue)
