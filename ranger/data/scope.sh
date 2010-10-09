#!/bin/bash

# This script is called whenever you preview a file.
# Its output is used as the preview.  ANSI color codes are supported.

# NOTES: This script is considered a configuration file.  If you upgrade
# ranger, it will be left untouched. (You must update it yourself)
# NEVER make this script interactive. (by starting mplayer or something)

# Meanings of exit codes:
# code | meaning    | action of ranger
# -----+------------+-------------------------------------------
# 0    | success    | display stdout as preview
# 1    | no preview | display no preview at all
# 2    | plain text | display the plain content of the file
# 3    | fix width  | success. Don't reload when width changes
# 4    | fix height | success. Don't reload when height changes
# 5    | fix both   | success. Don't ever reload

# Meaningful aliases for arguments:
path="$1"    # Full path of the selected file
width="$2"   # Width of the preview pane (number of fitting characters)
height="$3"  # Height of the preview pane (number of fitting characters)

# Find out something about the file:
mimetype=$(file --mime-type -Lb "$path")
extension=$(echo "$path" | grep '\.' | grep -o '[^.]\+$')

# Other useful stuff
maxln=200                                   # print up to $maxln lines
function have { type -P "$1" > /dev/null; } # test if program is installed

case "$extension" in
	# Archive extensions:
	7z|a|ace|alz|arc|arj|bz|bz2|cab|cpio|gz|jar|lha|lz|lzh|lzma|lzo\
	|rar|rpm|rz|t7z|tar|tbz|tbz2|tgz|tlz|txz|tZ|tzo|war|xz|Z|zip)
		atool -l "$path" | head -n $maxln && exit 3
		exit 1;;
	pdf)
		pdftotext -q "$path" - | head -n $maxln && exit 3
		exit 1;;
	# HTML Pages:
	htm|html|xhtml)
		have lynx && lynx -dump "$path" | head -n $maxln && exit 5
		have elinks && elinks -dump "$path" | head -n $maxln && exit 5
		;; # fall back to highlight/cat if theres no lynx/elinks
esac

case "$mimetype" in
	# Syntax highlight for text files:
	text/* | */xml)
		(highlight --ansi "$path" || cat "$path") | head -n $maxln
		exit 5;;
	# Ascii-previews of images:
	image/*)
		img2txt --gamma=0.6 --width="$width" "$path" && exit 4 || exit 1;;
esac

exit 1
