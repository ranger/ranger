#!/bin/bash

# This script is called whenever you preview a file.
# Its output is used as the preview.  ANSI color codes are supported.

# NOTE: This is considered to be a configuration file.  If you upgrade
# ranger, it will be left untouched. (You must update it yourself)

# Meanings of arguments:
# name | meaning
# -----+--------------------------------------------------------
# $1   | Full filename of the selected file
# $2   | Width of the preview pane (number of fitting characters)
# $3   | Height of the preview pane (number of fitting characters)

# Meanings of exit codes:
# code | meaning    | action of ranger
# -----+------------+-------------------------------------------
# 0    | success    | display stdout as preview
# 1    | no preview | display no preview at all
# 2    | plain text | display the plain content of the file

mimetype=$(file --mime-type -Lb "$1")
extension=$(echo "$1" | grep '\.' | grep -o '[^.]\+$')

case "$extension" in
	# Archive extensions:
	7z|a|ace|alz|arc|arj|bz|bz2|cab|cpio|gz|jar|lha|lz|lzh|lzma|lzo\
	|rar|rpm|rz|t7z|tar|tbz|tbz2|tgz|tlz|txz|tZ|tzo|war|xz|Z|zip)
		atool -l "$1" || exit 1
		exit 0;;
	# HTML Pages:
	htm|html|xhtml)
		lynx -dump "$1" || elinks -dump "$1" || exit 1
		exit 0;;
esac

case "$mimetype" in
	# Syntax highlight for text files:
	text/* | */xml)
		highlight --ansi "$1" || cat "$1" || exit 1
		exit 0;;
	# Ascii-previews of images:
	image/*)
		img2txt -W "$2" "$1" || exit 1
		exit 0;;
esac

exit 1
