from typing import Any, Dict, List, Optional

from github import Commit

from config.constants import TASK_KEY_PATTERN


class HotfixMixin:
    """
    Миксин для работы с ветками hotfix в GitHub.
    """

    def _add_hotfix_task_dict(
        self, commit: Commit.Commit, task_key: Optional[str] = None
    ):
        return {
            "is_epic": False,
            "number": [self.main_pull_request.number],  # type: ignore[attr-defined]
            "links": [self.main_pull_request.html_url],  # type: ignore[attr-defined]
            "message": commit.commit.message if task_key is None else None,
            "author": commit.author.login,
            "task_key": task_key,
            "tasks": [],
        }

    def collect_hotfix_tasks(self) -> List[Dict[str, Any]]:
        for commit in self.main_commits:  # type: ignore[attr-defined]
            commit_message = commit.commit.message
            if "Merge pull request" in commit_message:
                continue
            all_matches = self.extract_task_keys(commit_message, TASK_KEY_PATTERN)  # type: ignore[attr-defined]
            if all_matches:
                for task_key in all_matches:
                    self.tasks.append(self._add_hotfix_task_dict(commit, task_key))  # type: ignore[attr-defined]
            else:
                self.tasks.append(self._add_hotfix_task_dict(commit, task_key=None))  # type: ignore[attr-defined]
        sorted_tasks = sorted(
            self.tasks,  # type: ignore[attr-defined]
            key=lambda x: (x["task_key"] is None, x["task_key"], x["is_epic"]),
        )
        return sorted_tasks
