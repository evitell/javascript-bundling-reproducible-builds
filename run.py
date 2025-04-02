#!/usr/bin/env python

from lib import utils


if __name__=="__main__":
    # url = "https://github.com/expressjs/express.git"
    # commit = "cd7d4397c398a3f3ecadeaf9ef6ac1377bd414c4"
    url = "https://github.com/lodash/lodash"
    commit = "f299b52f39486275a9e6483b60a410e06520c538"
    data = utils.build(url,
              commit,log_shell=True,rmwork=False,verbose=False)
    
    print("install stdout")
    print(utils.decode_or_none(data["install_log"].stdout))
    print("install stderr")
    print(utils.decode_or_none(data["install_log"].stderr))
    if data["build_log"]:
        print("build stdout")
        print(utils.decode_or_none(data["build_log"].stdout))
        print("build stderr")
        print(utils.decode_or_none(data["build_log"].stderr))
        print("output hash")
    print(data["hash"])
