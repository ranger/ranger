# You should source this script, passing the command to start ranger
# as the arguments.
#
# Example command:
# source bash_integration.sh python3 /path/to/ranger.py

CACHEDIR=$HOME/.cache/ranger
[ -n "$XDG_CACHE_HOME" ] && CACHEDIR=$XDG_CACHE_HOME/ranger

PWD_BEFORE="$(pwd)"
$@ "$PWD_BEFORE"
PWD_AFTER="$(cat "$CACHEDIR"/last_dir)"

if [[ "$PWD_BEFORE" != "$PWD_AFTER" ]]; then
	cd "$PWD_AFTER"
fi

export RANGER_POINTER="$(cat "$CACHEDIR"/last_pointer)"
export RANGER_SCROLL_START="$(cat "$CACHEDIR"/last_scroll_start)"

d="$(cat "$CACHEDIR"/last_dir)"
f="$RANGER_POINTER"

function sel {
	xargs -d "\n" "$@" < "$CACHEDIR"/last_selection
}
