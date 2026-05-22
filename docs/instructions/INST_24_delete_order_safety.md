# INST_24: ファイル削除の順序見直し

## 目的

現行の削除処理は **file → manifest → DB** の順で実行している。
途中で例外が出た場合、「ファイルだけ消えて DB に残る」「manifest だけ古い」などの
不整合が発生する。**順序を逆転**し、各ステップを独立 try/except で囲むことで、
部分失敗時もできる限り整合性を保ち、リトライ可能にする。

## 対象ファイル

- `src/jatic_library/ui/main_window.py`（`_on_delete_file`）
- `tests/test_delete_file.py`（新規）

`Manifest.remove_file` と `Repository.delete_file` は既に **冪等** なので
コア層の変更は不要。

## 実装手順

### 1. 新しい順序

```
1. Repository.delete_file(file_id)        # DB行削除（行が無くてもOK）
2. Manifest.remove_file(target_code)+save # manifest更新（target不在でもOK）
3. Path.unlink(missing_ok=True)           # ファイル削除
```

`target_code` が None（統合 CSV など）の場合は DB / manifest をスキップし、
ファイル削除のみ実行する。

### 2. 実装差分

`MainWindow._on_delete_file` を以下に置き換える。

```python
def _on_delete_file(self, file_item: object) -> None:
    if not isinstance(file_item, LibraryFileItem):
        return

    path = file_item.file_path
    folder = path.parent
    errors: list[str] = []

    # 1. DB 行を先に削除（冪等）
    if file_item.target_code:
        try:
            row = self._repo.get_file(file_item.publish_ym, file_item.target_code)
            if row is not None and row.id is not None:
                self._repo.delete_file(row.id)
        except sqlite3.Error as exc:
            errors.append(f"DB: {exc}")

    # 2. manifest 更新（冪等）
    if file_item.target_code:
        try:
            manifest = Manifest.load(folder)
            if manifest is not None:
                manifest.remove_file(file_item.target_code)
                manifest.save(folder)
        except OSError as exc:
            errors.append(f"manifest: {exc}")

    # 3. 物理ファイル削除（冪等）
    try:
        path.unlink(missing_ok=True)
    except OSError as exc:
        errors.append(f"file: {exc}")

    self._refresh_data_tabs()

    if any(err.startswith("file:") for err in errors):
        QMessageBox.warning(
            self,
            "削除",
            "ファイル削除に失敗しました:\n" + "\n".join(errors),
        )
    elif errors:
        self.statusBar().showMessage(
            f"削除は完了しましたが警告があります（{len(errors)}件）", 7000
        )
    else:
        self.statusBar().showMessage("ファイルを削除しました", 5000)
```

`import sqlite3` は既に main_window.py に存在するため追加不要。

### 3. 警告ポリシー（案 D）

| 失敗箇所 | 通知 |
|---|---|
| 物理ファイル（`file:`） | 必ず `QMessageBox.warning`（現行の critical 相当を尊重） |
| DB / manifest のみ | `statusBar` のみ |
| 成功 | `statusBar`「ファイルを削除しました」 |

### 4. 補足: 統合 CSV ファイルの扱い

`target_code` が None のファイル（年次統合 CSV など）は DB / manifest に登録が無いため、
ステップ 1・2 を実行せず、ステップ 3（unlink）のみ実行する。これは現行動作と同じ。

## 受け入れ基準

- DB → manifest → file の順で実行される。
- 任意のステップが失敗しても、残りのステップは試行される。
- 同一ファイルに対する 2 回目の削除（既に物理ファイルが無い等）で例外を投げない。
- `target_code` が None の場合は DB / manifest 操作をスキップする。
- 物理ファイル削除の失敗時は必ず警告ダイアログを表示する。

## テスト

`tests/test_delete_file.py`（新規）に以下を実装：

- `test_delete_calls_db_before_manifest_before_file`
- `test_delete_missing_file_is_idempotent`
- `test_delete_skips_db_when_target_code_is_none`
- `test_delete_partial_failure_continues`

## コミット

`fix(ui): reorder library file deletion for consistency`
