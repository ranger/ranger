# Copyright (C) 2009, 2010, 2011  Roman Zimbelmann <romanz@lavabit.com>
# This software is distributed under the terms of the GNU GPL version 3.

from collections import deque
from time import time, sleep
from subprocess import Popen, PIPE
from ranger.core.shared import FileManagerAware
from ranger.ext.signals import SignalDispatcher
import os
import sys
import select
try:
	import chardet
	HAVE_CHARDET = True
except:
	HAVE_CHARDET = False

class Loadable(object):
	paused = False
	progressbar_supported = False
	def __init__(self, gen, descr):
		self.load_generator = gen
		self.description = descr
		self.percent = 0

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


class CommandLoader(Loadable, SignalDispatcher, FileManagerAware):
	"""
	Run an external command with the loader.

	Output from stderr will be reported.  Ensure that the process doesn't
	ever ask for input, otherwise the loader will be blocked until this
	object is removed from the queue (type ^C in ranger)
	"""
	finished = False
	process = None
	def __init__(self, args, descr, silent=False, read=False):
		SignalDispatcher.__init__(self)
		Loadable.__init__(self, self.generate(), descr)
		self.args = args
		self.silent = silent
		self.read = read
		self.stdout_buffer = ""

	def generate(self):
		null = open(os.devnull, 'r')
		self.process = process = Popen(self.args,
				stdout=PIPE, stderr=PIPE, stdin=null)
		self.signal_emit('before', process=process, loader=self)
		if self.silent and not self.read:
			while process.poll() is None:
				yield
				sleep(0.03)
		else:
			py3 = sys.version >= '3'
			selectlist = []
			if self.read:
				selectlist.append(process.stdout)
			if not self.silent:
				selectlist.append(process.stderr)
			while process.poll() is None:
				yield
				try:
					rd, _, __ = select.select(selectlist, [], [], 0.03)
					if rd:
						rd = rd[0]
						if rd == process.stderr:
							read = rd.readline()
							if py3:
								read = safeDecode(read)
							if read:
								self.fm.notify(read, bad=True)
						elif rd == process.stdout:
							read = rd.read(512)
							if py3:
								read = safeDecode(read)
							if read:
								self.stdout_buffer += read
				except select.error:
					sleep(0.03)
			if not self.silent:
				for l in process.stderr.readlines():
					if py3:
						l = safeDecode(l)
					self.fm.notify(l, bad=True)
			if self.read:
				read = process.stdout.read()
				if py3:
					read = safeDecode(read)
				self.stdout_buffer += read
		null.close()
		self.finished = True
		self.signal_emit('after', process=process, loader=self)

	def pause(self):
		if not self.finished and not self.paused:
			try:
				self.process.send_signal(20)
			except:
				pass
			Loadable.pause(self)
			self.signal_emit('pause', process=self.process, loader=self)

	def unpause(self):
		if not self.finished and self.paused:
			try:
				self.process.send_signal(18)
			except:
				pass
			Loadable.unpause(self)
			self.signal_emit('unpause', process=self.process, loader=self)

	def destroy(self):
		self.signal_emit('destroy', process=self.process, loader=self)
		if self.process:
			self.process.kill()


def safeDecode(string):
	try:
		return string.decode("utf-8")
	except (UnicodeDecodeError):
		if HAVE_CHARDET:
			return string.decode(chardet.detect(string)["encoding"])
		else:
			return ""


class Loader(FileManagerAware):
	seconds_of_work_time = 0.03
	throbber_chars = r'/-\|'
	throbber_paused = '#'
	paused = False

	def __init__(self):
		self.queue = deque()
		self.item = None
		self.load_generator = None
		self.throbber_status = 0
		self.rotate()
		self.old_item = None

	def rotate(self):
		"""Rotate the throbber"""
		# TODO: move all throbber logic to UI
		self.throbber_status = \
			(self.throbber_status + 1) % len(self.throbber_chars)
		self.status = self.throbber_chars[self.throbber_status]

	def add(self, obj):
		"""
		Add an object to the queue.
		It should have a load_generator method.
		"""
		while obj in self.queue:
			self.queue.remove(obj)
		self.queue.appendleft(obj)
		if self.paused:
			obj.pause()
		else:
			obj.unpause()

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
			if item.progressbar_supported:
				self.fm.ui.status.request_redraw()

	def pause(self, state):
		"""
		Change the pause-state to 1 (pause), 0 (no pause) or -1 (toggle)
		"""
		if state == -1:
			state = not self.paused
		elif state == self.paused:
			return

		self.paused = state

		if not self.queue:
			return

		if state:
			self.queue[0].pause()
		else:
			self.queue[0].unpause()

	def work(self):
		"""
		Load items from the queue if there are any.
		Stop after approximately self.seconds_of_work_time.
		"""
		if self.paused:
			self.status = self.throbber_paused
			return

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

		item.unpause()

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
			if item.progressbar_supported:
				self.fm.ui.status.request_redraw()
		except StopIteration:
			item.load_generator = None
			self.queue.remove(item)
			if item.progressbar_supported:
				self.fm.ui.status.request_redraw()
		except Exception as err:
			self.fm.notify(err)

	def has_work(self):
		"""Is there anything to load?"""
		return bool(self.queue)

	def destroy(self):
		while self.queue:
			self.queue.pop().destroy()
