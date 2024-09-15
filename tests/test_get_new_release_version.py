from unittest.mock import patch

from .base_test import BaseTestCase


class TestGithubServiceBuildGetReleaseVersion(BaseTestCase):

    @patch("helpers.github.Github")
    def test_build_get_release_version(self, mock_github):
        # Настройка mock для методов GitHub
        github_service, _, _ = self.prepare_github_service(mock_github)

        # Is not release
        last_version = "1.0.1"
        release_type = None
        new_release_version = github_service.get_new_release_version(
            last_version, release_type
        )
        self.assertEqual(new_release_version, last_version)

        # Is release
        release_type = "release"
        new_release_version = github_service.get_new_release_version(
            last_version, release_type
        )
        self.assertEqual(new_release_version, "1.1.0")

        # Is hotfix
        release_type = "hotfix"
        new_release_version = github_service.get_new_release_version(
            last_version, release_type
        )
        self.assertEqual(new_release_version, "1.0.2")
