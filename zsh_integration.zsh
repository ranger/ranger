# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
# This software is licensed under the GNU GPLv3. See COPYING for details.

# You should source this script in your zshrc, passing the command to start
# pithy as the arguments.  Then, start pithy with the command "zsh_pithy"
# or by typing the shortcut ^O

# Example zshrc entry:
# source /path/to/zsh_integration.sh python3 /path/to/pithy.py
# alias pithy=zsh_pithy

# If you have copied the default settings to $XDG_CONFIG_HOME/pithy/rc.py,
# you should add the argument --no-defaults at the end of the source-command
# so you don't load the default settings twice.

PITHY_EXEC="$@"

function zsh_pithy {
	CACHEDIR=$HOME/.cache/pithy
	[ -n "$XDG_CACHE_HOME" ] && CACHEDIR=$XDG_CACHE_HOME/pithy

	PWD_BEFORE="$(pwd)"
	if [ "$1" = "" ]; then
		# using $(pwd) as first argument fixes problems with symlinks.
		$=PITHY_EXEC "$PWD_BEFORE"
	else
		$=PITHY_EXEC "$@"
	fi
	RETURN_VALUE=$?
	PWD_AFTER="$(cat "$CACHEDIR"/directory)"

	if [ "$PWD_BEFORE" != "$PWD_AFTER" -a "$RETURN_VALUE" = 0 ]; then
		cd "$PWD_AFTER"
	fi

	export PITHY_POINTER="$(cat "$CACHEDIR"/pointer)"
	export PITHY_SCROLL_START="$(cat "$CACHEDIR"/scroll_start)"
	export PITHY_MARKED="$(cat "$CACHEDIR"/marked)"

	d="$PWD_AFTER"
	f="$PITHY_POINTER"
	if [ "$PITHY_MARKED" = "" ]; then
		PITHY_SELECTION="$PITHY_POINTER"
	else
		PITHY_SELECTION="$PITHY_MARKED"
	fi
}

function sel {
	echo "$PITHY_SELECTION" | xargs --delimiter="\n" "$@"
}

function pithy_widget_wrapper {
	zsh_pithy "$@" <$TTY
	zle -I
}

zle -N pithy_widget_wrapper
bindkey "^O" pithy_widget_wrapper
