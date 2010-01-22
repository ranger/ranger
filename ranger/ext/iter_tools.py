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

from collections import deque

def flatten(lst):
	"""
	Flatten an iterable.

	All contained tuples, lists, deques and sets are replaced by their
	elements and flattened as well.
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
	"""
	already_seen = []
	for item in iterable:
		if item not in already_seen:
			already_seen.append(item)
	return type(iterable)(already_seen)
