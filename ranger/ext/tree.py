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

class Tree(object):
	def __init__(self, dictionary=None, parent=None, key=None):
		if dictionary is None:
			self._tree = dict()
		else:
			self._tree = dictionary
		self.key = key
		self.parent = parent

	def copy(self):
		"""Create a deep copy"""
		def deep_copy_dict(dct):
			dct = dct.copy()
			for key, val in dct.items():
				if isinstance(val, dict):
					dct[key] = deep_copy_dict(val)
			return dct
		newtree = Tree()
		if isinstance(self._tree, dict):
			newtree._tree = deep_copy_dict(self._tree)
		else:
			newtree._tree = self._tree
		return newtree

	def merge(self, other, copy=False):
		"""Merge another Tree into a copy of self"""
		def deep_merge(branch, otherbranch):
			assert isinstance(otherbranch, dict)
			if not isinstance(branch, dict):
				branch = dict()
			elif copy:
				branch = branch.copy()
			for key, val in otherbranch.items():
				if isinstance(val, dict):
					if key not in branch:
						branch[key] = None
					branch[key] = deep_merge(branch[key], val)
				else:
					branch[key] = val
			return branch

		if isinstance(self._tree, dict) and isinstance(other._tree, dict):
			content = deep_merge(self._tree, other._tree)
		elif copy and hasattr(other._tree, 'copy'):
			content = other._tree.copy()
		else:
			content = other._tree
		return type(self)(content)

	def set(self, keys, value, force=True):
		"""Sets the element at the end of the path to <value>."""
		if not isinstance(keys, (list, tuple)):
			keys = tuple(keys)
		if len(keys) == 0:
			self.replace(value)
		else:
			fnc = force and self.plow or self.traverse
			subtree = fnc(keys)
			subtree.replace(value)

	def unset(self, iterable):
		chars = list(iterable)
		first = True

		while chars:
			if first or isinstance(subtree, Tree) and subtree.empty():
				top = chars.pop()
				subtree = self.traverse(chars)
				del subtree._tree[top]
			else:
				break
			first = False

	def empty(self):
		return len(self._tree) == 0

	def replace(self, value):
		if self.parent:
			self.parent[self.key] = value
		self._tree = value

	def plow(self, iterable):
		"""Move along a path, creating nonexistant subtrees"""
		tree = self._tree
		last_tree = None
		char = None
		for char in iterable:
			try:
				newtree = tree[char]
				if not isinstance(newtree, dict):
					raise KeyError()
			except KeyError:
				newtree = dict()
				tree[char] = newtree
			last_tree = tree
			tree = newtree
		if isinstance(tree, dict):
			return type(self)(tree, parent=last_tree, key=char)
		else:
			return tree

	def traverse(self, iterable):
		"""Move along a path, raising exceptions when failed"""
		tree = self._tree
		last_tree = tree
		char = None
		for char in iterable:
			last_tree = tree
			try:
				tree = tree[char]
			except TypeError:
				raise KeyError("trying to enter leaf")
			except KeyError:
				raise KeyError(repr(char) + " not in tree " + str(tree))
		if isinstance(tree, dict):
			return type(self)(tree, parent=last_tree, key=char)
		else:
			return tree

	__getitem__ = traverse
