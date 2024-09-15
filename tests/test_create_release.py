from unittest.mock import MagicMock, patch

from .base_test import BaseTestCase


class TestGithubServiceCreateRelease(BaseTestCase):

    @patch("helpers.github.Github")
    def test_update_create_release(self, mock_github):
        # Настройка mock для методов GitHub
        github_service, mock_repo, _ = self.prepare_github_service(mock_github)

        # Drfaft release not exist
        releases = ["1.0.0"]
        mocked_releases = []
        for release_version in releases:
            release = MagicMock()
            release.tag_name = f"v {release_version}"
            mocked_releases.append(release)

        mock_repo.get_latest_release = MagicMock(
            return_value=MagicMock(tag_name="v 1.0.0 ")
        )
        mock_repo.get_releases = MagicMock(return_value=mocked_releases)
        mock_repo.create_git_release = MagicMock(return_value=True)

        release_type = "release"
        description = "some_description"

        github_service.update_or_create_draft_release(release_type, description)

        # Ассерт на вызов метода create_git_release с нужными аргументами
        mock_repo.create_git_release.assert_called_once_with(
            tag="v1.1.0",  # Пример: в зависимости от логики обновления версии
            name="Release 1.1.0",
            message=description,
            draft=True,
            prerelease=True,
            target_commitish="master",
        )
