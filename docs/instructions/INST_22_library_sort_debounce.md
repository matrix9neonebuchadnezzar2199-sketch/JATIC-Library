# INST_22: 保管庫ソート保存のデバウンス・同値ガード

## 目的

`LibraryTab` のソート ComboBox を切り替えるたびに `ConfigStore.save()` が走り、`config.json`
ディスク書き込みが発生する。連続操作時の I/O を削減し、UX の引っかかりを防ぐ。

## 対象ファイル

- `src/jatic_library/ui/tabs/library_tab.py`
- `src/jatic_library/ui/main_window.py`（終了時フラッシュ）
- `tests/test_library_tab.py`（新規 or 既存拡張）

## 実装手順

### 1. 同値ガード

`LibraryTab._on_sort_changed()` の先頭で、現在の `self._config.ui.library_default_sort`
と等しい場合は早期 return する。

```python
def _on_sort_changed(self) -> None:
    sort_key = self._sort.currentData()
    if not isinstance(sort_key, str):
        return
    if sort_key == self._config.ui.library_default_sort:
        return
    self._config.ui.library_default_sort = sort_key
    self.refresh()
    self._schedule_sort_persist(sort_key)
```

### 2. デバウンスタイマ

`LibraryTab.__init__` で `QTimer(singleShot=True, interval=300)` を 1 本だけ生成し、
`timeout` でシグナルを emit するパターンに変更する。連続操作中は `start()` を呼び直すことで
リセットされ、最後の操作から 300ms 後に 1 回だけ保存される。

```python
self._sort_persist_timer = QTimer(self)
self._sort_persist_timer.setSingleShot(True)
self._sort_persist_timer.setInterval(300)
self._sort_persist_timer.timeout.connect(self._emit_sort_changed)
self._pending_sort_key: str | None = None

def _schedule_sort_persist(self, key: str) -> None:
    self._pending_sort_key = key
    self._sort_persist_timer.start()

def _emit_sort_changed(self) -> None:
    if self._pending_sort_key is None:
        return
    self.sort_changed.emit(self._pending_sort_key)
    self._pending_sort_key = None
```

`sort_changed` の接続先（`MainWindow._on_library_sort_changed`）は従来どおり `ConfigStore.save()`。

### 3. アプリ終了時のフラッシュ

`MainWindow.closeEvent`（完全終了パス）で `library_tab._sort_persist_timer.isActive()`
が True なら強制 timeout 発火＝即時保存。トレイ非表示時はフラッシュ不要。

```python
if self._library_tab._sort_persist_timer.isActive():
    self._library_tab._sort_persist_timer.stop()
    self._library_tab._emit_sort_changed()
```

## 受け入れ基準

- ComboBox を **同じ値**に再選択しても `ConfigStore.save()` が呼ばれない。
- ComboBox を 10 回連続で切り替えても、保存処理は最後の 1 回のみ（300ms 後）。
- アプリを終了する時点で未保存があれば、確実に保存される。

## テスト

`tests/test_library_tab.py` または `tests/ui/test_library_tab_sort.py` に以下を追加：

- `test_sort_changed_same_value_no_emit`
- `test_sort_changed_debounce_collapses_to_one_emit`（`QTest.qWait` + シグナルスパイ）
- `test_sort_changed_flush_on_close`

## コミット

`fix(ui): debounce library sort persistence`
