import argparse
import os

import requests

from operator import attrgetter


def parse_args() -> tuple[str, str, str, str]:
    parser = argparse.ArgumentParser(
        description="Get the URLs of questions in a leetcode list."
    )
    parser.add_argument(
        "list_slug", type=str, help="The list to fetch"
    )
    parser.add_argument(
        "--session",
        "-s",
        type=str,
        dest="leetcode_session",
        default=os.environ.get("LEETCODE_SESSION"),
        help="Leetcode session (get this from your browser)",
    )
    parser.add_argument(
        "--csrf-token",
        "-t",
        type=str,
        dest="csrf_token",
        default=os.environ.get("LEETCODE_CSRF_TOKEN"),
        help="Leetcode CSRF token (get this from your browser)",
    )
    parser.add_argument(
        "--sl-no",
        "-n",
        dest="add_sl_no",
        default=False,
        action="store_true",
        help="Add serial numbers to each URL",
    )
    args = parser.parse_args()
    return attrgetter("list_slug", "leetcode_session", "csrf_token", "add_sl_no")(args)


def get_cookies(csrf_token: str, session: str) -> dict[str, str]:
    return {
        "x-csrftoken": csrf_token,
        "csrftoken": csrf_token,
        "LEETCODE_SESSION": session,
        "Referer": "https://leetcode.com",
    }


def get_list(list_slug: str, cookies: dict[str, str]) -> list[str]:
    query = """
        query favoriteQuestionList($favoriteSlug: String!, $filter: FavoriteQuestionFilterInput) {
            favoriteQuestionList(favoriteSlug: $favoriteSlug, filter: $filter) {
                questions {
                    titleSlug
                }
            }
        }
    """
    variables = {
        "favoriteSlug": list_slug,
        "filter": {"positionRoleTagSlug": "", "skip": 0, "limit": 100},
    }
    try:
        response = requests.post(
            "https://leetcode.com/graphql",
            json={"query": query, "variables": variables},
            cookies=cookies,
        )
        response.raise_for_status()
        questions = [
            f"https://leetcode.com/problems/{question['titleSlug']}"
            for question in response.json()["data"]["favoriteQuestionList"]["questions"]
        ]
        return questions
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)


def print_urls(urls: list[str], add_sl_no: bool):
    for i, url in enumerate(urls):
        if add_sl_no:
            print(f"{i + 1}.", end="\t")
        print(url)


def main():
    list_slug, session, csrf_token, add_sl_no = parse_args()
    cookies = get_cookies(csrf_token=csrf_token, session=session)
    question_urls = get_list(list_slug=list_slug, cookies=cookies)
    print_urls(question_urls, add_sl_no)


if __name__ == "__main__":
    main()
