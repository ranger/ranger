# Automatically change the directory in fish after closing ranger
#
# This is a fish alias to automatically change the directory to the last visited
# one after ranger quits.
# To undo the effect of this function, you can type "cd -" to return to the
# original directory.
#
# Note: funcsave save the alias in fish's config files, you do not need to copy
# this file anywhere, just execute it once

alias ranger-cd 'ranger --choosedir=$HOME/.rangerdir; set RANGERDIR (cat $HOME/.rangerdir); cd $RANGERDIR'
funcsave ranger-cd

# To bind Ctrl-O to ranger-cd, save this in `~/.config/fish/config.fish`:
bind \co 'ranger-cd ; fish_prompt'
