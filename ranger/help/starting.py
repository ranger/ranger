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
2.2. open with:

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
documentation in ranger/applications.py for more information on this subject.


==============================================================================
2.4. Modes

Sometimes there are multiple variants to open a file.  For example, ranger
gives you 2 ways of opening a video (by default):

	0	fullscreen
	1	windowed

By specifying a mode, you can select one of those.  The "l" key will
start a file in mode 0. "4l" will start the file in mode 4 etc.
You can specify a mode in the "open with" console by simply adding
the number.  Eg: "open with: mplayer 1" or "open with: 1"

For a list of all programs and modes, see ranger/defaults/apps.py


==============================================================================
2.5. Flags

Flags give you a way to modify the behaviour of the spawned process.

	s	Silent mode.  Output will be discarded.
	d	Detach the process.
	p	Redirect output to the pager

For example, "open with: p" will pipe the output of that process into
the pager.

Note: Some combinations don't make sense, eg: "vim d" would open the file in
vim and detach it.  Since vim is a console application, you loose grip
of that process when you detach it.  It's up to you to do such sanity checks.


==============================================================================
"""
# vim:tw=78:sw=4:sts=8:ts=8:ft=help
