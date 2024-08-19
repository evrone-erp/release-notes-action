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


def create_task_dict(pull, task_key=None):
    return {
        "number": pull.number,
        "message": pull.title if task_key is None else None,
        "author": pull.user.login,
        "task_key": task_key,
    }


def process_commits(commits, pr_number):
    tasks = []
    for commit in commits:
        if "Merge pull request" in commit.commit.message:
            continue
        pulls = commit.get_pulls()
        for pull in pulls:
            if pull.number == pr_number or pull.mergeable:
                continue
            all_matches = {
                key
                for keys in TASK_KEY_PATTERN.findall(pull.title)
                for key in keys.replace(" ", "").split(",")
            }
            current_tasks = [
                create_task_dict(pull, task_key) for task_key in all_matches
            ]
            if not current_tasks:
                create_task_dict(pull)
            tasks.extend(current_tasks)
    return tasks


def build_task_lines(tasks, yandex_tracker):
    result = []
    for task in tasks:
        task_key = task.get("task_key")
        author = task.get("author")
        number = task.get("number")
        if task_key:
            title = yandex_tracker.get_issue_summary(task_key)
            if not title:
                logger.info("[%s] (No task found)", task_key)
                continue
            task_line = formatted_line(task_key, title, author, number)
        else:
            task_line = formatted_line(task_key, task.get("message"), author, number)
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
    tasks = process_commits(commits, pr_number)
    result = build_task_lines(tasks, yandex_tracker)
    change_pull_request_body(pull_request, result)


if __name__ == "__main__":
    main()
