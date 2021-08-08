#!/bin/sh
# Compatible with ranger 1.6.0 through 1.7.*
#
# This script searches image files in a directory, opens them all with sxiv and
# sets the first argument to the first image displayed by sxiv.
#
# This is supposed to be used in rifle.conf as a workaround for the fact that
# sxiv takes no file name arguments for the first image, just the number.  Copy
# this file somewhere into your $PATH and add this at the top of rifle.conf:
#
#   mime ^image, has sxiv, X, flag f = path/to/this/script -- "$@"
#
# Implementation notes: this script is quite slow because of POSIX limitations
# and portability concerns. First, using case statement to get absolute path is
# quicker than calling 'realpath' because it would fork a whole process, which
# is slow. Second, we need to append a file list to sxiv, which can only be done
# properly in two ways: arrays (which are not POSIX) or \0 sperated
# strings. Unfortunately, assigning \0 to a variable is not POSIX either (will
# not work in dash and others), so we cannot store the result of listfiles to a
# variable.

listfiles () {
    find -L "${target%/*}" -maxdepth 1 -type f -iregex \
      '.*\(jpe?g\|bmp\|png\|gif\|webp\)$' -print0 | sort -z
}

[ "$1" = '--' ] && shift
case "$1" in
    "") echo "Usage: ${0##*/} PICTURES" >/dev/stderr && exit ;;
    /*) target="$1" ;;
    *)  target="$PWD/$1" ;;
esac

count="$(listfiles | grep -m 1 -ZznF "$target" | cut -d: -f1)"

if [ -n "$count" ]; then
    listfiles | xargs -0 sxiv -n "$count" --
else
    sxiv -- "$@" # fallback
fi
