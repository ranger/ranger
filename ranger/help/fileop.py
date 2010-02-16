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
4. File Operations

4.1. Destructive Operations
4.2. The Selection
4.3. Copying and Pasting


==============================================================================
4.1. Destructive Operations

These are all the operations which can change, and with misuse, possibly
harm your files:

:chmod <number>    Change the rights of the selection
:delete            DELETES ALL FILES IN THE SELECTION WITHOUT CONFIRMATION
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
"""
# vim:tw=78:sw=4:sts=8:ts=8:ft=help
