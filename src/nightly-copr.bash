#!/bin/bash
#
# nightly-copr.bash: merge updates to master branch and push to build.
#

set -e -x
source ~/.ssh/agent
ssh-add -l > /dev/null
cd "$1"
git status --porcelain -uno | grep -m1 . && exit 0 ||:
git checkout master
git pull origin
git checkout copr
git merge master --no-commit
git status --porcelain -uno | grep -m1 . || exit 0
if ! ls *.spec.rpkg &>/dev/null; then
    nightly-spec.py *.spec
    git add *.spec
fi
git -c commit.gpgsign=false commit --no-edit
git push agriffis --mirror
