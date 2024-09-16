import requests

from config.logger_config import logger

_REQUEST_TIMEOUT = 300.0


class YandexTracker:  # pylint: disable=too-few-public-methods

    def __init__(self, org_id, token):
        self.org_id = org_id
        response = requests.post(
            headers={
                "Content-Type": "application/json",
            },
            url="https://iam.api.cloud.yandex.net/iam/v1/tokens",
            json={"yandexPassportOauthToken": token},
            timeout=300.0,
        )
        if response.status_code != 200:
            logger.error(
                "YandexTracker Get IAM token exception: %s: %s",
                response.status_code,
                response.text,
            )
            response.raise_for_status()
        response_data = response.json()
        self.iam_token = response_data.get("iamToken")

    def get_issue_summary(self, issue):
        url = f"https://api.tracker.yandex.net/v2/issues/{issue}"
        resp = requests.get(
            url=url,
            headers={
                "Authorization": f"Bearer {self.iam_token}",
                "X-Org-ID": self.org_id,
                "Content-Type": "application/json",
            },
            timeout=_REQUEST_TIMEOUT,
        )
        if resp.status_code != 200:
            logger.info(
                "Get Issue Summary BadRequest: status_code: %s; text: %s",
                resp.status_code,
                resp.text,
            )
            return None
        resp_json = resp.json()
        return resp_json["summary"]
