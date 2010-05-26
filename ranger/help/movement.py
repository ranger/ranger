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
1. Basic movement and browsing

1.1. Move around
1.2. Browser control
1.3. Searching
1.4. Sorting
1.5. Bookmarks
1.6. Tabs
1.7. Mouse usage
1.8. Misc keys


==============================================================================
1.1. Ranger has similar movement keys as vim:

Note: A ^ stands for the Ctrl key.

	k	move up
	j	move down
	h	move left (in browser: move one directory up)
	l	move right (in browser: enter this directory, or run this file)

	^U	move half the screen up
	^D	move half the screen down
	H	in browser: move back in history
	L	in browser: move forward in history

	gg	move to the top
	G	move to the bottom
	%	move to the middle

By prefixing a number, you can give more precise commands, eg:

	2^D	move 2 pages down
	5gg	move to the 5th line
	3h	move 3 characters to the left, or move 3 directories up
	30%	move to 30% of the screen

Using arrow keys is equivalent of using h/j/k/l in most cases.
An exception to this is the console, where you can move around with
arrow keys and pressing letters will insert the letter into the console.

Special keys like Home, Page Up,.. work as expected.

These keys work like in vim:

	^U      move half the screen up
	^D      move half the screen down
	^B      move up by one screen
	^F      move down by one screen

This keys can be used to make movements beyond the current directory

	]	move down in the parent directory
	[	move up in the parent directory

	}	traverse the directory tree, visiting each directory
	{	traverse in the other direction. (not implemented yet,
		currently this only moves back in history)


==============================================================================
1.2. Browser control

	?	view the help screen
	R	reload the current directory
	^R	clear the cache and reload the view
	^L	redraw the window
	:	open the console |3?|
	z	toggle options
	u	undo certain things (unyank, unmark,...)

	i	inspect the content of the file
	E	edit the file
	S	open a shell, starting in the current directory

Marking files allows you to use operations on multiple files at once.
If there are any marked files in this directory, "yy" will copy them instead
of the file you're pointing at.

	<Space> mark a file
	v	toggle all marks
	V, uv	remove all marks
	^V	mark files in a specific direction
		e.g. ^Vgg marks all files from the current to the top
	u^V	unmark files in a specific direction

By "tagging" files, you can highlight them and mark them to be
special in whatever context you want.  Tags are persistent across sessions.

	t	tag/untag the selection
	T	untag the selection

Midnight Commander lovers will find that the function keys work similarly.
There is no menu or drop down though.

	<F1>	view the help screen
	<F3>	view the file
	<F4>	edit the file
	<F5>	copy the selection
	<F6>	cut the selection
	<F7>	create a directory
	<F8>	delete the selection
	<F10>	exit ranger


==============================================================================
1.3. Searching

Use "/" to open the search console. |3?|
Enter a string and press <Enter> to search for it in all currently
visible files. Pressing "n" will move you to the next occurance,
"N" to the previous one.

You can search for more than just strings:
	cc	cycle through all files by their ctime (last inode change)
	cm	cycle by mime type, connecting similar files
	cs	cycle by size, large items first
	ct	search tagged files


==============================================================================
1.4. Sorting

To sort files, type "o" suffixed with a key that stands for a certain
sorting mode. By typing any of those keys in upper case, the order will
be reversed.

	os	sort by size
	ob, on	sort by basename
	om	sort by mtime (last modification)
	ot	sort by mime type
	or	reverse order


==============================================================================
1.5. Bookmarks

Type "m<key>" to bookmark the current directory. You can re-enter this
directory by typing "`<key>". <key> can be any letter or digit.  Unlike vim,
both lowercase and uppercase bookmarks are persistent.

Each time you jump to a bookmark, the special bookmark at key ` will be set
to the last directory. So typing "``" gets you back to where you were before.

Note: The ' key is equivalent to `.


==============================================================================
1.6. Tabs

Tabs are used to work in different directories in the same Ranger instance.
In Ranger, tabs are very simple though and only store the directory path.

	gt	Go to the next tab. (also TAB)
	gT	Go to the previous tab. (also Shift+TAB)
	gn, ^N	Create a new tab
	g<N>	Open a tab. N has to be a number from 1 to 9.
		If the tab doesn't exist yet, it will be created.
		On most terminals, Alt-1, Alt-2, etc., also work.
	gc, ^W	Close the current tab.  The last tab cannot be closed.


==============================================================================
1.7. Mouse usage

The mouse can be used to quickly enter directories which you point at,
or to scroll around with the mouse wheel. The implementation of the mouse
wheel is not stable due to problems with the ncurses library, but "it works
on my machine".

Clicking into the preview window will usually run the file. |2?|


==============================================================================
1.8 Misc keys

	W	Display the message log
	du	Display the disk usage of the current directory
	cd	Open the console with ":cd "
	cw	Open the console with ":rename "
	A	Open the console with ":rename <current filename>"
	I	Same as A, put the cursor at the beginning of the filename


==============================================================================
"""
# vim:tw=78:sw=4:sts=8:ts=8:ft=help
