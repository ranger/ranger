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

class LazyParser(object):
	"""Parse commands and extract information"""
	def __init__(self, line):
		self.line = line
		self._chunks = None
		self._rests = None
		self._rests_loaded = 0
		self._rests_gen_instance = None

		try:
			self.firstpart = line[:line.rindex(' ') + 1]
		except ValueError:
			self.firstpart = ''

	def chunk(self, n, otherwise=''):
		"""Chunks are pieces of the command seperated by spaces"""
		if self._chunks is None:
			self._chunks = line.split()

		if len(self._chunks) > n:
			return self._chunks[n]
		else:
			return otherwise

	def rest(self, n, otherwise=''):
		"""Rests are the strings which come after each word."""
		if self._rests is None:
			self._rests = list(self._rest_generator())
			# TODO: Don't calculate all the rest elements if not needed

		if len(self._rests) > n:
			return self._rests[n]
		else:
			return otherwise

	def _rest_generator(self):
		lastrest = self.line
		n = 0
		while n < len(lastrest):
			if lastrest[n] == ' ':
				n += 1
			else:
				yield lastrest[n:]
				n = lastrest.find(' ', n) + 1
				if n <= 0:
					break
				lastrest = lastrest[n:]
				n = 0

	def __add__(self, newpart):
		return self.firstpart + newpart
