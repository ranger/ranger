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
