#!/usr/bin/env python

from lib import utils


if __name__=="__main__":
    data = utils.build("https://github.com/lodash/lodash",
              "f299b52f39486275a9e6483b60a410e06520c538",log_shell=True,rmwork=False)
    
    print("install stdout")
    print(utils.decode_or_none(data["install_log"].stdout))
    print("install stderr")
    print(utils.decode_or_none(data["install_log"].stderr))
    print("build stdout")
    print(utils.decode_or_none(data["build_log"].stdout))
    print("build stderr")
    print(utils.decode_or_none(data["build_log"].stderr))
    print("output hash")
    print(data["hash"])
