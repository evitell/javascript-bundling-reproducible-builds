#!/bin/sh

GITHUB_TOKEN=$(cat $(dirname $0)/token.txt)

#echo $GITHUB_TOKEN
#exit
curl --request GET \
	--url "https://api.github.com/repos/octocat/Spoon-Knife/issues" \
	--header "Accept: application/vnd.github+json" \
	--header "Authorization: Bearer ${GITHUB_TOKEN}"
