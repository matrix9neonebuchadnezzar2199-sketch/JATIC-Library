# INST_24: ファイル削除の順序見直し

## 目的

現行の削除処理は **file → manifest → DB** の順で実行している。
途中で例外が出た場合、「ファイルだけ消えて DB に残る」「manifest だけ古い」などの
不整合が発生する。**順序を逆転**し、各ステップを冪等化することで、リトライ可能にする。

## 対象ファイル

- `src/jatic_library/ui/main_window.py`（`_on_delete_file`）
- `src/jatic_library/core/manifest.py`（`remove_file` の冪等性確認）
- `src/jatic_library/core/repository.py`（`delete_file` の冪等性確認）
- `tests/test_main_window.py` または `tests/test_delete_file.py`（新規 or 拡張）

## 実装手順

### 1. 新しい順序

```
1. Repository.delete_file(row_id)     # DB行削除（存在しなくてもOK）
2. Manifest.remove_file(...) + save   # manifest更新（存在しなくてもOK）
3. Path.unlink(missing_ok=True)       # ファイル削除
```

### 2. 各層の冪等化

`Repository.delete_file` は `DELETE FROM ... WHERE` で十分（行が無くてもエラーにしない）。
`Manifest.remove_file` は対象が無ければ no-op で抜ける。`Path.unlink` は `missing_ok=True`。

### 3. ログとエラーハンドリング

各ステップを個別の `try/except` で囲み、失敗してもログに残して次へ進む。
ただし「3 ステップ全部失敗」のときのみユーザーへ `QMessageBox.warning`。

```python
def _on_delete_file(self, file_item: LibraryFileItem) -> None:
    errors: list[str] = []
    if file_item.target_code:
        row = self._repo.get_file(file_item.publish_ym, file_item.target_code)
        if row is not None and row.id is not None:
            try:
                self._repo.delete_file(row.id)
            except OSError as exc:
                logger.exception("delete_file (db) failed")
                errors.append(f"DB: {exc}")

    folder = file_item.file_path.parent
    try:
        manifest = Manifest.load(folder)
        if manifest is not None and file_item.target_code:
            manifest.remove_file(file_item.target_code)
            manifest.save(folder)
    except OSError as exc:
        logger.exception("delete_file (manifest) failed")
        errors.append(f"manifest: {exc}")

    try:
        if file_item.file_path.is_file():
            file_item.file_path.unlink(missing_ok=True)
    except OSError as exc:
        logger.exception("delete_file (fs) failed")
        errors.append(f"file: {exc}")

    self._refresh_data_tabs()
    if len(errors) == 3:
        QMessageBox.warning(self, "削除エラー", "\n".join(errors))
    elif errors:
        self.statusBar().showMessage(
            f"削除は完了しましたが警告があります: {len(errors)}件", 5000
        )
```

## 受け入れ基準

- DB → manifest → file の順で実行される。
- 任意のステップが失敗しても、残りのステップは試行される。
- 同一ファイルに対する 2 回目の削除（既に物理ファイルが無い等）で例外を投げない。

## テスト

- `test_delete_order_db_first`（モックで呼び出し順を検証）
- `test_delete_missing_file_is_idempotent`
- `test_delete_partial_failure_continues`

## コミット

`fix(ui): reorder library file deletion for consistency`
