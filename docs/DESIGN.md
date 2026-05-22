# JATIC-Library 詳細設計書 v1.0

> Cursor 実装の正本。README の機能説明は本書に沿って都度更新する。

## 0. 概要

JARTIC「断面交通量情報」を自動取得・管理する Windows デスクトップアプリ。Python + PySide6、PyInstaller 同梱配布。

| 項目 | 内容 |
|------|------|
| プロジェクト名 | JATIC-Library |
| ローカル | `F:\Cursor\JATIC-Library` |
| リモート | `https://github.com/matrix9neonebuchadnezzar2199-sketch/JATIC-Library` |
| 対象サイト | `https://www.jartic.or.jp/service/opendata/` 内「断面交通量情報」(typeB) |
| 公開タイミング | 毎月1日、約2か月前の月分が公開（例：2026/5/1 → 「2026年03月分」） |
| 取得対象 | 51地域の ZIP（北海道5方面＋46都府県） |
| フォルダ命名 | `YYYY_M`（先頭ゼロなし、例：`2026_3`） |

## 1. プロジェクト構造

```
F:\Cursor\JATIC-Library\
├── README.md
├── LICENSE
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── build.bat
├── run.bat
├── .gitignore
├── .python-version
├── src\jatic_library\
│   ├── __init__.py
│   ├── __main__.py
│   ├── app.py
│   ├── constants.py
│   ├── core\          # targets, url_builder, scraper, downloader, ...
│   ├── ui\             # main_window, tabs, widgets, themes
│   ├── settings\       # config, store
│   └── resources\
├── tests\
└── docs\
```

```
F:\Cursor\JATIC-Library\
├── src\jatic_library\
│   ├── constants.py
│   ├── core\
│   │   ├── targets.py, url_builder.py, repository.py, models.py
│   │   ├── downloader.py, manifest.py, scheduler.py
│   │   ├── playwright_scraper.py, scraper.py
│   │   ├── git_sync.py, notifier.py, tray.py, exporter.py, csv_loader.py, logger.py
│   ├── settings\config.py, store.py
│   ├── ui\ (main_window, tabs, widgets, models, dialogs, themes)
│   └── resources\targets.json, icons\
├── tests\
└── docs\instructions\  # INST_01〜
```

実装済み（#01〜#04）: `constants`, `targets`, `url_builder`, `settings`, `repository`。

## 2. 依存ライブラリ

`requirements.txt` / `requirements-dev.txt` を正とする。

## 3. 定数（`constants.py`）

- `JARTIC_OPENDATA_PAGE`, `JARTIC_DATA_DIR_TPL`, `JARTIC_ZIP_TPL`
- `PUBLISH_LAG_MONTHS = 2`
- `APP_DATA_DIR` = `%LOCALAPPDATA%\JATIC-Library\`
- `CONFIG_PATH`, `DB_PATH`, `LOG_DIR`, `MANIFEST_FILENAME`

## 4. 地域マスタ（`core/targets.py`）

51 `Target` レコード。`filename_key` は Playwright 初回スキャンで `targets.json` に確定。コード内はフォールバック。

## 5. データモデル

### 5.1 設定（`settings/config.py`）

`AppConfig` 配下: `TargetSelection`, `DownloadSettings`（`save_root: Path | None`）, `ScheduleSettings`, `NotificationSettings`, `GitHubSettings`, `UISettings`, `TraySettings`, `LogSettings`。永続化: `%LOCALAPPDATA%\JATIC-Library\config.json`（`ConfigStore`、破損時 `.broken.*` バックアップ）。

### 5.2 SQLite（`core/repository.py`）

```sql
CREATE TABLE publications (
  publish_ym TEXT PRIMARY KEY,
  publish_date TEXT NOT NULL,
  detected_at TEXT NOT NULL,
  status TEXT NOT NULL  -- pending|partial|complete|failed
);
CREATE TABLE files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  publish_ym TEXT NOT NULL,
  target_code TEXT NOT NULL,
  display_name TEXT NOT NULL,
  file_path TEXT NOT NULL,
  file_size INTEGER NOT NULL,
  sha256 TEXT NOT NULL,
  source_url TEXT NOT NULL,
  downloaded_at TEXT NOT NULL,
  status TEXT NOT NULL,
  UNIQUE(publish_ym, target_code)
);
CREATE TABLE check_history (...);
CREATE TABLE tags (...);
CREATE TABLE tag_assignments (...);
CREATE TABLE event_logs (...);
```

日時は JST（`tzdata` 依存）。`Repository` は context manager / `transaction()` 対応。

### 5.3 マニフェスト（`{save_root}/2026_3/_manifest.json`）

```json
{
  "publish_ym": "2026_3",
  "publish_date": "2026-05-01",
  "downloaded_at": "2026-05-01T10:23:14+09:00",
  "source_dir_url": "https://www.jartic.or.jp/d/opendata/202605010000/",
  "app_version": "0.1.0",
  "files": [
    {
      "target_code": "tokyo",
      "display_name": "東京都",
      "filename": "東京都.zip",
      "source_url": "https://www.jartic.or.jp/d/opendata/202605010000/typeB_tokyo.zip",
      "size": 12345678,
      "sha256": "...",
      "downloaded_at": "..."
    }
  ]
}
```

## 6. コアロジック

| モジュール | 責務 |
|------------|------|
| `url_builder` | `PublishInfo` 計算、ZIP URL 生成 |
| `playwright_scraper` | 初回キー学習、再スキャン、404 フォールバック |
| `scraper` | 軽量 HTML（JS 無しでは空のため補助） |
| `downloader` | httpx 非同期並列 DL、ハッシュ、リトライ |
| `scheduler` | 起動時チェック（24h 間隔） |
| `manifest` | 読み書き・検証 |
| `repository` | SQLite |
| `git_sync` | 任意 commit & push |
| `notifier` | win11toast |
| `tray` | QSystemTrayIcon（任意・手動操作用） |

## 7. UI 仕様

タブ: 保管庫 / 設定。3ペイン保管庫、51 地域チェックリスト、進捗・タグ・About ダイアログ。`dark.qss` / `light.qss`。

画面ワイヤ・メニュー構成はマスター指示書 §7。

## UI フロー詳細

タブ構成・シグナル配線・主要操作のシーケンス図は [UI_FLOW.md](./UI_FLOW.md) を参照してください。
本ファイルは構造設計（モジュール分割・データフロー）に専念します。

## 8. 処理フロー

1. 起動 → 設定ロード → DB init → テーマ → MainWindow
2. `StartupScheduler.should_check_now()` → 必要なら DL
3. DL: targets.json → URL 構築 → 並列 GET → manifest → SQLite → (Git) → 通知

## 9. テスト方針

単体: `url_builder`, `targets`, `manifest`, `scheduler`。統合: httpx mock。UI: pytest-qt。

## 10. ビルド

`build.bat` → PyInstaller `--onedir`。Playwright Chromium は初回 `playwright install chromium`。

## 11. 留意事項

- 大容量 ZIP / Git LFS 警告
- `filename_key` は P5 で実サイト検証必須
- 過去月はサイト非公開のため遡及不可
- CSV は cp932 想定、`chardet` で判定

## 12. ロードマップ

- **進捗正本:** [DEV_STATUS.md](DEV_STATUS.md)（指示書トラッカー・機能マトリクス・残作業）
- 実装指示書: [instructions/README.md](instructions/README.md)（#01〜#21 完了、#22〜#26 Pre-release Hardening）
- UI フロー: [UI_FLOW.md](UI_FLOW.md)
- Phase 表: [ROADMAP.md](ROADMAP.md)

## 実装進捗

詳細は [DEV_STATUS.md](DEV_STATUS.md) を参照。サマリ: 機能実装（#01〜#21）完了。**残作業は配布・実行形式の仕上げ**（PyInstaller 検証、Playwright 同梱、マニュアル、配布 zip）。一覧は [DEV_STATUS.md §5](DEV_STATUS.md#5-残作業リリース配布まで)。
