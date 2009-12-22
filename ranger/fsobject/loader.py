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
		return math.log(n-2) * 0.2

class Loader(object):
	seconds_of_work_time = 0.1
	def __init__(self):
		self.queue = deque()
		self.item = None
		self.load_generator = None
		self.status_generator = status_generator()
		self.tick = 0
		self.rotate()
	
	def rotate(self):
		self.status = next(self.status_generator)
	
	def add(self, obj):
		self.queue.append(obj)

	def work(self):
		if self.item is None:
			try:
				self.item = self.queue.popleft()
			except IndexError:
				return

			self.load_generator = self.item.load_bit_by_bit()
			self.tick = 0

		self.rotate()
		self.tick += 1
		start_time = time()
		end_time = time() + delayfunc(self.tick)

		log(tuple(map(str, self.queue)))
		try:
#			log("loading " + self.item.basename)
			while time() < end_time:
				next(self.load_generator)

		except StopIteration:
			self.item = None
			self.load_generator = None
	
	def __nonzero__(self):
		return bool(self.queue or self.item is not None)
