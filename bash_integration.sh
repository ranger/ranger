# You should source this script in your bashrc, passing the command to start
# ranger as the arguments.  Then, start ranger with the command "bash_ranger"
# or by typing the shortcut ^O
#
# Example bashrc entry:
# source /path/to/bash_integration.sh python3 /path/to/ranger.py
# alias ranger=bash_ranger

RANGER_EXEC="$@"

function bash_ranger {
	CACHEDIR=$HOME/.cache/ranger
	[ -n "$XDG_CACHE_HOME" ] && CACHEDIR=$XDG_CACHE_HOME/ranger

	PWD_BEFORE="$(pwd)"
	$RANGER_EXEC "$PWD_BEFORE"
	RETURN_VALUE=$?
	PWD_AFTER="$(cat "$CACHEDIR"/last_dir)"

	if [ "$PWD_BEFORE" != "$PWD_AFTER" -a "$RETURN_VALUE" == 0 ]; then
		cd "$PWD_AFTER"
	fi

	export RANGER_POINTER="$(cat "$CACHEDIR"/last_pointer)"
	export RANGER_SCROLL_START="$(cat "$CACHEDIR"/last_scroll_start)"

	d="$(cat "$CACHEDIR"/last_dir)"
	f="$RANGER_POINTER"
}

function sel {
	xargs -d "\n" "$@" < "$CACHEDIR"/last_selection
}

bind -x '"\C-o": bash_ranger'
