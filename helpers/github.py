MARKDOWN_LINK = "{}{} by @{} in #{}"


def formatted_line(task_key, title, user_login, pr_number):
    task_key = (
        f"[[{task_key}](https://tracker.yandex.ru/{task_key})] " if task_key else ""
    )
    return MARKDOWN_LINK.format(task_key, title, user_login, pr_number)


def change_pull_request_body(pull_request, result):
    body = "\r\n".join(result)
    pull_request.edit(body=body)
