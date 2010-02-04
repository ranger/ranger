#!/bin/bash

# I work on a branch (named hut) which contains commits
# that should not be part of the standard distribution.
#
# This script picks all the good commits from hut and
# adds them to the master branch.
# Bad commits are marked with a "custom:" at the beginning
# of the commit message.

BRANCH=`git branch 2>/dev/null|grep -e ^* | tr -d \*\ `

git checkout master

while read -r hash tag rest; do
	if [ $tag != 'custom:' ]; then
		git cherry-pick $hash || exit 1
	fi
done < <(git log --oneline --no-color master..hut)

git checkout hut
git rebase master

git checkout $BRANCH
