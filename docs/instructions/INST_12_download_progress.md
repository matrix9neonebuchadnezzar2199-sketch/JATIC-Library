# 指示書 #12: ダウンロード進捗ダイアログ

## ゴール
GUI の更新確認・DL 実行中に per-region 進捗をモーダル表示する。

## ファイル
- `ui/widgets/download_progress_dialog.py`
- `ui/main_window.py`, `core/scheduler.py`（progress_cb 配線）
- `tests/test_download_progress_dialog.py`

## コミット
`feat(ui): add download progress dialog`
