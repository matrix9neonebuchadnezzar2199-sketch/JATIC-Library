# 現行コードと指示書 #01〜#08 の差分

**2026-05-20 更新: #01〜#08 照合完了。** 以降は #09 から UI 実装。

## 完了サマリ

| # | 主な成果 | 検証 |
|---|----------|------|
| 01 | setuptools、`Hello from JATIC-Library`、ディレクトリ雛形 | `python -m jatic_library` |
| 02 | constants / targets / url_builder / targets.json | pytest |
| 03 | AppConfig + ConfigStore（破損JSONバックアップ） | pytest |
| 04 | models + Repository 全CRUD | pytest |
| 05 | loguru 設定、win11toast Notifier | pytest |
| 06 | JarticHttpClient、Manifest、Downloader | pytest（モック HTTP） |
| 07 | Playwright スクレイパ、targets.json 更新 | pytest（モック） |
| 08 | StartupScheduler、CLI（check/download/scrape） | pytest |

## 意図的な差分（許容）

| 項目 | 指示書 | 採用 |
|------|--------|------|
| パッケージマネージャ | pip / venv 記載 | **uv** も `run.bat` / README で併記 |
| `LEARNED_TARGETS_PATH` | `TARGETS_CACHE_PATH` 名 | 同義で `TARGETS_CACHE_PATH` を使用 |
| DL 時 404 再スクレイプ | DESIGN に記載 | **#08 時点未実装**（`scrape` コマンドで手動更新） |

## 次の指示書

#09 PySide6 メインウィンドウ・タブ骨格 から。
