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

## 配布ビルド

```powershell
.\build.bat
```

`src\jatic_library\resources\icons\app.ico` が無い場合は PyInstaller の `--icon` を外すか、アイコンを配置してください。

## 設計書

機能・API・DBスキーマは [DESIGN.md](DESIGN.md) を正とします。
