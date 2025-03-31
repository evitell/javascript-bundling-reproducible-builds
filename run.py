#!/usr/bin/env python

from lib import utils

def decode_or_none(output):
    if output:
        return output.decode()
    return None

if __name__=="__main__":
    data = utils.build("https://github.com/lodash/lodash",
              "f299b52f39486275a9e6483b60a410e06520c538",log_shell=True)
    
    print("install stdout")
    print(decode_or_none(data["install_log"].stdout))
    print("install stderr")
    print(decode_or_none(data["install_log"].stderr))
    print("build stdout")
    print(decode_or_none(data["build_log"].stdout))
    print("build stderr")
    print(decode_or_none(data["build_log"].stderr))
    print("output hash")
    print(data["hash"])
