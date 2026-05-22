# INST_22: 保管庫ソート保存のデバウンス・同値ガード

## 目的

`LibraryTab` のソート ComboBox を切り替えるたびに `sort_changed` が即時 emit され、
`MainWindow._on_library_sort_changed` 経由で `ConfigStore.save()` が走り `config.json`
ディスク書き込みが発生する。連続操作時の I/O を削減し、UX の引っかかりを防ぐ。

## 対象ファイル

- `src/jatic_library/ui/tabs/library_tab.py`
- `src/jatic_library/ui/main_window.py`（終了時フラッシュ）
- `tests/test_library_tab_sort.py`（新規）

`_sync_sort_combo` が既に `blockSignals` で初期化時の emit を抑止しているため、
そちらの変更は不要。

## 実装手順

### 1. デバウンスタイマ（300ms・シングルショット）

`__init__` で `_sort_persist_timer` を生成。`_on_sort_changed` は同値ガード後に
`refresh()` と `_schedule_sort_persist()` のみ。emit は `_emit_sort_changed()` 経由。

### 2. 終了時フラッシュ

`LibraryTab.flush_pending_sort()` を `MainWindow._quit_application()` および
トレイ非表示でない `closeEvent` の `super()` 前に呼ぶ（`checkpoint()` より前）。

## 受け入れ基準

- 同値再選択で emit しない。
- 連続切替で最後の 1 回のみ emit（300ms デバウンス）。
- 完全終了時に未保存ソートがあれば persist される。
- `refresh()` / `_sync_sort_combo` ではデバウンスタイマが起動しない。

## テスト

`tests/test_library_tab_sort.py` — 4 件（同値・デバウンス・flush・refresh）。

## コミット

`fix(ui): debounce library sort persistence`
