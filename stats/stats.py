import subprocess
import requests
import hashlib
import json
import urllib3
import os


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


if __name__ == "__main__":
    start = 1000
    stop = 3000
    names = get_package_names()
    nnames = len(names)
    for index, name in enumerate(names):
        s = (f"{index}/{nnames}: {name}")
        filename = hashlib.sha256(name.encode()).hexdigest()
        file_path = f"data/by-name/{filename}"
        failed_file_path = f"data/failed-by-name/{filename}"

        if os.path.isfile(file_path):
            print(s + " (previously fetched)")
            continue
        elif os.path.isfile(failed_file_path):
            print(s + " (previously failed)")
            continue
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
