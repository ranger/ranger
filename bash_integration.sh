# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
# This software is licensed under the GNU GPLv3. See COPYING for details.

# You should source this script in your bashrc, passing the command to start
# pithy as the arguments.  Then, start pithy with the command "bash_pithy"
# or by typing the shortcut ^O

# Example bashrc entry:
# source /path/to/bash_integration.sh python3 /path/to/pithy.py
# alias pithy=bash_pithy

PITHY_EXEC="$@"

function bash_pithy {
	CACHEDIR=$HOME/.cache/pithy
	[ -n "$XDG_CACHE_HOME" ] && CACHEDIR=$XDG_CACHE_HOME/pithy

	PWD_BEFORE="$(pwd)"
	$PITHY_EXEC "$PWD_BEFORE"
	RETURN_VALUE=$?
	PWD_AFTER="$(cat "$CACHEDIR"/last_dir)"

	if [ "$PWD_BEFORE" != "$PWD_AFTER" -a "$RETURN_VALUE" == 0 ]; then
		cd "$PWD_AFTER"
	fi

	export PITHY_POINTER="$(cat "$CACHEDIR"/last_pointer)"
	export PITHY_SCROLL_START="$(cat "$CACHEDIR"/last_scroll_start)"

	d="$(cat "$CACHEDIR"/last_dir)"
	f="$PITHY_POINTER"
}

function sel {
	xargs -d "\n" "$@" < "$CACHEDIR"/last_selection
}

bind -x '"\C-o": bash_pithy'
