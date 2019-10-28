#!/usr/bin/python -O
# This file is part of ranger, the console file manager.  (coding: utf-8)
# License: GNU GPL version 3, see the file "AUTHORS" for details.

# =====================
# This embedded bash script can be executed by sourcing this file.
# It will cd to ranger's last location after you exit it.
# The first argument specifies the command to run ranger, the
# default is simply "ranger". (Not this file itself!)
# The other arguments are passed to ranger.
"""":
temp_file="$(mktemp -t "ranger_cd.XXXXXXXXXX")"
ranger="${1:-ranger}"
if [ -n "$1" ]; then
    shift
fi
"$ranger" --choosedir="$temp_file" -- "${@:-$PWD}"
return_value="$?"
if chosen_dir="$(cat -- "$temp_file")" && [ -n "$chosen_dir" ] && [ "$chosen_dir" != "$PWD" ]; then
    cd -- "$chosen_dir"
fi
rm -f -- "$temp_file"
return "$return_value"
"""

from __future__ import (absolute_import, division, print_function)

import sys

# Need to find out whether or not the flag --clean was used ASAP,
# because --clean is supposed to disable bytecode compilation
ARGV = sys.argv[1:sys.argv.index('--')] if '--' in sys.argv else sys.argv[1:]
sys.dont_write_bytecode = '-c' in ARGV or '--clean' in ARGV

# Start ranger
import ranger  # NOQA pylint: disable=import-self,wrong-import-position
sys.exit(ranger.main())  # pylint: disable=no-member
