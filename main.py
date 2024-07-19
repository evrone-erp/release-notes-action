import json
import re

from environs import Env
from github import Github

from helpers.github import change_pull_request_body, formatted_line
from helpers.yandex_tracker import YandexTracker

env = Env()

GITHUB_TOKEN = env("INPUT_TOKEN")
GITHUB_EVENT_PATH = env("GITHUB_EVENT_PATH")
GITHUB_REPOSITORY = env("GITHUB_REPOSITORY")

TASK_KEY_PATTERN = re.compile(r"[^[]*\[([^]]*)\]")


def main():
    with open(GITHUB_EVENT_PATH, "r", encoding="utf8") as f:
        data = json.load(f)

    yandex_tracker = YandexTracker()
    gh = Github(GITHUB_TOKEN)
    repo = gh.get_repo(GITHUB_REPOSITORY)
    pr_number = int(data["pull_request"]["number"])
    pull_request = repo.get_pull(number=pr_number)
    commits = pull_request.get_commits()

    all_pulls = []
    result = []
    tasks = {}
    for commit in commits:
        pulls = commit.get_pulls()
        for pull in pulls:
            if pull.number is not pr_number:
                all_pulls.append(pull)
                all_matches = TASK_KEY_PATTERN.findall(pull.title)
                for task_key in set(all_matches):
                    tasks[task_key] = pull
    for task_key, pr in tasks.items():
        title = yandex_tracker.get_issue_summery(task_key)
        task_line = formatted_line(task_key, title, pr.user.login, pr.number)
        result.append(task_line)

    change_pull_request_body(pull_request, result)

    for pull in all_pulls:
        print(pull.merge_commit_sha)
        print(pull.title)


if __name__ == "__main__":
    main()