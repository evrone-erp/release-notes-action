import json
import unittest
from unittest.mock import MagicMock, patch

from helpers.github import GithubService
from helpers.yandex_tracker import YandexTracker


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        # Патчим requests.post внутри метода setUp
        self.patcher = patch("requests.post")
        mock_post = self.patcher.start()

        # Создаем фиктивный ответ, который будет возвращен вместо реального вызова requests.post
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"iamToken": "fake_iam_token"}
        mock_post.return_value = mock_response

        ya_org_id = "fake_org_id"
        ya_token = "fake_token"  # noqa

        # Создаем экземпляр YandexTracker, который будет использовать замоканный requests.post
        self.mocked_tracker = YandexTracker(ya_org_id, ya_token)
        # Используем patch.object для замены метода get_issue_summary
        patch.object(
            self.mocked_tracker,
            "get_issue_summary",
            side_effect=lambda task_key: task_key if "ERP" in task_key else None,
        ).start()

    def prepare_github_service(self, mock_github):
        """
        Общий метод для подготовки github_service и его моков.
        """
        # Создаем мок репозитория и Pull Request
        mock_repo = MagicMock()
        mock_pull_request = MagicMock()

        # Настраиваем возвращаемые значения для методов
        mock_repo.get_pull.return_value = mock_pull_request
        mock_github_instance = mock_github.return_value
        mock_github_instance.get_repo.return_value = mock_repo

        # Настраиваем данные для тестов
        github_data_path = "mock_data.json"
        data = {"pull_request": {"number": 1}}

        # Мокируем чтение данных из файла
        with patch(
            "builtins.open", unittest.mock.mock_open(read_data=json.dumps(data))
        ):
            github_service = GithubService(
                github_data_path, "fake_token", "fake_repo", self.mocked_tracker
            )

        return github_service, mock_repo, mock_pull_request
