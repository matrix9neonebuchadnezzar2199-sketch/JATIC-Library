# INST_26: SQLite WAL モード化

## 目的

ワーカースレッドが `Repository(DB_PATH)` を新規生成してメインスレッドと同じ DB を開く設計のため、
書き込み競合時に `database is locked` が発生する余地がある。`PRAGMA journal_mode=WAL` を
有効化し、複数接続からの読み書き並行性を確保する。

## 対象ファイル

- `src/jatic_library/core/repository.py`
- `src/jatic_library/ui/main_window.py`（終了時 checkpoint）
- `docs/DESIGN.md`（永続データ一覧に `.db-wal` / `.db-shm` を追記）
- `tests/test_repository.py`（新規 or 拡張）

## 実装手順

### 1. `Repository.__init__` で WAL を発行

```python
def _init_pragmas(self) -> None:
    cur = self._conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute("PRAGMA synchronous=NORMAL")
    cur.execute("PRAGMA foreign_keys=ON")
    self._conn.commit()
```

接続時 `timeout=5.0` を維持または追加する。

### 2. WAL ファイルの扱い

WAL モード有効化後は `history.db-wal` と `history.db-shm` が `%LOCALAPPDATA%\JATIC-Library\`
に作られる。`docs/DESIGN.md` の永続データ一覧に明記する。

### 3. シャットダウン時のチェックポイント

`MainWindow.closeEvent` の完全終了パスで `repo.checkpoint()` を呼び、WAL を本体に統合する。

```python
def checkpoint(self) -> None:
    self._conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    self._conn.commit()
```

### 4. PyInstaller ビルドでの考慮

特になし（SQLite は標準ライブラリ）。配布物に `.db-wal` / `.db-shm` を同梱しないこと。

## 受け入れ基準

- `Repository` 起動直後に `PRAGMA journal_mode` が `wal` を返す。
- 2 つの接続から並行書き込みを行うストレステストで `database is locked` が発生しない
  （タイムアウト 5 秒以内）。
- 通常終了後、`history.db-wal` のサイズが 0 または `.db` 本体に統合済み。

## テスト

- `test_journal_mode_is_wal`
- `test_concurrent_writers_do_not_deadlock`（`ThreadPoolExecutor` で 2 並列書き込み）
- `test_checkpoint_truncates_wal`

## コミット

`fix(core): enable sqlite WAL mode for worker connections`
