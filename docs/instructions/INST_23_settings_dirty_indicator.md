# INST_23: 設定タブの未保存インジケータ

## 目的

`SettingsTab` の各ウィジェット編集は `apply_to_config()` でまとめて永続化される。
保存忘れのまま「今すぐ更新確認」を押すと、未反映の地域選択で DL が走る可能性がある。
タイトルバーと保存ボタンで **未保存状態を可視化** し、事故を防ぐ。

## 対象ファイル

- `src/jatic_library/ui/tabs/settings_tab.py`
- `src/jatic_library/ui/main_window.py`
- `tests/test_settings_dirty.py`（新規）

## 実装概要

- `dirty_changed` シグナル、`is_dirty` プロパティ、保存ボタンの活性制御
- `load_from_config()` は `QSignalBlocker` で dirty 化を抑止
- `MainWindow`: タイトルに `*`、未保存時は `run_update_check` をブロックして設定タブへ誘導

## 受け入れ基準

- 起動直後: `*` なし、保存ボタン disabled
- 編集後: `*` 付き、保存ボタン enabled
- 保存成功後: クリーン状態に戻る
- `load_from_config()` では dirty にならない
- 未保存のまま更新確認 → 警告＋設定タブ表示、worker 未起動

## コミット

`feat(ui): add settings tab dirty indicator`
