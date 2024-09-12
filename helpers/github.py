import json
import re
from typing import Dict, List, Optional, Set, Tuple

# isort: off
from github import Github  # type: ignore  # pylint: disable=no-name-in-module
from github import PullRequest

# isort: on

from config.constants import TASK_KEY_PATTERN
from config.logger_config import logger
from mixins.github import EpicTaskMixin, ReleaseMixin

from .yandex_tracker import YandexTracker


class GithubService(EpicTaskMixin, ReleaseMixin):

    def __init__(
        self,
        github_data_path: str,
        token: str,
        repo_name: str,
        yt_service: YandexTracker,
    ):
        # Загружаем данные из файла и инициализируем объекты Github и YandexTracker
        with open(github_data_path, "r", encoding="utf8") as f:
            data = json.load(f)
        gh = Github(token)
        self.repo = gh.get_repo(repo_name)
        pr_number = int(data["pull_request"]["number"])
        self.main_pull_request = self.repo.get_pull(number=pr_number)
        self.main_commits = self.main_pull_request.get_commits()
        self.yandex_tracker = yt_service
        self.tasks: List[Dict] = []

    def build_description_parts(self) -> List[str]:
        """
        Формирует части описания для Pull Request.

        :return: Список строк, представляющих описание изменений.
        """
        description_parts = ["# What's Changed \r\n"]
        tasks, unique_epic_tasks = self._collect_tasks()

        # Список задач, которые не являются эпиками и не привязаны к эпическим задачам
        simple_tasks = [
            task
            for task in tasks
            if not task["is_epic"]
            and (task["task_key"] is None or task["task_key"] not in unique_epic_tasks)
        ]
        tasks_descriptions = self.build_task_lines(simple_tasks)

        description_parts.extend(f"* {row}" for row in tasks_descriptions)
        description_parts.extend(
            self.add_description_for_epic(task) for task in tasks if task["is_epic"]
        )

        return description_parts

    def build_task_lines(self, tasks: List[Dict]) -> List[str]:
        """
        Формирует строки задач для описания Pull Request.

        :param tasks: Список задач.
        :return: Список строк в формате Markdown.
        """
        result = []
        for task in tasks:
            task_key = task.get("task_key")
            author = task.get("author")
            task_numbers: List[int] = task.get("number", [])
            links: List[str] = task.get("links", [])
            markdown_links = ", ".join(
                f"[#{task_num}]({link})" for task_num, link in zip(task_numbers, links)
            )

            if task_key:
                # Получаем заголовок задачи из YandexTracker по ключу
                title = self.yandex_tracker.get_issue_summary(task_key)
                if not title:
                    logger.info("[%s] (No task found)", task_key)
                    continue
                task_line = self.formatted_line(task_key, title, author, markdown_links)
            else:
                task_line = self.formatted_line(
                    task_key, task.get("message"), author, markdown_links
                )
            result.append(task_line)
        return result

    def _collect_tasks(self) -> Tuple[List[Dict], Set[str]]:
        """
        Собирает задачи из коммитов, связанных с Pull Request.

        :return: Кортеж из списка задач и уникальных ключей эпических задач.
        """
        unique_epic_tasks: Set[str] = set()

        for commit in self.main_commits:
            commit_message = commit.commit.message
            if "Merge pull request" in commit_message:
                continue
            pulls = commit.get_pulls()
            for pull in pulls:
                if pull.number == self.main_pull_request.number or pull.mergeable:
                    continue
                is_epic = False
                epic_tasks = []
                head_branch = pull.head.ref.split("/")
                if head_branch[0] == "epic" and len(head_branch) > 1:
                    exist_pt = any(
                        task["is_epic"] and pull.number in task["number"]
                        for task in self.tasks
                    )
                    if exist_pt:
                        continue
                    logger.info("Epic found %s #%s", pull.title, pull.number)
                    is_epic = True
                    epic_tasks = self._process_epic_tasks(pull)
                    task_keys = {
                        epic_task["task_key"]
                        for epic_task in epic_tasks
                        if epic_task["task_key"]
                    }
                    unique_epic_tasks.update(task_keys)
                self.process_pull(pull, commit_message, is_epic, epic_tasks)

        sorted_tasks = sorted(
            self.tasks,
            key=lambda x: (x["task_key"] is None, x["task_key"], x["is_epic"]),
        )
        return sorted_tasks, unique_epic_tasks

    def process_pull(
        self,
        pull: PullRequest.PullRequest,
        commit_message: str,
        is_epic: bool = False,
        epic_tasks: Optional[List[Dict]] = None,
    ):
        """
        Обрабатывает pull request и обновляет список задач.

        :param pull: Объект pull request.
        :param commit_message: Сообщение коммита.
        :param is_epic: Флаг, является ли pull request эпиком.
        :param epic_tasks: Список задач, связанных с эпиком.
        """
        if is_epic:
            pull_head = pull.head.ref.split("/")
            task_key = pull_head[1]
            self.update_or_create_task(pull, task_key, is_epic, epic_tasks)
            return
        all_matches = self.extract_task_keys(commit_message, TASK_KEY_PATTERN)
        if all_matches:
            for task_key in all_matches:
                self.update_or_create_task(pull, task_key, is_epic, epic_tasks)
        else:
            self.tasks.append(
                self.create_task_dict(pull=pull, is_epic=is_epic, epic_tasks=epic_tasks)
            )

    def update_or_create_task(
        self,
        pull: PullRequest.PullRequest,
        task_key: str,
        is_epic: bool = False,
        epic_tasks: Optional[List[Dict]] = None,
    ):
        """
        Обновляет существующую задачу или создаёт новую.

        :param pull: Объект pull request.
        :param task_key: Ключ задачи.
        :param is_epic: Флаг, является ли задача эпической.
        :param epic_tasks: Список задач, связанных с эпиком.
        """
        task_indexes = [
            i
            for i, task in enumerate(self.tasks)
            if task["task_key"] == task_key and task["author"] == pull.user.login
        ]
        if not task_indexes:
            self.tasks.append(
                self.create_task_dict(pull, task_key, is_epic, epic_tasks)
            )
            return
        for task_index in task_indexes:
            if pull.number not in self.tasks[task_index]["number"]:
                self.tasks[task_index]["number"].append(pull.number)
                self.tasks[task_index]["links"].append(pull.html_url)
            if is_epic and epic_tasks is not None:
                self.collect_epic_tasks(epic_tasks, task_index)

    @staticmethod
    def formatted_line(
        task_key: Optional[str],
        title: Optional[str],
        user_login: Optional[str],
        pr_numbers: str,
    ) -> str:
        """
        Форматирует строку для описания задачи.

        :param task_key: Ключ задачи.
        :param title: Заголовок задачи.
        :param user_login: Логин пользователя.
        :param pr_numbers: Номера pull request.
        :return: Строка в формате Markdown.
        """
        task_key_str = (
            f"[[{task_key}](https://tracker.yandex.ru/{task_key})] " if task_key else ""
        )
        user_login_str = f" by @{user_login}" if user_login else ""
        return f"{task_key_str}{title}{user_login_str} in {pr_numbers}"

    @staticmethod
    def extract_task_keys(commit_message: str, pattern: re.Pattern) -> Set[str]:
        """
        Извлекает ключи задач из сообщения коммита.

        :param commit_message: Сообщение коммита.
        :param pattern: Регулярное выражение для поиска ключей задач.
        :return: Множество ключей задач.
        """
        return {
            key.strip()
            for keys in pattern.findall(commit_message)
            for key in keys.split(",")
        }

    @staticmethod
    def create_task_dict(
        pull: PullRequest.PullRequest,
        task_key: Optional[str] = None,
        is_epic: bool = False,
        epic_tasks: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Создает словарь задачи.

        :param pull: Объект pull request.
        :param task_key: Ключ задачи.
        :param is_epic: Флаг, является ли задача эпической.
        :param epic_tasks: Список задач, связанных с эпиком.
        :return: Словарь задачи.
        """
        return {
            "is_epic": is_epic,
            "number": [pull.number],
            "links": [pull.html_url],
            "message": pull.title if task_key is None else None,
            "author": pull.user.login,
            "task_key": task_key,
            "tasks": epic_tasks,
        }

    def change_pull_request_body(self, body: str):
        """
        Изменяет тело основного pull request.

        :param body: Новое тело pull request.
        """
        self.main_pull_request.edit(body=body)
