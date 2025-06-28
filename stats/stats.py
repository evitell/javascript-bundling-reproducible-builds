import subprocess
try:
    import requests
except Exception:
    print(f"WARNING: could not import requests")
import hashlib
import json
try:
    import urllib3
except Exception:
    print(f"WARNING: could not import urllib3")

import os
import multiprocessing


def get_package_names(file: str = "data/package_names.txt") -> list[str]:
    with open(file, encoding="utf-8") as f:
        names = [name.strip() for name in f.readlines()]
    return names

# https://www.reddit.com/r/webdev/comments/1ff3ps5/these_5000_npm_packages_consume_45_pb_of_traffic/


def name2url(name: str) -> str:
    url = f"https://api.npmjs.org/downloads/point/last-week/{name}"
    return url


def get_stats(name: str) -> dict:

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
    }

    url = name2url(name)
    response = requests.get(url)
    if not response.ok:
        error_message = f"ERROR \"{url}\" returned status {response.status_code}"
        print(error_message)

        raise requests.HTTPError(error_message)
    return response.json()


def test_get_stats():
    name = "@arco-iconbox/vue-tuboshi2"
    stats = get_stats(name)
    print(stats)


def get_failed_file_path(name):
    filename = hashlib.sha256(name.encode()).hexdigest()
    failed_file_path = f"data/failed-by-name/{filename}"
    return failed_file_path


def get_file_path(name):
    filename = hashlib.sha256(name.encode()).hexdigest()
    file_path = f"data/by-name/{filename}"
    return file_path


def get_package_info(name):
    file_path = get_file_path(name)
    failed_file_path = get_failed_file_path(name)
    if os.path.isfile(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["name"] = name
        return data
    elif os.path.is_file(failed_file_path):
        return None
    else:
        raise Exception(f"{name} has never been fetched")


def get_all_package_info(fail=False, start=0, stop=-1, log=True):
    names = get_package_names()
    data = []
    for index, name in enumerate(names[start:stop]):
        if log:
            print(f"processing {index}/{len(names)}")
        try:
            info = get_package_info(name)
            if info:
                data.append(info)
        except Exception as e:
            if fail:
                raise e
    return data


def get_most_popular_packages(pkgs: list[dict], topn=None, min_downloads=None):
    if (topn is None) and (min_downloads is None):
        raise Exception("Either topn or min_downloads must be specified")
    elif (not topn is None) and (not min_downloads is None):
        raise Exceptio("Must specify exactly one of topn and min_downloads")
    pkgs_sorted = sorted(pkgs, key=lambda x: x["downloads"], reverse=True)
    if topn:
        return pkgs_sorted[:topn]
    n = 0
    while n < len(pkgs_sorted):
        dl = pkgs_sorted[n]["downloads"]
        if dl < min_downloads:
            break
        n += 1
    return pkgs_sorted[:n]


def full_fetch(name):
    s = ""
    filename = hashlib.sha256(name.encode()).hexdigest()
    file_path = f"data/by-name/{filename}"
    failed_file_path = f"data/failed-by-name/{filename}"

    if os.path.isfile(file_path):
        print(s + " (previously fetched)")
        # continue
        return
    elif os.path.isfile(failed_file_path):
        print(s + " (previously failed)")
        # continue
        return
    try:
        print(s + " (fetching)")

        data = get_stats(name)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except requests.HTTPError:

        with open(failed_file_path, "w", encoding="utf-8") as f:
            pass
    except urllib3.exceptions.ProtocolError:

        with open(failed_file_path, "w", encoding="utf-8") as f:
            pass

    except Exception as e:
        print(f"failed to fetch {name}")
        print(e)

        raise e
        raise Exception
    return


def fetch_all():
    start = 314552
    stop = 3000
    names = get_package_names()
    nnames = len(names)
    # https://www.kth.se/blogs/pdc/2019/02/parallel-programming-in-python-multiprocessing-part-1/
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    pool.map(full_fetch, names[start:])
    # for index, name in enumerate(names[start:]):
    #     s = (f"{index}/{nnames}: {name}")
    #     print(s,end="")
    #     full_fetch(name)


def get_detailed_stats(package_name: str, version="latest") -> dict:
    url = f"https://registry.npmjs.org/{package_name}/latest"
    r = requests.get(url)
    data = r.json()
    return data


if __name__ == "__main__":
    fetch_all()
