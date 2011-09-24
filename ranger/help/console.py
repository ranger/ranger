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
3. The Console

3.1. General Information
3.2. List of Commands
3.3. Macros
3.4. The more complicated Commands in Detail

==============================================================================
3.1. General Information

The console is opened by pressing ":".  Press <TAB> to cycle through all
available commands and press <F1> to view help about the current command.

All commands are defined in the file ranger/defaults/commands.py, which
also contains a detailed specification.


==============================================================================
3.2. List of Commands

All commands except for ":delete" can be abbreviated with the shortest
unambiguous name, e.g. ":chmod" can be written as ":ch" but not as ":c" since
it conflicts with ":cd".


:bulkrename
      This command opens a list of selected files in an external editor.
      After you edit and save the file, it will generate a shell script which
      does bulk renaming according to the changes you did in the file.

:cd <dirname>
      Changes the directory to <dirname>

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

:find <regexp>
      Quickly find files that match the regexp and execute the first
	  unambiguous match.

:grep <string>
      Looks for a string in all marked files or directory.
      (equivalent to "!grep [some options] -e <string> -r %s | less")

:mark <regexp>
      Mark all files matching a regular expression.

:unmark <regexp>
      Unmark all files matching a regular expression.

:mkdir <dirname>
      Creates a directory with the name <dirname>

:open_with [<program>] [<flags>] [<mode>]
      Open the current file with the program, flags and mode. |24?| |25?|
      All arguments are optional.  If none is given, its equivalent to
      pressing <Enter>

:quit
      Exits ranger

:rename <newname>
      Changes the name of the currently highlighted file to <newname>

:search <regexp>
      Search for a regexp in all file names, like the / key in vim.

:shell [-<flags>] <command>
      Run the command, optionally with some flags.  |25?|
      Example: shell -d firefox -safe-mode %s
      opens (detached from ranger) the selection in firefox' safe-mode

:terminal
      Spawns "x-terminal-emulator" starting in the current directory.

:touch <filename>
      Creates a file with the name <filename>


==============================================================================
3.3. Macros

Like in similar filemanagers there are some macros.  Use them in
commands and they will be replaced with a list of files.
	%f	the highlighted file
	%d	the path of the current directory
	%s	the selected files in the current directory.  If no files are
		selected, it defaults to the same as %f
	%t	all tagged files in the current directory
	%c	the full paths of the currently copied/cut files

The macros %f, %d and %s also have upper case variants, %F, %D and %S,
which refer to the next tab.  To refer to specific tabs, add a number in
between. Examples:
	%D	The path of the directory in the next tab
	%7s	The selection of the seventh tab

%c is the only macro which ranges out of the current directory. So you may
"abuse" the copying function for other purposes, like diffing two files which
are in different directories:

	Yank the file A (type yy), move to the file B and use:
	:shell -p diff %c %f


==============================================================================
3.4. The more complicated Commands in Detail

3.4.1. "find"
The find command is different than others: it doesn't require you to
press <RETURN>.  To speed things up, it tries to guess when you're
done typing and executes the command right away.
The key "f" opens the console with ":find "

3.4.2. "shell"
The shell command accepts flags |25?| as the first argument. This example
will use the "p"-flag, which pipes the output to the pager:
	:shell -p cat somefile.txt

There are some shortcuts which open the console with the shell command:
	"!" opens ":shell "
	"@" opens ":shell  %s"
	"#" opens ":shell -p "

3.4.3. "open_with"
The open_with command is explained in detail in chapter 2.2. |22?|

==============================================================================
"""
# vim:tw=78:sw=8:sts=8:ts=8:ft=help
