# v0.1.0-beta.1 — Beta Release

**Pre-release** — Windows 10/11 向け初回配布ビルドです。

## 入手

`JATIC-Library-0.1.0-beta.1-win64.zip` を展開し、フォルダ内の `JATIC-Library.exe` を起動してください。

## 主な機能

- JARTIC typeB（51 地域）の自動取得・保管庫閲覧
- 起動時 / 手動の更新確認、並列 DL、404 時の再スクレイプ
- 保管庫: ソート・再 DL・削除・タグ・月次エクスポート
- 初回 Chromium セットアップ UI（アプリ内インストール）
- トレイ・スタートアップ・Git 自動 commit

## 初回セットアップ（要約）

1. 設定タブで保存先を指定 → **設定を保存**
2. 「今すぐ更新確認」または「サイト再スキャン」で Chromium をインストール（約 200MB）
3. 保管庫タブで取得結果を確認

手順: [BETA_TEST.md](BETA_TEST.md) / 詳細: [USER_MANUAL.md](USER_MANUAL.md)

## 既知の制限

- 未コード署名のため SmartScreen 警告が出る場合があります
- クリーン環境での全項目検証はベータ公開後のフィードバックに一部委ねています（[BETA_TEST_LOG.md](BETA_TEST_LOG.md)）
- カレンダー・比較タブは未実装
- Git push は手動

## 検証

- `pytest` 147 passed / `ruff` / `mypy`
- `build.bat` 完走、配布 zip 約 136 MB

検証ログ: [BETA_TEST_LOG.md](BETA_TEST_LOG.md)
