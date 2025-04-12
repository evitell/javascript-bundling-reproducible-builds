#!/usr/bin/env python

from lib import utils
import tomllib


if __name__ == "__main__":
    with open("data/examples.toml", "rb") as f:
        examples = tomllib.load(f)["pkgs"]
    # url = "https://github.com/expressjs/express.git"
    # commit = "cd7d4397c398a3f3ecadeaf9ef6ac1377bd414c4"
    # url = "https://github.com/lodash/lodash"
    # commit = "f299b52f39486275a9e6483b60a410e06520c538"
    start = 0
    stop = 1
    for example in examples[start:stop]:
        url = example["url"]
        commit = example["commit"]
        data = utils.build(url,
                           commit, log_shell=True, rmwork=False, verbose=False)

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

        diff = utils.compare_dirs(
            data["stage_hashes"]["preinstall_hashes"], data["stage_hashes"]["post_hashes"])
        utils.display_diff(diff)
        # print(data["preinstall_hashes"])
        print(data.keys())
