# You should source this script, giving the command to start ranger
# as the arguments. Examples:
# long: source run.sh python3 /path/to/ranger.py
# short: . run.sh ranger

CACHEDIR=$HOME/.cache/ranger
[ -n "$XDG_CACHE_HOME" ] && CACHEDIR=$XDG_CACHE_HOME/ranger

PWD_BEFORE="$(pwd)"
$@
PWD_AFTER="$(cat $CACHEDIR/last_dir)"

if [[ "$PWD_BEFORE" != "$PWD_AFTER" ]]; then
	cd "$PWD_AFTER"
fi

RANGER_POINTER="$(cat $CACHEDIR/last_pointer)"
f="$RANGER_POINTER"
export RANGER_POINTER

RANGER_SCROLL_START="$(cat $CACHEDIR/last_scroll_start)"
export RANGER_SCROLL_START
