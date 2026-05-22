# INST_25: Playwright Chromium ガードの拡張

## 目的

`_warn_playwright_chromium_missing()` は `_start_worker(..., require_playwright=True)` 経由で
呼ばれているが、以下 2 経路では未適用のため、Chromium 未導入の exe 環境で
「黙って失敗する」可能性がある。

1. **`run_update_check`**: `_start_worker` を経由しない独自実装のため `require_playwright` フラグが効かない。
2. **`_on_redownload_file`**: 404 再ダウンロード時に `Downloader._maybe_rescrape_on_404` で Playwright へ連鎖するが、`require_playwright=False`（デフォルト）。

両経路に **事前ガード**を追加し、exe 配布版での事故を防ぐ。

## 対象ファイル

- `src/jatic_library/ui/main_window.py`
- `tests/test_playwright_guard.py`（新規）

`_warn_playwright_chromium_missing()` 本体と `chromium_missing_message()` /
`INSTALL_HINT` は既存のまま流用する。新規ヘルパーは不要。

## 実装手順

### 1. `run_update_check` の冒頭にガード挿入

`progress_dialog.show()` の **前** に呼ぶ。警告が出たらダイアログも開かずに return。

```python
if self._warn_playwright_chromium_missing():
    return
```

### 2. `_on_redownload_file` を `require_playwright=True` で起動

`_start_worker` の呼び出し引数に `require_playwright=True` を追加する。

### 3. `run_scrape` は現状維持

既に `require_playwright=True` で起動しているため変更不要。

### 4. 事後判定の維持

`run_update_check` の `_on_success` 内の `failures_look_like_missing_browser` は
事前ガード通過後の保険として残す（二段構え）。

## 受け入れ基準

- Chromium 未導入で「今すぐ更新確認」→ `progress_dialog` 前に警告、worker 未起動。
- Chromium 未導入で「再ダウンロード」→ 警告、worker 未起動。
- 「サイト再スキャン」は従来どおり（変更なし）。
- Chromium 導入済みでは全経路が従来どおり動作。
- `targets.json` の有無はガード判定に影響しない。

## テスト

`tests/test_playwright_guard.py` に 4 件（update_check blocked/proceeds、redownload blocked/proceeds）。

## コミット

`fix(ui): expand playwright chromium guard to check paths`
