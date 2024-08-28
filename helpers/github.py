from github.GithubException import UnknownObjectException

from config.logger_config import logger

MARKDOWN_LINK = "{}{} by @{} in {}"


def formatted_line(task_key, title, user_login, pr_numbers):
    task_key = (
        f"[[{task_key}](https://tracker.yandex.ru/{task_key})] " if task_key else ""
    )
    return MARKDOWN_LINK.format(task_key, title, user_login, pr_numbers)


def change_pull_request_body(pull_request, body):
    pull_request.edit(body=body)


def check_is_release(pull_request):
    branch_name = pull_request.head.ref.lower()
    release_type = branch_name.split("/")[0]
    if (
        release_type
        not in (
            "release",
            "hotfix",
        )
        or pull_request.base.ref != "master"
    ):
        return False, None
    return True, release_type


def get_latest_release_version(repo):
    release_version = "1.0.0"
    try:
        latest_release = repo.get_latest_release()
        release_version = latest_release.tag_name.strip().replace("v", "")
    except UnknownObjectException:
        logger.info("No releases yet")
    return release_version


def get_new_release_version(last_version: str, release_type: str) -> str:
    logger.info("get_new_release_version last_versionЖ %s", last_version)
    main_version, release_version, hotfix_version = [
        int(version) for version in last_version.split(".")
    ]
    if release_type == "release":
        release_version += 1
        hotfix_version = 0
    if release_type == "hotfix":
        hotfix_version += 1
    return f"{main_version}.{release_version}.{hotfix_version}"


def check_draft_release_exist(repo, last_version):
    releases = repo.get_releases()
    current_version_releases = [
        release for release in releases if last_version in release.tag_name
    ]
    if not current_version_releases:
        return None
    return current_version_releases[0]


def update_release(release, new_body: str):
    release.update_release(
        name=release.title,  # Можно оставить текущее название
        message=new_body,  # Обновляемое тело релиза
        draft=release.draft,  # Сохраняем текущее состояние draft
        prerelease=release.prerelease,  # Сохраняем текущее состояние prerelease
    )


def create_release(repo, description: str, version: str, release_type: str):
    title_prefix = "Release" if release_type == "release" else "Hotfix release"
    title = f"{title_prefix} {version}"
    return repo.create_git_release(
        tag=f"v{version}",
        name=title,
        message=description,
        draft=True,
        prerelease=True,
        target_commitish="master",
    )


def update_or_create_draft_release(repo, release_type, pr_description):
    last_version = get_latest_release_version(repo)
    new_version = get_new_release_version(last_version, release_type)
    current_release = check_draft_release_exist(repo, new_version)
    if current_release:
        update_release(current_release, pr_description)
    else:
        current_release = create_release(
            repo, pr_description, new_version, release_type
        )
    return current_release
