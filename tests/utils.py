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


def get_tasks_with_epic():
    return [
        # need contniue
        {"commit.message": "Merge pull request", "pulls": []},
        # epic
        {
            "commit.message": "[ERP-2] task 2",
            "pulls": [
                {
                    "number": 2,
                    "mergeable": False,
                    "head.ref": "epic/1",
                    "title": "Some title",
                    "user.login": "user",
                    "html_url": LINK_EXAMPLE,
                    "epic_commits": [
                        # need to continue
                        {"commit.message": "Some commit nessage"},
                        # real epic commit
                        {
                            "commit.message": """Merge pull request #5 fifth task
                            [ERP-5] fifth task
                            [ERP-6] six task
                            """,
                        },
                    ],
                }
            ],
        },
        # simple task
        {
            "commit.message": "[ERP-4] forth task",
            "pulls": [
                {
                    "number": 4,
                    "html_url": LINK_EXAMPLE,
                    "title": "Pull title 4",
                    "user.login": "user",
                    "mergeable": False,
                    "head.ref": "feature/4/forth_task",
                }
            ],
        },
        # epic task
        {
            "commit.message": "[ERP-5] fifth task",
            "pulls": [
                {
                    "number": 5,
                    "html_url": LINK_EXAMPLE,
                    "title": "Pull title 5",
                    "user.login": "user",
                    "mergeable": False,
                    "head.ref": "feature/5/fifth_task",
                }
            ],
        },
    ]
