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

"""The Console widget implements a vim-like console for entering
commands, searching and executing files."""
import string
import curses
from collections import deque

from . import Widget
from ranger import commands
from ranger.gui.widgets.console_mode import is_valid_mode, mode_to_class
from ranger import log
from ranger.ext.shell_escape import shell_escape

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
	commandlist = None
	last_cursor_mode = 1
	prompt = ':'
	copy = ''
	tab_deque = None
	original_line = None
	history = None
	histories = None
	override = None

	def __init__(self, win):
		from ranger.container import CommandList, History
		Widget.__init__(self, win)
		self.commandlist = CommandList()
		self.settings.keys.initialize_console_commands(self.commandlist)
		self.clear()
		self.histories = [None] * 4
		self.histories[DEFAULT_HISTORY] = History()
		self.histories[SEARCH_HISTORY] = History()
		self.histories[QUICKOPEN_HISTORY] = History()
		self.histories[OPEN_HISTORY] = History()
	
	def init(self):
		"""override this. Called directly after class change"""

	def draw(self):
		if self.mode is None:
			return
		
		self.win.erase()
		self.addstr(0, 0, self.prompt)
		self.addstr(self.line)

	def finalize(self):
		try:
			self.fm.ui.win.move(self.y,
					self.x + self.pos + len(self.prompt))
		except:
			pass

	def open(self, mode, string=''):
		if not is_valid_mode(mode):
			return False

		cls = mode_to_class(mode)

		self.last_cursor_mode = curses.curs_set(1)
		self.mode = mode
		self.__class__ = cls
		self.history = self.histories[DEFAULT_HISTORY]
		self.init()
		self.tab_deque = None
		self.focused = True
		self.visible = True
		self.line = string
		self.pos = len(string)
		self.history.add('')
		return True

	def close(self):
		curses.curs_set(self.last_cursor_mode)
		self.add_to_history()
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
		from curses.ascii import ctrl, ESC

		try:
			cmd = self.commandlist[self.env.keybuffer.tuple_with_numbers()]
		except KeyError:
			self.env.key_clear()
			return

		if cmd == self.commandlist.dummy_object:
			return

		try:
			cmd.execute_wrap(self)
		except Exception as error:
			self.fm.notify(error)
		self.env.key_clear()

	def type_key(self, key):
		self.tab_deque = None

		if isinstance(key, int):
			key = chr(key)

		if self.pos == len(self.line):
			self.line += key
		else:
			self.line = self.line[:self.pos] + key + self.line[self.pos:]

		self.pos += len(key)
		self.on_line_change()

	def history_move(self, n):
		from ranger.container.history import HistoryEmptyException
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

	def move(self, relative = 0, absolute = None):
		if absolute is not None:
			if absolute < 0:
				self.pos = len(self.line) + 1 + absolute
			else:
				self.pos = absolute

		self.pos = min(max(0, self.pos + relative), len(self.line))

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
		if mod == -1 and len(self.line) == 0:
			self.close()
		pos = self.pos + mod

		self.line = self.line[0:pos] + self.line[pos+1:]
		self.move(relative = mod)
		self.on_line_change()

	def execute(self):
		self.tab_deque = None
		self.close()

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
		if cmd is None:
			cmd = self._get_cmd()

		if cmd:
			try:
				cmd.execute()
			except Exception as error:
				self.fm.notify(error)

		Console.execute(self)

	def _get_cmd(self):
		command_class = self._get_cmd_class()
		if command_class:
			return command_class(self.line, self.mode)
		else:
			return None

	def _get_cmd_class(self):
		try:
			command_name = self.line.split()[0]
		except IndexError:
			return None

		try:
			return commands.by_name[command_name]
		except KeyError:
			return None
	
	def _get_tab(self):
		if ' ' in self.line:
			cmd = self._get_cmd()
			if cmd:
				return cmd.tab()
			else:
				return None

		return commands.command_generator(self.line)


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
		cmd = self._get_cmd()
		if cmd and cmd.quick_open():
			self.execute(cmd)


class SearchConsole(Console):
	prompt = '/'

	def init(self):
		self.history = self.histories[SEARCH_HISTORY]

	def execute(self):
		import re
		if self.fm.env.pwd:
			regexp = re.compile(self.line, re.L | re.U | re.I)
			self.fm.env.last_search = regexp
			if self.fm.search(order='search'):
				self.fm.env.cf = self.fm.env.pwd.pointed_obj
		Console.execute(self)


class OpenConsole(ConsoleWithTab):
	"""
	The OpenConsole allows you to execute shell commands:
	!vim *         will run vim and open all files in the directory.

	%f will be replaced with the basename of the highlighted file
	%s will be selected with all files in the selection

	There is a special syntax for more control:

	!d! mplayer    will run mplayer with flags (d means detached)
	!@ mplayer     will open the selected files with mplayer
	               (equivalent to !mplayer %s)

	those two can be combinated:

	!d!@mplayer    will open the selection with a detached mplayer

	For a list of other flags than "d", look at the documentation
	of ranger.applications.
	"""
	prompt = '!'

	def init(self):
		self.history = self.histories[OPEN_HISTORY]
	
	def execute(self):
		from ranger.applications import run
		from subprocess import STDOUT, PIPE
		command, flags = self._parse()
		if command:
			if _CustomTemplate.delimiter in command:
				command = self._substitute_metachars(command)
			log(command)
			self.fm.execute_command(command, flags=flags)
		Console.execute(self)

	def _get_tab(self):
		# for now, just add " %s"
		return self.line + ' %s'

	def _substitute_metachars(self, command):
		dct = {}

		if self.fm.env.cf:
			dct['f'] = shell_escape(self.fm.env.cf.basename)
		else:
			dct['f'] = ''

		dct['s'] = ' '.join(shell_escape(fl.basename) \
				for fl in self.fm.env.get_selection())

		return _CustomTemplate(command).safe_substitute(dct)
	
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
			cmd += ' ' + ' '.join(shell_escape(fl.basename) \
					for fl in self.env.get_selection())

		return (cmd, flags)


class QuickOpenConsole(ConsoleWithTab):
	"""
	The QuickOpenConsole allows you to open files with
	pre-defined programs and modes very quickly. By adding flags
	to the command, you can specify precisely how the program is run,
	ie. the d-flag will run it detached from the filemanager.
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
		Console.execute(self)

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
		return self.fm.apps.has(arg)

	def _is_flags(self, arg):
		from ranger.applications import ALLOWED_FLAGS
		return all(x in ALLOWED_FLAGS for x in arg)

	def _is_mode(self, arg):
		return all(x in '0123456789' for x in arg)
