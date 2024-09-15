import json
import unittest
from unittest.mock import MagicMock, patch

from helpers.github import GithubService


class TestGithubServiceInit(unittest.TestCase):

    @patch("helpers.github.Github")
    def test_init(self, mock_github):
        # Настраиваем mocks для GitHub и YandexTracker
        mock_repo = MagicMock()
        mock_pull_request = MagicMock()
        mock_commits = MagicMock()
        mock_tracker = MagicMock()

        # Возвращаемые значения моков
        mock_github_instance = mock_github.return_value
        mock_github_instance.get_repo.return_value = mock_repo
        mock_repo.get_pull.return_value = mock_pull_request
        mock_pull_request.get_commits.return_value = mock_commits

        # Мок данных для json файла
        github_data_path = "mock_data.json"
        data = {"pull_request": {"number": 1}}

        # Мокируем open для чтения данных из файла
        with patch(
            "builtins.open", unittest.mock.mock_open(read_data=json.dumps(data))
        ):
            service = GithubService(
                github_data_path, "fake_token", "fake_repo", mock_tracker
            )

        # Проверка инициализации
        mock_github.assert_called_once_with("fake_token")
        mock_github_instance.get_repo.assert_called_once_with("fake_repo")
        mock_repo.get_pull.assert_called_once_with(number=1)
        self.assertEqual(service.main_pull_request, mock_pull_request)
        self.assertEqual(service.main_commits, mock_commits)
        self.assertEqual(service.yandex_tracker, mock_tracker)
