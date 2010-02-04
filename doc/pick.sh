#!/bin/bash

# I work on a branch (named hut) which contains commits
# that should not be part of the standard distribution.
#
# This script picks all the good commits from hut and
# adds them to the master branch.
# Bad commits are marked with a "custom:" at the beginning
# of the commit message.

MASTER_BRANCH='master'
CUSTOM_BRANCH='hut'
ORIGINAL_BRANCH=`git branch 2>/dev/null|grep -e ^* | tr -d \*\ `

git checkout $MASTER_BRANCH

while read -r hash tag rest; do
	if [ $tag != 'custom:' ]; then
		git cherry-pick $hash || exit 1
	fi
done < <(git log --oneline --no-color $MASTER_BRANCH..$CUSTOM_BRANCH)

git checkout $CUSTOM_BRANCH
git rebase $MASTER_BRANCH
git checkout $ORIGINAL_BRANCH
