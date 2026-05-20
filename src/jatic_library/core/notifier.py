"""Windows toast notifications."""

from __future__ import annotations

from dataclasses import dataclass

from loguru import logger

from jatic_library.constants import APP_NAME
from jatic_library.core.playwright_env import INSTALL_COMMAND, failures_look_like_missing_browser
from jatic_library.settings.config import NotificationSettings


@dataclass(frozen=True)
class DownloadSummary:
    """Minimal download result for notifications."""

    publish_ym: str
    succeeded: int
    skipped: int
    failed: int
    failed_details: tuple[tuple[str, str], ...] = ()


class Notifier:
    """Send optional Windows toast notifications."""

    def __init__(self, settings: NotificationSettings) -> None:
        self._settings = settings

    def notify_new_publish(self, publish_ym: str) -> None:
        """Notify when a new publication month is detected."""
        if not self._settings.on_new_publish:
            return
        self._toast("新規公開を検知", f"{publish_ym} の取得を開始します")

    def notify_complete(self, summary: DownloadSummary) -> None:
        """Notify when a download batch completes."""
        if not self._settings.on_complete:
            return
        if summary.failed and failures_look_like_missing_browser(list(summary.failed_details)):
            body = (
                f"{summary.publish_ym}: Chromium 未セットアップのため "
                f"失敗 {summary.failed} 件。{INSTALL_COMMAND} を実行してください。"
            )
        else:
            body = (
                f"{summary.publish_ym}: 成功 {summary.succeeded}, "
                f"スキップ {summary.skipped}, 失敗 {summary.failed}"
            )
        self._toast("ダウンロード完了", body)

    def notify_error(self, message: str) -> None:
        """Notify on error."""
        if not self._settings.on_error:
            return
        self._toast("エラー", message[:200])

    def _toast(self, title: str, body: str) -> None:
        try:
            from win11toast import toast

            toast(f"{title}\n{body}", app_id=APP_NAME)
        except Exception as exc:
            logger.debug("Toast notification skipped: {}", exc)
