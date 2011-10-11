# Copyright (C) 2010 David Barnett <davidbarnett2@gmail.com>
# Copyright (C) 2010, 2011  Roman Zimbelmann <romanz@lavabit.com>
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
A library to help to convert ANSI codes to curses instructions.
"""

from ranger.gui import color
import re

ansi_re = re.compile('(\x1b' + r'\[\d*(?:;\d+)*?[a-zA-Z])')
reset = '\x1b[0m'

def split_ansi_from_text(ansi_text):
	return ansi_re.split(ansi_text)

def text_with_fg_bg_attr(ansi_text):
	for chunk in split_ansi_from_text(ansi_text):
		if chunk and chunk[0] == '\x1b':
			if chunk[-1] != 'm':
				continue
			match = re.match(r'^.\[(.*).$', chunk)
			attr_args = match.group(1)
			fg, bg, attr = -1, -1, 0

			# Convert arguments to attributes/colors
			for arg in attr_args.split(';'):
				try:
					n = int(arg)
				except:
					if arg == '':
						n = 0
					else:
						continue
				if n == 0:
					fg, bg, attr = -1, -1, 0
				elif n == 1:
					attr |= color.bold
				elif n == 4:
					attr |= color.underline
				elif n == 5:
					attr |= color.blink
				elif n == 7:
					attr |= color.reverse
				elif n == 8:
					attr |= color.invisible
				elif n >= 30 and n <= 37:
					fg = n - 30
				elif n == 39:
					fg = -1
				elif n >= 40 and n <= 47:
					bg = n - 40
				elif n == 49:
					bg = -1
			yield (fg, bg, attr)
		else:
			yield chunk

def char_len(ansi_text):
	"""
	Count the number of visible characters.

	>>> char_len("\x1b[0;30;40mX\x1b[0m")
	1
	>>> char_len("\x1b[0;30;40mXY\x1b[0m")
	2
	>>> char_len("\x1b[0;30;40mX\x1b[0mY")
	2
	>>> char_len("hello")
	5
	>>> char_len("")
	0
	"""
	return len(ansi_re.sub('', ansi_text))

def char_slice(ansi_text, start, length):
	"""
	Slices a string with respect to ansi code sequences

	Acts as if the ansi codes aren't there, slices the text from the
	given start point to the given length and adds the codes back in.

	>>> test_string = "abcde\x1b[30mfoo\x1b[31mbar\x1b[0mnormal"
	>>> split_ansi_from_text(test_string)
	['abcde', '\\x1b[30m', 'foo', '\\x1b[31m', 'bar', '\\x1b[0m', 'normal']
	>>> char_slice(test_string, 1, 3)
	'bcd'
	>>> char_slice(test_string, 5, 6)
	'\\x1b[30mfoo\\x1b[31mbar'
	>>> char_slice(test_string, 0, 8)
	'abcde\\x1b[30mfoo'
	>>> char_slice(test_string, 4, 4)
	'e\\x1b[30mfoo'
	>>> char_slice(test_string, 11, 100)
	'\\x1b[0mnormal'
	>>> char_slice(test_string, 9, 100)
	'\\x1b[31mar\\x1b[0mnormal'
	>>> char_slice(test_string, 9, 4)
	'\\x1b[31mar\\x1b[0mno'
	"""
	chunks = []
	last_color = ""
	pos = old_pos = 0
	for i, chunk in enumerate(split_ansi_from_text(ansi_text)):
		if i % 2 == 1:
			last_color = chunk
			continue

		old_pos = pos
		pos += len(chunk)
		if pos <= start:
			pass # seek
		elif old_pos < start and pos >= start:
			chunks.append(last_color)
			chunks.append(chunk[start-old_pos:start-old_pos+length])
		elif pos > length + start:
			chunks.append(last_color)
			chunks.append(chunk[:start-old_pos+length])
		else:
			chunks.append(last_color)
			chunks.append(chunk)
		if pos - start >= length:
			break
	return ''.join(chunks)

if __name__ == '__main__':
	import doctest
	doctest.testmod()
