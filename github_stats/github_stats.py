import os
import requests
import json

# GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

with open(os.path.dirname(__file__) + "/token.txt", encoding="utf-8") as f:
    GITHUB_TOKEN = f.read().strip()

# Things to remember:
# http://docs.github.com/en/rest/search/search?apiVersion=2022-11-28
# * Max 30 requests per minute
def gh_fetch(url):
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f"Bearer {GITHUB_TOKEN}",
    }

    response = requests.get(url, headers=headers)
    return response


def gh_search(params):

    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {GITHUB_TOKEN}',
        'X-GitHub-Api-Version': '2022-11-28',
    }

    # params = (
    #     ('q', query),
    #     ("per_page", 100)
    # )

    response = requests.get(f'https://api.github.com/search/repositories',
                            headers=headers,
                              params=params
                            )
    return response

def get_fetched_data()->list[dict]:
    with open(f"data/gh_repos.json","r") as f:
        repos = json.load(f)
    return repos


def fetch_1000(q, filename):
    MAX_REPOS = 15
    page = 1
    repos = []
    while True:
        print(f"fetching page {page}")

        params = (
            ('q', q),
            ("per_page", 100),
            ("sort", "stars"),
            ("order", "desc"),
            ("page", page)
        )
        r = gh_search(params)
        data = r.json()

        # Only the first 1000 search results are available
        if not "items" in data.keys():
            break

        li = data["items"]
        num_items = len(li)
        repos += li
        print(num_items)
        if num_items < 100:
            break

        if page > MAX_REPOS:
            break

        page += 1
    with open(filename,"w") as f:
        json.dump(repos,f)



if __name__ == "__main__":
    # url = 'https://api.github.com/repos/octocat/Spoon-Knife/issues'
    # r = gh_fetch(url)

    # fetch_1000('lang:js', "data/gh_repos.json")
    fetch_1000('lang:ts', "data/gh_repos_ts.json")
