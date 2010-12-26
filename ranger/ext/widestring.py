# -*- encoding: utf8 -*-
# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
# Copyright (C) 2004, 2005  Timo Hirvonen
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
#
# ----
# This file contains portions of code from cmus (uchar.c).

import sys

ASCIIONLY = set(chr(c) for c in range(1, 128))
NARROW = 1
WIDE = 2

def _utf_char_to_int(string):
	# Squash the last 6 bits of each byte together to an integer
	if sys.version > '3':
		return ord(string)
	else:
		# THIS CODE IS INCORRECT
		u = 0
		for c in string:
			u = (u << 6) | (ord(c) & 0b00111111)
		return u

def utf_char_width_(u):
	if u < 0x1100:
		return NARROW
	# Hangul Jamo init. constonants
	if u <= 0x115F:
		return WIDE
	# Angle Brackets
	if u == 0x2329 or u == 0x232A:
		return WIDE
	if u < 0x2e80:
		return NARROW
	# CJK ... Yi
	if u < 0x302A:
		return WIDE
	if u <= 0x302F:
		return NARROW
	if u == 0x303F or u == 0x3099 or u == 0x309a:
		return NARROW
	# CJK ... Yi
	if u <= 0xA4CF:
		return WIDE
	# Hangul Syllables
	if u >= 0xAC00 and u <= 0xD7A3:
		return WIDE
	# CJK Compatibility Ideographs
	if u >= 0xF900 and u <= 0xFAFF:
		return WIDE
	# CJK Compatibility Forms
	if u >= 0xFE30 and u <= 0xFE6F:
		return WIDE
	# Fullwidth Forms
	if u >= 0xFF00 and u <= 0xFF60 or u >= 0xFFE0 and u <= 0xFFE6:
		return WIDE
	# CJK Extra Stuff
	if u >= 0x20000 and u <= 0x2FFFD:
		return WIDE
	# ?
	if u >= 0x30000 and u <= 0x3FFFD:
		return WIDE
	return NARROW  # invalid (?)

def uchars(string):
	if sys.version >= '3':
		return list(string)
	end = len(string)
	i = 0
	result = []
	while i < end:
		bytelen = utf_byte_length(string[i:])
		result.append(string[i:i+bytelen])
		i += bytelen
	return result


def utf_byte_length(string):
	"""Return the byte length of one utf character"""
	if sys.version >= '3':
		firstord = string.encode("utf-8")[0]
	else:
		firstord = ord(string[0])
	if firstord < 0b01111111:
		return 1
	if firstord < 0b10111111:
		return 1  # invalid
	if firstord < 0b11011111:
		return 2
	if firstord < 0b11101111:
		return 3
	if firstord < 0b11110100:
		return 4
	return 1  # invalid


def utf_char_width(string):
	"""Return the width of a single character"""
	u = _utf_char_to_int(string)
	return utf_char_width_(u)


def width(string):
	"""Return the width of a string"""
	end = len(string)
	i = 0
	width = 0
	while i < end:
		bytelen = utf_byte_length(string[i:])
		width += utf_char_width(string[i:i+bytelen])
		i += bytelen
	return width


def string_to_charlist(string):
	if not set(string) - ASCIIONLY:
		return list(string)
	end = len(string)
	i = 0
	result = []
	py3 = sys.version > '3'
	while i < end:
		if py3:
			result.append(string[i:i+1])
			i += 1
		else:
			bytelen = utf_byte_length(string[i:])
			result.append(string[i:i+bytelen])
			i += bytelen
		if utf_char_width_(_utf_char_to_int(result[-1])) == WIDE:
			result.append('')
	return result


class WideString(object):
	def __init__(self, string, chars=None):
		self.string = string
		if chars is None:
			self.chars = string_to_charlist(string)
		else:
			self.chars = chars

	def __add__(self, string):
		"""
		>>> (WideString("a") + WideString("b")).string
		'ab'
		>>> (WideString("a") + WideString("b")).chars
		['a', 'b']
		>>> (WideString("afd") + "bc").chars
		['a', 'f', 'd', 'b', 'c']
		"""
		if isinstance(string, str):
			return WideString(self.string + string)
		elif isinstance(string, WideString):
			return WideString(self.string + string.string,
					self.chars + string.chars)

	def __radd__(self, string):
		"""
		>>> ("bc" + WideString("afd")).chars
		['b', 'c', 'a', 'f', 'd']
		"""
		if isinstance(string, str):
			return WideString(string + self.string)
		elif isinstance(string, WideString):
			return WideString(string.string + self.string,
					string.chars + self.chars)

	def __str__(self):
		return self.string

	def __repr__(self):
		return '<' + self.__class__.__name__ + " '" + self.string + "'>"

	#def __getslice__(self, a, z):
		#"""
		#>>> WideString("asdf")[1:3]
		#<WideString 'sd'>
		#>>> WideString("モヒカン")[2:4]
		#<WideString 'ヒ'>
		#>>> WideString("モヒカン")[2:5]
		#<WideString 'ヒ '>
		#>>> WideString("モヒカン")[1:5]
		#<WideString ' ヒ '>
		#>>> WideString("モヒカン")[:]
		#<WideString 'モヒカン'>
		#>>> WideString("asdfモ")[0:6]
		#<WideString 'asdfモ'>
		#>>> WideString("asdfモ")[0:5]
		#<WideString 'asdf '>
		#>>> WideString("asdfモ")[0:4]
		#<WideString 'asdf'>
		#"""
		#if z is None or z >= len(self.chars):
			#z = len(self.chars) - 1
		#if a is None or a < 0:
			#a = 0
		#if z < len(self.chars) - 1 and self.chars[z] == '':
			#if self.chars[a] == '':
				#return WideString(' ' + ''.join(self.chars[a:z - 1]) + ' ')
			#return WideString(''.join(self.chars[a:z - 1]) + ' ')
		#if self.chars[a] == '':
			#return WideString(' ' + ''.join(self.chars[a:z - 1]))
		#return WideString(''.join(self.chars[a:z]))

	def __getslice__(self, a, z):
		"""
		>>> WideString("asdf")[1:3]
		<WideString 'sd'>
		>>> WideString("モヒカン")[2:4]
		<WideString 'ヒ'>
		>>> WideString("モヒカン")[2:5]
		<WideString 'ヒ '>
		>>> WideString("モabカン")[2:5]
		<WideString 'ab '>
		>>> WideString("モヒカン")[1:5]
		<WideString ' ヒ '>
		>>> WideString("モヒカン")[:]
		<WideString 'モヒカン'>
		>>> WideString("aモ")[0:3]
		<WideString 'aモ'>
		>>> WideString("aモ")[0:2]
		<WideString 'a '>
		>>> WideString("aモ")[0:1]
		<WideString 'a'>
		"""
		if z is None or z > len(self.chars):
			z = len(self.chars)
		if a is None or a < 0:
			a = 0
		if z < len(self.chars) and self.chars[z] == '':
			if self.chars[a] == '':
				return WideString(' ' + ''.join(self.chars[a:z - 1]) + ' ')
			return WideString(''.join(self.chars[a:z - 1]) + ' ')
		if self.chars[a] == '':
			return WideString(' ' + ''.join(self.chars[a:z - 1]))
		return WideString(''.join(self.chars[a:z]))

	def __getitem__(self, i):
		"""
		>>> WideString("asdf")[2]
		<WideString 'd'>
		>>> WideString("……")[0]
		<WideString '…'>
		>>> WideString("……")[1]
		<WideString '…'>
		"""
		if isinstance(i, slice):
			return self.__getslice__(i.start, i.stop)
		return self.__getslice__(i, i+1)

	def __len__(self):
		"""
		>>> len(WideString("poo"))
		3
		>>> len(WideString("モヒカン"))
		8
		"""
		return len(self.chars)


if __name__ == '__main__':
	import doctest
	doctest.testmod()
