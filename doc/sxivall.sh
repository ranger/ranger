#!/bin/bash
#
# This script searches image files in a directory, opens them all with sxiv
# and sets the first argument to the first image displayed by sxiv.
#
# This is supposed to be used in rifle.conf as a workaround for the fact that
# sxiv takes no file name arguments for the first image, just the number.
# Copy this file somewhere into your $PATH and add this at the top of rifle.conf:
#
#   mime ^image, has sxiv, X, flag f = sxivall.sh -- "$@"
#

[ "$1" == '--' ] && shift
target="$(realpath -s "$1")"
function listfiles {
  find "$(dirname "$target")" -maxdepth 1 -type f -iregex '.*\(jpe?g\|bmp\|png\|gif\)$' -print0 | sort -z
}

count="$(listfiles | grep -m 1 -Zznx "$target" | cut -d: -f1)"

if [ -n "$count" ]; then
  listfiles | xargs -0 sxiv -n "$count" --
else
  sxiv -- "$@" # fallback
fi
