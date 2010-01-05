"""
1. Basic Movement With Ranger

1.1. Ranger has similar movement keys as vim:

	k       move up
	j       move down
	h       move left (in browser: move one directory up)
	l       move right (in browser: enter this directory, or run this file)

	K       move half the screen up
	J       move half the screen down
	H       in browser: move back in history
	L       in browser: move forward in history

	gg      move to the top
	G       move to the bottom

By prefixing a number, you can give more precise commands, eg:

	2J      move 2 pages down
	5gg     move to the 5th line
	3h      move 3 characters to the left, or move 3 directories up

Using arrow keys is equivalent of using h/j/k/l in most cases.
An exception to this is the console, where you can move around with
arrow keys and pressing letters will insert the letter into the console.
----------------------------------------

1.2. Special Keys

Special keys like Home, Page Up,.. work as expected.
The Enter key is equivalent to l except that files will be opened
in "mode 1" instead of the default mode 0. (5?)

These keys give you more movement control: (^X = Ctrl X)

	K, ^D   move half the screen up
	J, ^U   move half the screen down
	^B      move up by one screen
	^F      move down by one screen
----------------------------------------

1.3. Cycling

You can't only move up and down through the list, but also cycle through
the items in different logical orders.

	/       open the "search console" and cycle through matches (3?)
	TAB     cycle through tagged items
	cc      cycle by ctime (last modification)
	cm      cycle by mime type, connecting similar files
	cs      cycle by size, large items first

	n       move to the next item
	N       move to the previous item

	See also: sorting (4?)

Example:

	csnn    move to the third largest item
----------------------------------------
"""
