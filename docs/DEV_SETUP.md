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
uv run pytest -q
```

全件: **147 passed**（2026-05-22 時点、GUI/Qt 含む）。

### モック中心テスト（DL・スケジューラ・ガード等）

```powershell
uv run pytest tests/test_downloader.py tests/test_downloader_rescrape.py `
  tests/test_scheduler_flow.py tests/test_playwright_guard.py `
  tests/test_playwright_setup_dialog.py tests/test_http_client.py `
  tests/test_git_sync.py tests/test_tray.py tests/test_workers.py -q
```

## 配布ビルド（ベータ）

初回のみ dev 依存を入れる:

```powershell
uv sync --group dev
```

ビルド（dist クリーン → PyInstaller → README/LICENSE/BETA_TEST コピー → zip）:

```powershell
.\build.bat
```

| 成果物 | パス |
|--------|------|
| onedir 一式 | `dist\JATIC-Library\`（`JATIC-Library.exe` + `_internal\`） |
| 配布 zip | `dist\JATIC-Library-0.1.0-beta.1-win64.zip` |

- `build.bat` は `uv run pyinstaller` を使用
- Playwright **driver**（node + cli）は exe に同梱。Chromium 本体は初回に INST_27 ダイアログで DL
- `scripts\package-beta.ps1` はレガシー（`build.bat` が zip まで行うため通常不要）

検証手順: [BETA_TEST.md](BETA_TEST.md) / 記録: [BETA_TEST_LOG.md](BETA_TEST_LOG.md)

`src\jatic_library\resources\icons\app.ico` が無い場合は PyInstaller の `--icon` を外すか、アイコンを配置してください。

## 設計書

機能・API・DBスキーマは [DESIGN.md](DESIGN.md) を正とします。進捗は [DEV_STATUS.md](DEV_STATUS.md)。
