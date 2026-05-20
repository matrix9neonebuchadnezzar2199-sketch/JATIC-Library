# 現行コードと指示書 #01〜#04 の差分

**2026-05-20 更新: #01〜#04 照合完了。** 以降は #05 から新規実装。

## 完了サマリ

| # | 主な成果 | 検証 |
|---|----------|------|
| 01 | setuptools、`Hello from JATIC-Library`、ディレクトリ雛形 | `python -m jatic_library` |
| 02 | constants / targets / url_builder / targets.json | pytest 20件+ |
| 03 | AppConfig + ConfigStore（破損JSONバックアップ） | pytest 15件+ |
| 04 | models + Repository 全CRUD | pytest 25件+ |

## 意図的な差分（許容）

| 項目 | 指示書 | 採用 |
|------|--------|------|
| パッケージマネージャ | pip / venv 記載 | **uv** も `run.bat` / README で併記 |
| `LEARNED_TARGETS_PATH` | `TARGETS_CACHE_PATH` 名 | 同義で `TARGETS_CACHE_PATH` を使用 |

## 次の指示書

#05 ロガー・ノーティファイア から（マスター作成待ち）。
