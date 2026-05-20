# 指示書 #09: PySide6 メインウィンドウ・アプリ起動

## 前提
- 完了済み指示書: #01〜#08
- 参照: docs/DESIGN.md §7, §8

## ゴール
`python -m jatic_library`（引数なし）で GUI が起動する。
4 タブ骨格（保管庫 / 設定 / カレンダー / 比較）、テーマ適用、DB 接続、起動時チェック（バックグラウンド）まで。

## 作成・変更ファイル
- `src/jatic_library/app.py`
- `src/jatic_library/ui/main_window.py`
- `src/jatic_library/ui/theme.py`
- `src/jatic_library/ui/tabs/`（library / settings / calendar / compare）
- `src/jatic_library/ui/workers.py`
- `src/jatic_library/__main__.py`
- `tests/test_main_window.py`

## 実装要件
- `run_app() -> int`: QApplication、設定ロード、logging、Repository、テーマ、`MainWindow`
- `MainWindow`: QTabWidget、メニュー（終了 / 更新確認 / About）、ステータスバー
- 未設定 `save_root` 時は設定タブへ誘導
- `AsyncTaskWorker` で `StartupScheduler.run_check` を非同期実行
- CLI は `check` / `download` / `scrape` サブコマンドのまま維持

## やらないこと
- 設定フォーム詳細（#10）
- 保管庫ツリー（#11）

## コミットメッセージ案
`feat(ui): add PySide6 main window and application bootstrap`
