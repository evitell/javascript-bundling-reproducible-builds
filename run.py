#!/usr/bin/env python

from lib import utils
from github_stats import github_stats
import tomllib
import subprocess
import json
import os

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
                           commit, log_shell=True, rmwork=True, verbose=False)

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
    MAX = 40
    SKIP_PREV = True
    gh_repos = github_stats.get_fetched_data()
    failed = 0
    succeded = 0
    filenotfound = 0
    print(f"will build {MAX} of {len(gh_repos)} pkgs")
    tmpdir_deleted = True
    for index, repo in enumerate(gh_repos):

        if not tmpdir_deleted:
            subprocess.run(["rm", "-rvf", tmpdir], check=True)
        # print(repo)
        # exit()
        url = repo["clone_url"]
        name = repo["name"]
        print(url)
        # print(repo)
        # exit()
        data_file_path = f"data/builds/{name}.json"
        if os.path.exists(data_file_path) and SKIP_PREV:
            continue

        tmpdir_deleted = False
        tmpdir = utils.mktemp()

        try:
            data = utils.build(url,
                               log_shell=True, rmwork=True, verbose=False, tmpdir=tmpdir)
            print(data["hash"])

            # tmpdir = data["tmpdir"]
            print("tmpdir is", tmpdir)
            # _ = input("press any key to continue")

            if os.path.exists(tmpdir):
                raise Exception(f"tmpdir {tmpdir} exists")
            tmpdir_deleted = True

            # Not json serializeable
            data["install_log"] = None
            data["build_log"] = None
            with open(data_file_path, "w", encoding="utf-8") as f:
                json.dump(data,f)
            succeded += 1
        except subprocess.CalledProcessError:
            with open(data_file_path, "w", encoding="utf-8") as f:
                json.dump("failed",f)
            print(f"failed to build {url}")
            failed += 1

        # TODO: figure out why this happens
        except FileNotFoundError as e:
            print(e)
            filenotfound += 1
        except KeyboardInterrupt:
            break

        print("Deleting directories (again)")
        # out_proc = subprocess.run(["./rm.sh"], check=True, capture_output=True)
        # out = out_proc.stdout.decode()
        # out += out_proc.stderr.decode()
        # print(f"Resulting in out: {out}")

        if index > MAX:
            break

    print(f"Finished with {succeded} succeded and {failed} failed builds ({filenotfound} file not found errors)")
