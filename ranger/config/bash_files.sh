#!/usr/bin/env bash

query() {
    local COMP_WORDS=("$@")
    printf '%s\n' $(compgen -f "${COMP_WORDS[0]}") | LC_ALL=C sort
}

query $@
