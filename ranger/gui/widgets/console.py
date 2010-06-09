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

"""
The Console widget implements a vim-like console for entering
commands, searching and executing files.
"""

import string
import curses
from collections import deque

from . import Widget
from ranger.gui.widgets.console_mode import is_valid_mode, mode_to_class
from ranger import log, relpath_conf
from ranger.core.runner import ALLOWED_FLAGS
from ranger.ext.shell_escape import shell_quote
from ranger.ext.utfwidth import uwid
from ranger.container.keymap import CommandArgs
from ranger.ext.get_executables import get_executables
from ranger.ext.direction import Direction
from ranger.ext.utfwidth import uwid, uchars
from ranger.container import History
from ranger.container.history import HistoryEmptyException
import ranger

DEFAULT_HISTORY = 0
SEARCH_HISTORY = 1
QUICKOPEN_HISTORY = 2
OPEN_HISTORY = 3

class _CustomTemplate(string.Template):
	"""A string.Template subclass for use in the OpenConsole"""
	delimiter = '%'
	idpattern = '[a-z]'


class Console(Widget):
	mode = None
	visible = False
	last_cursor_mode = None
	prompt = ':'
	copy = ''
	tab_deque = None
	original_line = None
	history = None
	histories = None
	override = None
	allow_close = False
	historypaths = []

	def __init__(self, win):
		Widget.__init__(self, win)
		self.clear()
		self.histories = []
		# load histories from files
		if ranger.arg.clean:
			for i in range(4):
				self.histories.append(
						History(self.settings.max_console_history_size))
		else:
			self.historypaths = [relpath_conf(x) for x in \
				('history', 'history_search', 'history_qopen', 'history_open')]
			for i, path in enumerate(self.historypaths):
				hist = History(self.settings.max_console_history_size)
				self.histories.append(hist)
				if ranger.arg.clean: continue
				try: f = open(path, 'r')
				except: continue
				for line in f:
					hist.add(line[:-1])
				f.close()

	def destroy(self):
		# save histories from files
		if ranger.arg.clean or not self.settings.save_console_history:
			return
		for i, path in enumerate(self.historypaths):
			try: f = open(path, 'w')
			except: continue
			for entry in self.histories[i]:
				f.write(entry + '\n')
			f.close()

	def init(self):
		"""override this. Called directly after class change"""

	def draw(self):
		if self.mode is None:
			return

		self.win.erase()
		self.addstr(0, 0, self.prompt)
		overflow = -self.wid + len(self.prompt) + uwid(self.line) + 1
		if overflow > 0: 
			#XXX: cut uft-char-wise, consider width
			self.addstr(self.line[overflow:])
		else:
			self.addstr(self.line)

	def finalize(self):
		try:
			xpos = uwid(self.line[0:self.pos]) + len(self.prompt)
			self.fm.ui.win.move(self.y, self.x + min(self.wid-1, xpos))
		except:
			pass

	def open(self, mode, string='', prompt=None):
		if not is_valid_mode(mode):
			return False
		if prompt is not None:
			assert isinstance(prompt, str)
			self.prompt = prompt
		elif 'prompt' in self.__dict__:
			del self.prompt

		cls = mode_to_class(mode)

		if self.last_cursor_mode is None:
			try:
				self.last_cursor_mode = curses.curs_set(1)
			except:
				pass
		self.mode = mode
		self.__class__ = cls
		self.history = self.histories[DEFAULT_HISTORY]
		self.init()
		self.allow_close = False
		self.tab_deque = None
		self.focused = True
		self.visible = True
		self.line = string
		self.pos = len(string)
		self.history.add('')
		return True

	def close(self):
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
		self.env.keymanager.use_context('console')
		self.env.key_append(key)
		kbuf = self.env.keybuffer
		cmd = kbuf.command

		if kbuf.failure:
			kbuf.clear()
			return
		elif not cmd:
			return

		self.env.cmd = cmd

		if cmd.function:
			try:
				cmd.function(CommandArgs.from_widget(self))
			except Exception as error:
				self.fm.notify(error)
			if kbuf.done:
				kbuf.clear()
		else:
			kbuf.clear()

	def type_key(self, key):
		self.tab_deque = None

		if isinstance(key, int):
			try:
				key = chr(key)
			except ValueError:
				return

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
			self.history.move(n)
			current = self.history.current()
			if self.line != current:
				self.line = self.history.current()
				self.pos = len(self.line)

	def add_to_history(self):
		self.history.fast_forward()
		self.history.modify(self.line)

	def move(self, **keywords):
		direction = Direction(keywords)
		if direction.horizontal():
			# Ensure that the pointer is moved utf-char-wise
			uc = uchars(self.line)
			upos = len(uchars(self.line[:self.pos]))
			newupos = direction.move(
					direction=direction.right(),
					minimum=0,
					maximum=len(uc) + 1,
					current=upos)
			self.pos = len(''.join(uc[:newupos]))

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

	def delete_word(self):
		self.tab_deque = None
		try:
			i = self.line.rindex(' ', 0, self.pos - 1) + 1
			self.line = self.line[:i] + self.line[self.pos:]
			self.pos = len(self.line)
		except ValueError:
			self.line = ''
			self.pos = 0
		self.on_line_change()

	def delete(self, mod):
		self.tab_deque = None
		if mod == -1 and self.pos == 0:
			if not self.line:
				self.close()
			return
		# Delete utf-char-wise
		uc = uchars(self.line)
		upos = len(uchars(self.line[:self.pos])) + mod
		left_part = ''.join(uc[:upos])
		self.pos = len(left_part)
		self.line = left_part + ''.join(uc[upos+1:])
		self.on_line_change()

	def execute(self):
		pass

	def tab(self):
		pass

	def on_line_change(self):
		pass


class ConsoleWithTab(Console):
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

	def _get_tab(self):
		"""
		Override this function in the subclass!

		It should return either a string, an iterable or None.
		If a string is returned, tabbing will result in the line turning
		into that string.
		If another iterable is returned, each tabbing will cycle through
		the elements of the iterable (which have to be strings).
		If None is returned, nothing will happen.
		"""

		return None


class CommandConsole(ConsoleWithTab):
	prompt = ':'

	def execute(self, cmd=None):
		self.allow_close = True
		if cmd is None:
			cmd = self._get_cmd()

		if cmd:
			try:
				cmd.execute()
			except Exception as error:
				self.fm.notify(error)

		if self.allow_close:
			self.close()

	def _get_cmd(self):
		try:
			command_class = self._get_cmd_class()
		except KeyError:
			self.fm.notify("Invalid command! Press ? for help.", bad=True)
		except:
			return None
		else:
			return command_class(self.line, self.mode)

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


class QuickCommandConsole(CommandConsole):
	"""
	The QuickCommandConsole is essentially the same as the
	CommandConsole, and includes one additional feature:
	After each letter you type, it checks whether the command as it
	stands there could be executed in a meaningful way, and if it does,
	run it right away.

	Example:
	>cd ..
	As you type the last dot, The console will recognize what you mean
	and enter the parent directory saving you the time of pressing enter.
	"""
	prompt = '>'
	def on_line_change(self):
		try:
			cls = self._get_cmd_class()
		except (KeyError, ValueError, IndexError):
			pass
		else:
			cmd = cls(self.line, self.mode)
			if cmd and cmd.quick():
				self.execute(cmd)


class SearchConsole(Console):
	prompt = '/'

	def init(self):
		self.history = self.histories[SEARCH_HISTORY]

	def execute(self):
		self.fm.search_file(self.line, regexp=True)
		self.close()


class OpenConsole(ConsoleWithTab):
	"""
	The Open Console allows you to execute shell commands:
	!vim *         will run vim and open all files in the directory.

	%f will be replaced with the basename of the highlighted file
	%s will be selected with all files in the selection

	There is a special syntax for more control:

	!d! mplayer    will run mplayer with flags (d means detached)
	!@ mplayer     will open the selected files with mplayer
			   (equivalent to !mplayer %s)

	Those two can be combinated:

	!d!@mplayer    will open the selection with a detached mplayer
				   (again, this is equivalent to !d!mplayer %s)

	For a list of other flags than "d", check chapter 2.5 of the documentation
	"""
	prompt = '!'

	def init(self):
		self.history = self.histories[OPEN_HISTORY]

	def execute(self):
		command, flags = self._parse()
		if not command and 'p' in flags:
			command = 'cat %f'
		if command:
			if _CustomTemplate.delimiter in command:
				command = self._substitute_metachars(command)
			self.fm.execute_command(command, flags=flags)
		self.close()

	def _get_tab(self):
		try:
			i = self.line.index('!')+1
		except ValueError:
			line = self.line
			start = ''
		else:
			line = self.line[i:]
			start = self.line[:i]

		try:
			position_of_last_space = line.rindex(" ")
		except ValueError:
			return (start + program + ' ' for program \
					in get_executables() if program.startswith(line))
		if position_of_last_space == len(line) - 1:
			return self.line + '%s '
		else:
			before_word, start_of_word = self.line.rsplit(' ', 1)
			return (before_word + ' ' + file.shell_escaped_basename \
					for file in self.fm.env.cwd.files \
					if file.shell_escaped_basename.startswith(start_of_word))

	def _substitute_metachars(self, command):
		macros = {}

		if self.fm.env.cf:
			macros['f'] = shell_quote(self.fm.env.cf.basename)
		else:
			macros['f'] = ''

		macros['s'] = ' '.join(shell_quote(fl.basename) \
				for fl in self.fm.env.get_selection())

		macros['c'] = ' '.join(shell_quote(fl.path)
				for fl in self.fm.env.copy)

		macros['t'] = ' '.join(shell_quote(fl.basename)
				for fl in self.fm.env.cwd.files
				if fl.realpath in self.fm.tags)

		if self.fm.env.cwd:
			macros['d'] = shell_quote(self.fm.env.cwd.path)
		else:
			macros['d'] = '.'

		return _CustomTemplate(command).safe_substitute(macros)

	def _parse(self):
		if '!' in self.line:
			flags, cmd = self.line.split('!', 1)
		else:
			flags, cmd = '', self.line

		add_selection = False
		if cmd.startswith('@'):
			cmd = cmd[1:]
			add_selection = True
		elif flags.startswith('@'):
			flags = flags[1:]
			add_selection = True

		if add_selection:
			cmd += ' ' + ' '.join(shell_quote(fl.basename) \
					for fl in self.env.get_selection())

		return (cmd, flags)


class QuickOpenConsole(ConsoleWithTab):
	"""
	The Quick Open Console allows you to open files with predefined programs
	and modes very quickly.  By adding flags to the command, you can specify
	precisely how the program is run, e.g. the d-flag will run it detached
	from the file manager.

	For a list of other flags than "d", check chapter 2.5 of the documentation

	The syntax is "open with: <application> <mode> <flags>".
	The parsing of the arguments is very flexible.  You can leave out one or
	more arguments (or even all of them) and it will fall back to default
	values.  You can switch the order as well.
	There is just one rule:

	If you supply the <application>, it has to be the first argument.

	Examples:

	open with: mplayer D     open the selection in mplayer, but not detached
	open with: 1             open it with the default handler in mode 1
	open with: d             open it detached with the default handler
	open with: p             open it as usual, but pipe the output to "less"
	open with: totem 1 Ds    open in totem in mode 1, will not detach the
							 process (flag D) but discard the output (flag s)
	"""

	prompt = 'open with: '

	def init(self):
		self.history = self.histories[QUICKOPEN_HISTORY]

	def execute(self):
		split = self.line.split()
		app, flags, mode = self._get_app_flags_mode()
		self.fm.execute_file(
				files = [self.env.cf],
				app = app,
				flags = flags,
				mode = mode )
		self.close()

	def _get_app_flags_mode(self):
		"""
		Extracts the application, flags and mode from
		a string entered into the "openwith_quick" console.
		"""
		# examples:
		# "mplayer d 1" => ("mplayer", "d", 1)
		# "aunpack 4" => ("aunpack", "", 4)
		# "p" => ("", "p", 0)
		# "" => None

		app = ''
		flags = ''
		mode = 0
		split = self.line.split()

		if len(split) == 0:
			pass

		elif len(split) == 1:
			part = split[0]
			if self._is_app(part):
				app = part
			elif self._is_flags(part):
				flags = part
			elif self._is_mode(part):
				mode = part

		elif len(split) == 2:
			part0 = split[0]
			part1 = split[1]

			if self._is_app(part0):
				app = part0
				if self._is_flags(part1):
					flags = part1
				elif self._is_mode(part1):
					mode = part1
			elif self._is_flags(part0):
				flags = part0
				if self._is_mode(part1):
					mode = part1
			elif self._is_mode(part0):
				mode = part0
				if self._is_flags(part1):
					flags = part1

		elif len(split) >= 3:
			part0 = split[0]
			part1 = split[1]
			part2 = split[2]

			if self._is_app(part0):
				app = part0
				if self._is_flags(part1):
					flags = part1
					if self._is_mode(part2):
						mode = part2
				elif self._is_mode(part1):
					mode = part1
					if self._is_flags(part2):
						flags = part2
			elif self._is_flags(part0):
				flags = part0
				if self._is_mode(part1):
					mode = part1
			elif self._is_mode(part0):
				mode = part0
				if self._is_flags(part1):
					flags = part1

		return app, flags, int(mode)

	def _get_tab(self):
		if ' ' not in self.line:
			all_apps = self.fm.apps.all()
			if all_apps:
				return (app for app in all_apps if app.startswith(self.line))

		return None

	def _is_app(self, arg):
		return self.fm.apps.has(arg) or \
			(not self._is_flags(arg) and arg in get_executables())

	def _is_flags(self, arg):
		return all(x in ALLOWED_FLAGS for x in arg)

	def _is_mode(self, arg):
		return all(x in '0123456789' for x in arg)
