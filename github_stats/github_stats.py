import os
import requests

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


if __name__ == "__main__":
    url = 'https://api.github.com/repos/octocat/Spoon-Knife/issues'
    # r = gh_fetch(url)

    page = 1
    for _ in range(1,3):
        print(f"fetching page {page}")

        params = (
            ('q', 'lang:js'),
            ("per_page", 100),
            ("sort", "stars"),
            ("order", "desc"),
            ("page", page)
        )
        q = "lang:js&sort=stars&order=desc"
        r = gh_search(params)
        data = r.json()
        li = data["items"]
        num_items = len(li)
        print(num_items)
        if num_items < 100:
            break

        page += 1
