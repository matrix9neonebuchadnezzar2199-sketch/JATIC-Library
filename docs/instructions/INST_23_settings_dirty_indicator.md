# INST_23: 設定タブの未保存インジケータ

## 目的

`SettingsTab` の各ウィジェット編集は `apply_to_config()` でまとめて永続化される。
保存忘れのまま「今すぐ更新確認」を押すと、未反映の地域選択で DL が走る可能性がある。
タイトルバーと保存ボタンで **未保存状態を可視化** し、事故を防ぐ。

## 対象ファイル

- `src/jatic_library/ui/tabs/settings_tab.py`
- `src/jatic_library/ui/main_window.py`
- `tests/test_settings_tab.py`（新規 or 既存拡張）

## 実装手順

### 1. `_dirty` 状態の追加

`SettingsTab` に `_dirty: bool` フィールドと `dirty_changed = Signal(bool)` を追加。

```python
class SettingsTab(QWidget):
    dirty_changed = Signal(bool)

    def __init__(self, ...):
        ...
        self._dirty = False
        self._wire_dirty_signals()
```

### 2. すべての編集系シグナルを接続

`RegionSelector.selection_changed`、`QLineEdit.textChanged`、`QCheckBox.toggled`、
`QSpinBox.valueChanged`、`QComboBox.currentIndexChanged` を **一括で** `_mark_dirty` に接続。
プログラム的にウィジェットを更新する `load_from_config()` 中は `QSignalBlocker` で抑止。

```python
def _wire_dirty_signals(self) -> None:
    self._region_selector.selection_changed.connect(self._mark_dirty)
    self._save_root.textChanged.connect(self._mark_dirty)
    # ... 他フィールドも同様

def _mark_dirty(self, *_: object) -> None:
    self._set_dirty(True)

def _set_dirty(self, value: bool) -> None:
    if self._dirty == value:
        return
    self._dirty = value
    self.dirty_changed.emit(value)
    self._save_button.setEnabled(value)
```

### 3. 保存ボタンの活性制御

`_save_button.setEnabled(False)` を初期値にし、`_set_dirty(True)` で活性化。
`save_to_store()` 成功後に `_set_dirty(False)`。

### 4. タイトルバーへの `*`

`MainWindow` で `settings_tab.dirty_changed` を受け、`setWindowTitle("JATIC-Library *")`
または `JATIC-Library` を切り替える。

```python
self._settings_tab.dirty_changed.connect(self._on_settings_dirty_changed)

def _on_settings_dirty_changed(self, dirty: bool) -> None:
    base = f"{__app_name__} v{__version__}"
    self.setWindowTitle(f"{base} *" if dirty else base)
```

### 5. 「今すぐ更新確認」時の警告（任意）

`run_update_check(force=True)` の入口で `settings_tab._dirty` を見て、未保存があれば
`QMessageBox.warning` で「設定が未保存です。先に保存しますか？」と確認する。

## 受け入れ基準

- 起動直後はタイトルに `*` なし、保存ボタンは disabled。
- 任意の編集で即座にタイトルに `*` が付き、保存ボタンが enabled。
- 「設定を保存」成功で `*` が消え、保存ボタンが disabled に戻る。
- `load_from_config()` 経由の値変更では dirty にならない。

## テスト

`tests/test_settings_tab.py` または `tests/ui/test_settings_dirty.py`：

- `test_initial_state_clean`
- `test_region_change_marks_dirty`
- `test_save_clears_dirty`
- `test_load_from_config_does_not_mark_dirty`

## コミット

`feat(ui): add settings tab dirty indicator`
