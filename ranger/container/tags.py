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

from os.path import isdir, exists, dirname, abspath, realpath, expanduser

class Tags(object):
	def __init__(self, filename):

		self._filename = realpath(abspath(expanduser(filename)))

		if isdir(dirname(self._filename)) and not exists(self._filename):
			open(self._filename, 'w')

		self.sync()

	def __contains__(self, item):
		return item in self.tags

	def add(self, *items):
		self.sync()
		for item in items:
			self.tags.add(item)
		self.dump()

	def remove(self, *items):
		self.sync()
		for item in items:
			try:
				self.tags.remove(item)
			except KeyError:
				pass
		self.dump()

	def toggle(self, *items):
		self.sync()
		for item in items:
			if item in self:
				try:
					self.tags.remove(item)
				except KeyError:
					pass
			else:
				self.tags.add(item)
		self.dump()

	def sync(self):
		try:
			f = open(self._filename, 'r')
		except OSError:
			pass
		else:
			self.tags = self._parse(f)
			f.close()

	def dump(self):
		try:
			f = open(self._filename, 'w')
		except OSError:
			pass
		else:
			self._compile(f)
			f.close()

	def _compile(self, f):
		for line in self.tags:
			f.write(line + '\n')

	def _parse(self, f):
		result = set()
		for line in f:
			result.add(line.strip())
		return result

	def __nonzero__(self):
		return True
	__bool__ = __nonzero__
