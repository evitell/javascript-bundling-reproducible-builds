#!/bin/sh -e

# https://www.npmjs.com/package/all-the-package-names

command -v all-the-package-names ||
    npm install -g all-the-package-names

OUT=data/package_names.txt
if [ ! -f "${OUT}" ]; then
    all-the-package-names > "${OUT}"
fi
