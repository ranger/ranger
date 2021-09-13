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

tmp="/tmp/sxiv_rifle_$$"

listfiles () {
    find -L "///${1%/*}" \( ! -path "///${1%/*}" -prune \) -type f \
      \( -name '*.jpg' -o -name '*.jpeg' -o -name '*.png' -o -name '*.gif' \
      -o -name '*.webp' -o -name '*.tiff' -o -name '*.bmp' \) -print |
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
