# Note: funcsave save the alias in fish's config files, you do not need to copy
# this file anywhere, just execute it once

alias ranger-cd 'ranger --choosedir=$HOME/.rangerdir; set RANGERDIR (cat $HOME/.rangerdir); cd $RANGERDIR'
funcsave ranger-cd
