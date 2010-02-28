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

class Accumulator(object):
	def __init__(self):
		self.pointer = 0
		self.pointed_obj = None

	def move(self, relative=0, absolute=None, pages=None, narg=None):
		i = self.pointer
		lst = self.get_list()
		if not lst:
			return self.pointer
		length = len(lst)

		if isinstance(absolute, int):
			if isinstance(narg, int):
				absolute = narg
			if absolute < 0: # wrap
				i = absolute + length
			else:
				i = absolute

		if relative != 0:
			if isinstance(pages, int):
				relative *= pages * self.get_height()
			if isinstance(narg, int):
				relative *= narg
		i = int(i + relative)

		if i >= length:
			i = length - 1
		if i < 0:
			i = 0

		self.pointer = i
		self.correct_pointer()
		return self.pointer

	def move_to_obj(self, arg, attr=None):
		if not arg:
			return

		lst = self.get_list()

		if not lst:
			return

		do_get_attr = isinstance(attr, str)

		good = arg
		if do_get_attr:
			try:
				good = getattr(arg, attr)
			except (TypeError, AttributeError):
				pass

		for obj, i in zip(lst, range(len(lst))):
			if do_get_attr:
				try:
					test = getattr(obj, attr)
				except AttributeError:
					continue
			else:
				test = obj

			if test == good:
				self.move(absolute=i)
				return True

		return self.move(absolute=self.pointer)

	def correct_pointer(self):
		lst = self.get_list()

		if not lst:
			self.pointer = 0
			self.pointed_obj = None

		else:
			i = self.pointer

			if i is None:
				i = 0
			if i >= len(lst):
				i = len(lst) - 1
			if i < 0:
				i = 0

			self.pointer = i
			self.pointed_obj = lst[i]

	def pointer_is_synced(self):
		lst = self.get_list()
		try:
			return lst[self.pointer] == self.pointed_obj
		except (IndexError, KeyError):
			return False

	def sync_index(self, **kw):
		self.move_to_obj(self.pointed_obj, **kw)

	def get_list(self):
		"""OVERRIDE THIS"""
		return []

	def get_height(self):
		"""OVERRIDE THIS"""
		return 25
