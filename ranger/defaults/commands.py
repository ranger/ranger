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

'''
This is the default file for command definitions.

Each command is a subclass of `Command'.  Several methods are defined
to interface with the console:
	execute: call this method when the command is executed.
	tab: call this method when tab is pressed.
	quick: call this method after each keypress in the QuickCommandConsole.

The return values for tab() can be either:
	None: There is no tab completion
	A string: Change the console to this string
	A list/tuple/generator: cycle through every item in it
The return value for quick() can be:
	False: Nothing happens
	True: Execute the command afterwards
The return value for execute() doesn't matter.

If you want to add custom commands, you can create a file
~/.ranger/commands.py, add the line:
	from ranger.api.commands import *

and write some command definitions, for example:

	class tabnew(Command):
		def execute(self):
			self.fm.tab_new()

	class tabgo(Command):
		"""
		:tabgo <n>

		Go to the nth tab.
		"""
		def execute(self):
			num = self.line.split()[1]
			self.fm.tab_open(int(num))

For a list of all actions, check /ranger/core/actions.py.
'''

from ranger.api.commands import *

alias('e', 'edit')
alias('q', 'quit')
alias('q!', 'quit!')
alias('qall', 'quit!')

class cd(Command):
	"""
	:cd <dirname>

	The cd command changes the directory.
	The command 'cd -' is equivalent to typing ``.

	In the quick console, the directory will be entered without the
	need to press enter, as soon as there is one unambiguous match.
	"""

	def execute(self):
		line = parse(self.line)
		try:
			destination = line.rest(1)
		except IndexError:
			destination = '~'

		if destination == '-':
			self.fm.enter_bookmark('`')
		else:
			self.fm.cd(destination)

	def tab(self):
		return self._tab_only_directories()

	def quick(self):
		from os.path import isdir, join, normpath
		line = parse(self.line)
		cwd = self.fm.env.cwd.path

		rel_dest = line.rest(1)
		if not rel_dest:
			return False

		abs_dest = normpath(join(cwd, rel_dest))
		return rel_dest != '.' and isdir(abs_dest)


class find(Command):
	"""
	:find <string>

	The find command will attempt to find a partial, case insensitive
	match in the filenames of the current directory.

	In the quick command console, once there is one unambiguous match,
	the file will be run automatically.
	"""

	count = 0
	tab = Command._tab_directory_content

	def execute(self):
		if self.mode != cmode.COMMAND_QUICK:
			self._search()

		import re
		search = parse(self.line).rest(1)
		search = re.escape(search)
		self.fm.env.last_search = re.compile(search, re.IGNORECASE)
		self.fm.search_method = 'search'

		if self.count == 1:
			self.fm.move(right=1)
			self.fm.block_input(0.5)

	def quick(self):
		self._search()
		if self.count == 1:
			return True

	def _search(self):
		self.count = 0
		line = parse(self.line)
		cwd = self.fm.env.cwd
		try:
			arg = line.rest(1)
		except IndexError:
			return False

		deq = deque(cwd.files)
		deq.rotate(-cwd.pointer)
		i = 0
		case_insensitive = arg.lower() == arg
		for fsobj in deq:
			if case_insensitive:
				filename = fsobj.basename_lower
			else:
				filename = fsobj.basename
			if arg in filename:
				self.count += 1
				if self.count == 1:
					cwd.move(to=(cwd.pointer + i) % len(cwd.files))
					self.fm.env.cf = cwd.pointed_obj
			if self.count > 1:
				return False
			i += 1

		return self.count == 1


class set(Command):
	"""
	:set <option name>=<python expression>

	Gives an option a new value.
	"""
	def execute(self):
		line = parse(self.line)
		name = line.chunk(1)
		name, value, _ = line.parse_setting_line()
		if name and value:
			try:
				value = eval(value)
			except:
				pass
			self.fm.settings[name] = value

	def tab(self):
		line = parse(self.line)
		from ranger import log
		log(line.parse_setting_line())
		name, value, name_done = line.parse_setting_line()
		settings = self.fm.settings
		if not name:
			return (line + setting for setting in settings)
		if not value and not name_done:
			return (line + setting for setting in settings \
					if setting.startswith(name))
		if not value:
			return line + repr(settings[name])
		if bool in settings.types_of(name):
			if 'true'.startswith(value.lower()):
				return line + 'True'
			if 'false'.startswith(value.lower()):
				return line + 'False'


class quit(Command):
	"""
	:quit

	Closes the current tab.  If there is only one tab, quit the program.
	"""

	def execute(self):
		if len(self.fm.tabs) <= 1:
			self.fm.exit()
		self.fm.tab_close()


class quit_now(Command):
	"""
	:quit!

	Quits the program immediately.
	"""
	name = 'quit!'

	def execute(self):
		self.fm.exit()


class terminal(Command):
	"""
	:terminal

	Spawns an "x-terminal-emulator" starting in the current directory.
	"""
	def execute(self):
		self.fm.run('x-terminal-emulator', flags='d')


class delete(Command):
	"""
	:delete

	Tries to delete the selection.

	"Selection" is defined as all the "marked files" (by default, you
	can mark files with space or v). If there are no marked files,
	use the "current file" (where the cursor is)

	When attempting to delete non-empty directories or multiple
	marked files, it will require a confirmation: The last word in
	the line has to start with a 'y'.  This may look like:
	:delete yes
	:delete seriously? yeah!
	"""

	allow_abbrev = False

	def execute(self):
		line = parse(self.line)
		lastword = line.chunk(-1)

		if lastword.startswith('y'):
			# user confirmed deletion!
			return self.fm.delete()
		elif self.line.startswith(DELETE_WARNING):
			# user did not confirm deletion
			return

		cwd = self.fm.env.cwd
		cf = self.fm.env.cf

		if cwd.marked_items or (cf.is_directory and not cf.is_link \
				and len(os.listdir(cf.path)) > 0):
			# better ask for a confirmation, when attempting to
			# delete multiple files or a non-empty directory.
			return self.fm.open_console(self.mode, DELETE_WARNING)

		# no need for a confirmation, just delete
		self.fm.delete()


class mark(Command):
	"""
	:mark <regexp>

	Mark all files matching a regular expression.
	"""
	do_mark = True

	def execute(self):
		import re
		cwd = self.fm.env.cwd
		line = parse(self.line)
		input = line.rest(1)
		searchflags = re.UNICODE
		if input.lower() == input: # "smartcase"
			searchflags |= re.IGNORECASE 
		pattern = re.compile(input, searchflags)
		for fileobj in cwd.files:
			if pattern.search(fileobj.basename):
				cwd.mark_item(fileobj, val=self.do_mark)
		self.fm.ui.status.need_redraw = True
		self.fm.ui.need_redraw = True


class unmark(mark):
	"""
	:unmark <regexp>

	Unmark all files matching a regular expression.
	"""
	do_mark = False


class mkdir(Command):
	"""
	:mkdir <dirname>

	Creates a directory with the name <dirname>.
	"""

	def execute(self):
		from os.path import join, expanduser, lexists
		from os import mkdir

		line = parse(self.line)
		dirname = join(self.fm.env.cwd.path, expanduser(line.rest(1)))
		if not lexists(dirname):
			mkdir(dirname)
		else:
			self.fm.notify("file/directory exists!", bad=True)


class touch(Command):
	"""
	:touch <fname>

	Creates a file with the name <fname>.
	"""

	def execute(self):
		from os.path import join, expanduser, lexists
		from os import mkdir

		line = parse(self.line)
		fname = join(self.fm.env.cwd.path, expanduser(line.rest(1)))
		if not lexists(fname):
			open(fname, 'a')
		else:
			self.fm.notify("file/directory exists!", bad=True)


class edit(Command):
	"""
	:edit <filename>

	Opens the specified file in vim
	"""

	def execute(self):
		line = parse(self.line)
		self.fm.edit_file(line.rest(1))

	def tab(self):
		return self._tab_directory_content()


class eval_(Command):
	"""
	:eval <python code>

	Evaluates the python code.
	`fm' is a reference to the FM instance.
	To display text, use the function `p'.

	Examples:
	:eval fm
	:eval len(fm.env.directories)
	:eval p("Hello World!")
	"""
	name = 'eval'

	def execute(self):
		code = parse(self.line).rest(1)
		fm = self.fm
		p = fm.notify
		try:
			try:
				result = eval(code)
			except SyntaxError:
				exec(code)
			else:
				if result:
					p(result)
		except Exception as err:
			p(err)


class rename(Command):
	"""
	:rename <newname>

	Changes the name of the currently highlighted file to <newname>
	"""

	def execute(self):
		from ranger.fsobject.file import File
		line = parse(self.line)
		if not line.rest(1):
			return self.fm.notify('Syntax: rename <newname>', bad=True)
		self.fm.rename(self.fm.env.cf, line.rest(1))
		f = File(line.rest(1))
		self.fm.env.cwd.pointed_obj = f
		self.fm.env.cf = f

	def tab(self):
		return self._tab_directory_content()


class chmod(Command):
	"""
	:chmod <octal number>

	Sets the permissions of the selection to the octal number.

	The octal number is between 0 and 777. The digits specify the
	permissions for the user, the group and others.

	A 1 permits execution, a 2 permits writing, a 4 permits reading.
	Add those numbers to combine them. So a 7 permits everything.
	"""

	def execute(self):
		line = parse(self.line)
		mode = line.rest(1)

		try:
			mode = int(mode, 8)
			if mode < 0 or mode > 0o777:
				raise ValueError
		except ValueError:
			self.fm.notify("Need an octal number between 0 and 777!", bad=True)
			return

		for file in self.fm.env.get_selection():
			try:
				os.chmod(file.path, mode)
			except Exception as ex:
				self.fm.notify(ex)

		try:
			# reloading directory.  maybe its better to reload the selected
			# files only.
			self.fm.env.cwd.load_content()
		except:
			pass


class filter(Command):
	"""
	:filter <string>

	Displays only the files which contain <string> in their basename.
	"""

	def execute(self):
		line = parse(self.line)
		self.fm.set_filter(line.rest(1))
		self.fm.reload_cwd()


class grep(Command):
	"""
	:grep <string>

	Looks for a string in all marked files or directories
	"""

	def execute(self):
		line = parse(self.line)
		if line.rest(1):
			action = ['grep', '--color=always', '--line-number']
			action.extend(['-e', line.rest(1), '-r'])
			action.extend(f.path for f in self.fm.env.get_selection())
			self.fm.execute_command(action, flags='p')
