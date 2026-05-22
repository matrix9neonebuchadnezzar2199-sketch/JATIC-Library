# INST_27: 初回起動時 Playwright Chromium セットアップ

## 目的

配布版 exe でサイト再スキャン・404 再ダウンロード・更新確認を使う前に、Chromium を
アプリ内からインストールできる UI を提供する。

INST_25 の事前ガードは「メッセージのみ」だった。本タスクで **PlaywrightSetupDialog** を
差し込み、ワンクリックインストールにする。

## 意思決定（確定）

| 項目 | 採用 |
|------|------|
| 発動タイミング | **案 A** — Chromium が要る操作時のみ（`_warn_playwright_chromium_missing`） |
| インストール起動 | **ハイブリッド** — `getattr(sys, "frozen", False)` で分岐 |
| 凍結時 | `node.exe` + `cli.js`（`compute_driver_executable()` → `Tuple[str, str]`） |
| 開発時 | `sys.executable -m playwright install chromium` |
| `__main__.py` シム | **Plan B**（INST_28 以降）。本 INST では触らない |

## 対象ファイル

- `src/jatic_library/core/playwright_env.py`
- `src/jatic_library/ui/widgets/playwright_setup_dialog.py`（新規）
- `src/jatic_library/ui/main_window.py`
- `tests/test_playwright_setup_dialog.py`（新規）
- `tests/test_playwright_env.py`（`_resolve_install_command` 追記）

## 実装要点

### `install_chromium` / `_resolve_install_command`

- 凍結時のみ `playwright._impl._driver` を import。失敗時は `(None, None)`。
- コマンドは `[node, cli, "install", "chromium"]`（tuple を正しく展開）。
- 失敗メッセージに `PROXY_HINT` を付与。

### `PlaywrightSetupDialog`

- Yes → バックグラウンド `QThread` で `install_chromium`。
- 完了時 `layout.replaceWidget` + Close 単一ボタン。
- `install_succeeded()` が True かつ `chromium_is_ready()` ならガード通過。

### `MainWindow._warn_playwright_chromium_missing`

- `chromium_is_ready()` なら即 `False`。
- 否则 `PlaywrightSetupDialog.exec()` → 成功時 `False`、それ以外 `True`。

## 受け入れ基準

- Chromium 未導入で「サイト再スキャン」「今すぐ更新確認」「再ダウンロード」→ セットアップダイアログ。
- 「いいえ」→ worker 未起動（ブロック）。
- 「はい」→ 進捗表示 → 成功後に続行可能。
- Chromium 導入済み → ダイアログなし。

## テスト

- `test_resolve_install_command_dev_uses_module_invocation`
- `test_resolve_install_command_frozen_uses_driver`
- `test_playwright_setup_dialog.py`（exec / install_succeeded / 行転送）
- 既存 `test_playwright_guard.py` 4 件維持

実インストール（ネットワーク DL）は **手動 smoke test** のみ。

## 関連

- INST_25: ガード経路
- INST_28: PyInstaller ビルド（本ダイアログを exe に同梱）

## コミット

`feat(ui): add in-app Playwright Chromium setup dialog`
