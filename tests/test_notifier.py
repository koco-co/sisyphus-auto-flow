"""Tests for webhook notifier — DingTalk, Feishu, Slack."""
from unittest.mock import MagicMock, patch

import pytest

from scripts.notifier import (
    NotificationPayload,
    format_dingtalk,
    format_feishu,
    format_slack,
    send_notification,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TITLE = "Deploy succeeded"
BODY = "Branch main was deployed to production."


def make_payload(title: str = TITLE, body: str = BODY) -> NotificationPayload:
    return NotificationPayload(title=title, body=body)


# ---------------------------------------------------------------------------
# TestFormatDingtalk
# ---------------------------------------------------------------------------


class TestFormatDingtalk:
    def test_markdown_format(self) -> None:
        payload = make_payload()
        msg = format_dingtalk(payload)

        assert msg["msgtype"] == "markdown"
        assert TITLE in msg["markdown"]["title"]
        assert BODY in msg["markdown"]["text"]

    def test_truncates_long_body(self) -> None:
        long_body = "x" * 10_000
        payload = make_payload(body=long_body)
        msg = format_dingtalk(payload)

        assert len(msg["markdown"]["text"]) <= 5000


# ---------------------------------------------------------------------------
# TestFormatFeishu
# ---------------------------------------------------------------------------


class TestFormatFeishu:
    def test_card_format(self) -> None:
        payload = make_payload()
        msg = format_feishu(payload)

        assert msg["msg_type"] == "interactive"
        assert TITLE in str(msg)


# ---------------------------------------------------------------------------
# TestFormatSlack
# ---------------------------------------------------------------------------


class TestFormatSlack:
    def test_blocks_format(self) -> None:
        payload = make_payload()
        msg = format_slack(payload)

        assert "blocks" in msg
        assert TITLE in str(msg["blocks"])


# ---------------------------------------------------------------------------
# TestSendNotification
# ---------------------------------------------------------------------------


class TestSendNotification:
    def test_sends_dingtalk(self) -> None:
        payload = make_payload()
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("scripts.notifier.httpx.post", return_value=mock_response) as mock_post:
            result = send_notification("dingtalk", "https://example.com/webhook", payload)

        assert result is True
        mock_post.assert_called_once()

    def test_returns_false_on_failure(self) -> None:
        payload = make_payload()

        with patch("scripts.notifier.httpx.post", side_effect=Exception("network error")):
            result = send_notification("dingtalk", "https://example.com/webhook", payload)

        assert result is False

    def test_unknown_channel_raises_value_error(self) -> None:
        payload = make_payload()

        with pytest.raises(ValueError, match="Unknown channel"):
            send_notification("unknown_channel", "https://example.com/webhook", payload)
