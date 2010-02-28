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

def to_string(i):
	try:
		return chr(i)
	except ValueError:
		return '?'

from collections import deque
from curses.ascii import ascii

ZERO = ord('0')
NINE = ord('9')

class KeyBuffer(object):
	def __init__(self):
		self.number = None
		self.queue = deque()
		self.queue_with_numbers = deque()

	def clear(self):
		"""Clear the keybuffer and restore the initial state"""
		self.number = None
		self.queue.clear()
		self.queue_with_numbers.clear()

	def append(self, key):
		"""
		Append a key to the keybuffer, or initial numbers to
		the number attribute.
		"""
		self.queue_with_numbers.append(key)

		if not self.queue and key >= ZERO and key <= NINE:
			if self.number is None:
				self.number = 0
			try:
				self.number = self.number * 10 + int(chr(key))
			except ValueError:
				return
		else:
			self.queue.append(key)

	def tuple_with_numbers(self):
		"""Get a tuple of ascii codes."""
		return tuple(self.queue_with_numbers)

	def tuple_without_numbers(self):
		"""
		Get a tuple of ascii codes.
		If the keybuffer starts with numbers, those will
		be left out. To access them, use keybuffer.number
		"""
		return tuple(self.queue)

	def __str__(self):
		"""returns a concatenation of all characters"""
		return "".join( map( to_string, self.queue_with_numbers ) )
