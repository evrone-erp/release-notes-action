import json
import re
from typing import Dict, List

from environs import Env
from github import Github  # type: ignore  # pylint: disable=no-name-in-module

from config.logger_config import logger

# isort: off
from helpers.github import (
    change_pull_request_body,
    check_is_release,
    formatted_line,
    update_or_create_draft_release,
)

# isort: on
from helpers.yandex_tracker import YandexTracker

env = Env()

GITHUB_TOKEN = env("INPUT_TOKEN")
GITHUB_EVENT_PATH = env("GITHUB_EVENT_PATH")
GITHUB_REPOSITORY = env("GITHUB_REPOSITORY")

TASK_KEY_PATTERN = re.compile(r"[^[]*\[([^]]*)\]")


def create_task_dict(pull, task_key=None):
    return {
        "number": [pull.number],
        "message": pull.title if task_key is None else None,
        "author": pull.user.login,
        "task_key": task_key,
    }


def extract_task_keys(commit_message: str) -> set:
    """Extract key patterns"""
    return {
        key.strip()
        for keys in TASK_KEY_PATTERN.findall(commit_message)
        for key in keys.split(",")
    }


def update_or_create_task(tasks: List[Dict], pull, task_key: str):
    """Обновляет существующую задачу или создаёт новую."""
    task_indexes = [
        i
        for i, task in enumerate(tasks)
        if task["task_key"] == task_key and task["author"] == pull.user.login
    ]
    if task_indexes:
        for task_index in task_indexes:
            tasks[task_index]["number"].append(pull.number)
    else:
        tasks.append(create_task_dict(pull, task_key))


def process_pull(pull, commit_message: str, tasks: List[Dict]):
    """Обрабатывает pull request и обновляет список задач."""
    all_matches = extract_task_keys(commit_message)
    if all_matches:
        for task_key in all_matches:
            update_or_create_task(tasks, pull, task_key)
    else:
        tasks.append(create_task_dict(pull))


def process_commits(commits, pr_number):
    tasks: List[Dict] = []

    for commit in commits:
        if "Merge pull request" in commit.commit.message:
            continue
        pulls = commit.get_pulls()
        for pull in pulls:
            if pull.number == pr_number or pull.mergeable:
                continue
            process_pull(pull, commit.commit.message, tasks)

    sorted_tasks = sorted(tasks, key=lambda x: (x["task_key"] is None, x["task_key"]))
    return sorted_tasks


def build_task_lines(tasks, yandex_tracker):
    result = []
    for task in tasks:
        task_key = task.get("task_key")
        author = task.get("author")
        numbers = ", ".join([f"#{number}" for number in task.get("number")])
        if task_key:
            title = yandex_tracker.get_issue_summary(task_key)
            if not title:
                logger.info("[%s] (No task found)", task_key)
                continue
            task_line = formatted_line(task_key, title, author, numbers)
        else:
            task_line = formatted_line(task_key, task.get("message"), author, numbers)
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
    pr_description = "\r\n".join(result)
    change_pull_request_body(pull_request, pr_description)

    # Create draft release if release or hotfix release
    status, release_type = check_is_release(pull_request)
    if not status:
        return
    release = update_or_create_draft_release(repo, release_type, pr_description)
    logger.info("Created new draft release %s", release.title)


if __name__ == "__main__":
    main()
