import requests
from environs import Env

env = Env()

YANDEX_ORG_ID = env("INPUT_YANDEX_ORG_ID")
YANDEX_OAUTH2_TOKEN = env("INPUT_YANDEX_OAUTH2_TOKEN")
_REQUEST_TIMEOUT = 300.0


class YandexTracker:  # pylint: disable=too-few-public-methods

    def __init__(self):
        response = requests.post(
            headers={
                "Content-Type": "application/json",
            },
            url="https://iam.api.cloud.yandex.net/iam/v1/tokens",
            json={"yandexPassportOauthToken": YANDEX_OAUTH2_TOKEN},
            timeout=300.0,
        ).json()

        self.iam_token = response.get("iamToken")

    def get_issue_summery(self, issue):
        url = f"https://api.tracker.yandex.net/v2/issues/{issue}"
        resp = requests.get(
            url=url,
            headers={
                "Authorization": f"Bearer {self.iam_token}",
                "X-Org-ID": YANDEX_ORG_ID,
                "Content-Type": "application/json",
            },
            timeout=_REQUEST_TIMEOUT,
        )
        if resp.status_code != 200:
            return  # TODO: check missing tasks
        resp_json = resp.json()
        return resp_json["summary"]
