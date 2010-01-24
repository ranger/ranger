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

class Tags(object):
	def __init__(self, filename):
		from os.path import isdir, exists, dirname, abspath, realpath, expanduser

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
