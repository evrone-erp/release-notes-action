from unittest.mock import MagicMock, patch

from config.constants import EPIC_TITLE_NAME, MAIN_TITLE_NAME

from .base_test import BaseTestCase
from .utils import LINK_EXAMPLE, get_tasks_with_epic


class TestGithubServiceEpicTasks(BaseTestCase):

    @patch("helpers.github.Github")
    def test_epic_tasks(self, mock_github):
        # Создаем мок репозитория и Pull Request
        github_service, mock_repo, _ = self.prepare_github_service(mock_github)
        commits_data = get_tasks_with_epic()
        github_service.main_commits = []
        for commit in commits_data:
            mock_commit = MagicMock()
            mock_commit.commit.message = commit.get("commit.message")
            commit_pulls = []
            for pull in commit["pulls"]:
                pull_request = MagicMock()
                pull_request.number = pull.get("number")
                pull_request.mergeable = pull.get("mergeable")
                pull_request.head.ref = pull.get("head.ref")
                pull_request.title = pull.get("title")
                pull_request.user.login = pull.get("user.login")
                pull_request.html_url = pull.get("html_url")
                epic_commits = []
                for epic_commit in pull.get("epic_commits", []):
                    epic_commit_instance = MagicMock()
                    epic_commit_instance.commit.message = epic_commit.get(
                        "commit.message"
                    )
                    epic_commits.append(epic_commit_instance)
                pull_request.get_commits = MagicMock(return_value=epic_commits)
                commit_pulls.append(pull_request)
            mock_commit.get_pulls = MagicMock(return_value=commit_pulls)
            github_service.main_commits.append(mock_commit)

        mock_repo.get_pull = MagicMock(
            return_value=MagicMock(html_url=LINK_EXAMPLE, number=5)
        )

        description_parts = github_service.build_description_parts()

        expected_parts = [
            MAIN_TITLE_NAME,
            "* [[ERP-4](https://tracker.yandex.ru/ERP-4)] ERP-4 by @user in [#4](https://link.com)",
            (
                f"\n {EPIC_TITLE_NAME}: 1\n* "
                "[[ERP-5](https://tracker.yandex.ru/ERP-5)] ERP-5 by @user in [#5](https://link.com)\n* "
                "[[ERP-6](https://tracker.yandex.ru/ERP-6)] ERP-6 by @user in [#5](https://link.com)"
            ),
        ]
        self.assertEqual(description_parts, expected_parts)
