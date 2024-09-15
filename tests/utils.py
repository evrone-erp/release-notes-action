LINK_EXAMPLE = "https://link.com"


def get_tasks4proces_pull():
    return [
        # simple task
        {
            "pull": {
                "number": 2,
                "html_url": LINK_EXAMPLE,
                "title": "Pull title 2",
                "user.login": "user",
            },
            "commit_message": "[ERP-2] feature 2",
        },
        # 2 tasks with patterns
        {
            "pull": {
                "number": 3,
                "html_url": LINK_EXAMPLE,
                "title": "Pull title 3",
                "user.login": "user",
            },
            "commit_message": "[ERP-3, ERP-4] feature 3",
        },
        # 2 tasks with patterns
        {
            "pull": {
                "number": 5,
                "html_url": LINK_EXAMPLE,
                "title": "Pull title 5",
                "user.login": "user",
            },
            "commit_message": "[ERP-3][Backend] feature 5",
        },
        # 1 task without patterns
        {
            "pull": {
                "number": 6,
                "html_url": LINK_EXAMPLE,
                "title": "Pull title 6",
                "user.login": "user",
            },
            "commit_message": "Support: some fix",
        },
        # 1 tasks that exist yet
        {
            "pull": {
                "number": 7,
                "html_url": LINK_EXAMPLE,
                "title": "Pull title 7",
                "user.login": "user",
            },
            "commit_message": "Need to miss this task",
        },
    ]


def get_tasks4_create():
    return [
        {
            "pull": {
                "number": 2,
                "html_url": LINK_EXAMPLE,
                "title": "Pull title 2",
                "user.login": "user",
            },
            "task_key": "ERP-2",
            "is_epic": False,
        },
        {
            "pull": {
                "number": 3,
                "html_url": LINK_EXAMPLE,
                "title": "Pull title 3",
                "user.login": "user",
            },
            "task_key": None,
            "is_epic": False,
        },
    ]
