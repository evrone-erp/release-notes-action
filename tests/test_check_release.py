from unittest.mock import patch

from .base_test import BaseTestCase


class TestGithubServiceBuildCheckRelease(BaseTestCase):

    @patch("helpers.github.Github")
    def test_build_check_release(self, mock_github):
        # Настройка mock для методов GitHub
        github_service, _, mock_pull_request = self.prepare_github_service(mock_github)

        # feature branch, not release
        mock_pull_request.base.ref = "master"
        mock_pull_request.head.ref = "feature/ERP-1/some_task"
        is_release, release_type = github_service.check_is_release()
        self.assertFalse(is_release)
        self.assertEqual(release_type, "")

        # release branch in master
        mock_pull_request.head.ref = "release/ERP-1/some_task"
        is_release, release_type = github_service.check_is_release()
        self.assertTrue(is_release)
        self.assertEqual(release_type, "release")

        # hotfix branch in master
        mock_pull_request.head.ref = "hotfix/ERP-1/some_task"
        is_release, release_type = github_service.check_is_release()
        self.assertTrue(is_release)
        self.assertEqual(release_type, "hotfix")

        # release branch not in master
        mock_pull_request.base.ref = "development"
        is_release, release_type = github_service.check_is_release()
        self.assertFalse(is_release)
        self.assertEqual(release_type, "")
