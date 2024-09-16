from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

from .base_test import BaseTestCase
from .utils import get_tasks4proces_pull


class TestGithubServiceProcessPull(BaseTestCase):

    @patch("helpers.github.Github")
    def test_process_pull(self, mock_github):
        github_service, _, _ = self.prepare_github_service(mock_github)
        pull_requests_data: List[Dict[str, Any]] = get_tasks4proces_pull()

        github_service.tasks = [
            {
                "is_epic": False,
                "number": [7],
                "links": ["https://some_url.com"],
                "message": "Pull title 7",
                "author": "user",
                "task_key": None,
                "tasks": [],
            }
        ]

        for pr_data in pull_requests_data:
            pull_request = MagicMock()
            pull_request.number = pr_data["pull"]["number"]
            pull_request.html_url = pr_data["pull"]["html_url"]
            pull_request.title = pr_data["pull"]["title"]
            pull_request.user.login = pr_data["pull"]["user.login"]
            github_service.process_pull(pull_request, pr_data["commit_message"])
        self.assertEqual(len(github_service.tasks), 7)
