from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

from .base_test import BaseTestCase
from .utils import get_tasks4_create


class TestGithubServiceCreateTask(BaseTestCase):

    @patch("helpers.github.Github")
    def test_create_task_dict(self, mock_github):
        # Создаем мок репозитория и Pull Request
        github_service, _, _ = self.prepare_github_service(mock_github)
        tasks4add: List[Dict[str, Any]] = get_tasks4_create()

        for task in tasks4add:
            pull_request = MagicMock()
            pull_request.number = task["pull"]["number"]
            pull_request.html_url = task["pull"]["html_url"]
            pull_request.title = task["pull"]["title"]
            pull_request.user.login = task["pull"]["user.login"]
            created_task = github_service.create_task_dict(
                pull_request, task["task_key"], task["is_epic"], []
            )
            expected_value = {
                "is_epic": task["is_epic"],
                "number": [pull_request.number],
                "links": [pull_request.html_url],
                "message": pull_request.title if task["task_key"] is None else None,
                "author": pull_request.user.login,
                "task_key": task["task_key"],
                "tasks": [],
            }
            self.assertEqual(created_task, expected_value)
