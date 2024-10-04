from unittest.mock import MagicMock, patch

from config.constants import EPIC_TITLE_NAME, MAIN_TITLE_NAME

from .base_test import BaseTestCase


class TestGithubServiceBuildDescriptionParts(BaseTestCase):

    @patch("helpers.github.Github")
    def test_build_description_parts(self, mock_github):
        # Настройка mock для методов GitHub
        github_service, _, _ = self.prepare_github_service(mock_github)

        # Мокируем метод collect_tasks
        LINK_EXAMPLE = "https://link.com"
        github_service.collect_tasks = MagicMock(
            return_value=(
                [  # Список задач
                    {
                        "is_epic": False,
                        "task_key": None,
                        "message": "Support: something",
                        "author": "user",
                        "number": [1],
                        "links": [LINK_EXAMPLE],
                    },
                    {
                        "is_epic": False,
                        "task_key": "ERP-1",
                        "message": None,
                        "author": "user",
                        "number": [2, 3],
                        "links": [LINK_EXAMPLE, LINK_EXAMPLE],
                    },
                    {
                        "is_epic": False,
                        "task_key": "ERP-2",
                        "message": None,
                        "author": "user",
                        "number": [3],
                        "links": [LINK_EXAMPLE],
                    },
                    {
                        "is_epic": False,
                        "task_key": "Backend",
                        "message": None,
                        "author": "user",
                        "number": [3],
                        "links": [LINK_EXAMPLE],
                    },
                    {
                        "is_epic": True,
                        "task_key": "ERP-5",
                        "number": [4],
                        "links": [LINK_EXAMPLE],
                        "tasks": [
                            {
                                "is_epic": False,
                                "task_key": "ERP-2",
                                "message": None,
                                "author": "user",
                                "number": [5],
                                "links": [LINK_EXAMPLE],
                            },
                            {
                                "is_epic": False,
                                "task_key": "ERP-3",
                                "message": None,
                                "author": "user",
                                "number": [5],
                                "links": [LINK_EXAMPLE],
                            },
                        ],
                    },
                ],
                {"ERP-2"},  # Уникальные эпические задачи
            )
        )

        # Вызываем тестируемый метод
        description_parts = github_service.build_description_parts()
        epic_description = (
            f"\n {EPIC_TITLE_NAME}: [[ERP-5](https://tracker.yandex.ru/ERP-5)] ERP-5 in [#4](https://link.com)\n"
            "* [[ERP-2](https://tracker.yandex.ru/ERP-2)] ERP-2 by @user in [#5](https://link.com)\n"
            "* [[ERP-3](https://tracker.yandex.ru/ERP-3)] ERP-3 by @user in [#5](https://link.com)"
        )
        # Проверяем результат
        expected_description = [
            MAIN_TITLE_NAME,
            "* Support: something by @user in [#1](https://link.com)",
            "* [[ERP-1](https://tracker.yandex.ru/ERP-1)] ERP-1 by @user in [#2](https://link.com), [#3](https://link.com)",
            epic_description,
        ]
        self.assertEqual(description_parts, expected_description)
