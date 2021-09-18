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
# Implementation note: the script tries to be POSIX compliant both in terms of
# shell syntax and calls being made to external utilities, such as grep or find.
# This makes it portable across many unix like systems, although it may not be
# the cleanest or fastest approach.
#
# First, using case statement to get absolute path is quicker than calling
# 'realpath' because it would fork a whole process, which is slow.
#
# Second, we need to append a file list to sxiv, which can only be done
# properly in three ways: arrays (which are not POSIX).
# \0 separated strings; but assigning \0 to a variable is not POSIX either
# so we cannot store the result of listfiles to a variable.
#
# The third approach is to store the result to a tmpfile and using `-i` to feed
# the list to sxiv. This is the fastest approach since we won't have to call
# listfiles twice.


TMPDIR="${TMPDIR:-/tmp}"
tmp="$TMPDIR/sxiv_rifle_$$"

listfiles () {
    find -L "///${1%/*}" \( ! -path "///${1%/*}" -prune \) -type f -print |
      grep -iE '\.(jpe?g|png|gif|webp|tiff|bmp)$' |
      sort | tee "$tmp"
}

is_img () {
    case "${1##*.}" in
        "jpg"|"jpeg"|"png"|"gif"|"webp"|"tiff"|"bmp") return 0 ;;
        *) return 1 ;;
    esac
}

open_img () {
    is_img "$1" || exit 1
    trap 'rm -f $tmp' EXIT
    count="$(listfiles "$1" | grep -nF "$1")"
    if [ -n "$count" ]; then
        sxiv -i -n "${count%%:*}" -- < "$tmp"
    else
        sxiv -- "$@" # fallback
    fi
}

[ "$1" = '--' ] && shift
case "$1" in
    "") echo "Usage: ${0##*/} PICTURES" >&2; exit 1 ;;
    /*) open_img "$1" ;;
    "~"/*) open_img "$HOME/${1#"~"/}" ;;
    *) open_img "$PWD/$1" ;;
esac
