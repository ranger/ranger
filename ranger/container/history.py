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

class HistoryEmptyException(Exception):
	pass

class History(object):
	def __init__(self, maxlen = None):
		from collections import deque
		self.history = deque(maxlen = maxlen)
		self.history_forward = deque(maxlen = maxlen)
	
	def add(self, item):
		if len(self.history) == 0 or self.history[-1] != item:
			self.history.append(item)
			self.history_forward.clear()
	
	def modify(self, item):
		try:
			self.history[-1] = item
		except IndexError:
			raise HistoryEmptyException

	def __len__(self):
		return len(self.history)

	def current(self):
		try:
			return self.history[-1]
		except IndexError:
			raise HistoryEmptyException()

	def top(self):
		try:
			return self.history_forward[-1]
		except IndexError:
			try:
				return self.history[-1]
			except IndexError:
				raise HistoryEmptyException()

	def bottom(self):
		try:
			return self.history[0]
		except IndexError:
			raise HistoryEmptyException()

	def back(self):
		if len(self.history) > 1:
			self.history_forward.appendleft( self.history.pop() )
		return self.current()

	def move(self, n):
		if n > 0:
			return self.forward()
		if n < 0:
			return self.back()

	def __iter__(self):
		return self.history.__iter__()

	def next(self):
		return self.history.next()

	def forward(self):
		if len(self.history_forward) > 0:
			self.history.append( self.history_forward.popleft() )
		return self.current()

	def fast_forward(self):
		if self.history_forward:
			self.history.extend(self.history_forward)
			self.history_forward.clear()
