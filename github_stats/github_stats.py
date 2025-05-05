import os
import requests

# GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

with open(os.path.dirname(__file__) + "/token.txt", encoding="utf-8") as f:
    GITHUB_TOKEN = f.read().strip()


def gh_fetch(url):
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f"Bearer {GITHUB_TOKEN}",
    }

    response = requests.get(url, headers=headers)
    return response


def gh_search(query: str):
    s = f"q={query}"
    url = 'https://api.github.com/search'
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {GITHUB_TOKEN}',
        'X-GitHub-Api-Version': '2022-11-28',
    }

    params = (
        ('q', query),
    )

    response = requests.get(f'https://api.github.com/search/repositories?q={query}',
                            headers=headers,
                            #   params=params
                            )
    return response


if __name__ == "__main__":
    url = 'https://api.github.com/repos/octocat/Spoon-Knife/issues'
    # r = gh_fetch(url)

    q = "lang:js&sort=stars&order=desc"
    r = gh_search(q)
    print(r.json())
