"""
1. Basic movement and browsing

1.1. Move around
1.2. Browser control
1.3. Searching
1.4. Cycling
1.5. Bookmarks
1.6. Mouse usage

==============================================================================
1.1. Ranger has similar movement keys as vim:

	k	move up
	j	move down
	h	move left (in browser: move one directory up)
	l	move right (in browser: enter this directory, or run this file)

	K	move half the screen up
	J	move half the screen down
	H	in browser: move back in history
	L	in browser: move forward in history

	gg	move to the top
	G	move to the bottom
	%	move to the middle

By prefixing a number, you can give more precise commands, eg:

	2J	move 2 pages down
	5gg	move to the 5th line
	3h	move 3 characters to the left, or move 3 directories up
	30%	move to 30% of the screen

Using arrow keys is equivalent of using h/j/k/l in most cases.
An exception to this is the console, where you can move around with
arrow keys and pressing letters will insert the letter into the console.

Special keys like Home, Page Up,.. work as expected.

These keys work like in vim:

	^D      move half the screen up
	^U      move half the screen down
	^B      move up by one screen
	^F      move down by one screen

==============================================================================
1.2. Browser control

	?	view the help screen
	^R	clear the cache and reload the view
	^L	redraw the window
	:	open the console |3?|

	i	inspect the content of the file
	E	edit the file
	s	open a shell, starting in the current directory

Marking files allows you to use operations on multiple files at once.
If there are any marked files in this directory, "yy" will copy them instead
of the file you're pointing at.

	<Space> mark a file
	v	toggle all marks
	V	remove all marks

By "tagging" files, you can highlight them and mark them to be
special in whatever context you want.

	b	tag/untag a file
	B	untag a file

==============================================================================
1.3. Searching

Use "/" to open the search console. |3?|
Enter a string and press <Enter> to search for it in all currently
visible files. Pressing "n" will move you to the next occurance,
"N" to the previous one.

You can search for more than just strings:
	TAB	search tagged files
	cc	cycle through all files by their ctime (last modification)
	cm	cycle by mime type, connecting similar files
	cs	cycle by size, large items first

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
directory by typing "`<key>". <key> can be any letter or digit.
Each time you jump to a bookmark, the special bookmark at key ` will be set
to the last directory. So typing "``" gets you back to where you were before.

Note: The ' key is equivalent to `.
==============================================================================

1.6. Mouse usage

The mouse can be used to quickly enter directories which you point at,
or to scroll around with the mouse wheel. The implementation of the mouse
wheel is not stable due to problems with the ncurses library, but "it works
on my machine".

Clicking into the preview window will usually run the file. |2?|
==============================================================================
"""
# vim:tw=78:sw=4:sts=8:ts=8:ft=help
