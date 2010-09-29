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

try:
	from sys import maxint
except:
	from sys import maxsize as maxint

NARROW = 1
WIDE = 2

def uwid(string, count=maxint):
	"""Return the width of a string"""
	try:
		string = string.decode('utf8', 'replace')
	except AttributeError:
		pass
	width = 0
	for c in string:
		width += utf_char_width(c)
		count -= 1
		if not count:
			break
	return width

def uchars(string):
	"""Return a list with one string for each character"""
	try:
		string = string.decode('utf-8', 'replace')
	except AttributeError:
		pass
	return list(string)
	result = []
	while i < end:
		bytelen = utf_byte_length(string[i:])
		result.append(string[i:i+bytelen])
		i += bytelen
	return result

def uwidslice(string, start=0, end=maxint):
	chars = []
	for c in uchars(string):
		c_wid = utf_char_width(c)
		if c_wid == NARROW:
			chars.append(c)
		elif c_wid == WIDE:
			chars.append("")
			chars.append(c)
	return "".join(chars[start:end])

def utf_char_width(string):
	"""Return the width of a single character"""
	u = ord(string)
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
