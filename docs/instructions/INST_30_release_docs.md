# INST_30: 公開後ドキュメント仕上げ（R5〜R7）

## 目的

`v0.1.0-beta.1` pre-release 公開後、利用者・開発者向けドキュメントを実態に合わせて整える。
INST_29 のスコープ外（R5〜R7）を担当する。

## 対象ファイル

- `docs/USER_MANUAL.md`（R5）
- `README.md`（R6: スクリーンショット・バッジ・exe 導線）
- `docs/DEV_SETUP.md`（R7: PyInstaller・Playwright 制限・pytest 件数）

## 前提

- `MainWindow` は **2 タブ**（保管庫 / 設定）。#16/#17 は P11
- 配布 zip: `JATIC-Library-0.1.0-beta.1-win64.zip`
- Chromium: INST_27 ダイアログ（方式 B）、driver は `_internal/playwright/driver/`

## 受け入れ基準

- exe 利用者が README → BETA_TEST → USER_MANUAL だけで主要操作できる
- DEV_SETUP のビルド手順が `build.bat` 一本と一致（`package-beta.ps1` は任意・レガシー明記）

## 関連

- INST_29: smoke / Release
- [DEV_STATUS.md](../DEV_STATUS.md) §5.2b

## 状態

**完了**（2026-05-22）— USER_MANUAL / README / DEV_SETUP / RELEASE ノート
