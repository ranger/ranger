# Copyright (C) 2009, 2010, 2011  Roman Zimbelmann <romanz@lavabit.com>
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
	def __init__(self, maxlen=None, unique=True):
		if isinstance(maxlen, History):
			self._history = list(maxlen._history)
			self._index = maxlen._index
			self.maxlen = maxlen.maxlen
			self.unique = maxlen.unique
		else:
			self._history = []
			self._index = 0
			self.maxlen = maxlen
			self.unique = unique

	def add(self, item):
		# Remove everything after index
		if self._index < len(self._history) - 2:
			del self._history[:self._index+1]
		# Remove Duplicates
		if self.unique:
			try:
				self._history.remove(item)
			except:
				pass
		else:
			if self._history and self._history[-1] == item:
				del self._history[-1]
		# Remove first if list is too long
		if len(self._history) > self.maxlen - 1:
			del self._history[0]
		# Append the item and fast forward
		self._history.append(item)
		self._index = len(self._history) - 1

	def modify(self, item, unique=False):
		if self._history and unique:
			try:
				self._history.remove(item)
				self._index -= 1
			except:
				pass
		try:
			self._history[self._index] = item
		except IndexError:
			self.add(item)

	def __len__(self):
		return len(self._history)

	def current(self):
		if self._history:
			return self._history[self._index]
		else:
			raise HistoryEmptyException

	def top(self):
		try:
			return self._history[-1]
		except IndexError:
			raise HistoryEmptyException()

	def bottom(self):
		try:
			return self._history[0]
		except IndexError:
			raise HistoryEmptyException()

	def back(self):
		self._index -= 1
		if self._index < 0:
			self._index = 0
		return self.current()

	def move(self, n):
		self._index += n
		if self._index > len(self._history) - 1:
			self._index = len(self._history) - 1
		if self._index < 0:
			self._index = 0
		return self.current()

	def search(self, string, n):
		if n != 0 and string:
			step = n > 0 and 1 or -1
			i = self._index
			steps_left = steps_left_at_start = int(abs(n))
			while steps_left:
				i += step
				if i >= len(self._history) or i < 0:
					break
				if self._history[i].startswith(string):
					steps_left -= 1
			if steps_left != steps_left_at_start:
				self._index = i
		return self.current()

	def __iter__(self):
		return self._history.__iter__()

	def next(self):
		return self._history.next()

	def forward(self):
		if self._history:
			self._index += 1
			if self._index > len(self._history) - 1:
				self._index = len(self._history) - 1
		else:
			self._index = 0
		return self.current()

	def fast_forward(self):
		if self._history:
			self._index = len(self._history) - 1
		else:
			self._index = 0

	def _left(self):  # used for unit test
		return self._history[0:self._index+1]
