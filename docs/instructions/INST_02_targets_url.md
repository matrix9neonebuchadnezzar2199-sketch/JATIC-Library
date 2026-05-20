# 指示書 #02: 定数・地域マスタ・URL生成

## 前提
- 完了済み指示書: #01
- 参照ドキュメント: docs/DESIGN.md の §3, §4, §6.1

## ゴール
アプリ全体で使う定数・51地域マスタ・URL生成ロジックを実装し、
すべての単体テストがpassする状態にする。
特に「2026/5/15時点 → 公開対象は2026_3」のような publish_info計算が正確であること。

## 作成・変更ファイル
- `src/jatic_library/constants.py`（実装）
- `src/jatic_library/core/targets.py`（新規）
- `src/jatic_library/core/url_builder.py`（新規）
- `src/jatic_library/resources/targets.json`（新規、ハードコード版）
- `tests/test_constants.py`（新規）
- `tests/test_targets.py`（新規）
- `tests/test_url_builder.py`（新規）

## 実装要件

### constants.py
DESIGN.md §3 の内容をそのまま実装。`REPO_URL`, `TARGETS_CACHE_PATH`, `TZ_JST` を含む。
`JARTIC_DATA_DIR_TPL` は `JARTIC_BASE + "/d/opendata/{publish_ym_compact}/"` 形式。

### core/targets.py
DESIGN.md §4 の TARGETS タプル全51件。ヘルパ:

- `by_code(code: str) -> Target`（KeyError）
- `by_region(region: Region) -> list[Target]`
- `all_targets() -> tuple[Target, ...]`
- `all_codes() -> list[str]`（order順）
- `load_overrides(cache_path: Path) -> tuple[Target, ...]`
- `save_overrides(targets: list[Target], cache_path: Path) -> None`

JSON: `{"version": 1, "scraped_at": null, "targets": [{"code": "...", "filename_key": "..."}]}`

### core/url_builder.py
- `PublishInfo` dataclass
- `compute_publish_info(today: date) -> PublishInfo`
- `build_zip_url(info, filename_key)` — `JARTIC_ZIP_TPL.format(...)`
- `parse_folder_name(folder_name: str) -> tuple[int, int]`（ValueError）

### resources/targets.json
51件の code / filename_key バックアップ。

## テスト要件

### tests/test_constants.py
- APP_NAME, JARTIC_BASE 等の値確認

### tests/test_targets.py
- 51件、order 1〜51、code重複なし
- by_code / by_region（北海道5、関東8、沖縄1、全Region合計51）
- load_overrides / save_overrides 往復

### tests/test_url_builder.py
パラメータ化テーブル:

| today | publish_year | publish_month | data_year | data_month | folder_name |
|-------|--------------|---------------|-----------|------------|-------------|
| 2026-05-15 | 2026 | 5 | 2026 | 3 | 2026_3 |
| 2026-05-01 | 2026 | 5 | 2026 | 3 | 2026_3 |
| 2026-05-31 | 2026 | 5 | 2026 | 3 | 2026_3 |
| 2026-01-01 | 2026 | 1 | 2025 | 11 | 2025_11 |
| 2026-02-15 | 2026 | 2 | 2025 | 12 | 2025_12 |
| 2026-03-01 | 2026 | 3 | 2026 | 1 | 2026_1 |
| 2026-12-31 | 2026 | 12 | 2026 | 10 | 2026_10 |

- build_zip_url → `https://www.jartic.or.jp/d/opendata/202605010000/typeB_tokyo.zip`
- parse_folder_name 正常/異常ケース

## 動作確認手順
1. `pytest tests/ -v`（20件以上）
2. `ruff check src/ tests/`
3. インタラクティブで `compute_publish_info(date(2026,5,15))` → folder `2026_3`

## やらないこと（スコープ外）
- 実サイトアクセス（#07）
- filename_key 実値検証
- Pydantic設定（#03）

## コミットメッセージ案
```
feat(core): add constants, targets master, and URL builder with unit tests
```
