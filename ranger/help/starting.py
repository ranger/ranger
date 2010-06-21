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
2. Running Files

2.1. How to run files
2.2. The "open with" prompt
2.2. Programs
2.4. Modes
2.5. Flags


==============================================================================
2.1. How to run files

While highlighting a file, press the "l" key to fire up the automatic
filetype detection mechanism and attempt to start the file.

	l	run the selection
	r	open the "open with" prompt

Note: The selection means, if there are marked files in this directory,
use them.  Otherwise use the file under the cursor.


==============================================================================
2.2. The "open with" prompt

If the automatic filetype detection fails or starts the file in a wrong
way, you can press "r" to manually tell ranger how to run it.

Syntax: open with: <program> <flags> <mode>

Examples:
Open this file with vim:
	open with: vim
Run this file like with "./file":
	open with: self
Open this file with mplayer with the "detached" flag:
	open with: mplayer d

The parameters <program>, <flags> and <mode> are explained in the
following paragraphs

Note: The "open with" console is named QuickOpenConsole in the source code.


==============================================================================
2.3. Programs

Programs have to be defined in ranger/defaults/apps.py.  Each function
in the class CustomApplications which starts with "app_" can be used
as a program in the "open with" prompt.

You're encouraged to add your own program definitions to the list.  Refer to
the existing examples in the apps.py, it should be easy to adapt it for your
purposes.


==============================================================================
2.4. Modes

Sometimes there are multiple variants to open a file.  For example, ranger
gives you 2 ways of opening a video (by default):

	0	windowed
	1	fullscreen

By specifying a mode, you can select one of those.  The "l" key will
start a file in mode 0. "4l" will start the file in mode 4 etc.
You can specify a mode in the "open with" console by simply adding
the number.  Eg: "open with: mplayer 1" or "open with: 1"

For a list of all programs and modes, see ranger/defaults/apps.py


==============================================================================
2.5. Flags

Flags give you a way to modify the behaviour of the spawned process.

	s	Silent mode.  Output will be discarded.
	d	Detach the process.  (Run in background)
	p	Redirect output to the pager
	w	Wait for an enter-press when the process is done

For example, "open with: p" will pipe the output of that process into
the pager.

An uppercase flag has the opposite effect.  If a program will be detached by
default, use "open with: D" to not detach it.

Note: Some combinations don't make sense, eg: "vim d" would open the file in
vim and detach it.  Since vim is a console application, you loose grip
of that process when you detach it.  It's up to you to do such sanity checks.


==============================================================================
"""
# vim:tw=78:sw=4:sts=8:ts=8:ft=help
