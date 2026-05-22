# 実装指示書一覧

Cursor へ **1 本ずつ** 投入し、完了ごとに `pytest` → `ruff` → `mypy` → コミット。

**進捗の正本:** [../DEV_STATUS.md](../DEV_STATUS.md)

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
| 12 | [INST_12_download_progress.md](INST_12_download_progress.md) | DL 進捗ダイアログ | **完了** |
| 13 | [INST_13_dl_404_rescrape.md](INST_13_dl_404_rescrape.md) | 404 自動再スクレイプ | **完了** |
| 14 | [INST_14_library_actions.md](INST_14_library_actions.md) | 保管庫拡張 | **完了** |
| 15 | [INST_15_tags.md](INST_15_tags.md) | タグ UI | **完了** |
| 16 | [INST_16_calendar_missing.md](INST_16_calendar_missing.md) | カレンダー・欠損月 | **先送り**（P11） |
| 17 | [INST_17_compare_tab.md](INST_17_compare_tab.md) | 比較タブ | **先送り**（P11） |
| 18 | [INST_18_export_chart.md](INST_18_export_chart.md) | エクスポート・グラフ | **一部**（エクスポート済・チャート P11） |
| 19 | [INST_19_git_sync.md](INST_19_git_sync.md) | Git 連携 | **完了** |
| 20 | [INST_20_system_tray.md](INST_20_system_tray.md) | トレイ・スタートアップ | **完了** |
| 21 | [INST_21_pyinstaller.md](INST_21_pyinstaller.md) | PyInstaller | **完了** |
| 22 | [INST_22_library_sort_debounce.md](INST_22_library_sort_debounce.md) | 保管庫ソート保存デバウンス | **完了** |
| 23 | [INST_23_settings_dirty_indicator.md](INST_23_settings_dirty_indicator.md) | 設定タブ未保存インジケータ | **完了** |
| 24 | [INST_24_delete_order_safety.md](INST_24_delete_order_safety.md) | 削除順序の見直し | **完了** |
| 25 | [INST_25_playwright_guard_expand.md](INST_25_playwright_guard_expand.md) | Playwright ガード拡張 | **完了** |
| 26 | [INST_26_sqlite_wal_mode.md](INST_26_sqlite_wal_mode.md) | SQLite WAL モード化 | **完了** |
| 27 | [INST_27_playwright_first_run_setup.md](INST_27_playwright_first_run_setup.md) | Chromium セットアップ UI | **完了** |
| 28 | [INST_28_pyinstaller_build_refine.md](INST_28_pyinstaller_build_refine.md) | PyInstaller ビルド・zip | **完了** |
| 29 | [INST_29_release_smoke_test.md](INST_29_release_smoke_test.md) | smoke test・Release | **完了** |
| 30 | [INST_30_release_docs.md](INST_30_release_docs.md) | 公開後ドキュメント（R5〜R7） | **完了** |
| 31 | [INST_31_reliability_perf_patch.md](INST_31_reliability_perf_patch.md) | 信頼性・性能パッチ（#1〜#5） | **完了** |
| 32 | [INST_32_library_tab_responsiveness.md](INST_32_library_tab_responsiveness.md) | 保管庫応答性フォローアップ・ツリー／CSV 結合 | **完了** |

## Post-beta 改善（#31〜#32）

- **#31:** Cursor へ **#1 → #5 の順に 1 本ずつ** 投入。[INST_31_reliability_perf_patch.md](INST_31_reliability_perf_patch.md)（**完了**）。
- **#32:** **#1 → #3** の順。保管庫キャッシュ仕上げ（INST_31 #1 の差分）、`ROLE_MONTH_ITEM`、ストリーミング統合 CSV。[INST_32_library_tab_responsiveness.md](INST_32_library_tab_responsiveness.md)。

## Pre-release Hardening（#22〜#26）

リリース前に適用する保守・堅牢化タスク群。`MainWindow` 解析（[UI_FLOW.md](../UI_FLOW.md)）に基づく
リスク抽出から生まれた小さなパッチの集まりです。各指示書は **1 つの目的に絞った独立タスク** として
着手できます。

| # | リンク | 概要 |
|---|---|---|
| 22 | [INST_22_library_sort_debounce.md](./INST_22_library_sort_debounce.md) | 保管庫ソート保存のデバウンス・同値ガード（完了） |
| 23 | [INST_23_settings_dirty_indicator.md](./INST_23_settings_dirty_indicator.md) | 設定タブの未保存インジケータ（完了） |
| 24 | [INST_24_delete_order_safety.md](./INST_24_delete_order_safety.md) | ファイル削除の順序見直し（完了） |
| 25 | [INST_25_playwright_guard_expand.md](./INST_25_playwright_guard_expand.md) | Chromium ガードを更新確認にも展開（完了） |
| 26 | [INST_26_sqlite_wal_mode.md](./INST_26_sqlite_wal_mode.md) | SQLite WAL モード化（完了） |

## 配布・リリース（#27〜#29）

| # | リンク | 概要 |
|---|---|---|
| 27 | [INST_27_playwright_first_run_setup.md](./INST_27_playwright_first_run_setup.md) | アプリ内 Chromium インストール UI（完了） |
| 28 | [INST_28_pyinstaller_build_refine.md](./INST_28_pyinstaller_build_refine.md) | `.spec` / `build.bat` 改善（完了） |
| 29 | [INST_29_release_smoke_test.md](./INST_29_release_smoke_test.md) | smoke test / Release（完了） |
| 30 | [INST_30_release_docs.md](./INST_30_release_docs.md) | R5〜R7 ドキュメント仕上げ（完了） |

- 差分メモ: [ALIGNMENT.md](ALIGNMENT.md)
- 正本設計: [../DESIGN.md](../DESIGN.md)

## 依存関係

```
01 → 02 → … → 21
```
