# JATIC-Library Beta テスト手順

**バージョン:** `0.1.0-beta.1`（配布 zip 名: `JATIC-Library-0.1.0-beta.1-win64.zip`）

## 1. 起動

`JATIC-Library.exe` をダブルクリックして起動します。
Windows Defender / SmartScreen の警告が出た場合は「詳細情報」→「実行」で続行してください。

**注意:** exe 単体では動きません。zip を展開したフォルダ一式をそのままコピーしてください。

## 2. 初回セットアップ

- 「設定」タブで保存先フォルダを指定し、「設定を保存」を押します。
- 「サイト再スキャン」または「今すぐ更新確認」を初回実行時、
  Chromium のインストールダイアログが出ます。「はい」を選んで約 200MB の
  ダウンロードを待ちます（インターネット接続必須）。

## 3. データ取得

「今すぐ更新確認」を押すと当月分の typeB データを取得します。
取得済みファイルは「保管庫」タブで確認できます。

## 既知の制限

- Windows 10 / 11 のみ対応
- 過去月の遡及取得は不可（JARTIC が typeB を非公開化）
- 初回起動時に `%LOCALAPPDATA%\JATIC-Library\` が作成されます
- GUI exe ではログは `%LOCALAPPDATA%\JATIC-Library\logs\` のファイルのみ

## 開発者向けビルド

```powershell
cd JATIC-Library
uv sync --group dev
.\build.bat
```

## 問題報告

GitHub Issues: https://github.com/matrix9neonebuchadnezzar2199-sketch/JATIC-Library/issues

報告時: ヘルプのバージョン、`download.save_root`（パスのみ）、直近ログ。
