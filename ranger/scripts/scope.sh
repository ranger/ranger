#!/bin/bash
# This script is responsible to generate the previews for ranger.
mimetype=$(file --mime-type -Lb "$1")
basetype=$(echo "$mimetype" | grep -o '^[^/]\+')
extension=$(echo "$1" | grep '\.' | grep -o '[^.]\+$')

case "$basetype" in
	text)
		highlight --ansi "$1" || cat "$1"
		exit 0;;
	image)
		img2txt "$1" || exit 1
		exit 0;;
esac

case "$extension" in
	zip|gz)
		atool -l "$1"
		exit 0;;
esac

exit 1
