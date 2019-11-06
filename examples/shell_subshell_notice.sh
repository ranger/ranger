# shellcheck shell=sh

# Compatible with ranger 1.5.3 through 1.9.*
#
# Change the prompt when you open a shell from inside ranger
#
# Source this file from your shell startup file (.bashrc, .zshrc etc) for it to
# work.

[ -n "$RANGER_LEVEL" ] && PS1="$PS1"'(in ranger) '
