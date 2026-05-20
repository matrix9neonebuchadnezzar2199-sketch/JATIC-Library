# 指示書 #11: 保管庫タブ

## 前提
- 完了済み指示書: #01〜#10

## ゴール
保存先フォルダを走査し、**年 → 月 → 地域 ZIP** のツリー表示、詳細ペイン、ZIP 内 CSV の先頭プレビューができる。

## 作成・変更ファイル
- `src/jatic_library/core/library_scanner.py`
- `src/jatic_library/core/csv_loader.py`
- `src/jatic_library/ui/tabs/library_tab.py`
- `src/jatic_library/ui/widgets/file_detail_panel.py`
- `src/jatic_library/ui/widgets/csv_preview.py`
- `tests/test_library_scanner.py`
- `tests/test_csv_loader.py`
- `tests/test_library_tab.py`

## 実装要件
- `scan_library(save_root, repo)` → 年ノード配列（`YYYY_M` フォルダ + manifest/SQLite マージ）
- 検索ボックスで地域名フィルタ
- 詳細: パス・サイズ・SHA256・DL日時・URL
- 右クリック: エクスプローラーで開く / パスをコピー
- DL 完了・設定保存後にツリー再読込

## やらないこと
- 欠損月バッジ（#14）
- 再 DL / 削除（#13）

## コミットメッセージ案
`feat(ui): add library tab with year-month-region tree and CSV preview`
