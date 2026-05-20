"""Tests for toast notifier."""

from unittest.mock import patch

from jatic_library.core.notifier import DownloadSummary, Notifier
from jatic_library.settings.config import NotificationSettings


def test_notifier_respects_disabled() -> None:
    notifier = Notifier(NotificationSettings(on_complete=False))
    with patch.object(notifier, "_toast") as mock_toast:
        notifier.notify_complete(DownloadSummary("2026_3", 1, 0, 0))
    mock_toast.assert_not_called()


def test_notifier_calls_toast_when_enabled() -> None:
    notifier = Notifier(NotificationSettings(on_complete=True))
    with patch.object(notifier, "_toast") as mock_toast:
        notifier.notify_complete(DownloadSummary("2026_3", 2, 1, 0))
    mock_toast.assert_called_once()
