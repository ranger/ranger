# ===================================================================
# This configuration file contains custom commands.  It's all in python;
# lines beginning with # are comments.
#
# Scroll down for a few examples.
#
# Every class defined here which is a subclass of `Command' will be used as a
# command in ranger.  Several methods are defined to interface with ranger:
#   execute(): called when the command is executed.
#   cancel():  called when closing the console.
#   tab():     called when <TAB> is pressed.
#   quick():   called after each keypress.
#
# The return values for tab() can be either:
#   None: There is no tab completion
#   A string: Change the console to this string
#   A list/tuple/generator: cycle through every item in it
#
# The return value for quick() can be:
#   False: Nothing happens
#   True: Execute the command afterwards
#
# The return value for execute() and cancel() doesn't matter.
#
# ===================================================================
# Commands have certain attributes and methods that facilitate parsing of
# the arguments:
#
# self.line: The whole line that was written in the console.
# self.args: A list of all (space-separated) arguments to the command.
# self.quantifier: If this command was mapped to the key "X" and
#      the user pressed 6X, self.quantifier will be 6.
# self.arg(n): The n-th argument, or an empty string if it doesn't exist.
# self.rest(n): The n-th argument plus everything that followed.  For example,
#      If the command was "search foo bar a b c", rest(2) will be "bar a b c"
# self.start(n): The n-th argument and anything before it.  For example,
#      If the command was "search foo bar a b c", rest(2) will be "bar a b c"
#
# ===================================================================
# And this is a little reference for common ranger functions and objects:
#
# self.fm: A reference to the "fm" object which contains most information
#      about ranger.
# self.fm.notify(string): Print the given string on the screen.
# self.fm.notify(string, bad=True): Print the given string in RED.
# self.fm.reload_cwd(): Reload the current working directory.
# self.fm.env.cwd: The current working directory. (A File object.)
# self.fm.env.cf: The current file. (A File object too.)
# self.fm.env.cwd.get_selection(): A list of all selected files.
# self.fm.execute_console(string): Execute the string as a ranger command.
# self.fm.open_console(string): Open the console with the given string
#      already typed in for you.
# self.fm.move(direction): Moves the cursor in the given direction, which
#      can be something like down=3, up=5, right=1, left=1, to=6, ...
#
# File objects (for example self.fm.env.cf) have these useful attributes and
# methods:
#
# cf.path: The path to the file.
# cf.basename: The base name only.
# cf.load_content(): Force a loading of the directories content (which
#      obviously works with directories only)
# cf.is_directory: True/False depending on whether it's a directory.
#
# For advanced commands it is unavoidable to dive a bit into the source code
# of ranger.
# ===================================================================
# Here are some example commands:

from ranger.api.commands import *

#class tabnew(Command):
#	def execute(self):
#		self.fm.tab_new()

#class tabgo(Command):
#	""" Go to the n-th tab. """
#	def execute(self):
#		num = self.line.split()[1]
#		self.fm.tab_open(int(num))

#class terminal(Command):
#	"""
#	:terminal
#
#	Spawns an "x-terminal-emulator" starting in the current directory.
#	"""
#	def execute(self):
#		self.fm.run('x-terminal-emulator', flags='d')

#class edit(Command):
#	def execute(self):
#		if not self.arg(1):
#			self.fm.edit_file(self.fm.env.cf.path)
#		else:
#			self.fm.edit_file(self.rest(1))
#
#	def tab(self):
#		return self._tab_directory_content()

#class incremental_search(Command):
#	def quick(self):
#		self.fm.search_file(self.rest(1), regexp=True, offset=0)
