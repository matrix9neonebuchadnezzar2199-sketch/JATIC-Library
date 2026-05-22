# INST_32: 保管庫タブの応答性フォローアップとツリー／CSV 結合の堅牢化（Cursor 向け修正指示書）

**目的:** INST_31 で見送った保管庫まわりの運用改善（キャッシュ掃除・並列度）、月ノード引き当ての堅牢化、統合 CSV 結合の OOM 低減を **1 修正 = 1 コミット = 1 PR** で land する。

**前提:** リポジトリ `matrix9neonebuchadnezzar2199-sketch/JATIC-Library`、ブランチ `master`、Python 3.11 / PySide6 6.7.2 / httpx 0.27.0 / polars 1.5.0 / Playwright 1.45.0 / Windows 10–11。

**ベースライン（2026-05-22）:** HEAD `4089faa`、pytest **165 passed**。INST_31 #1〜#5 land 済。

**作業順:** **#1 → #2 → #3**（#2・#3 は #1 に非依存だが、レビューしやすさのため UI 堅牢化を最後に置かない。#3 は I/O 重いため #2 の後でも可）。

**コミット規約:** Conventional Commits（`perf:` `fix:` `refactor:`）。各 PR で `uv run ruff check src tests` / `uv run mypy` / `uv run pytest -q` をすべて green にすること。

**作業ルール:** 実装 → 開発日記追記 → commit → push → 次、を INST_31 と同様に繰り返す。

---

## INST_31 との関係（必読）

| トピック | INST_31 | INST_32 |
|----------|---------|---------|
| 保管庫 UI フリーズ（キャッシュ + 非同期行数） | **#1 として land 済**（`ff7ef52`） | **#1 はフォローアップのみ**（下記差分） |
| `_month_from_node` ラベル部分一致 | 見送り（本書 #2） | **#2** |
| `merge_region_zip_csvs` OOM | 見送り（本書 #3） | **#3** |

### INST_31 #1 で既に入っている実装（再実装しない）

| 要素 | パス / シンボル |
|------|----------------|
| JSON 永続キャッシュ | `src/jatic_library/core/library_scan_cache.py`、`LIBRARY_SCAN_CACHE_PATH`（`constants.py`） |
| スキャン時の遅延行数 | `library_scanner.scan_library()` — ミス時 `row_count=None` |
| バックグラウンド統計 | `ui/widgets/library_stats_worker.py`、`library_tab._schedule_stats_refresh()` |
| 世代 ID によるキャンセル | `library_tab._scan_generation` |
| テスト | `tests/test_library_scan_cache.py`、`tests/test_library_scanner.py` |

**INST_32 では SQLite キャッシュへの置き換えは行わない。** `history.db` とは寿命が異なる統計キャッシュであり、INST_31 で採用した JSON + 原子的 `*.tmp` 置換を正とする。SQLite 案は本指示書から削除した（Cursor が旧ドラフトを参照しても二重実装しないこと）。

---

## 修正 #1 [perf, Medium] — 保管庫キャッシュ運用の仕上げと受け入れ検証

### 対象ファイル

| 種別 | パス |
|------|------|
| 変更 | `src/jatic_library/core/library_scan_cache.py` |
| 変更 | `src/jatic_library/ui/tabs/library_tab.py` |
| 変更 | `src/jatic_library/ui/widgets/library_stats_worker.py` |
| 変更 | `tests/test_library_scan_cache.py` |

### 現状のギャップ（INST_31 後）

- `refresh()` 後に **削除済み ZIP のキャッシュエントリが残る**（JSON が肥大化しうる）。
- `QThreadPool.globalInstance()` の **並列度未制限** — キャッシュミス多数時にディスク I/O が競合し、後追い更新が遅くなることがある。
- 受け入れ目標（初回 ≤500ms / 再起動 ≤200ms）は **自動テスト未固定**（手動計測 + PR 記載が必要）。

### 修正方針

**A. キャッシュ掃除 `evict_stale_entries(valid_paths: set[Path]) -> int`**

- `library_scan_cache.py` に追加。`_load_entries()` の各キーは `cache_key_for` と同形式の JSON 配列 `[resolved_path, size, mtime_ns]`。パス文字列が `valid_paths` に含まれない、または `Path(path).is_file()` が偽のエントリを削除して `_save_entries`。
- `library_tab.refresh()` の `scan_library` 完了後、今回ツリーに載った全 `LibraryFileItem.file_path` の集合を渡して掃除する。

**B. バックグラウンド並列度**

- `LibraryTab` 専用の `QThreadPool`（`self._stats_pool`）を `__init__` で生成し `setMaxThreadCount(2)`。`enqueue_file_stats(..., pool)` に渡す（`globalInstance` は使わない）。

**C. 受け入れ検証（手動・PR 必須）**

| 条件 | 目標 | 計測 |
|------|------|------|
| 初回（キャッシュ空） | ツリー骨格が操作可能になるまで **≤ 500ms** | `topLevelItemCount() > 0` の時刻（保管庫タブ表示直後から） |
| 2 回目以降（キャッシュ温） | **≤ 200ms** で行数・サイズが揃う（または後追い完了までの合計を PR に明記） |
| 計算中の UI | スクロール・タブ切替・検索入力がブロックされない | 体感 + 可能なら動画/GIF 不要、数値のみ可 |

**計測・リリース:** [PERF_MEASUREMENT_RULES.md](PERF_MEASUREMENT_RULES.md) に従う（実装 land と計測は別タイミング可。**`v0.1.0-beta.2` は計測「達成」後のみ**）。未達時は INST_33 等でチューニング。報告・記録には **計測未済 / 達成（数値） / 未達（数値）** を明記。

**PR 本文に併記する測定環境（必須）:** OS バージョン、ストレージ種別（SSD / HDD）、論理 CPU コア数、保管庫 ZIP 件数と合計サイズ（概算可）。RSS は PowerShell `Get-Process` または `resmon.exe` でも可（ルール正本参照）。

大規模 fixture が無い CI では閾値の **自動アサートは任意**。代わりに `test_scan_library_completes_under_100ms_with_cache_hits`（INST_31 既存）の維持を確認すること。

### 追加すべきテスト

`tests/test_library_scan_cache.py`:

```python
def test_evict_stale_entries_removes_missing_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None: ...
```

- 2 ファイル分キャッシュ → 1 ファイル削除 → `evict_stale_entries({remaining})` が 1 を返し、削除側キーが読めないこと。

### コミット例

`perf(library): evict stale scan cache entries and cap stats pool`

---

## 修正 #2 [refactor, Low-Medium] — `_month_from_node` のラベル一致脆弱性を解消

### 対象ファイル

- 変更: `src/jatic_library/ui/tabs/library_tab.py`
- 任意: `tests/test_library_tab.py`（新規または拡張）

### 現状（実コード）

`library_tab.py` 付近:

```python
def _month_from_node(self, month_node: QTreeWidgetItem) -> LibraryMonthItem | None:
    label = month_node.text(0)
    for year_item in self._tree_data:
        for month_item in year_item.months:
            if month_item.folder_name in label:
                return month_item
    return None
```

`_make_month_node()`（同ファイル ~289 行）では `ROLE_NODE_KIND` のみ設定。ラベルは `f"{month.year}年{month.month}月分 ({month.folder_name}){status_suffix}"` 形式。

**リスク:** ラベル書式変更で即壊れる。`folder_name` の部分一致で誤マッチしうる（例: `2026_3` vs `2026_30` の前方一致）。

### 修正方針

`LibraryMonthItem` を `QTreeWidgetItem` に直接紐付ける。

### 適用 diff

```diff
 ROLE_NODE_KIND = Qt.ItemDataRole.UserRole
 ROLE_FILE_ITEM = Qt.ItemDataRole.UserRole + 1
+ROLE_MONTH_ITEM = Qt.ItemDataRole.UserRole + 2

 # _make_month_node 内
         month_node = QTreeWidgetItem([label])
         month_node.setData(0, ROLE_NODE_KIND, KIND_MONTH)
+        month_node.setData(0, ROLE_MONTH_ITEM, month)
         month_node.setExpanded(True)

 # _month_from_node
     def _month_from_node(self, month_node: QTreeWidgetItem) -> LibraryMonthItem | None:
-        label = month_node.text(0)
-        for year_item in self._tree_data:
-            for month_item in year_item.months:
-                if month_item.folder_name in label:
-                    return month_item
-        return None
+        data = month_node.data(0, ROLE_MONTH_ITEM)
+        return data if isinstance(data, LibraryMonthItem) else None
```

### 受け入れ条件

- 月ノード右クリックの **月次 ZIP / CSV エクスポート** が従来どおり動作。
- 検索フィルタ（地域名）が従来どおり動作。
- `_month_from_node` がラベル文字列に依存しない。

### 追加すべきテスト

- **推奨:** `tests/test_library_tab.py` に `test_month_from_node_uses_role_data`（`QApplication` fixture 既存なら流用）。ダミー `QTreeWidgetItem` に `setData(0, ROLE_MONTH_ITEM, month_item)` し、戻り値が同一インスタンスであること。
- **代替:** 手動確認手順を PR 本文に記載（エクスポート成功スクショ不要、手順 3 行で可）。

### コミット例

`refactor(library): bind month nodes with ROLE_MONTH_ITEM`

---

## 修正 #3 [perf, Medium] — `merge_region_zip_csvs` の OOM リスク低減

### 対象ファイル

| 種別 | パス |
|------|------|
| 変更 | `src/jatic_library/core/csv_loader.py` |
| 変更 | `src/jatic_library/core/publication_postprocess.py`（`write_merged_csv`） |
| 確認 | `src/jatic_library/core/exporter.py`（月次 CSV エクスポート — 必要なら同 API へ） |
| 変更 | `tests/test_csv_loader.py` |

### 現状（実コード）

`csv_loader.py` 94–99 行付近:

```python
def merge_region_zip_csvs(zip_paths: list[Path]) -> pl.DataFrame:
    frames = [read_csv_frame_from_zip(path) for path in zip_paths]
    ...
    return pl.concat(frames, how="vertical_relaxed")
```

51 地域 × 大容量 CSV を **全件メモリ展開**してから `concat` するため、ピーク RSS がデータサイズに比例する。

### 修正方針

1. **新規** `merge_region_zip_csvs_to_path(zip_paths: list[Path], dest_path: Path) -> None`  
   - 各 ZIP の先頭 CSV を **一時ディレクトリ**（`tempfile.TemporaryDirectory()`）へ utf-8 化して書き出し。  
   - エンコーディングは **最初の ZIP のみ** `read_csv_frame_from_bytes` 相当で判定し、以降同じエンコーディングを使う（JARTIC 公開データが utf-8 のみなら判定省略可 — `data/` 実サンプルで確認し PR に記載）。  
   - `pl.scan_csv` → `pl.concat(lazy_frames, how="vertical_relaxed").sink_csv(dest_path)` でストリーミング書き出し。  
   - `with` 終了で一時ファイル削除。

2. **既存** `merge_region_zip_csvs` は **API 互換のため残す**（テスト・小規模呼び出し用）。内部で `to_path` + `read_csv` に委譲してもよいが、大規模パスでは使わない。

3. **呼び出し切替:** `publication_postprocess.write_merged_csv` を `merge_region_zip_csvs_to_path` に変更（`dest_csv` へ直接 sink）。

### 受け入れ条件

| 項目 | 基準 |
|------|------|
| メモリ | 51 地域結合時の RSS ピーク **≤ 2GB**（`psutil` またはタスクマネージャ — PR に数値） |
| 正しさ | 新実装の `統合.csv` が旧 `merge_region_zip_csvs` 結果と **行数一致**（セル完全一致は必須としない。改行・型ゆれは許容） |
| 空入力 | `zip_paths == []` で `CsvLoadError` |

### 追加すべきテスト

`tests/test_csv_loader.py`:

```python
def test_merge_region_zip_csvs_to_path_matches_in_memory(tmp_path: Path) -> None: ...
def test_merge_region_zip_csvs_to_path_empty_raises(tmp_path: Path) -> None: ...
```

小さな ZIP 3 つで `to_path` 出力と `merge_region_zip_csvs` の行数・主要列を比較。

大規模 RSS は CI 対象外 — PR 本文に手動計測を記載。

### コミット例

`perf(csv): stream region ZIP merge to disk via LazyFrame`

---

## 全修正完了後の検証（Cursor 必須）

```powershell
cd F:\Cursor\JATIC-Library
uv sync --group dev
uv run ruff check src tests
uv run mypy
uv run pytest -q
```

**手動（PR 本文に数値記載）:**

1. 保管庫タブ: 初回 / 再起動の表示時間（#1）。
2. 月次エクスポート・検索（#2）。
3. ダウンロード完了後の `統合.csv` 生成、または `write_merged_csv` 相当操作（#3）+ RSS ピーク。

---

## ドキュメント更新

INST_31 と同様:

| ファイル | 内容 |
|----------|------|
| `docs/instructions/README.md` | INST_32 行を **完了** に更新 |
| `docs/DEV_STATUS.md` | #32 行追加、pytest 件数更新（#1 +1〜2、#2 +0〜1、#3 +2 見込み → **約 168〜173**） |
| 本ファイル末尾 | land 済みコミット hash を追記 |
| `docs/YYYY-MM-DD_開発日記.html` | 修正ごとに 1 エントリ |

---

## 本パッチに含めない項目（将来課題）

| 項目 | 理由 |
|------|------|
| SQLite 版 `library_scan_cache` | INST_31 JSON 実装を正とする。必要性が出たら別 INST |
| 行数後追いの進捗バー（`m / n 件`） | フィードバック次第で別パッチ |
| 保管庫表示時間の追加チューニング（#1 未達時） | **INST_33**（#1 マージ禁止ルール参照） |
| `uncompressed_csv_size_in_zip` の ZIP64 境界 | キャッシュで実害は吸収。ZIP64 本格運用時に検証 |
| 月ノード以外のツリー `setData` 統一（年ノード等） | #2 の範囲外 |

---

## 指示書メタ

| 項目 | 値 |
|------|-----|
| 番号 | INST_32 |
| 作成 | 2026-05-22 |
| 依存 | INST_11（保管庫）, INST_31 #1（キャッシュ基盤） |
| 想定 PR 数 | 3（#1〜#3 各 1） |
| 実装状態 | **完了**（#1 `b3944a7` / #2 `51284ea` / #3 `cc00937`） |
| 計測状態 | **待ち**（#1 表示時間、#3 RSS — [PERF_MEASUREMENT_RULES.md](PERF_MEASUREMENT_RULES.md)） |
