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

NARROW = 1
WIDE = 2

def utf_byte_length(string):
	"""Return the byte length of one utf character"""
	firstord = ord(string[0])
	if firstord < 0x01111111:
		return 1
	if firstord < 0x10111111:
		return 0  # invalid
	if firstord < 0x11011111:
		return min(2, len(string))
	if firstord < 0x11101111:
		return min(3, len(string))
	if firstord < 0x11110100:
		return min(4, len(string))
	return 0  # invalid

def utf_char_width(string):
	# XXX
	u = _utf_char_to_int(string)
	if u < 0x1100:
		return NARROW
	else:
		return WIDE

def _utf_char_to_int(string):
	u = 0
	for c in string:
		u = (u << 6) | (ord(c) & 0b00111111)
	return u

def uwid(string):
	end = len(string)
	i = 0
	width = 0
	while i < end:
		bytelen = utf_byte_length(string[i:])
		if bytelen:
			width += utf_char_width(string[i:i+bytelen])
		else:
			width += 1
		i += bytelen
	return width
