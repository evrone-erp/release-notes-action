from unittest.mock import MagicMock, patch

from config.constants import MAIN_TITLE_NAME

from .base_test import BaseTestCase
from .utils import LINK_EXAMPLE


class TestGithubServiceHotfixBranchPrepare(BaseTestCase):

    @patch("helpers.github.Github")
    def test_hotfix_branch_prepare(self, mock_github):
        # Настройка mock для методов GitHub
        github_service, _, mock_pull_request = self.prepare_github_service(mock_github)
        mock_pull_request.head.ref = "hotfix/fix_something"
        mock_pull_request.number = 1
        mock_pull_request.html_url = LINK_EXAMPLE

        commits_messages = [
            "Merge pull request",
            "Fix anything",
            "[ERP-23] fix error",
        ]
        github_service.main_commits = []
        for commit_message in commits_messages:
            commit = MagicMock()
            commit.commit.message = commit_message
            commit.author.login = "user"
            github_service.main_commits.append(commit)
        description_parts = github_service.build_description_parts()
        expected_description_parts = [
            MAIN_TITLE_NAME,
            "* [[ERP-23](https://tracker.yandex.ru/ERP-23)] ERP-23 by @user in [#1](https://link.com)",
            "* Fix anything by @user in [#1](https://link.com)",
        ]
        self.assertEqual(description_parts, expected_description_parts)
