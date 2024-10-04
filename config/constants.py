import re

TASK_KEY_PATTERN = re.compile(r"[^[]*\[([^]]*)\]")
MERGE_PULL_REQUEST_PATTERN = re.compile(r"Merge pull request #(\d+)")

# Description title names
MAIN_TITLE_NAME = "## What's Changed \n"
EPIC_TITLE_NAME = "### Epic"
