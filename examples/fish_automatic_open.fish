# Automatically open the file with xdg-open after selecting it
#
# This is a fish alias to automatically open selected the file and then exit
# the ranger. It ilustrates how to use ranger as a file opener. For example you
# can use 'urxvt -e fish -c "ranger-open"'.
#
# Note: funcsave save the alias in fish's config files, you do not need to copy
# this file anywhere, just execute it once

function ranger-open
	set dir (mktemp -t ranger_open.XXX)
	set ranger_bin (which ranger)
	$ranger_bin --choosefile=$dir $argv
	echo (cat $dir)
	nohup xdg-open (cat $dir) &
	rm $dir
end
funcsave ranger-open
