import re

TASK_KEY_PATTERN = re.compile(r"[^[]*\[([^]]*)\]")
MERGE_PULL_REQUEST_PATTERN = re.compile(r"Merge pull request #(\d+)")
