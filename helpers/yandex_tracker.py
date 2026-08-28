import requests

from config.logger_config import logger

_REQUEST_TIMEOUT = 300.0


class YandexTracker:  # pylint: disable=too-few-public-methods

    def __init__(self, org_id, token):
        self.org_id = org_id
        self.token = token

    def get_issue_summary(self, issue):
        url = f"https://api.tracker.yandex.net/v2/issues/{issue}"
        resp = requests.get(
            url=url,
            headers={
                "Authorization": f"OAuth {self.token}",
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
