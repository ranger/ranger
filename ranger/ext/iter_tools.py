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

from collections import deque

def flatten(lst):
	"""
	Flatten an iterable.

	All contained tuples, lists, deques and sets are replaced by their
	elements and flattened as well.

	>>> l = [1, 2, [3, [4], [5, 6]], 7]
	>>> list(flatten(l))
	[1, 2, 3, 4, 5, 6, 7]
	>>> list(flatten(()))
	[]
	"""
	for elem in lst:
		if isinstance(elem, (tuple, list, set, deque)):
			for subelem in flatten(elem):
				yield subelem
		else:
			yield elem

def unique(iterable):
	"""
	Return an iterable of the same type which contains unique items.

	This function assumes that:
	type(iterable)(list(iterable)) == iterable
	which is true for tuples, lists and deques (but not for strings)

	>>> unique([1, 2, 3, 1, 2, 3, 4, 2, 3, 4, 1, 1, 2])
	[1, 2, 3, 4]
	>>> unique(('w', 't', 't', 'f', 't', 'w'))
	('w', 't', 'f')
	"""
	already_seen = []
	for item in iterable:
		if item not in already_seen:
			already_seen.append(item)
	return type(iterable)(already_seen)

if __name__ == '__main__':
	import doctest
	doctest.testmod()
