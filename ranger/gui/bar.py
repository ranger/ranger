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

	def shrink_by_cutting(self, wid):
		fixedsize = self.fixedsize()
		if wid < fixedsize:
			raise ValueError("Cannot shrink down to that size by cutting")

		leftsize = self.left.sumsize()
		rightsize = self.right.sumsize()
		nonfixed_items = self.left.nonfixed_items()

		itemsize = int(float(wid - rightsize - fixedsize) / nonfixed_items) + 1

		for item in self.left:
			if not item.fixed:
				item.cut_off_to(itemsize)

		self.fill_gap(' ', wid, gapwidth=False)

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
		if 'fixedsize' in kw:
			cs.fixed = kw['fixedsize']
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
	fixed = False

	def __init__(self, string, *lst):
		self.string = string
		self.lst = lst

	def cut_off(self, n):
		n = max(n, min(len(self.string), 1))
		self.string = self.string[:-n]

	def cut_off_to(self, n):
		self.string = self.string[:n]

	def __len__(self):
		return len(self.string)

	def __str__(self):
		return self.string
