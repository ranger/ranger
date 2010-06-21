#!/bin/bash

# This script is called whenever you preview a file.
# Its output is used as the preview.  ANSI color codes are supported.

# Meaning of exit codes:
# code | meaning    | action of ranger
# -----+------------+-------------------------------------------
# 0    | success    | display stdout as preview
# 1    | no preview | display no preview at all


mimetype=$(file --mime-type -Lb "$1")
extension=$(echo "$1" | grep '\.' | grep -o '[^.]\+$')

case "$mimetype" in
	text/*)
		highlight --ansi "$1" || cat "$1" || exit 1
		exit 0;;
	image/*)
		img2txt "$1" || exit 1
		exit 0;;
esac

case "$extension" in
	zip|gz)
		atool -l "$1" || exit 1
		exit 0;;
esac

exit 1
