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
    tasks = []
    added_pulls = []
    for commit in commits:
        pulls = commit.get_pulls()
        is_pr_commit = False
        sub_commits = []
        if "Merge pull request" in commit.commit.message:
            continue
        logger.info(f"{commit.commit.message} by {commit.author.login}")
        for pull in pulls:
            if pull.number != pr_number and pull.number not in added_pulls:
                all_matches = TASK_KEY_PATTERN.findall(pull.title)
                for task_key in set(all_matches):
                    tasks.append(
                        {
                            "number": pull.number,
                            "message": None,
                            "author": pull.user.login,
                            "task_key": task_key,
                        }
                    )
                added_pulls.append(pull.number)
                is_pr_commit = True
            else:
                sub_commits.append(
                    {
                        "number": pull.number,
                        "message": commit.commit.message,
                        "author": commit.author.login,
                        "task_key": None,
                    }
                )
        if not is_pr_commit and sub_commits:
            tasks += sub_commits
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
                print(f"[{task_key}] (No task found)")
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
