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

class NoDefault(object):
	pass

class Direction(object):
	"""An object with a down and right method"""
	def __init__(self, right=None, down=None, absolute=False,
			percent=False, pages=False, **keywords):
		self.has_explicit_direction = False

		if 'up' in keywords:
			self.down = -keywords['up']
		else:
			self.down = down

		if 'left' in keywords:
			self.right = -keywords['left']
		else:
			self.right = right

		if 'relative' in keywords:
			self.absolute = not relative
		else:
			self.absolute = absolute

		if 'default' in keywords:
			self.default = keywords['default']
		else:
			self.default = NoDefault

		self.original_down = self.down
		self.original_right = self.right

		self.percent = percent
		self.pages = pages
	
	@property
	def up(self):
		if self.down is None:
			return None
		return -self.down

	@property
	def left(self):
		if self.right is None:
			return None
		return -self.right

	@property
	def relative(self):
		return not self.absolute

	def down_or_default(self, default):
		if self.has_been_modified:
			return self.down
		return default

	def steps_down(self, page_length=10):
		if self.pages:
			return self.down * page_length
		else:
			return self.down

	def steps_right(self, page_length=10):
		if self.pages:
			return self.right * page_length
		else:
			return self.right

	def copy(self):
		new = type(self)()
		new.__dict__.update(self.__dict__)
		return new

	def __mul__(self, other):
		copy = self.copy()
		if self.absolute:
			if self.down is not None:
				copy.down = other
			if self.right is not None:
				copy.right = other
		else:
			if self.down is not None:
				copy.down *= other
			if self.right is not None:
				copy.right *= other
		copy.original_down = self.original_down
		copy.original_right = self.original_right
		return copy
	__rmul__ = __mul__

	def __str__(self):
		s = ['<Direction']
		if self.down is not None:
			s.append(" down=" + str(self.down))
		if self.right is not None:
			s.append(" right=" + str(self.right))
		if self.absolute:
			s.append(" absolute")
		else:
			s.append(" relative")
		if self.pages:
			s.append(" pages")
		if self.percent:
			s.append(" percent")
		s.append('>')
		return ''.join(s)
