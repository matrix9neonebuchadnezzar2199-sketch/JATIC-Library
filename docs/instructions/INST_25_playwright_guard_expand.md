# INST_25: Playwright Chromium ガードの拡張

## 目的

`_warn_playwright_chromium_missing` は現在 `run_scrape()` のみで呼ばれる。
しかし **404 再ダウンロード時の自動再スクレイプ**（INST_13）でも Playwright が必要なため、
exe 配布環境で Chromium 未導入だと「更新確認」中に黙って失敗する可能性がある。

ガードを共通化し、Playwright を **使う可能性のある経路**すべてに適用する。

## 対象ファイル

- `src/jatic_library/ui/main_window.py`
- `src/jatic_library/core/playwright_env.py`（既存ヘルパの再利用）
- `src/jatic_library/core/scheduler.py`（任意：エラー型を明確化）
- `tests/test_playwright_env.py` または `tests/test_main_window.py`（新規 or 拡張）

## 実装手順

### 1. ガードを共通ヘルパに昇格

```python
def _require_playwright_chromium(self, *, reason: str) -> bool:
    """Chromium 未導入時は警告ダイアログを出し False を返す。"""
    hint = chromium_missing_message()
    if hint is None:
        return True
    QMessageBox.warning(self, "Playwright のセットアップ", f"{reason}\n\n{hint}")
    return False
```

### 2. 呼び出し箇所

- `run_scrape()`：既存どおり呼ぶ。
- `run_update_check(force=...)`：**`targets.json` が無い場合**にガード発動。
  常時要求すると通常運用が止まるため、短期対応はこの条件のみ。
- `_on_redownload_file()`：404 再スクレイプが走る可能性がある場合にガード（`targets.json` 欠如時）。

### 3. Scheduler 層からの明示エラー（推奨・任意）

`scheduler.run_check()` が再スクレイプ中に専用例外を投げ、
`MainWindow` でキャッチして案内するパターンも採用可能。
本指示書では UI 側ガードを最低ラインとする。

## 受け入れ基準

- Chromium 未導入の環境で「サイト再スキャン」を押すと従来どおり警告が出る。
- 同環境で「今すぐ更新確認」を押した時、`targets.json` が無ければ警告が出て worker は開始しない。
- 404 再ダウンロード経路でも、Chromium 必須となった場合に警告される。

## テスト

- `test_guard_blocks_scrape_when_chromium_missing`
- `test_guard_blocks_check_when_targets_missing_and_chromium_missing`
- `test_guard_passes_when_chromium_available`

## コミット

`fix(ui): expand playwright chromium guard to check paths`
