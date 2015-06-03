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
tempfile="$(mktemp)"
ranger="${1:-$0}"
test -z "$1" || shift
"$ranger" --choosedir="$tempfile" "${@:-$(pwd)}"
returnvalue=$?
test -f "$tempfile" &&
if [ "$(cat -- "$tempfile")" != "$(echo -n `pwd`)" ]; then
    cd "$(cat "$tempfile")"
fi
rm -f -- "$tempfile"
return $returnvalue
""" and None

import sys
from os.path import exists, abspath

# Need to find out whether or not the flag --clean was used ASAP,
# because --clean is supposed to disable bytecode compilation
argv = sys.argv[1:sys.argv.index('--')] if '--' in sys.argv else sys.argv[1:]
sys.dont_write_bytecode = '-c' in argv or '--clean' in argv

# Don't import ./ranger when running an installed binary at /usr/.../ranger
if __file__[:4] == '/usr' and exists('ranger') and abspath('.') in sys.path:
    sys.path.remove(abspath('.'))

# Start ranger
import ranger
sys.exit(ranger.main())
