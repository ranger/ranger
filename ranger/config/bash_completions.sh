#!/usr/bin/env bash

query() {
    local COMP_LINE="$*"
    local COMP_WORDS=("$@")

    if [[ ${#COMP_WORDS[@]} -le 1 ]]; then
        printf '%s\n' $(compgen -c "${COMP_WORDS[0]}") | LC_ALL=C sort
        return
    fi

    . /usr/share/bash-completion/bash_completion

    local COMP_CWORD=${#COMP_WORDS[@]}
    ((COMP_CWORD--))
    local COMP_POINT=${#COMP_LINE}
    local COMP_WORDBREAKS='"'"'><=;|&(:"
    local COMP_TYPE=9
    local COMP_KEY=9
    _command_offset 0
    printf '%s\n' "${COMPREPLY[@]}" | LC_ALL=C sort
}

query $@
