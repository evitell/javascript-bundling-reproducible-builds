#!/usr/bin/env python

from json.decoder import JSONDecodeError
from lib import utils
from github_stats import github_stats
import tomllib
import subprocess
import json
import os
import test_stats


def dbg_recursive_type(o, i="", key=None):
    print(f"{i} {type(o)}")
    i += " "

    if type(o) is subprocess.CompletedProcess:
        print("completed_process")
        print("key= ", key)
        print(str(o)[0:2000])
        raise Exception("cproc")

    if type(o) is dict:
        for k, v in o.items():
            print(i, k, type(v))
            dbg_recursive_type(v, i=i+" ", key=k)
    elif type(o) is list:
        for v in o:
            dbg_recursive_type(v, i+" ")


def test_diffoscope(gh_repos=None):
    # with open("data/examples.toml", "rb") as f:
    #     examples = tomllib.load(f)["pkgs"]
    if not os.path.isdir("data/gh_diffoscope"):
        os.makedirs("data/gh_diffoscope")
    if gh_repos is None:
        gh_repos = github_stats.get_fetched_data()

    # example = examples[1]
    # for index, example in enumerate(examples):
    tmpdir1 = None
    tmpdir2 = None
    for index, repo in enumerate(gh_repos):
        print(f"running for {index+1}:th time")
        try:
            url = repo["clone_url"]
            name = repo["name"]
        except KeyError as e:
            print("FAILED", repo)
            raise e
        commit = None
        if "commit" in repo.keys():
            commit = repo["commit"]
        else:
            commit = None
        fp = f"data/gh_diffoscope/{index}_{name}.json"
        if os.path.exists(fp):
            print("previously done")
            continue
        print(f"name = {name}, = {url}, commit = {commit}")
        # url = example["url"]
        # commit = example["commit"]

        if not ((tmpdir1 is None) and (tmpdir2 is None)):

            subprocess.run(["rm", "-rf", tmpdir1], check=True)
            subprocess.run(["rm", "-rf", tmpdir2], check=True)

        tmpdir1 = utils.mktemp()
        tmpdir2 = utils.mktemp()
        shell1 = os.path.abspath("./shell1.nix")
        shell2 = os.path.abspath("./shell2.nix")
        try:
            data1 = utils.build(url=url,
                                log_shell=False, rmwork=False, verbose=False, tmpdir=tmpdir1, nix_shell_path=shell1, ignore_completed_process=True)
            logged_commit = data1["commit"]
            print(
                f"build 1 succeded, now building {name} for a second time (url = {url}, commit={commit}, logged_commit = {logged_commit})")
            data2 = utils.build(url=url, commit=logged_commit,
                                log_shell=False, rmwork=False, verbose=False, tmpdir=tmpdir2, nix_shell_path=shell2, ignore_completed_process=True)

        except KeyboardInterrupt as e:
            raise e
        except subprocess.CalledProcessError:
            logged_commit = None
            data1 = None
            data2 = None
            with open(fp, "w") as f:
                json.dump("buildfail", f)
                continue
        builddir1 = os.path.join(tmpdir1, "build")
        builddir2 = os.path.join(tmpdir2, "build")
        try:
            diff_data = utils.diffoscope_compare(builddir1, builddir2)
        except:
            logged_commit = None
            data1 = None
            with open(fp, "w") as f:
                json.dump("diffail", f)
                continue
        data = {
            "build1": data1,
            "build2": data2,
            "diff": diff_data,
        }
        logged_commit = None
        data1 = None
        data2 = None
        with open(fp, "w") as f:
            try:
                json.dump(data, f)
            except TypeError as e:
                # print(f"failed to dump\n", data)
                dbg_recursive_type(data)

                raise e

        subprocess.run(["rm", "-rf", tmpdir1], check=True)
        subprocess.run(["rm", "-rf", tmpdir2], check=True)
        if index > 100:
            break


def build_examples():
    with open("data/examples.toml", "rb") as f:
        examples = tomllib.load(f)["pkgs"]
    # url = "https://github.com/expressjs/express.git"
    # commit = "cd7d4397c398a3f3ecadeaf9ef6ac1377bd414c4"
    # url = "https://github.com/lodash/lodash"
    # commit = "f299b52f39486275a9e6483b60a410e06520c538"
    start = 1
    stop = start+10
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


def build_gh_top():
    MAX = 40
    SKIP_PREV = False
    gh_repos = github_stats.get_fetched_data()
    failed = 0
    succeded = 0
    filenotfound = 0
    print(f"will build {MAX} of {len(gh_repos)} pkgs")
    tmpdir_deleted = True
    for index, repo in enumerate(gh_repos):

        if not tmpdir_deleted:
            subprocess.run(["rm", "-rf", tmpdir], check=True)
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
                json.dump(data, f)
            succeded += 1
        except subprocess.CalledProcessError:
            with open(data_file_path, "w", encoding="utf-8") as f:
                json.dump("failed", f)
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

    print(
        f"Finished with {succeded} succeded and {failed} failed builds ({filenotfound} file not found errors)")


if __name__ == "__main__":
    # build_examples()
    data = test_stats.get_n_detailed(20)
    repos = [test_stats.filter_detailed_npm_package_data(x) for x in data]
    for index, _ in enumerate(repos):
        repos[index]["commit"] = None
    # print(repos)
    # exit()
    test_diffoscope(repos)
