# Copyright (C) 2010 David Barnett <davidbarnett2@gmail.com>
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

import re

ansi_re = re.compile('(\x1b' + r'\[\d+(?:;\d+)*?m)')

def split_ansi_from_text(ansi_text):
	return ansi_re.split(ansi_text)

def text_with_fg_bg(ansi_text):
	for chunk in split_ansi_from_text(ansi_text):
		if chunk.startswith('\x1b'):
			attr_text = re.match('\x1b' + r'\[(.*?)m', chunk).group(1)
			fg, bg = -1, -1
			for attr in attr_text.split(';'):
				m = re.match('^3(\d)$', attr)
				if m:
					fg = int(m.group(1))
				m = re.match('^4(\d)$', attr)
				if m:
					bg = int(m.group(1))
			yield (fg, bg)
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
