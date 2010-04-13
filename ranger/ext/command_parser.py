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

import re
SETTINGS_RE = re.compile(r'^([^\s]+?)=(.*)$')

class LazyParser(object):
	"""Parse commands and extract information"""
	def __init__(self, line):
		self.line = line
		self._chunks = None
		self._rests = None
		self._setting_line = None
		self._rests_loaded = 0
		self._rests_gen_instance = None
		self._starts = None

		try:
			self.firstpart = line[:line.rindex(' ') + 1]
		except ValueError:
			self.firstpart = ''

	def chunk(self, n, otherwise=''):
		"""Chunks are pieces of the command seperated by spaces"""
		if self._chunks is None:
			self._chunks = self.line.split()

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

	def start(self, n):
		if self._starts is None:
			self._starts = ['']
			line = self.line
			result = ""
			while True:
				try:
					index = line.index(' ') + 1
				except:
					break
				if index == 1:
					continue
				result = line[:index]
				self._starts.append(result)
				line = line[index:]
		try:
			return self._starts[n]
		except:
			return self._starts[-1]

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

	def parse_setting_line(self):
		if self._setting_line is not None:
			return self._setting_line
		match = SETTINGS_RE.match(self.rest(1))
		if match:
			self.firstpart += match.group(1) + '='
			result = [match.group(1), match.group(2), True]
		else:
			result = [self.chunk(1), self.rest(2), ' ' in self.rest(1)]
		self._setting_line = result
		return result

	def __add__(self, newpart):
		return self.firstpart + newpart
