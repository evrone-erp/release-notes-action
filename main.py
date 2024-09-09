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


def create_task_dict(pull, task_key=None, is_epic: bool = False, epic_tasks=None):
    return {
        "is_epic": is_epic,
        "number": [pull.number],
        "links": [pull.html_url],
        "message": pull.title if task_key is None else None,
        "author": pull.user.login,
        "task_key": task_key,
        "tasks": epic_tasks,
    }


def create_epic_task(pull_number, task_key, message, author, link):
    return {
        "number": [pull_number],
        "links": [link],
        "message": message if task_key is None else None,
        "author": author,
        "task_key": task_key,
    }


def extract_task_keys(commit_message: str) -> set:
    """Extract key patterns"""
    return {
        key.strip()
        for keys in TASK_KEY_PATTERN.findall(commit_message)
        for key in keys.split(",")
    }


def collect_epic_tasks(tasks, epic_tasks, task_index):
    current_epic_tasks = tasks[task_index]["tasks"]
    for epic_task in epic_tasks:
        epic_task_exist = any(
            task["task_key"] == epic_task["task_key"]
            and task["message"] == epic_task["message"]
            for task in current_epic_tasks
        )
        if epic_task_exist:
            continue
        tasks[task_index]["tasks"].append(epic_task)


def update_or_create_task(
    tasks: List[Dict], pull, task_key: str, is_epic=False, epic_tasks=None
):
    """Обновляет существующую задачу или создаёт новую."""
    task_indexes = [
        i
        for i, task in enumerate(tasks)
        if task["task_key"] == task_key and task["author"] == pull.user.login
    ]
    if not task_indexes:
        tasks.append(create_task_dict(pull, task_key, is_epic, epic_tasks))
        return
    for task_index in task_indexes:
        if pull.number not in tasks[task_index]["number"]:
            tasks[task_index]["number"].append(pull.number)
            tasks[task_index]["links"].append(pull.html_url)
        if is_epic:
            collect_epic_tasks(tasks, epic_tasks, task_index)


def process_pull(
    pull, commit_message: str, tasks: List[Dict], is_epic: bool = False, epic_tasks=None
):
    """Обрабатывает pull request и обновляет список задач."""
    if is_epic:
        pull_head = pull.head.ref.split("/")
        task_key = pull_head[1]
        update_or_create_task(tasks, pull, task_key, is_epic, epic_tasks)
        return
    all_matches = extract_task_keys(commit_message)
    if all_matches:
        for task_key in all_matches:
            update_or_create_task(tasks, pull, task_key, is_epic, epic_tasks)
    else:
        tasks.append(
            create_task_dict(pull=pull, is_epic=is_epic, epic_tasks=epic_tasks)
        )


def process_epic_tasks(repo, commits, pull):
    epic_tasks: List[Dict] = []
    for commit in commits:
        if "Merge pull request" not in commit.commit.message:
            continue
        pull_number = pull.number
        link = pull.html_url
        author = pull.user.login
        message = commit.commit.message
        match = re.search(r"Merge pull request #(\d+)", message)
        if match:
            pull_number = match.group(1)
            pull_request = repo.get_pull(number=int(pull_number))
            link = pull_request.html_url
        cur_pulls = commit.get_pulls()
        for cur_pull in cur_pulls:
            if cur_pull.number == pull.number:
                author = cur_pull.user.login
                break
        all_matches = extract_task_keys(message)
        if all_matches:
            epic_tasks.extend(
                create_epic_task(pull_number, task_key, message, author, link)
                for task_key in all_matches
            )
        else:
            epic_tasks.append(
                create_epic_task(
                    pull_number=pull_number,
                    task_key=None,
                    message=message,
                    author=author,
                    link=link,
                )
            )
    return epic_tasks


def collect_tasks(commits, pr_number, repo):
    tasks: List[Dict] = []
    unique_epic_tasks: set = set()

    for commit in commits:
        commit_message = commit.commit.message
        if "Merge pull request" in commit_message:
            continue
        pulls = commit.get_pulls()
        for pull in pulls:
            if pull.number == pr_number or pull.mergeable:
                continue
            is_epic = False
            epic_tasks = []
            head_branch = pull.head.ref.split("/")
            if head_branch[0] == "epic" and len(head_branch) > 1:
                exist_pt = any(
                    task["is_epic"] and pull.number in task["number"] for task in tasks
                )
                if exist_pt:
                    continue
                logger.info("Epic found %s #%s", pull.title, pull.number)
                is_epic = True
                epic_tasks = process_epic_tasks(repo, pull.get_commits(), pull)
                task_keys = {
                    epic_task["task_key"]
                    for epic_task in epic_tasks
                    if epic_task["task_key"]
                }
                unique_epic_tasks = unique_epic_tasks.union(task_keys)
            process_pull(pull, commit_message, tasks, is_epic, epic_tasks)

    sorted_tasks = sorted(
        tasks, key=lambda x: (x["task_key"] is None, x["task_key"], x["is_epic"])
    )
    return sorted_tasks, unique_epic_tasks


def build_task_lines(tasks, yandex_tracker):
    result = []
    for task in tasks:
        task_key = task.get("task_key")
        author = task.get("author")
        task_numbers = task.get("number")
        links = task.get("links")
        markdown_links = ", ".join(
            [f"[#{task_num}]({link})" for task_num, link in zip(task_numbers, links)]
        )
        if task_key:
            title = yandex_tracker.get_issue_summary(task_key)
            if not title:
                logger.info("[%s] (No task found)", task_key)
                continue
            task_line = formatted_line(task_key, title, author, markdown_links)
        else:
            task_line = formatted_line(
                task_key, task.get("message"), author, markdown_links
            )
        result.append(task_line)
    return result


def create_draft_release(repo, pull_request, pr_description):
    # Create draft release if release or hotfix release
    status, release_type = check_is_release(pull_request)
    if not status:
        return
    release = update_or_create_draft_release(repo, release_type, pr_description)
    logger.info("Created new draft release %s", release.title)


def add_description_for_epic(epic_task, yandex_tracker):
    description_parts = []
    epic_task["author"] = None
    epic_task_lines = build_task_lines([epic_task], yandex_tracker)
    if epic_task_lines:
        description_parts.append(f"\r\n # Epic: {epic_task_lines[0]}")
    else:
        task_key = epic_task["task_key"]
        description_parts.append(f"\r\n # Epic: {task_key}")
    epic_result = build_task_lines(epic_task["tasks"], yandex_tracker)
    description_parts.extend(f"* {row}" for row in epic_result)
    epic_description = "\r\n".join(description_parts)
    return epic_description


def initialize():
    with open(GITHUB_EVENT_PATH, "r", encoding="utf8") as f:
        data = json.load(f)
    yandex_tracker = YandexTracker()
    gh = Github(GITHUB_TOKEN)
    repo = gh.get_repo(GITHUB_REPOSITORY)
    pr_number = int(data["pull_request"]["number"])
    pull_request = repo.get_pull(number=pr_number)
    commits = pull_request.get_commits()
    return yandex_tracker, repo, pull_request, commits


def build_description_parts(commits, pr_number, repo, yandex_tracker):
    description_parts = ["# What's Changed \r\n"]
    tasks, unique_epic_tasks = collect_tasks(commits, pr_number, repo)
    simple_tasks = [
        task
        for task in tasks
        if not task["is_epic"]
        and (task["task_key"] is None or task["task_key"] not in unique_epic_tasks)
    ]
    tasks_descriptions = build_task_lines(simple_tasks, yandex_tracker)
    description_parts.extend(f"* {row}" for row in tasks_descriptions)
    description_parts.extend(
        add_description_for_epic(task, yandex_tracker)
        for task in tasks
        if task["is_epic"]
    )
    return description_parts


def main():
    yandex_tracker, repo, pull_request, commits = initialize()
    # Collect commits and task numbers
    description_parts = build_description_parts(
        commits, pull_request, repo, yandex_tracker
    )
    pr_description = "\r\n".join(description_parts)
    change_pull_request_body(pull_request, pr_description)
    create_draft_release(repo, pull_request, pr_description)


if __name__ == "__main__":
    main()
