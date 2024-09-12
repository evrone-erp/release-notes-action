from environs import Env

from helpers.github import GithubService
from helpers.yandex_tracker import YandexTracker

env = Env()

GITHUB_TOKEN = env("INPUT_TOKEN")
GITHUB_EVENT_PATH = env("GITHUB_EVENT_PATH")
GITHUB_REPOSITORY = env("GITHUB_REPOSITORY")


def main():
    yandex_tracker = YandexTracker()
    github_service = GithubService(
        GITHUB_EVENT_PATH, GITHUB_TOKEN, GITHUB_REPOSITORY, yandex_tracker
    )
    description_parts = github_service.build_description_parts()
    pr_description = "\r\n".join(description_parts)
    github_service.change_pull_request_body(pr_description)
    github_service.create_draft_release(pr_description)


if __name__ == "__main__":
    main()
