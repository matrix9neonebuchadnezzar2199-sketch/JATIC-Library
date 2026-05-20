# 指示書 #05: ロガー・ノーティファイア

## 前提
- 完了済み指示書: #01〜#04
- 参照: docs/DESIGN.md §6（notifier）

## ゴール
loguru の設定を `LogSettings` と連動させ、Windows トースト通知を提供する。
ダウンロード完了・エラー時にオプションで通知（設定 OFF 時は no-op）。

## 作成・変更ファイル
- `src/jatic_library/core/logger.py`
- `src/jatic_library/core/notifier.py`
- `tests/test_logger.py`
- `tests/test_notifier.py`

## 実装要件
- `setup_logging(log_dir, log_settings: LogSettings | None)` — レベル・保持期間
- `get_logger()` — loguru logger 返却
- `Notifier(settings: NotificationSettings)` — `notify_new_publish`, `notify_complete`, `notify_error`
- win11toast 失敗時はログのみ（テストではモック）

## やらないこと
- Repository への自動 log sink（#06 で主要イベントを明示記録）

## コミットメッセージ案
`feat(core): add configurable logging and Windows toast notifier`
