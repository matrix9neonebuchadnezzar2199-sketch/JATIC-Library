# ベータ版テスト手順（v0.1.0-beta）

## ビルド

```powershell
cd JATIC-Library
python -m uv sync --group dev
.\build.bat
.\scripts\package-beta.ps1
```

成果物:

| 種類 | パス |
|------|------|
| フォルダ一式 | `dist\JATIC-Library\`（`JATIC-Library.exe` + `_internal\`） |
| 配布 zip | `dist\JATIC-Library-0.1.0-beta-win64.zip` |

**注意:** `JATIC-Library.exe` 単体では動きません。zip を展開したフォルダごとコピーしてください。

## 初回セットアップ（テスト PC）

1. zip を任意の場所に展開（例: `C:\Apps\JATIC-Library\`）
2. `JATIC-Library.exe` を起動
3. **設定**タブ: 保存先を確認（既定は exe 横の `data\`）
4. **PC起動と同時にチェック**: 「起動時に自動チェック」ON + 「Windows 起動時に自動起動」ON → **設定を保存**
5. 対象地域を選び **設定を保存**

## スモークテスト（R1）

| # | 操作 | 期待結果 |
|---|------|----------|
| 1 | exe 起動 | ウィンドウが中央付近に表示、クラッシュしない |
| 2 | 起動直後 | 進捗ダイアログ（更新確認）。未完了なら DL、完了済みなら短時間で終了 |
| 3 | 保管庫 | 取得済み月・地域がツリー表示（行数・GB） |
| 4 | 設定 → 今すぐ更新確認 | 手動チェックが動作 |
| 5 | PC 再起動（Windows 自動起動 ON 時） | ログオン後に exe が起動し、チェックが走る |
| 6 | `data\YYYY_M\` | 地域 ZIP、`extracted\`、`統合.csv` が存在（DL 実施後） |

## 既知の制限（ベータ）

- **ログ:** GUI exe（コンソールなし）では標準エラー出力に出せないため、ログは `%LOCALAPPDATA%\JATIC-Library\logs\` のファイルのみです。
- **Playwright（Chromium）** は同梱していません。通常の HTTP ダウンロードは exe のみで可。サイト再スキャン・404 再スクレイプには別途 Chromium が必要です。
- SmartScreen の警告が出る場合があります（未署名 exe）。
- 開発 PC と同じ `%LOCALAPPDATA%\JATIC-Library\config.json` を共有しないこと（別 PC では新規設定）。

## 問題報告時に添える情報

- バージョン（ヘルプ → バージョン情報）
- `config.json` の `download.save_root`（パスのみ）
- `%LOCALAPPDATA%\JATIC-Library\logs\` の直近ログ
