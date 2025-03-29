#!/usr/bin/env python

from lib import utils

if __name__=="__main__":
    data = utils.build("https://github.com/lodash/lodash",
              "f299b52f39486275a9e6483b60a410e06520c538")
    for key in data:
        print(key, data[key])
