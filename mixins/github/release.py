from typing import Optional

from github import GitRelease
from github.GithubException import UnknownObjectException

from config.logger_config import logger


class ReleaseMixin:
    """
    Миксин для работы с релизами в GitHub.
    """

    def create_draft_release(self, pr_description: str) -> None:
        """
        Создаёт черновик релиза, если текущая ветка является релизной или хотфиксной.

        :param pr_description: Описание pull request.
        """
        status, release_type = self.check_is_release()
        if not status:
            return

        self.update_or_create_draft_release(release_type, pr_description)

    def check_is_release(self) -> tuple[bool, str]:
        """
        Проверяет, является ли текущая ветка релизной или хотфиксной.

        :return: Кортеж с флагом и типом релиза.
        """
        branch_name = self.main_pull_request.head.ref.lower()  # type: ignore[attr-defined]
        release_type = branch_name.split("/")[0]

        if (
            release_type not in ("release", "hotfix")
            or self.main_pull_request.base.ref != "master"  # type: ignore[attr-defined]
        ):
            return False, ""

        return True, release_type

    def update_or_create_draft_release(
        self, release_type: str, pr_description: str
    ) -> None:
        """
        Обновляет существующий черновик релиза или создаёт новый.

        :param release_type: Тип релиза ("release" или "hotfix").
        :param pr_description: Описание pull request.
        :return: Объект GitRelease.
        """
        last_version = self._get_latest_release_version()
        new_version = self.get_new_release_version(last_version, release_type)
        if current_release := self._check_draft_release_exist(new_version):
            self._update_release(current_release, pr_description)
            return
        self._create_release(pr_description, new_version, release_type)

    def _get_latest_release_version(self) -> str:
        """
        Получает последнюю версию релиза из GitHub.

        :return: Строка с последней версией релиза.
        """
        release_version = "1.0.0"
        try:
            latest_release = self.repo.get_latest_release()  # type: ignore[attr-defined]
            release_version = latest_release.tag_name.strip().replace("v", "")
        except UnknownObjectException:
            logger.info("No releases yet")

        return release_version

    def _check_draft_release_exist(
        self, last_version: str
    ) -> Optional[GitRelease.GitRelease]:
        """
        Проверяет существование черновика релиза с указанной версией.

        :param last_version: Последняя версия релиза.
        :return: Объект GitRelease или None.
        """
        releases = self.repo.get_releases()  # type: ignore[attr-defined]
        current_version_releases = [
            release for release in releases if last_version in release.tag_name
        ]

        if not current_version_releases:
            return None

        return current_version_releases[0]

    def get_new_release_version(self, last_version: str, release_type: str) -> str:
        """
        Генерирует новую версию релиза на основе последней версии и типа релиза.

        :param last_version: Последняя версия релиза.
        :param release_type: Тип релиза ("release" или "hotfix").
        :return: Новая версия релиза.
        """
        logger.info("get_new_release_version last_version: %s", last_version)
        main_version, release_version, hotfix_version = [
            int(version) for version in last_version.split(".")
        ]

        if release_type == "release":
            release_version += 1
            hotfix_version = 0
        elif release_type == "hotfix":
            hotfix_version += 1

        return f"{main_version}.{release_version}.{hotfix_version}"

    @staticmethod
    def _update_release(release: GitRelease.GitRelease, new_body: str) -> None:
        """
        Обновляет существующий черновик релиза.

        :param release: Объект GitRelease.
        :param new_body: Новое описание релиза.
        """
        release.update_release(
            name=release.title,  # Оставляем текущее название
            message=new_body,  # Обновляемое тело релиза
            draft=release.draft,  # Сохраняем текущее состояние draft
            prerelease=release.prerelease,  # Сохраняем текущее состояние prerelease
        )

    def _create_release(self, description: str, version: str, release_type: str):
        title_prefix = "Release" if release_type == "release" else "Hotfix release"
        title = f"{title_prefix} {version}"
        self.repo.create_git_release(  # type: ignore[attr-defined]
            tag=f"v{version}",
            name=title,
            message=description,
            draft=True,
            prerelease=True,
            target_commitish="master",
        )
