import os
from lib import utils


DIFF_DATADIR = os.getenv("DIFF_DATADIR")

if DIFF_DATADIR is None:
    # DIFF_DATADIR = "data/gh_diffoscope"
    DIFF_DATADIR = "data/github_projects"


def strip_path_prefix(path: str, strip_count: int) -> str:
    dirs_n_files = tuple(filter(lambda s: len(s) > 0, path.split("/")))

    assert (len(dirs_n_files) > strip_count)

    return "/".join(dirs_n_files[strip_count:])


def read_data(maxcount=-1):

    fs = os.listdir(DIFF_DATADIR)
    fs.sort(key=lambda x: int(x.split("_")[0]))
    n = len(fs)
    if maxcount > 0:
        n = maxcount
    res = [None] * n
    for i, fp in enumerate([f"{DIFF_DATADIR}/{f}" for f in fs]):
        if i >= n:
            break
        print(fp)
        d = utils.read_json(fp)
        if type(d) is dict:
            d["fp"] = fp
        res[i] = d

    return res


def filter_diff_results():
    pass


def main():
    data = read_data()
    scount = 0
    diff2name = {}
    for d in data:
        if type(d) is dict:
            diff = d["diff"]
            scount += 1
            if "details" in diff.keys():
                details = diff["details"]
                # print(d.keys())
                print("fp", d["fp"])
                for detail in details:
                    # print(detail.keys())
                    s1 = detail["source1"]
                    s2 = detail["source2"]
                    s1 = strip_path_prefix(s1, 3)
                    s2 = strip_path_prefix(s2, 3)
                    assert (s1 == s2)
                    print("s1, s2:", s1, s2)
                    if not s1 in diff2name.keys():
                        diff2name[s1] = [d["fp"]]
                    else:
                        diff2name[s1].append(d["fp"])
                print()

    for diff in diff2name.keys():
        names = diff2name[diff]
        print(f"diff {diff} ({len(names)}):")
        for p in names:
            print(f"\t{p}")
        print()

    print("total number of completed builds:", scount)


if __name__ == "__main__":
    main()
