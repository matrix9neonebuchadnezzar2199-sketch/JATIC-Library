# 指示書 #01: プロジェクト初期化

## 前提
- 完了済み指示書: なし（初回）
- 参照ドキュメント: docs/DESIGN.md の §1, §2, §10
- 作業ディレクトリ: F:\Cursor\JATIC-Library

## ゴール
JATIC-Libraryプロジェクトの雛形を作成し、`pip install -e .` が成功し、
`python -m jatic_library` で「Hello from JATIC-Library v0.1.0」が表示される状態にする。

## 作成ファイル一覧

### ルート直下
- `.gitignore`（新規）
- `.python-version`（新規、内容: `3.11`）
- `README.md`（新規）
- `LICENSE`（新規、MITライセンス）
- `pyproject.toml`（新規）
- `requirements.txt`（新規）
- `requirements-dev.txt`（新規）
- `run.bat`（新規）
- `build.bat`（新規、最小ひな形のみ）

### ディレクトリ構造（空ディレクトリは `.gitkeep` を置く）
```
src/
  jatic_library/
    __init__.py
    __main__.py
    app.py
    constants.py
    core/
      __init__.py
    ui/
      __init__.py
      widgets/
        __init__.py
      models/
        __init__.py
      dialogs/
        __init__.py
      themes/
        .gitkeep
    settings/
      __init__.py
    resources/
      icons/
        .gitkeep
      version.txt        ← 内容: "0.1.0"
tests/
  __init__.py
docs/
  DESIGN.md
  ROADMAP.md
  instructions/
```

## 実装要件

### pyproject.toml
- ビルドシステム: setuptools
- name: jatic-library
- version: 0.1.0（src/jatic_library/__init__.py の __version__ と一致させる）
- requires-python: ">=3.11,<3.12"
- description: "JARTIC断面交通量情報の自動取得・管理ツール"
- authors: matrix9neonebuchadnezzar2199-sketch
- license: MIT
- dependencies: requirements.txt と同期（直接列挙でよい）
- [project.scripts]: jatic-library = "jatic_library.__main__:main"
- [tool.setuptools.packages.find]: where = ["src"]
- [tool.setuptools.package-data]:
    "jatic_library" = ["resources/**/*", "ui/themes/*.qss"]
- [tool.ruff]: line-length = 100, target-version = "py311"
- [tool.pytest.ini_options]: testpaths = ["tests"], asyncio_mode = "auto"

### requirements.txt
```
PySide6==6.7.2
httpx[http2]==0.27.0
selectolax==0.3.21
polars==1.5.0
pyqtgraph==0.13.7
GitPython==3.1.43
pydantic==2.8.2
pydantic-settings==2.4.0
win11toast==0.35
playwright==1.45.0
loguru==0.7.2
chardet==5.2.0
```

### requirements-dev.txt
```
-r requirements.txt
pytest==8.3.2
pytest-qt==4.4.0
pytest-asyncio==0.23.8
ruff==0.5.7
mypy==1.11.1
pyinstaller==6.10.0
```

### .gitignore
- Python標準（__pycache__, *.pyc, .venv, build, dist, *.egg-info）
- IDE（.vscode, .idea, .cursor）
- OS（Thumbs.db, .DS_Store）
- アプリ固有（*.log, .pytest_cache, .mypy_cache, .ruff_cache）
- PyInstaller出力（dist/, build/, *.spec）

### src/jatic_library/__init__.py
```python
__version__ = "0.1.0"
__app_name__ = "JATIC-Library"
```

### src/jatic_library/__main__.py
```python
"""エントリポイント: python -m jatic_library"""
from jatic_library import __app_name__, __version__


def main() -> int:
    """暫定実装。指示書#09でPySide6アプリ起動に置き換える。"""
    print(f"Hello from {__app_name__} v{__version__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### src/jatic_library/app.py
- 中身は空（`"""QApplication起動。指示書#09で実装。"""` のみのdocstring）

### src/jatic_library/constants.py
- 中身は空（`"""定数定義。指示書#02で実装。"""` のみのdocstring）

### run.bat
```bat
@echo off
cd /d %~dp0
python -m jatic_library %*
```

### build.bat（最小ひな形）
```bat
@echo off
echo PyInstallerビルドは指示書#19で実装します。
exit /b 0
```

### README.md
- プロジェクト名、概要（DESIGN.md §0から要約）
- セットアップ手順（venv / pip install -e .）
- 開発: `run.bat`、`pytest`
- ライセンス: MIT
- リポジトリ: https://github.com/matrix9neonebuchadnezzar2199-sketch/JATIC-Library

### docs/ROADMAP.md
- Phase 0〜10の表（DESIGN.md §12を転記）
- 指示書一覧（#01〜#20のタイトルと進捗チェックボックス）

## テスト要件
本指示書ではテストコードは作成しない（次の指示書から）。

## 動作確認手順
1. `python -m venv .venv`
2. `.venv\Scripts\activate`
3. `pip install -r requirements-dev.txt`
4. `pip install -e .`
5. `python -m jatic_library` → `Hello from JATIC-Library v0.1.0`
6. `run.bat` でも同様
7. `pytest` → テスト0件で正常終了
8. `ruff check src/` → エラー0件

## やらないこと（スコープ外）
- 実際の機能実装は一切しない（雛形のみ）
- DESIGN.mdの内容記述は手動配置とする
- Playwrightブラウザのインストールは実行しない

## コミットメッセージ案
```
chore: initialize project skeleton with PySide6/httpx/polars stack
```
