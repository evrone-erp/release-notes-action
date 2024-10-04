from typing import Any, Dict, List, Optional

from github import PullRequest

# conflict with black linter
# isort: off
from config.constants import (
    EPIC_TITLE_NAME,
    MERGE_PULL_REQUEST_PATTERN,
    TASK_KEY_PATTERN,
)

# isort: on


class EpicTaskMixin:
    """
    Миксин для обработки эпических задач из pull requests.
    """

    def _process_epic_tasks(self, pull: PullRequest.PullRequest) -> List[Dict]:
        """
        Обрабатывает задачи, связанные с эпическим pull request.

        :param pull: Объект pull request.
        :return: Список словарей с информацией о задачах.
        """
        epic_tasks: List[Dict] = []
        commits = pull.get_commits()

        for commit in commits:
            if "Merge pull request" not in commit.commit.message:
                continue

            # Извлекаем номер pull request, ссылку, автора и сообщение коммита
            pull_number = pull.number
            link = pull.html_url
            author = pull.user.login
            message = commit.commit.message

            # Проверка на наличие ссылки на другой pull request в сообщении коммита
            match = MERGE_PULL_REQUEST_PATTERN.search(message)
            if match:
                pull_number = int(match.group(1))
                pull_request = self.repo.get_pull(number=pull_number)  # type: ignore[attr-defined]
                link = pull_request.html_url

            # Определение автора pull request, связанного с коммитом
            cur_pulls = commit.get_pulls()
            for cur_pull in cur_pulls:
                if cur_pull.number == pull.number:
                    author = cur_pull.user.login
                    break

            # Извлечение ключей задач из сообщения коммита
            all_matches = self.extract_task_keys(message, TASK_KEY_PATTERN)  # type: ignore[attr-defined]
            if all_matches:
                epic_tasks.extend(
                    self.create_epic_task(pull_number, task_key, message, author, link)
                    for task_key in all_matches
                )
            else:
                epic_tasks.append(
                    self.create_epic_task(
                        pull_number=pull_number,
                        task_key=None,
                        message=message,
                        author=author,
                        link=link,
                    )
                )
        sorted_tasks = sorted(
            epic_tasks,
            key=lambda x: (x["task_key"] is None, x["task_key"]),
        )
        return sorted_tasks

    def collect_epic_tasks(self, epic_tasks: List[Dict], task_index: int):
        """
        Собирает задачи для эпика и добавляет их к соответствующему индексу задачи.

        :param epic_tasks: Список задач для эпика.
        :param task_index: Индекс задачи в общем списке задач.
        """
        current_epic_tasks = self.tasks[task_index]["tasks"]  # type: ignore[attr-defined]
        for epic_task in epic_tasks:
            epic_task_exist = any(
                task["task_key"] == epic_task["task_key"]
                and task["message"] == epic_task["message"]
                for task in current_epic_tasks
            )
            if epic_task_exist:
                continue
            self.tasks[task_index]["tasks"].append(epic_task)  # type: ignore[attr-defined]

    def add_description_for_epic(self, epic_task: Dict) -> str:
        """
        Добавляет описание для эпической задачи.

        :param epic_task: Словарь с информацией о эпической задаче.
        :return: Строка с описанием эпической задачи.
        """
        description_parts: List[str] = []
        epic_task["author"] = None
        epic_task_lines = self.build_task_lines([epic_task])  # type: ignore[attr-defined]

        if epic_task_lines:
            description_parts.append(f"\n {EPIC_TITLE_NAME}: {epic_task_lines[0]}")
        else:
            task_key = epic_task["task_key"]
            description_parts.append(f"\n {EPIC_TITLE_NAME}: {task_key}")

        epic_result = self.build_task_lines(epic_task["tasks"])  # type: ignore[attr-defined]
        description_parts.extend(f"* {row}" for row in epic_result)
        return "\n".join(description_parts)

    @staticmethod
    def create_epic_task(
        pull_number: int, task_key: Optional[str], message: str, author: str, link: str
    ) -> Dict[str, Any]:
        """
        Создает словарь с информацией о эпической задаче.

        :param pull_number: Номер pull request.
        :param task_key: Ключ задачи.
        :param message: Сообщение коммита.
        :param author: Автор коммита.
        :param link: Ссылка на pull request.
        :return: Словарь с информацией о эпической задаче.
        """
        return {
            "number": [pull_number],
            "links": [link],
            "message": message if task_key is None else None,
            "author": author,
            "task_key": task_key,
        }
