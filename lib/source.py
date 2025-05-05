import requests


def fetch_pkg_data(name: str, version: str = "latest") -> dict:
    url = f"https://registry.npmjs.org/{name}/{version}"
    r = requests.get(url)
    data = r.json()
    return data


def get_source(data: dict):
    git_head = data["gitHead"]
    repository = data["repositpry"]


if __name__ == "__main__":
    data = fetch_pkg_data("express", "5.1.0")
    print(data)
