from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

from .base_test import BaseTestCase


class TestGithubServiceCollectTasks(BaseTestCase):

    @patch("helpers.github.Github")
    def test_collect_tasks(self, mock_github):
        # Создаем мок репозитория и Pull Request
        github_service, _, mock_pull_request = self.prepare_github_service(mock_github)

        # Настраиваем Pull Request
        mock_pull_request.number = 1
        mock_pull_request.head.ref = "feature/some-feature"
        mock_pull_request.mergeable = True

        # Мокаем `_process_epic_tasks` и `process_pull` для упрощения теста
        github_service._process_epic_tasks = MagicMock(  # pylint: disable=W0212
            return_value=[]
        )
        LINK_EXAMPLE = "https://link.com"
        commits_data: List[Dict[str, Any]] = [
            {
                "message": "Support: fixed a bug",
                "pulls": [
                    {
                        "mergeable": False,
                        "number": 2,
                        "head.ref": "feature/2",
                        "user.login": "user",
                        "title": "Support: fixed a bug",
                        "html_url": LINK_EXAMPLE,
                    }
                ],
            },
            {
                "message": "Merge pull request 3",
                "pulls": [
                    {
                        "mergeable": False,
                        "number": 3,
                        "head.ref": "feature/3",
                        "user.login": "user",
                        "title": "Merge pull request 3",
                        "html_url": LINK_EXAMPLE,
                    }
                ],
            },
            {
                "message": "Merge pull request 3",
                "pulls": [
                    {
                        "mergeable": False,
                        "number": 3,
                        "head.ref": "feature/3",
                        "user.login": "user",
                        "title": "Merge pull request 3",
                        "html_url": LINK_EXAMPLE,
                    }
                ],
            },
            {
                "message": "[ERP-163] New feature",
                "pulls": [
                    {
                        "mergeable": True,
                        "number": 4,
                        "head.ref": "feature/4",
                        "user.login": "user",
                        "title": "[ERP-163] Need to miss",
                        "html_url": LINK_EXAMPLE,
                    },
                    {
                        "mergeable": False,
                        "number": 1,
                        "head.ref": "feature/1",
                        "user.login": "user",
                        "title": "[ERP-163] Need to miss",
                        "html_url": LINK_EXAMPLE,
                    },
                    {
                        "mergeable": False,
                        "number": 4,
                        "head.ref": "feature/4",
                        "user.login": "user",
                        "title": "[ERP-163] New feature",
                        "html_url": LINK_EXAMPLE,
                    },
                ],
            },
        ]
        main_commits = []
        for commit in commits_data:
            mock_commit = MagicMock()
            mock_commit.commit.message = commit["message"]
            mock_pulls = []
            for pull in commit["pulls"]:
                mocked_pull = MagicMock()
                mocked_pull.mergeable = pull["mergeable"]
                mocked_pull.number = pull["number"]
                mocked_pull.head.ref = pull["head.ref"]
                mocked_pull.user.login = pull["user.login"]
                mocked_pull.title = pull["title"]
                mocked_pull.html_url = pull["html_url"]
                mock_pulls.append(mocked_pull)
            mock_commit.get_pulls = MagicMock(return_value=mock_pulls)
            main_commits.append(mock_commit)
        github_service.main_commits = main_commits

        # Вызываем тестируемый метод
        tasks, unique_epic_tasks = github_service.collect_tasks()

        # Ожидаемый результат
        expected_tasks = [
            {
                "is_epic": False,
                "number": [4],
                "links": ["https://link.com"],
                "message": None,
                "author": "user",
                "task_key": "ERP-163",
                "tasks": [],
            },
            {
                "is_epic": False,
                "number": [2],
                "links": ["https://link.com"],
                "message": "Support: fixed a bug",
                "author": "user",
                "task_key": None,
                "tasks": [],
            },
        ]
        # Проверяем результат
        self.assertEqual(tasks, expected_tasks)
        self.assertEqual(unique_epic_tasks, set())
