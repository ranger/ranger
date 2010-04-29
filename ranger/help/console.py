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
3. Basic movement and browsing

3.1. Overview of all the Console Modes
3.2. List of Commands
3.3. The (Quick) Command Console
3.4. The Open Console


==============================================================================
3.1. Overview of all the Console Modes:

There are, as of now, five different types of consoles:

3.1.1. The Command Console, opened by pressing ":"
      Usable for entering commands like you know it from vim.
      Use the tab key to cycle through all available commands
      and press F1 to view the docstring of the current command.

3.1.2. The Quick Command Console, opened with ">"
      Works just like 3.1.1, but it saves you pressing <RETURN> by checking
      whether the current input can be executed in a meaningful way
      and doing so automatically.  (works with commands like cd, find.)

3.1.3. The Search Console, opened with "/"
      Very much like the console you get in vim after pressing "/".
      The current directory will be searched for files whose names
      match the given regular expression.

3.1.4. The Open Console, activated with "!"
      Similar to ":!..." in vim.  The given command will be executed,
      "%s" will be replaced with all the files in the selection,
      "%f" is replaced with only the current highlighted file.
      There are further options to tweak how the command is executed.

3.1.5. The Quick Open Console, opened by pressing "r"
      Rather than having to enter the full command, this console gives
      you a higher level interface to running files.
      You can define the application, the mode and the flags separated
      with spaces.


==============================================================================
3.2. List of Commands

This is a list of the few commands which are implemented by default.
All commands except for ":delete" can be abbreviated to the shortest
unambiguous name, e.g. ":chmod" can be written as ":ch" but not as ":c" since
it conflicts with ":cd".


:cd <dirname>
      Changes the directory to <dirname> *

:chmod <octal_number>
      Sets the permissions of the selection to the octal number.

:delete
      Deletes the current selection.
      "Selection" is defined as all the "marked files" (by default, you
      can mark files with space or v).  If there are no marked files,
      use the "current file" (where the cursor is)

:edit <filename>
      Opens the specified file in the text editor.

:eval <python_code>
      Evaluates the given code inside ranger. `fm' is a reference to
      the filemanager instance, `p' is a function to print text.

:filter <string>
      Displays only files which contain <string> in their basename.

:find <string>
      Look for a partial, case insensitive match in the filenames
      of the current directory and execute it if there is only
      one match. *

:grep <string>
      Looks for a string in all marked files or directory.
      (equivalent to "!grep [some options] -e <string> -r %s | less")

:mark <regexp>
      Mark all files matching a regular expression.

:unmark <regexp>
      Unmark all files matching a regular expression.

:mkdir <dirname>
      Creates a directory with the name <dirname>

:quit
      Exits ranger

:rename <newname>
      Changes the name of the currently highlighted file to <newname>

:terminal
      Spawns "x-terminal-emulator" starting in the current directory.

:touch <filename>
      Creates a file with the name <filename>

* implements handler for the Quick Command Console.


==============================================================================
3.3. The (Quick) Command Console

Open these consoles by pressing ":" or ">"

The Command Console and the "Quick" Command Console are mostly identical
since they share the commands.  As explained in 3.1.2, the point in using
the Quick Command Console is that the command is executed without the
need to press <RETURN> as soon as ranger thinks you want it executed.

Take the "find" command, for example.  It will attempt to find a file
or directory which matches the given input, and if there is one unambiguous
match, that file will be executed or that directory will be entered.
If you use the "find" command in the quick console, as soon as there is
one unambiguous match, <RETURN> will be pressed for you, giving you a
very fast way to browse your files.


All commands are defined in ranger/defaults/commands.py.  You can refer to this
file for a list of commands.  Implementing new commands should be intuitive:
Create a new class, a subclass of Command, and define the execute method
is usually enough.  For parsing command input, the command parser in
ranger/ext/command_parser.py is used.  The tab method should return None,
a string or an iterable sequence containing the strings which should be
cycled through by pressing tab.

Only those commands which implement the quick_open method will be specially
treated by the Quick Command Console.  For the rest, both consoles are equal.
quick_open is called after each key press and if it returns True, the
command will be executed immediately.


Pressing F1 inside the console displays the docstring of the current command
in the pager if docstrings are available (i.e.  unless python is run with
the flag "-OO" which removes all docstrings.)


==============================================================================
3.4. The Open Console

Open this console by pressing "!" or "s"

The Open Console allows you to execute shell commands:
!vim *         will run vim and open all files in the directory.

Like in similar filemanagers there are some macros.  Use them in
commands and they will be replaced with a list of files.
	%f	the highlighted file
	%d	the path of the current directory
	%s	the selected files in the current directory
	%t	all tagged files in the current directory
	%c	the full paths of the currently copied/cut files

%c is the only macro which ranges out of the current directory. So you may
"abuse" the copying function for other purposes, like diffing two files which
are in different directories:

	Yank the file A (type yy), move to the file B and use:
	!p!diff %c %f

There is a special syntax for more control:

!d! mplayer    will run mplayer with flags (d means detached)
!@ mplayer     will open the selected files with mplayer
	       (equivalent to !mplayer %s)

Those two can be combinated:

!d!@mplayer    will open the selection with a detached mplayer
               (again, this is equivalent to !d!mplayer %s)

This keys open the console with a predefined text:
	@	"!@"	Good for things like "@mount"
	#	"!p!"	For commands with output.
			Note: A plain "!p!" will be translated to "!p!cat %f"

For a list of other flags than "d", check chapter 2.5 of the documentation


==============================================================================
3.5. The Quick Open Console

Open this console by pressing "r"

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


==============================================================================
"""
# vim:tw=78:sw=8:sts=8:ts=8:ft=help
