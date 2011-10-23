# Copyright (C) 2009, 2010, 2011  Roman Zimbelmann <romanz@lavabit.com>
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
The Console widget implements a vim-like console for entering
commands, searching and executing files.
"""

import curses
import re
from collections import deque

from . import Widget
from ranger.ext.direction import Direction
from ranger.ext.widestring import uwid, WideString
from ranger.container.history import History, HistoryEmptyException
import ranger

class Console(Widget):
	visible = False
	last_cursor_mode = None
	history_search_pattern = None
	prompt = ':'
	copy = ''
	tab_deque = None
	original_line = None
	history = None
	history_backup = None
	override = None
	allow_close = False
	historypath = None

	def __init__(self, win):
		Widget.__init__(self, win)
		self.clear()
		self.history = History(self.settings.max_console_history_size)
		# load history from files
		if not ranger.arg.clean:
			self.historypath = self.fm.confpath('history')
			try:
				f = open(self.historypath, 'r')
			except:
				pass
			else:
				for line in f:
					self.history.add(line[:-1])
				f.close()
		self.history_backup = History(self.history)

	def destroy(self):
		# save history to files
		if ranger.arg.clean or not self.settings.save_console_history:
			return
		if self.historypath:
			try:
				f = open(self.historypath, 'w')
			except:
				pass
			else:
				for entry in self.history_backup:
					f.write(entry + '\n')
				f.close()

	def draw(self):
		self.win.erase()
		self.addstr(0, 0, self.prompt)
		line = WideString(self.line)
		overflow = -self.wid + len(self.prompt) + len(line) + 1
		if overflow > 0: 
			self.addstr(0, len(self.prompt), str(line[overflow:]))
		else:
			self.addstr(0, len(self.prompt), self.line)

	def finalize(self):
		try:
			pos = uwid(self.line[0:self.pos]) + len(self.prompt)
			self.fm.ui.win.move(self.y, self.x + min(self.wid-1, pos))
		except:
			pass

	def open(self, string='', prompt=None, position=None):
		if prompt is not None:
			assert isinstance(prompt, str)
			self.prompt = prompt
		elif 'prompt' in self.__dict__:
			del self.prompt

		if self.last_cursor_mode is None:
			try:
				self.last_cursor_mode = curses.curs_set(1)
			except:
				pass
		self.allow_close = False
		self.tab_deque = None
		self.focused = True
		self.visible = True
		self.unicode_buffer = ""
		self.line = string
		self.history_search_pattern = self.line
		self.pos = len(string)
		if position is not None:
			self.pos = min(self.pos, position)
		self.history_backup.fast_forward()
		self.history = History(self.history_backup)
		self.history.add('')
		return True

	def close(self, trigger_cancel_function=True):
		if trigger_cancel_function:
			cmd = self._get_cmd(quiet=True)
			if cmd:
				try:
					cmd.cancel()
				except Exception as error:
					self.fm.notify(error)
		if self.last_cursor_mode is not None:
			try:
				curses.curs_set(self.last_cursor_mode)
			except:
				pass
			self.last_cursor_mode = None
		self.add_to_history()
		self.tab_deque = None
		self.clear()
		self.__class__ = Console
		self.focused = False
		self.visible = False
		if hasattr(self, 'on_close'):
			self.on_close()

	def clear(self):
		self.pos = 0
		self.line = ''

	def press(self, key):
		self.env.keymaps.use_keymap('console')
		if not self.fm.ui.press(key):
			self.type_key(key)

	def type_key(self, key):
		self.tab_deque = None

		if isinstance(key, int):
			try:
				key = chr(key)
			except ValueError:
				return

		if self.fm.py3:
			self.unicode_buffer += key
			try:
				decoded = self.unicode_buffer.encode("latin-1").decode("utf-8")
			except UnicodeDecodeError:
				return
			except UnicodeEncodeError:
				return
			else:
				self.unicode_buffer = ""
				if self.pos == len(self.line):
					self.line += decoded
				else:
					pos = self.pos
					self.line = self.line[:pos] + decoded + self.line[pos:]
				self.pos += len(decoded)
		else:
			if self.pos == len(self.line):
				self.line += key
			else:
				self.line = self.line[:self.pos] + key + self.line[self.pos:]
			self.pos += len(key)

		self.on_line_change()

	def history_move(self, n):
		try:
			current = self.history.current()
		except HistoryEmptyException:
			pass
		else:
			if self.line != current and self.line != self.history.top():
				self.history.modify(self.line)
			if self.history_search_pattern:
				self.history.search(self.history_search_pattern, n)
			else:
				self.history.move(n)
			current = self.history.current()
			if self.line != current:
				self.line = self.history.current()
				self.pos = len(self.line)

	def add_to_history(self):
		self.history_backup.fast_forward()
		self.history_backup.add(self.line)
		self.history = History(self.history_backup)

	def move(self, **keywords):
		direction = Direction(keywords)
		if direction.horizontal():
			# Ensure that the pointer is moved utf-char-wise
			if self.fm.py3:
				self.pos = direction.move(
						direction=direction.right(),
						minimum=0,
						maximum=len(self.line) + 1,
						current=self.pos)
			else:
				if self.fm.py3:
					uc = list(self.line)
					upos = len(self.line[:self.pos])
				else:
					uc = list(self.line.decode('utf-8', 'ignore'))
					upos = len(self.line[:self.pos].decode('utf-8', 'ignore'))
				newupos = direction.move(
						direction=direction.right(),
						minimum=0,
						maximum=len(uc) + 1,
						current=upos)
				self.pos = len(''.join(uc[:newupos]).encode('utf-8', 'ignore'))

	def delete_rest(self, direction):
		self.tab_deque = None
		if direction > 0:
			self.copy = self.line[self.pos:]
			self.line = self.line[:self.pos]
		else:
			self.copy = self.line[:self.pos]
			self.line = self.line[self.pos:]
			self.pos = 0
		self.on_line_change()

	def paste(self):
		if self.pos == len(self.line):
			self.line += self.copy
		else:
			self.line = self.line[:self.pos] + self.copy + self.line[self.pos:]
		self.pos += len(self.copy)
		self.on_line_change()

	def delete_word(self, backward=True):
		if self.line:
			self.tab_deque = None
			if backward:
				right_part = self.line[self.pos:]
				i = self.pos - 2
				while i >= 0 and re.match(r'[\w\d]', self.line[i], re.U):
					i -= 1
				self.copy = self.line[i + 1:self.pos]
				self.line = self.line[:i + 1] + right_part
				self.pos = i + 1
			else:
				left_part = self.line[:self.pos]
				i = self.pos + 1
				while i < len(self.line) and re.match(r'[\w\d]', self.line[i], re.U):
					i += 1
				self.copy = self.line[self.pos:i]
				if i >= len(self.line):
					self.line = left_part
					self.pos = len(self.line)
				else:
					self.line = left_part + self.line[i:]
					self.pos = len(left_part)
			self.on_line_change()

	def delete(self, mod):
		self.tab_deque = None
		if mod == -1 and self.pos == 0:
			if not self.line:
				self.close(trigger_cancel_function=False)
			return
		# Delete utf-char-wise
		if self.fm.py3:
			left_part = self.line[:self.pos + mod]
			self.pos = len(left_part)
			self.line = left_part + self.line[self.pos + 1:]
		else:
			uc = list(self.line.decode('utf-8', 'ignore'))
			upos = len(self.line[:self.pos].decode('utf-8', 'ignore')) + mod
			left_part = ''.join(uc[:upos]).encode('utf-8', 'ignore')
			self.pos = len(left_part)
			self.line = left_part + ''.join(uc[upos+1:]).encode('utf-8', 'ignore')
		self.on_line_change()

	def execute(self, cmd=None):
		self.allow_close = True
		self.fm.execute_console(self.line)
		if self.allow_close:
			self.close(trigger_cancel_function=False)

	def _get_cmd(self, quiet=False):
		try:
			command_class = self._get_cmd_class()
		except KeyError:
			if not quiet:
				error = "Command not found: `%s'" % self.line.split()[0]
				self.fm.notify(error, bad=True)
		except:
			return None
		else:
			return command_class(self.line)

	def _get_cmd_class(self):
		return self.fm.commands.get_command(self.line.split()[0])

	def _get_tab(self):
		if ' ' in self.line:
			cmd = self._get_cmd()
			if cmd:
				return cmd.tab()
			else:
				return None

		return self.fm.commands.command_generator(self.line)

	def tab(self, n=1):
		if self.tab_deque is None:
			tab_result = self._get_tab()

			if isinstance(tab_result, str):
				self.line = tab_result
				self.pos = len(tab_result)
				self.on_line_change()

			elif tab_result == None:
				pass

			elif hasattr(tab_result, '__iter__'):
				self.tab_deque = deque(tab_result)
				self.tab_deque.appendleft(self.line)

		if self.tab_deque is not None:
			self.tab_deque.rotate(-n)
			self.line = self.tab_deque[0]
			self.pos = len(self.line)
			self.on_line_change()

	def on_line_change(self):
		self.history_search_pattern = self.line
		try:
			cls = self._get_cmd_class()
		except (KeyError, ValueError, IndexError):
			pass
		else:
			cmd = cls(self.line)
			if cmd and cmd.quick():
				self.execute(cmd)
