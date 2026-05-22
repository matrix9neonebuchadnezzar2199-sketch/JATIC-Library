# INST_31: 信頼性・性能向上パッチ（Cursor 向け修正指示書）

**目的:** 保管庫 UI フリーズ解消、404 再スクレイプ並行ガード、HTTP/1.1 フォールバック競合防止、統合 CSV タグ孤立解消、CSV ローダ型の精緻化を **1 修正 = 1 コミット = 1 PR** で land する。

**前提:** リポジトリ `matrix9neonebuchadnezzar2199-sketch/JATIC-Library`、ブランチ `master`、Python 3.11 / PySide6 6.7.2 / httpx 0.27.0 / polars 1.5.0 / Playwright 1.45.0 / Windows 10–11。

**作業順:** **#1 → #5**（#1 は他と疎結合で UX 影響最大）。各 PR で `uv run ruff check src tests` / `uv run mypy` / `uv run pytest -q` をすべて green にすること。

**コミット規約:** Conventional Commits（`perf:` `fix:` `refactor:`）。既存テスト破壊時は PR 本文に理由を明記。

**コード確認日:** 2026-05-22（`master` @ Chromium 同梱ビルド後）。行番号はこの時点の `src/` を基準とする。マージでずれた場合はシンボル名で再特定すること。

---

## 修正 #1 [perf, High] — 保管庫タブ初回表示の UI スレッドフリーズ解消

### 対象ファイル

| 種別 | パス |
|------|------|
| 新規 | `src/jatic_library/core/library_scan_cache.py` |
| 変更 | `src/jatic_library/core/library_scanner.py` |
| 変更 | `src/jatic_library/core/csv_loader.py`（キャッシュ呼び出しの薄いラッパのみ。ロジック本体は cache モジュールから呼ぶ） |
| 変更 | `src/jatic_library/ui/tabs/library_tab.py` |
| 定数 | `src/jatic_library/constants.py` に `LIBRARY_SCAN_CACHE_PATH` 追加（推奨） |

### 現状（実コード）

| 箇所 | 行 | 内容 |
|------|-----|------|
| `library_tab.py` | 71 | `__init__` 末尾で `self.refresh()` |
| `library_tab.py` | 148–156 | `refresh()` → `scan_library()` を **UI スレッド**で同期実行 |
| `library_scanner.py` | 94–108 | `_merge_file()` が `uncompressed_csv_size_in_zip()` + `count_data_rows_for_path()` を毎 ZIP で実行 |
| `library_scanner.py` | 131–146 | 統合 CSV も `count_data_rows_for_path(merged_csv)` |
| `csv_loader.py` | 38–47 | `uncompressed_csv_size_in_zip` — ZIP 中央ディレクトリ参照（比較的軽い） |
| `csv_loader.py` | 50–58 | `count_data_rows_in_zip` — CSV を **1MB チャンクで全走査**（重い） |
| `library_tab.py` | 217–222 | `format_library_file_label(..., row_count)` でツリーラベル構築 |

51 地域 × 複数月 × 数百 MB ZIP があると、保管庫タブ表示が数十秒〜数分ブロックし「応答なし」になりうる。

### 修正方針

**A. ディスク走査キャッシュ（`library_scan_cache.py`）**

- 保存先: `%LOCALAPPDATA%\JATIC-Library\library_scan_cache.json`（`APP_DATA_DIR / "library_scan_cache.json"` と `constants.py` で公開）。
- キー: `(path_str, file_size, mtime_ns)` — `Path.stat()` の `st_size` / `st_mtime_ns`（`st_mtime` のみだと ns 精度不足に注意。Python 3.11+ は `st_mtime_ns` 優先）。
- 値: `{"row_count": int | null, "uncompressed_csv_size": int | null}`（JSON では `null` 許容）。
- API 案:
  - `cache_key_for(path: Path) -> tuple[str, int, int]`
  - `get_cached_stats(path: Path) -> tuple[int | None, int | None] | None`（ミス時 `None`）
  - `set_cached_stats(path, row_count, uncompressed_size) -> None`
  - `invalidate_if_stale(path) -> bool`（キー不一致ならエントリ削除）
- I/O は try/except で包み、壊れた JSON は空 dict にリセットして続行（握り潰し禁止: loguru で warning）。

**B. `scan_library` / `_merge_file` の同期コスト削減**

- ツリー構築時:
  - キャッシュ **ヒット** → 保存済み `row_count` / `uncompressed_csv_size` を `LibraryFileItem` に設定。
  - **ミス** → `row_count=None`、`file_size` は ZIP の `st_size` または `uncompressed_csv_size_in_zip` の軽量取得のみ（方針: 行数だけ遅延、サイズはキャッシュ or 軽量 API。両方遅延でも可だがプレースホルダは `—行  —GB` に統一）。
- `count_data_rows_for_path` / `uncompressed_csv_size_in_zip` のフル走査を **`scan_library` のホットパスから除去**（キャッシュミス時は UI 側ワーカーが後から計算して cache に書く）。

**C. UI 非同期後追い（`library_tab.py`）**

- `_rebuild_tree()` 直後、キャッシュミスの `LibraryFileItem` 一覧に対し `QThreadPool.globalInstance()` + `QRunnable`（または `QThread` + `QObject` worker）で統計計算。
- 完了時に `QTreeWidgetItem.setText(0, new_label)` でラベル更新（`ROLE_FILE_ITEM` の参照はそのまま）。
- スレッド境界: Qt オブジェクトはワーカー内で触らない。完了は `Signal` または `QMetaObject.invokeMethod(..., Qt.QueuedConnection)` で UI スレッドへ。
- 初回ラベル例: `東京都  —行  —GB`（`format_library_file_label` の `row_count is None` 分支を既に利用可能、`library_scanner.py:25`）。
- `refresh()` 再入時: 進行中 runnable をキャンセルする世代 ID（`self._scan_generation: int`）を increment し、古い完了コールバックは無視。

**D. 受け入れの目安**

| 条件 | 目標 |
|------|------|
| 初回（キャッシュ空）51×12 ZIP | ツリー骨格表示 **≤ 500ms**（行数は後追い） |
| 2 回目以降（キャッシュ温） | **≤ 200ms** で行数・サイズ表示 |
| ZIP 更新（mtime/size 変化） | 該当エントリのみ再計算 |

### 追加テスト

**新規** `tests/test_library_scan_cache.py`

```python
def test_cache_hit_returns_stored_row_count(tmp_path: Path) -> None: ...
def test_cache_miss_when_mtime_changes(tmp_path: Path) -> None: ...
def test_cache_miss_when_file_size_changes(tmp_path: Path) -> None: ...
```

**拡張** `tests/test_library_scanner.py`

```python
def test_scan_library_fast_when_row_count_mocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import time
    monkeypatch.setattr(
        "jatic_library.core.library_scanner.count_data_rows_for_path",
        lambda _p: 100,
    )
    monkeypatch.setattr(
        "jatic_library.core.library_scanner.uncompressed_csv_size_in_zip",
        lambda _p: 1024,
    )
    # 51 zip を模した最小 fixture でも可
    start = time.perf_counter()
    scan_library(save_root)
    assert time.perf_counter() - start < 0.1
```

**任意** `tests/test_library_tab.py` — `QSignalSpy` で refresh 後すぐにツリー top-level が存在すること（Qt test、重い場合はスキップ可）。

### コミット例

`perf(library): defer ZIP row counting and persist scan cache`

---

## 修正 #2 [fix, High] — 404 再スクレイプの並行多重実行ガード

### 対象ファイル

`src/jatic_library/core/downloader.py`

### 現状（`downloader.py:245-258`）

```245:258:src/jatic_library/core/downloader.py
    async def _maybe_rescrape_on_404(self, exc: Exception, rescrape_state: dict[str, bool]) -> bool:
        if rescrape_state.get("done"):
            return False
        status_code = None
        if isinstance(exc, httpx.HTTPStatusError):
            status_code = exc.response.status_code
        if status_code != httpx.codes.NOT_FOUND:
            return False
        logger.warning("404 for ZIP URL, running one-time Playwright rescrape")
        from jatic_library.core.playwright_scraper import scrape_and_save_targets

        await scrape_and_save_targets()
        rescrape_state["done"] = True
        return True
```

`Downloader.__init__`（`downloader.py:77-83`）にロックなし。`asyncio.Semaphore`（`concurrency` 既定 3）で並行 DL 中、複数タスクが同時 404 → **Playwright が並列起動**しうる。

既存テスト `tests/test_downloader_rescrape.py::test_maybe_rescrape_runs_once` は **同一 coroutine 内の直列 2 回呼び出し**のみ。並行は未カバー。

### 修正方針

`Downloader.__init__` に `self._rescrape_lock = asyncio.Lock()` を追加。

`status_code` 判定はロック **外**（404 以外は待たない）。404 のみ `async with self._rescrape_lock:` 内で `rescrape_state["done"]` を再チェック → scrape → `done=True`。

### 適用 diff

```diff
     def __init__(
         self,
         settings: DownloadSettings,
         repo: Repository,
     ) -> None:
         self._settings = settings
         self._repo = repo
+        self._rescrape_lock = asyncio.Lock()

     async def _maybe_rescrape_on_404(self, exc: Exception, rescrape_state: dict[str, bool]) -> bool:
-        if rescrape_state.get("done"):
-            return False
         status_code = None
         if isinstance(exc, httpx.HTTPStatusError):
             status_code = exc.response.status_code
         if status_code != httpx.codes.NOT_FOUND:
             return False
-        logger.warning("404 for ZIP URL, running one-time Playwright rescrape")
-        from jatic_library.core.playwright_scraper import scrape_and_save_targets
-
-        await scrape_and_save_targets()
-        rescrape_state["done"] = True
-        return True
+        async with self._rescrape_lock:
+            if rescrape_state.get("done"):
+                return False
+            logger.warning("404 for ZIP URL, running one-time Playwright rescrape")
+            from jatic_library.core.playwright_scraper import scrape_and_save_targets
+
+            await scrape_and_save_targets()
+            rescrape_state["done"] = True
+            return True
```

`asyncio` はファイル先頭で **既に import 済み**（`downloader.py:5`）。

### 受け入れ条件

- `asyncio.gather` で 5 タスクが同時に 404 経路を踏んでも `scrape_and_save_targets` の **await 回数は 1**。
- HTTP 500 等はロック未取得のまま `False`（`Lock.acquire` モックで検証可）。

### 追加テスト（`tests/test_downloader_rescrape.py`）

```python
@pytest.mark.asyncio
async def test_rescrape_on_404_concurrency_protection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """並行 404 でも Playwright rescrape は 1 回だけ。"""
    from unittest.mock import AsyncMock
    # Downloader 生成 → scrape AsyncMock → gather 5 × _maybe_rescrape_on_404
    # assert mock.call_count == 1

@pytest.mark.asyncio
async def test_rescrape_skipped_for_non_404_without_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """500 ではロックを取らない。"""
    # patch asyncio.Lock.acquire を spy → 500 経路で acquire 0 回
```

### コミット例

`fix(downloader): serialize 404 rescrape with asyncio lock`

---

## 修正 #3 [fix, Medium] — HTTP/2 → HTTP/1.1 フォールバックの競合防止

### 対象ファイル

`src/jatic_library/core/http_client.py`

### 現状（`http_client.py:56-66`）

```56:66:src/jatic_library/core/http_client.py
    async def _fallback_to_http1(self) -> None:
        global _http1_only, _fallback_logged
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        _http1_only = True
        self._use_http2 = False
        if not _fallback_logged:
            logger.warning("HTTP/2 unavailable, fell back to HTTP/1.1")
            _fallback_logged = True
        await self._ensure_client()
```

並行リクエストが同時に HTTP/2 ネゴシエーション失敗すると、`aclose()` 競合・二重 `_ensure_client()` の可能性。

**注意:** `import asyncio` は現状 **未 import**（ファイル先頭に追加必須）。

**禁止:** モジュールトップレベルの `asyncio.Lock()`（イベントループ未束縛）。**インスタンス属性** `self._fallback_lock = asyncio.Lock()` in `__init__`（`http_client.py:28-31` 付近）。

### 修正方針

ロック内で「既に HTTP/1.1 クライアントが有効」なら早期 return:

```python
if not self._use_http2 and self._client is not None:
    return
```

その後 `aclose` → グローバル `_http1_only` 更新 → `_ensure_client()`。

### 適用 diff

```diff
+import asyncio
 ...
 class JarticHttpClient:
     def __init__(self, timeout_sec: float = 60.0) -> None:
         self._timeout = timeout_sec
         self._client: httpx.AsyncClient | None = None
         self._use_http2 = not _http1_only
+        self._fallback_lock = asyncio.Lock()

     async def _fallback_to_http1(self) -> None:
         global _http1_only, _fallback_logged
-        if self._client is not None:
-            await self._client.aclose()
-            self._client = None
-        _http1_only = True
-        self._use_http2 = False
-        if not _fallback_logged:
-            logger.warning("HTTP/2 unavailable, fell back to HTTP/1.1")
-            _fallback_logged = True
-        await self._ensure_client()
+        async with self._fallback_lock:
+            if not self._use_http2 and self._client is not None:
+                return
+            if self._client is not None:
+                await self._client.aclose()
+                self._client = None
+            _http1_only = True
+            self._use_http2 = False
+            if not _fallback_logged:
+                logger.warning("HTTP/2 unavailable, fell back to HTTP/1.1")
+                _fallback_logged = True
+            await self._ensure_client()
```

### 受け入れ条件

- 同一 `JarticHttpClient` に対し `asyncio.gather(*[client._fallback_to_http1() for _ in range(5)])` で `httpx.AsyncClient` の生成は実質 1 回、`aclose` も 1 回。
- フォールバック後の `head` / `get_stream` が HTTP/1.1 で動作（既存テスト維持）。

### 追加テスト（`tests/test_http_client.py`）

```python
@pytest.mark.asyncio
async def test_fallback_to_http1_is_idempotent_under_concurrency() -> None:
    from unittest.mock import AsyncMock, MagicMock, patch
    reset_http_fallback_state_for_tests()
    client = JarticHttpClient(timeout_sec=5.0)
    mock_httpx = MagicMock()
    mock_httpx.aclose = AsyncMock()
    client._client = mock_httpx
    client._use_http2 = True
    await asyncio.gather(*[client._fallback_to_http1() for _ in range(5)])
    assert mock_httpx.aclose.await_count == 1
    assert client._use_http2 is False
```

`autouse` fixture `_reset_http` は既存（`test_http_client.py:13-15`）。

### コミット例

`fix(http): guard HTTP/1.1 fallback with per-client lock`

---

## 修正 #4 [fix, Medium] — 統合 CSV 削除時の tag_assignments 孤立

### 対象ファイル

`src/jatic_library/ui/main_window.py`

### 現状（`main_window.py:428-445`）

```428:445:src/jatic_library/ui/main_window.py
    def _on_delete_file(self, file_item: object) -> None:
        ...
        if file_item.target_code:
            try:
                row = self._repo.get_file(file_item.publish_ym, file_item.target_code)
                if row is not None and row.id is not None:
                    self._repo.delete_file(row.id)
                    code = file_item.target_code or file_item.file_name
                    scope_key = f"{file_item.publish_ym}/{code}"
                    self._repo.delete_tag_assignments("file", scope_key)
            except sqlite3.Error as exc:
                errors.append(f"DB: {exc}")
```

- 統合 CSV は `library_scanner.py:139` で `target_code="merged"`。**`files` テーブルに行なし** → `row is None` → **`delete_tag_assignments` がスキップ**。
- `library_tab.py` のタグ UI は統合 CSV にも付与可能（`target_code="merged"` → `scope_key = "{publish_ym}/merged"`、`library_tab.py:288-290` の `_file_scope_key`）。

### 修正方針

`delete_tag_assignments` を **`files` 行削除ブロックの外**に独立させ、`target_code` があれば常に実行。

`delete_file(row.id)` は従来どおり `row is not None` のときのみ。

### 適用 diff

```diff
         if file_item.target_code:
             try:
                 row = self._repo.get_file(file_item.publish_ym, file_item.target_code)
                 if row is not None and row.id is not None:
                     self._repo.delete_file(row.id)
-                    code = file_item.target_code or file_item.file_name
-                    scope_key = f"{file_item.publish_ym}/{code}"
-                    self._repo.delete_tag_assignments("file", scope_key)
             except sqlite3.Error as exc:
                 errors.append(f"DB: {exc}")

+        if file_item.target_code:
+            try:
+                code = file_item.target_code or file_item.file_name
+                scope_key = f"{file_item.publish_ym}/{code}"
+                self._repo.delete_tag_assignments("file", scope_key)
+            except sqlite3.Error as exc:
+                errors.append(f"DB Tags: {exc}")
+
         if file_item.target_code:
             try:
                 manifest = Manifest.load(folder)
```

manifest / 物理削除の順序は INST_24 どおり維持（DB 行 → タグ → manifest → file）。

### 受け入れ条件

- `target_code="merged"` でタグ付与 → 削除後 `list_tags_for("file", "2026_3/merged")` が `[]`。
- 通常 ZIP（`tokyo` 等）の削除・タグ削除・順序は回帰なし。

### 追加テスト

**新規** `tests/test_main_window_delete.py`（または `tests/test_delete_file.py` に追記）

```python
def test_delete_merged_csv_removes_tag_assignments(
    qapp: QApplication, tmp_path: Path
) -> None:
    """統合 CSV は files 行がなくても tag_assignments を掃除する。"""
    # Repository 実 DB
    # assign_tag → LibraryFileItem(target_code="merged", publish_ym="2026_3", ...)
    # _on_delete_file → list_tags_for が空
```

既存 `test_delete_calls_db_before_manifest_before_file`（`tests/test_delete_file.py:78-108`）は **tokyo ZIP** 向け。`delete_tag_assignments` の呼び出し位置変更後も `mock_tags.assert_called_once_with("file", "2026_3/tokyo")` が維持されること。

### コミット例

`fix(ui): delete tag assignments for merged CSV without files row`

---

## 修正 #5 [fix, Low-Medium] — CSV ローダの型と例外の精緻化

### 対象ファイル

`src/jatic_library/core/csv_loader.py`

### 現状

| 箇所 | 行 | 問題 |
|------|-----|------|
| `_count_newlines_in_binary_stream` | 16–23 | 引数 `zipfile.ZipExtFile \| object` + `# type: ignore[union-attr]` |
| `read_csv_frame_from_bytes` | 71–84 | `except Exception` が広すぎ（`MemoryError` も `CsvLoadError` に化ける） |

### 修正方針

```diff
+from typing import IO
 ...
-def _count_newlines_in_binary_stream(stream: zipfile.ZipExtFile | object) -> int:
+def _count_newlines_in_binary_stream(stream: IO[bytes]) -> int:
     total = 0
-    while chunk := stream.read(1024 * 1024):  # type: ignore[union-attr]
-        if isinstance(chunk, str):
-            chunk = chunk.encode("utf-8")
+    while chunk := stream.read(1024 * 1024):
         total += chunk.count(b"\n")
```

`read_csv_frame_from_bytes`:

```diff
-        except Exception as exc:
+        except (UnicodeDecodeError, pl.exceptions.ComputeError) as exc:
             last_error = exc
+    # MemoryError 等は握り潰さない — そのまま伝播
     raise CsvLoadError(str(last_error or "Could not decode CSV"))
```

**実装時確認:** polars 1.5.0 に `pl.exceptions.NoDataError` があるか。無ければ `ComputeError` のみで足りるかテストで確認。空 CSV で `NoDataError` が出るならタプルに追加。

### 受け入れ条件

- `uv run mypy` で `csv_loader.py` エラーなし。
- `pl.read_csv` が `MemoryError` を投げた場合、`CsvLoadError` ではなく `MemoryError` がそのまま上がる。

### 追加テスト（`tests/test_csv_loader.py`）

```python
def test_memory_error_is_not_swallowed(monkeypatch: pytest.MonkeyPatch) -> None:
    import polars as pl
    def boom(*args, **kwargs):
        raise MemoryError("simulated OOM")
    monkeypatch.setattr(pl, "read_csv", boom)
    with pytest.raises(MemoryError):
        read_csv_frame_from_bytes(b"a,b\n1\n")
```

### コミット例

`refactor(csv): tighten loader types and exception handling`

---

## 全修正完了後の検証（Cursor 必須）

リポジトリルートで順に実行:

```powershell
cd F:\Cursor\JATIC-Library
uv sync --group dev
uv run ruff check src tests
uv run mypy
uv run pytest -q
```

**手動（PR 本文に記載）:**

1. `uv run python -m jatic_library` で GUI 起動。
2. 保管庫タブを開き、骨格表示が **体感 1 秒以内**、行数が後から埋まること（#1）。
3. 統合 CSV にタグ付与 → 削除 → DB にタグ残存なし（#4）。

配布 exe 確認時は `.\build.bat` 後の `dist\JATIC-Library\JATIC-Library.exe` を使用（Chromium 同梱ビルド）。

---

## 本パッチに含めない項目（次フェーズ推奨）

| 項目 | 箇所 | 理由 |
|------|------|------|
| 月ノード特定のラベル部分一致 | `library_tab.py:261-267` `_month_from_node` | ローカル影響・顕在化しにくい。`LibraryMonthItem` を `QTreeWidgetItem` の `setData` で保持する構造改修を別 issue 化 |
| `merge_region_zip_csvs` の OOM | `csv_loader.py:95-100` | 現行データ規模では稀。LazyFrame + `sink_csv` は別 issue |

---

## 指示書メタ

| 項目 | 値 |
|------|-----|
| 番号 | INST_31 |
| 作成 | 2026-05-22 |
| 依存 | INST_11（保管庫）, INST_13（404 rescrape）, INST_06（HTTP client） |
| 想定 PR 数 | 5（#1〜#5 各 1） |
