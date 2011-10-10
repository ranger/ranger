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

"""
Directions provide convenient methods for movement operations.

Direction objects are handled just like dicts but provide
methods like up() and down() which give you the correct value
for the vertical direction, even if only the "up" or "down" key
has been defined.


>>> d = Direction(down=5)
>>> d.down()
5
>>> d.up()
-5
>>> bool(d.horizontal())
False
"""

class Direction(dict):
	def __init__(self, dictionary=None, **keywords):
		if dictionary is not None:
			dict.__init__(self, dictionary)
		else:
			dict.__init__(self, keywords)
		if 'to' in self:
			self['down'] = self['to']
			self['absolute'] = True

	def copy(self):
		return Direction(**self)

	def _get_bool(self, first, second, fallback=None):
		try: return self[first]
		except:
			try: return not self[second]
			except: return fallback

	def _get_direction(self, first, second, fallback=0):
		try: return self[first]
		except:
			try: return -self[second]
			except: return fallback

	def up(self):
		return -Direction.down(self)

	def down(self):
		return Direction._get_direction(self, 'down', 'up')

	def right(self):
		return Direction._get_direction(self, 'right', 'left')

	def absolute(self):
		return Direction._get_bool(self, 'absolute', 'relative')

	def left(self):
		return -Direction.right(self)

	def relative(self):
		return not Direction.absolute(self)

	def vertical_direction(self):
		down = Direction.down(self)
		return (down > 0) - (down < 0)

	def horizontal_direction(self):
		right = Direction.right(self)
		return (right > 0) - (right < 0)

	def vertical(self):
		return set(self) & set(['up', 'down'])

	def horizontal(self):
		return set(self) & set(['left', 'right'])

	def pages(self):
		return 'pages' in self and self['pages']

	def percentage(self):
		return 'percentage' in self and self['percentage']

	def multiply(self, n):
		for key in ('up', 'right', 'down', 'left'):
			try:
				self[key] *= n
			except:
				pass

	def set(self, n):
		for key in ('up', 'right', 'down', 'left'):
			if key in self:
				self[key] = n

	def move(self, direction, override=None, minimum=0, maximum=9999,
			current=0, pagesize=1, offset=0):
		"""
		Calculates the new position in a given boundary.

		Example:
		>>> d = Direction(pages=True)
		>>> d.move(direction=3)
		3
		>>> d.move(direction=3, current=2)
		5
		>>> d.move(direction=3, pagesize=5)
		15
		>>> # Note: we start to count at zero.
		>>> d.move(direction=3, pagesize=5, maximum=10)
		9
		>>> d.move(direction=9, override=2)
		18
		"""
		pos = direction
		if override is not None:
			if self.absolute():
				pos = override
			else:
				pos *= override
		if self.pages():
			pos *= pagesize
		elif self.percentage():
			pos *= maximum / 100.0
		if self.absolute():
			if pos < minimum:
				pos += maximum
		else:
			pos += current
		return int(max(min(pos, maximum + offset - 1), minimum))

	def select(self, lst, current, pagesize, override=None, offset=1):
		dest = self.move(direction=self.down(), override=override,
			current=current, pagesize=pagesize, minimum=0, maximum=len(lst))
		selection = lst[min(current, dest):max(current, dest) + offset]
		return dest + offset - 1, selection

if __name__ == '__main__':
	import doctest
	doctest.testmod()
