# 実装指示書一覧

Cursor へ **1 本ずつ** 投入し、完了ごとに `pytest` → `ruff` → `mypy` → コミット。

| # | ファイル | タイトル | 状態 |
|---|----------|----------|------|
| 01 | [INST_01_project_init.md](INST_01_project_init.md) | プロジェクト初期化 | **完了** |
| 02 | [INST_02_targets_url.md](INST_02_targets_url.md) | 定数・地域マスタ・URL生成 | **完了** |
| 03 | [INST_03_settings.md](INST_03_settings.md) | 設定管理 | **完了** |
| 04 | [INST_04_repository.md](INST_04_repository.md) | SQLiteリポジトリ | **完了** |
| 05 | [INST_05_logger_notifier.md](INST_05_logger_notifier.md) | ロガー・ノーティファイア | **完了** |
| 06 | [INST_06_downloader_manifest.md](INST_06_downloader_manifest.md) | ダウンローダ・マニフェスト・HTTP | **完了** |
| 07 | [INST_07_playwright_scraper.md](INST_07_playwright_scraper.md) | スクレイパ（Playwright） | **完了** |
| 08 | [INST_08_scheduler_cli.md](INST_08_scheduler_cli.md) | スケジューラ・CLI | **完了** |
| 09 | [INST_09_main_window.md](INST_09_main_window.md) | メインウィンドウ・起動 | **完了** |
| 10 | [INST_10_settings_tab.md](INST_10_settings_tab.md) | 設定タブ | **完了** |
| 11 | [INST_11_library_tab.md](INST_11_library_tab.md) | 保管庫タブ | **完了** |
| 12〜20 | — | 常駐 / 拡張 / ビルド | 未作成 |

- 差分メモ: [ALIGNMENT.md](ALIGNMENT.md)
- 正本設計: [../DESIGN.md](../DESIGN.md)

## 依存関係

```
01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 10 → 11 → 12 → ...
```
