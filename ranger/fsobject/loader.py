from collections import deque
from time import time
from ranger import log
import math

def status_generator():
	while True:
		yield '/'
		yield '-'
		yield '\\'
		yield '|'

def delayfunc(n):
	if n < 4:
		return 0.05
	else:
		return 0.3
#		return math.log(n-2) * 0.2

class Loader(object):
	seconds_of_work_time = 0.1
	def __init__(self):
		self.queue = deque()
		self.item = None
		self.load_generator = None
		self.status_generator = status_generator()
		self.tick = 0
		self.rotate()
		self.old_item = None
	
	def rotate(self):
		self.status = next(self.status_generator)
	
	def add(self, obj):
		while obj in self.queue:
			self.queue.remove(obj)
		self.queue.appendleft(obj)

	def work(self):
		if not self.queue:
			return

		item = self.queue[0]
		if item.load_generator is None:
			self.queue.popleft()

		self.rotate()
		self.tick += 1
		if item != self.old_item:
			self.tick = 0
			self.old_item = item

		end_time = time() + delayfunc(self.tick)
		try:
			while time() < end_time:
				next(item.load_generator)
		except StopIteration:
			item.load_generator = None
			self.queue.popleft()
	
	def has_work(self):
		return bool(self.queue)
