# 開発環境セットアップ

## 要件

- Windows 10/11
- Python **3.11.x**（`.python-version` 参照）
- [uv](https://github.com/astral-sh/uv) 推奨

## 初回セットアップ

```powershell
cd F:\Cursor\JATIC-Library
uv venv --python 3.11
uv sync --group dev
uv run playwright install chromium
```

## 実行

```powershell
uv run python -m jatic_library
# または
.\run.bat
```

## 品質チェック

```powershell
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy
uv run pytest
```

### モック中心テスト（DL・常駐・スクレイプ動線）

ネットワーク・実サイト・トレイ実機に依存しないサブセット（2026-05-20 時点 **22 件**）:

```powershell
uv run pytest tests/test_downloader.py tests/test_downloader_rescrape.py `
  tests/test_scheduler_flow.py tests/test_playwright_scraper.py `
  tests/test_http_client.py tests/test_git_sync.py `
  tests/test_tray.py tests/test_workers.py tests/test_startup.py -v
```

全件: `uv run pytest -q`（**98 passed**、GUI/Qt 含む）。

## 配布ビルド

```powershell
.\build.bat
```

`src\jatic_library\resources\icons\app.ico` が無い場合は PyInstaller の `--icon` を外すか、アイコンを配置してください。

## 設計書

機能・API・DBスキーマは [DESIGN.md](DESIGN.md) を正とします。
