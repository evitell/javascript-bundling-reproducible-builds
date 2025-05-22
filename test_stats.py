from stats import stats
# import pandas as pd
import pickle

DATA_DIR="data"
# DATA_DIR="data_clean"

def dump_all():
    pkgs = stats.get_all_package_info()

    with open(f"{DATA_DIR}/all.pickle","wb") as f:
        pickle.dump(pkgs,f)


def read_all():

    with open(f"{DATA_DIR}/all.pickle","rb") as f:
        data = pickle.load(f)

    return data

def dump_most_popular():
    all_pkgs = read_all()
    top_pkgs = stats.get_most_popular_packages(all_pkgs, min_downloads=10)


    with open(f"{DATA_DIR}/top10.pickle","wb") as f:
        pickle.dump(top_pkgs,f)
    print(top_pkgs)


if __name__ == "__main__":
    # dump_all()
    dump_most_popular()
    # exit()
    with open(f"{DATA_DIR}/top10.pickle","rb") as f:
        pkgs = pickle.load(f)

    pkg = pkgs[0]
    print(pkg)
