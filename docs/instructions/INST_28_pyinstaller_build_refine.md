# INST_28: PyInstaller ビルドの改善と配布物作成

## 目的

`build.bat` / `jatic-library.spec` を実運用レベルに引き上げ、
`v0.1.0-beta.1` の配布 zip を 1 コマンドで生成する。

## 意思決定（確定）

| 項目 | 採用 |
|------|------|
| UPX | **無効**（`upx=False`） |
| `playwright/driver/` | **datas 同梱**（Node ランタイム含む） |
| `uv sync` in build.bat | **しない**（DEV_SETUP で初回案内） |

## 対象ファイル

- `jatic-library.spec`, `build.bat`
- `pyproject.toml`, `src/jatic_library/__init__.py`, `constants.py`
- `docs/BETA_TEST.md`, `.gitignore`

## 受け入れ基準

- `build.bat` 完走 → `dist/JATIC-Library/JATIC-Library.exe` + zip
- zip に README, LICENSE, BETA_TEST, `playwright/driver/` を含む
- exe で GUI 起動（タイトルまで）。詳細 smoke は INST_29

## 関連

- INST_27: frozen install が `playwright._impl._driver` と driver datas に依存
- INST_29: smoke test / クリーン環境

## コミット

`build(release): refine PyInstaller spec and distribution zip`
