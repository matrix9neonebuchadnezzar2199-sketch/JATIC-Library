# 指示書 #10: 設定タブ

## 前提
- 完了済み指示書: #01〜#09

## ゴール
設定タブから `AppConfig` を編集・保存でき、テーマ即時反映、「今すぐ更新確認」「サイト再スキャン」が動作する。

## 作成・変更ファイル
- `src/jatic_library/ui/widgets/region_selector.py`
- `src/jatic_library/ui/tabs/settings_tab.py`（拡張）
- `tests/test_settings_tab.py`

## 実装要件
- 保存先フォルダ（参照ダイアログ）
- 51 地域チェックリスト（地方別・全選択/解除）
- 起動時自動チェック、再チェック間隔（時間）
- 同時 DL 数・リトライ・タイムアウト
- 通知 ON/OFF、テーマ、ログ保持
- 「設定を保存」→ `ConfigStore.save`
- 空選択＝全地域（`TargetSelection` 慣習に合わせ UI は全チェック表示）

## コミットメッセージ案
`feat(ui): add settings tab with region selector and actions`
