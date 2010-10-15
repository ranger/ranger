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

import curses.ascii
from string import ascii_lowercase

def parse_keybinding(obj):
	"""
	Translate a keybinding to a sequence of integers

	Example:
	lol<CR>   =>   (ord('l'), ord('o'), ord('l'), ord('\n'))
	          =>   (108, 111, 108, 10)
	x<A-Left> =>   (120, (27, curses.KEY_LEFT))
	"""
	assert isinstance(obj, (tuple, int, str))
	if isinstance(obj, tuple):
		for char in obj:
			yield char
	elif isinstance(obj, int):
		yield obj
	elif isinstance(obj, str):
		in_brackets = False
		bracket_content = None
		for char in obj:
			if in_brackets:
				if char == '>':
					in_brackets = False
					string = ''.join(bracket_content).lower()
					try:
						keys = special_keys[string]
						for key in keys:
							yield key
					except KeyError:
						yield ord('<')
						for c in bracket_content:
							yield ord(c)
						yield ord('>')
					except TypeError:
						yield keys  # it was no tuple, just an int
				else:
					bracket_content.append(char)
			else:
				if char == '<':
					in_brackets = True
					bracket_content = []
				else:
					yield ord(char)
		if in_brackets:
			yield ord('<')
			for c in bracket_content:
				yield ord(c)

# Arbitrary numbers which are not used with curses.KEY_XYZ
DIRKEY = 9001
ANYKEY = 9002
PASSIVE_ACTION = 9003

very_special_keys = {
	'dir': DIRKEY,
	'any': ANYKEY,
	'bg': PASSIVE_ACTION,
}

special_keys = {
	'bs': curses.KEY_BACKSPACE,
	'backspace': curses.KEY_BACKSPACE,
	'backspace2': curses.ascii.DEL,
	'delete': curses.KEY_DC,
	'cr': ord("\n"),
	'enter': ord("\n"),
	'return': ord("\n"),
	'space': ord(" "),
	'esc': curses.ascii.ESC,
	'escape': curses.ascii.ESC,
	'down': curses.KEY_DOWN,
	'up': curses.KEY_UP,
	'left': curses.KEY_LEFT,
	'right': curses.KEY_RIGHT,
	'pagedown': curses.KEY_NPAGE,
	'pageup': curses.KEY_PPAGE,
	'home': curses.KEY_HOME,
	'end': curses.KEY_END,
	'tab': ord('\t'),
	's-tab': curses.KEY_BTAB,
}

for key, val in tuple(special_keys.items()):
	special_keys['a-' + key] = (27, val)

for char in ascii_lowercase + '0123456789':
	special_keys['a-' + char] = (27, ord(char))

for char in ascii_lowercase:
	special_keys['c-' + char] = ord(char) - 96

for n in range(64):
	special_keys['f' + str(n)] = curses.KEY_F0 + n

special_keys.update(very_special_keys)
