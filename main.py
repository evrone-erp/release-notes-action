import json
import re

from environs import Env
from github import Github  # type: ignore  # pylint: disable=no-name-in-module

from config.logger_config import logger
from helpers.github import change_pull_request_body, formatted_line
from helpers.yandex_tracker import YandexTracker

env = Env()

GITHUB_TOKEN = env("INPUT_TOKEN")
GITHUB_EVENT_PATH = env("GITHUB_EVENT_PATH")
GITHUB_REPOSITORY = env("GITHUB_REPOSITORY")

TASK_KEY_PATTERN = re.compile(r"[^[]*\[([^]]*)\]")


def process_commits(commits, pr_number):
    all_pulls = []
    tasks = {}
    for commit in commits:
        pulls = commit.get_pulls()
        for pull in pulls:
            if pull.number != pr_number:
                all_pulls.append(pull)
                all_matches = TASK_KEY_PATTERN.findall(pull.title)
                for task_key in set(all_matches):
                    tasks[task_key] = pull
    return all_pulls, tasks


def build_task_lines(tasks, yandex_tracker):
    result = []
    for task_key, pr in tasks.items():
        title = yandex_tracker.get_issue_summary(task_key)
        if not title:
            logger.info("[%s] (No task found)", task_key)
            continue
        task_line = formatted_line(task_key, title, pr.user.login, pr.number)
        result.append(task_line)
    return result


def main():
    with open(GITHUB_EVENT_PATH, "r", encoding="utf8") as f:
        data = json.load(f)
    yandex_tracker = YandexTracker()
    gh = Github(GITHUB_TOKEN)
    repo = gh.get_repo(GITHUB_REPOSITORY)
    pr_number = int(data["pull_request"]["number"])
    pull_request = repo.get_pull(number=pr_number)
    commits = pull_request.get_commits()

    # Collect commits and task numbers
    all_pulls, tasks = process_commits(commits, pr_number)
    result = build_task_lines(tasks, yandex_tracker)
    change_pull_request_body(pull_request, result)

    for pull in all_pulls:
        logger.info(pull.merge_commit_sha)
        logger.info(pull.title)


if __name__ == "__main__":
    main()
