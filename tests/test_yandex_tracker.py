import unittest
from unittest.mock import MagicMock, patch

from helpers.yandex_tracker import YandexTracker


class TestYandexTracker(unittest.TestCase):
    @patch("helpers.yandex_tracker.requests.get")
    def test_get_issue_summary_uses_oauth_authorization(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"summary": "Test issue"}
        mock_get.return_value = mock_response

        tracker = YandexTracker("fake_org_id", "fake_token")
        summary = tracker.get_issue_summary("ERP-1")

        self.assertEqual(summary, "Test issue")
        mock_get.assert_called_once_with(
            url="https://api.tracker.yandex.net/v2/issues/ERP-1",
            headers={
                "Authorization": "OAuth fake_token",
                "X-Org-ID": "fake_org_id",
                "Content-Type": "application/json",
            },
            timeout=300.0,
        )

    @patch("helpers.yandex_tracker.requests.get")
    def test_get_issue_summary_returns_none_on_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_get.return_value = mock_response

        tracker = YandexTracker("fake_org_id", "fake_token")
        summary = tracker.get_issue_summary("ERP-999")

        self.assertIsNone(summary)
