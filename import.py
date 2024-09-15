import argparse
import os
import sys
import time

import requests

from operator import attrgetter


def parse_args() -> tuple[str, str, str, str, str]:
    parser = argparse.ArgumentParser(
        description="Create a leetcode list from a file containing question slugs."
    )
    parser.add_argument("filename", help="File with URLs")
    parser.add_argument("list_name", type=str, help="Name of list to be created")
    parser.add_argument(
        "--session",
        "-s",
        type=str,
        dest="leetcode_session",
        default=os.environ.get("LC_IMPORT_SESSION"),
        help="Leetcode session (get this from your browser)",
    )
    parser.add_argument(
        "--csrf-token",
        "-t",
        type=str,
        dest="csrf_token",
        default=os.environ.get("LC_IMPORT_TOKEN"),
        help="Leetcode CSRF token (get this from your browser)",
    )
    parser.add_argument(
        "--private",
        "-p",
        dest="is_private",
        default=False,
        action="store_true",
        help="Make the created list private",
    )
    args = parser.parse_args()
    return attrgetter(
        "filename", "list_name", "leetcode_session", "csrf_token", "is_private"
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


def create_list(
    filename: str,
    list_name: str,
    is_private: str,
    cookies: dict[str, str],
    headers: dict[str, str],
) -> str:
    list_created = False
    failed = []
    with open(filename) as f:
        for line in f:
            question_slug = line.rstrip()
            if not list_created:
                list_slug = add_question_to_new_list(
                    question_slug, list_name, is_private, cookies, headers
                )
                list_created = True
            else:
                time.sleep(1)
                if not add_question_to_list(question_slug, list_slug, cookies, headers):
                    failed.append(question_slug)
    if len(failed) > 0:
        _err(f"\nFailed to add the following questions to list: ")
        for question in failed:
            _err(f"\t{question}")
    return list_slug


def add_question_to_new_list(
    question_slug: str,
    list_name: str,
    is_private: bool,
    cookies: dict[str, str],
    headers: dict[str, str],
) -> str:
    query = """
        mutation AddQuestionToNewFavoriteV2(
            $name: String!
            $isPublicFavorite: Boolean!
            $questionSlug: String!
        ) {
            addQuestionToNewFavoriteV2(
                name: $name
                isPublicFavorite: $isPublicFavorite
                questionSlug: $questionSlug
            ) {
                ok
                error
                slug
            }
        }
    """
    variables = {
        "questionSlug": question_slug,
        "name": list_name,
        "isPublicFavorite": not is_private,
    }
    try:
        response = requests.post(
            "https://leetcode.com/graphql",
            json={"query": query, "variables": variables},
            cookies=cookies,
            headers=headers,
        )
        response.raise_for_status()
        response_data = response.json()["data"]["addQuestionToNewFavoriteV2"]
        if not response_data["ok"]:
            raise SystemExit(response_data["error"])
        print(f"Created list {list_name} with slug: {response_data['slug']}")
        print(f"Added {question_slug} to list")
        return response_data["slug"]
    except requests.exceptions.RequestException as e:
        _err("Error while adding question to new list")
        raise SystemExit(e)


def add_question_to_list(
    question_slug: str, list_slug: str, cookies: dict[str, str], headers: dict[str, str]
) -> bool:
    query = """
        mutation addQuestionToFavoriteV2($favoriteSlug: String!, $questionSlug: String!) {
            addQuestionToFavoriteV2(
                favoriteSlug: $favoriteSlug
                questionSlug: $questionSlug
            ) {
                ok
                error
            }
        }
    """
    variables = {
        "favoriteSlug": list_slug,
        "questionSlug": question_slug,
    }
    try:
        response = requests.post(
            "https://leetcode.com/graphql",
            json={"query": query, "variables": variables},
            cookies=cookies,
            headers=headers,
        )
        response.raise_for_status()
        response_data = response.json()["data"]["addQuestionToFavoriteV2"]
        if not response_data["ok"]:
            _err(
                f"Error while adding question {question_slug} to list: response_data['error']"
            )
            return False
        print(f"Added {question_slug} to list")
        return True
    except requests.exceptions.RequestException as e:
        _err(
            f"Error while adding question {question_slug} to list: {e.response.status_code} - {e.response.reason}"
        )
        return False


def _err(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def main():
    filename, list_name, session, csrf_token, is_private = parse_args()
    cookies = get_cookies(csrf_token=csrf_token, session=session)
    headers = get_headers(csrf_token=csrf_token)
    list_slug = create_list(filename, list_name, is_private, cookies, headers)
    print(f"\nCreated list: https://leetcode.com/problem-list/{list_slug}")


if __name__ == "__main__":
    main()
