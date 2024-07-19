MARKDOWN_LINK = "[[{}](https://tracker.yandex.ru/{})] {} by @{} in #{}"


def formatted_line(task_key, title, user_login, pr_number):
    return MARKDOWN_LINK.format(task_key, task_key, title, user_login, pr_number)


def change_pull_request_body(pull_request, result):
    body = "\r\n".join(result)
    pull_request.edit(body=body)
