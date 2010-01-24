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
