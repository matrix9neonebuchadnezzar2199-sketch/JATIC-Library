# 指示書 #04: SQLiteリポジトリ

## 前提
- 完了済み指示書: #01, #02, #03
- 参照ドキュメント: docs/DESIGN.md の §5.2

## ゴール
SQLiteによる履歴管理層を実装。スキーマ作成・マイグレーション・各テーブルへのCRUDが
動作し、すべての単体テストがpassする状態にする。

## 作成・変更ファイル
- `src/jatic_library/core/models.py`（新規）
- `src/jatic_library/core/repository.py`（新規）
- `tests/test_repository.py`（新規）

## 実装要件

### core/models.py
`PublicationRow`, `FileRow`, `CheckHistoryRow`, `TagRow`, `TagAssignmentRow`, `EventLogRow`
および Literal 型エイリアス。

### core/repository.py
- `SCHEMA_VERSION = 1`, `SCHEMA_SQL`（schema_meta 含む）
- `connect` / `close` / context manager / `transaction`
- `PRAGMA foreign_keys=ON`, `journal_mode=WAL`
- publications: upsert, get, list, is_publication_complete
- files: upsert, get, list, delete
- check_history: add, get_last, list
- tags: create, list, delete, assign, unassign, list_tags_for, list_targets_with_tag
- event_logs: add, list, purge_old_logs
- `list_missing_publications(start_ym, end_ym)` — #02 `parse_folder_name` 使用

日時は JST: `datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(timespec="seconds")`

## テスト要件

### tests/test_repository.py（25件以上）
- 接続・マイグレーション冪等・foreign_keys
- publications upsert / complete 判定
- files upsert 上書き / delete
- check_history 降順 limit
- tags CASCADE / IntegrityError
- event_logs フィルタ / purge
- list_missing_publications
- transaction ロールバック

## 動作確認手順
1. `pytest tests/test_repository.py -v`
2. `ruff check src/ tests/`
3. インタラクティブで Repository 往復

## やらないこと（スコープ外）
- ダウンローダ結合（#06）
- loguru 連携（#05）
- UI（#11）

## コミットメッセージ案
```
feat(core): add SQLite repository layer with publications/files/tags/logs
```
