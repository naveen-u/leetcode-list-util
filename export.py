import argparse
import os

import requests

from operator import attrgetter


def parse_args() -> tuple[str, str, str, str, str]:
    parser = argparse.ArgumentParser(
        description="Get the questions in a leetcode list."
    )
    parser.add_argument("list_slug", type=str, help="The list to fetch")
    parser.add_argument(
        "--session",
        "-s",
        type=str,
        dest="leetcode_session",
        default=os.environ.get("LC_EXPORT_SESSION"),
        help="Leetcode session (get this from your browser)",
    )
    parser.add_argument(
        "--csrf-token",
        "-t",
        type=str,
        dest="csrf_token",
        default=os.environ.get("LC_EXPORT_TOKEN"),
        help="Leetcode CSRF token (get this from your browser)",
    )
    parser.add_argument(
        "--urls",
        "-u",
        dest="print_urls",
        default=False,
        action="store_true",
        help="Print URLs instead of question slugs",
    )
    parser.add_argument(
        "--sl-no",
        "-n",
        dest="add_sl_no",
        default=False,
        action="store_true",
        help="Add serial numbers to each question slug/URL",
    )
    args = parser.parse_args()
    return attrgetter(
        "list_slug", "leetcode_session", "csrf_token", "print_urls", "add_sl_no"
    )(args)


def get_headers(csrf_token: str) -> dict[str, str]:
    return {
        "x-csrftoken": csrf_token,
        "Referer": "https://leetcode.com",
    }


def get_cookies(csrf_token: str, session: str) -> dict[str, str]:
    return {
        "csrftoken": csrf_token,
        "LEETCODE_SESSION": session,
    }


def get_list(
    list_slug: str, cookies: dict[str, str], headers: dict[str, str]
) -> list[str]:
    query = """
        query favoriteQuestionList($favoriteSlug: String!, $filter: FavoriteQuestionFilterInput) {
            favoriteQuestionList(favoriteSlug: $favoriteSlug, filter: $filter) {
                questions {
                    titleSlug
                }
                hasMore
            }
        }
    """
    limit = 500
    skip = 0
    variables = {
        "favoriteSlug": list_slug,
        "filter": {"positionRoleTagSlug": "", "skip": skip, "limit": limit},
    }
    questions = []
    try:
        while True:
            variables["filter"]["skip"] = skip
            variables["filter"]["limit"] = limit
            response = requests.post(
                "https://leetcode.com/graphql",
                json={"query": query, "variables": variables},
                cookies=cookies,
                headers=headers,
            )
            response.raise_for_status()
            response_data = response.json()["data"]["favoriteQuestionList"]
            questions.extend([
                question["titleSlug"]
                for question in response_data["questions"]
            ])
            if not response_data["hasMore"]:
                break
            skip += limit
        return questions
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)


def to_urls(questions: list[str]) -> list[str]:
    return [f"https://leetcode.com/problems/{question}" for question in questions]


def print_qs(questions: list[str], add_sl_no: bool):
    for i, question in enumerate(questions):
        if add_sl_no:
            print(f"{i + 1}.", end="\t")
        print(question)


def main():
    list_slug, session, csrf_token, print_urls, add_sl_no = parse_args()
    cookies = get_cookies(csrf_token=csrf_token, session=session)
    headers = get_headers(csrf_token=csrf_token)
    questions = get_list(list_slug=list_slug, cookies=cookies, headers=headers)
    if print_urls:
        questions = to_urls(questions)
    print_qs(questions, add_sl_no)


if __name__ == "__main__":
    main()
