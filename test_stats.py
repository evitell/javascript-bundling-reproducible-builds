from stats import stats
import pandas as pd
import pickle

def dump_all():
    pkgs = stats.get_all_package_info()

    with open("data/all.pickle","wb") as f:
        pickle.dump(pkgs,f)


def read_all():

    with open("data/all.pickle","rb") as f:
        data = pickle.load(f)

    print(data)

if __name__ == "__main__":
    dump_all()
    read_all()
