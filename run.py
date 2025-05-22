#!/usr/bin/env python

from lib import utils
from github_stats import github_stats
import tomllib
import subprocess

def build_examples():
    with open("data/examples.toml", "rb") as f:
        examples = tomllib.load(f)["pkgs"]
    # url = "https://github.com/expressjs/express.git"
    # commit = "cd7d4397c398a3f3ecadeaf9ef6ac1377bd414c4"
    # url = "https://github.com/lodash/lodash"
    # commit = "f299b52f39486275a9e6483b60a410e06520c538"
    start = 1
    stop = start+1
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
        utils.display_diff(diff, ignore=["node_modules/"])
        # print(data["preinstall_hashes"])
        print(data.keys())



if __name__ == "__main__":
    MAX=20
    gh_repos = github_stats.get_fetched_data()
    failed = 0
    succeded = 0
    for index, repo in enumerate(gh_repos):
        url = repo["clone_url"]
        print(url)
        # print(repo)
        # exit()
        try:
            data = utils.build(url,
                               log_shell=True, rmwork=True, verbose=False)
            print(data["hash"])
            succeded += 1
        except subprocess.CalledProcessError:
            print(f"failed to build {url}")
            failed += 1
        except FileNotFoundError as e:
            print(e)
            failed += 1

        if index > MAX:
            break

    print(f"Finished with {succeded} succeded and {failed} failed builds")
