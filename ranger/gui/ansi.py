# Copyright (C) 2010 David Barnett <davidbarnett2@gmail.com>
# Copyright (C) 2010  Roman Zimbelmann <romanz@lavabit.com>
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

from ranger.gui import color
import re

ansi_re = re.compile('(\033' + r'\[\d*(?:;\d+)*?[a-zA-Z])')
reset = '\033[0m'

def split_ansi_from_text(ansi_text):
	return ansi_re.split(ansi_text)

def text_with_fg_bg_attr(ansi_text):
	for chunk in split_ansi_from_text(ansi_text):
		if chunk and chunk[0] == '\033':
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
	return len(ansi_re.sub('', ansi_text))

def char_slice(ansi_text, start, end):
	slice_chunks = []
	# skip to start
	last_color = None
	skip_len_left = start
	len_left = end - start
	for chunk in split_ansi_from_text(ansi_text):
		m = ansi_re.match(chunk)
		if m:
			if chunk[-1] == 'm':
				last_color = chunk
		else:
			if skip_len_left > len(chunk):
				skip_len_left -= len(chunk)
			else:		# finished skipping to start
				if skip_len_left > 0:
					chunk = chunk[skip_len_left:]
				chunk_left = chunk[:len_left]
				if len(chunk_left):
					if last_color is not None:
						slice_chunks.append(last_color)
					slice_chunks.append(chunk_left)
					len_left -= len(chunk_left)
				if len_left == 0:
					break
	return ''.join(slice_chunks)
