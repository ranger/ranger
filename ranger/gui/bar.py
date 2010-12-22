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

from ranger.ext.utfwidth import uwid

class Bar(object):
	left = None
	right = None
	gap = None

	def __init__(self, base_color_tag):
		self.left = BarSide(base_color_tag)
		self.right = BarSide(base_color_tag)
		self.gap = BarSide(base_color_tag)

	def add(self, *a, **kw):
		self.left.add(*a, **kw)

	def addright(self, *a, **kw):
		self.right.add(*a, **kw)

	def sumsize(self):
		return self.left.sumsize() + self.right.sumsize()

	def fixedsize(self):
		return self.left.fixedsize() + self.right.fixedsize()

	def shrink_by_removing(self, wid):
		leftsize = self.left.sumsize()
		rightsize = self.right.sumsize()
		sumsize = leftsize + rightsize

		# remove elemets from the left until it fits
		if sumsize > wid:
			while len(self.left) > 0:
				leftsize -= len(self.left.pop(-1).string)
				if leftsize + rightsize <= wid:
					break
			sumsize = leftsize + rightsize

			# remove elemets from the right until it fits
			if sumsize > wid:
				while len(self.right) > 0:
					rightsize -= len(self.right.pop(0).string)
					if leftsize + rightsize <= wid:
						break
				sumsize = leftsize + rightsize

		if sumsize < wid:
			self.fill_gap(' ', (wid - sumsize), gapwidth=True)

	def shrink_from_the_left(self, wid):
		fixedsize = self.fixedsize()
		if wid < fixedsize:
			raise ValueError("Cannot shrink down to that size by cutting")
		leftsize = self.left.sumsize()
		rightsize = self.right.sumsize()
		oversize = leftsize + rightsize - wid - 1
		if oversize <= 0:
			return self.fill_gap(' ', wid, gapwidth=False)
		nonfixed_items = self.left.nonfixed_items()

		# Shrink items to a minimum size of 1 until there is enough room.
		for item in self.left:
			if not item.fixed:
				itemlen = len(item)
				if oversize > itemlen - 1:
					item.cut_off_to(1)
					oversize -= (itemlen - 1)
				else:
					item.cut_off(oversize)
					break

	def fill_gap(self, char, wid, gapwidth=False):
		del self.gap[:]

		if not gapwidth:
			wid = wid - self.sumsize()

		if wid > 0:
			self.gap.add(char * wid, 'space')

	def combine(self):
		return self.left + self.gap + self.right


class BarSide(list):
	def __init__(self, base_color_tag):
		self.base_color_tag = base_color_tag

	def add(self, string, *lst, **kw):
		cs = ColoredString(string, self.base_color_tag, *lst)
		cs.__dict__.update(kw)
		self.append(cs)

	def add_space(self, n=1):
		self.add(' ' * n, 'space')

	def sumsize(self):
		return sum(len(item) for item in self)

	def fixedsize(self):
		n = 0
		for item in self:
			if item.fixed:
				n += len(item)
			else:
				n += 1
		return n

	def nonfixed_items(self):
		return sum(1 for item in self if not item.fixed)


class ColoredString(object):
	def __init__(self, string, *lst):
		self.string = string
		self.lst = lst
		self.fixed = False

	def cut_off(self, n):
		if n >= 1:
			self.string = self.string[:-n]

	def cut_off_to(self, n):
		self.string = self.string[:n]

	def __len__(self):
		return uwid(self.string)

	def __str__(self):
		return self.string
