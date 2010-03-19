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
4. File Operations

4.1. Destructive Operations
4.2. The Selection
4.3. Copying and Pasting
4.4. Task View


==============================================================================
4.1. Destructive Operations

These are all the operations which can change, and with misuse, possibly
harm your files:

:chmod <number>    Change the rights of the selection
:delete            DELETES ALL FILES IN THE SELECTION
:rename <newname>  Change the name of the current file
pp, pl, po         Pastes the copied files in different ways

Think twice before using these commands or key combinations.


==============================================================================
4.2. The Selection

Many commands operate on the selection, so it's important to know what
it is:

If there are marked files:
    The selection contains all the marked files.
Otherwise:
    The selection contains only the highlighted file.

"Marked files" are the files which are slightly indented and marked in
yellow (in the default color scheme.) You can mark files by typing "v" or
<space>.

The "highlighted file", or the "current file", is the one below the cursor.


==============================================================================
4.3. Copying and Pasting

	yy	copy the selection
	dd	cut the selection

	pp	paste the copied/cut files. No file will be overwritten.
		Instead, a "_" character will be appended to the new filename.
	po	paste the copied/cut files. Existing files are overwritten.
	pl	create symbolic links to the copied/cut files.

The difference between copying and cutting should be intuitive:

When pasting files which are copied, the original file remains unchanged
in any case.

When pasting files which are cut, the original file will be renamed.
If renaming is not possible because the source and the destination are
on separate devices, it will be copied and eventually the source is deleted.
This implies that a file can only be cut + pasted once.


==============================================================================
4.4. Task View

The task view lets you manage IO tasks like copying, moving and
loading directories by changing their priority or stop them.

	w	open or close the task view
	dd	stop the task
	J	decrease the priority of the task
	K	increase the priority of the task

The execution of tasks is not parallel but sequential.  Only the
topmost task is executed.  Ranger constantly switches between
handling GUI and executing tasks.  One movement of the throbber at
the top right represents such a switch, so while the throbber is
standing still, ranger is locked by a Input/Output operation and
you will not be able to input any commands.


==============================================================================
"""
# vim:tw=78:sw=4:sts=8:ts=8:ft=help
