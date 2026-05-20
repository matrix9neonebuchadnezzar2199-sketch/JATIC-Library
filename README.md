# JATIC-Library

JARTIC（日本道路交通情報センター）が公開する **断面交通量情報（typeB）** を、Windows 上で自動取得・整理・閲覧するためのデスクトップアプリです。

毎月1日頃に更新されるオープンデータを、手作業で51ボタンを押して落とす代わりに、**起動時チェック・並列ダウンロード・保管庫管理**まで一括で行います。

- リポジトリ: https://github.com/matrix9neonebuchadnezzar2199-sketch/JATIC-Library
- 詳細設計: [docs/DESIGN.md](docs/DESIGN.md)
- 実装指示書: [docs/instructions/](docs/instructions/)（Cursor 投入用 #01〜）
- 開発手順: [docs/DEV_SETUP.md](docs/DEV_SETUP.md)

---

## このツールでできること

### 自動ダウンロード

- JARTIC オープンデータページの **断面交通量（typeB）** ZIP を、**最大51地域**（北海道5方面＋46都府県）から取得
- 公開ルールに合わせたフォルダ名（例: `2026_3` = 2026年03月分）で保存
- **起動時の自動チェック**（既定: 24時間に1回まで）と **「今すぐ更新確認」** ボタン
- 並列ダウンロード（同時数 1〜5）、リトライ、SHA256 ハッシュ記録
- 部分取得済みの月は **不足地域だけ** 追加ダウンロード
- URL テンプレート方式を主とし、404 時は **Playwright によるサイト再スキャン**で `filename_key` を学習・更新

### 保管庫（ライブラリ）

- **年 → 月フォルダ → 地域ファイル** の3階層ツリー表示
- ソート（日付・地域・サイズ・ステータス）、フィルタ（年範囲・地方・タグ）
- 地域名・年月の **インクリメンタル検索**
- 選択ファイルのメタ情報（DL日時、サイズ、SHA256、元URL）
- ZIP 内 CSV の **プレビュー**（先頭1000行、文字コード自動判定）
- **簡易グラフ**（時間帯別交通量の折れ線など）
- **欠損月の検出**（2019年6月〜現在の穴を警告表示）
- 右クリック: エクスプローラーで開く / 再DL / 削除 / タグ編集 / エクスポート

### カレンダー・通知

- 公開済み月のマーカー、**次回公開予定日**（翌月1日）のハイライトとカウントダウン
- Windows **トースト通知**（新規公開・完了・エラー）
- **タスクトレイ常駐**（オプション）、スタートアップ登録

### 比較・エクスポート

- 同一地域の **2か月分を並べて比較**（テーブル＋差分グラフ）
- 複数月の **ZIP 一括** / **統合 CSV** / Parquet 出力
- 任意の **タグ付け** とタグ検索

### GitHub 連携（任意）

- ダウンロード完了後、指定ローカルリポジトリへ **自動 commit & push**（OFF が既定）
- 大容量データ向けに LFS 推奨の警告表示

### 見た目・運用

- **ライト / ダーク** テーマ（QSS、即時切替）
- 設定の JSON 永続化（`%LOCALAPPDATA%\JATIC-Library\config.json`）
- 取得履歴 SQLite（高速検索・タグ・イベントログ）

---

## 開発状況

| 指示書 | 内容 | 状態 |
|--------|------|------|
| #01 | プロジェクト初期化（Hello / setuptools） | 完了 |
| #02 | 定数・51地域マスタ・URL生成 | 完了 |
| #03 | Pydantic 設定・JSON 永続化 | 完了 |
| #04 | SQLite リポジトリ（CRUD） | 完了 |
| #05 | ロガー（loguru）・Windows トースト | 完了 |
| #06 | HTTP/2→1.1、マニフェスト、並列 DL | 完了 |
| #07 | Playwright スクレイパ・targets 学習 | 完了 |
| #08 | 起動スケジューラ・CLI | 完了 |
| #09〜 | UI・常駐・拡張・ビルド | 未着手 |

| Phase | 内容 | 状態 |
|-------|------|------|
| P2 | downloader, manifest, scheduler, CLI | 完了 |
| P3 | 設定タブ GUI | 未着手 |
| P4 | 保管庫タブ | 未着手 |
| P5〜P10 | スクレイパ、通知、カレンダー、ビルド等 | 未着手 |

> README の機能説明は、実装が進むたびに **「できること」と「開発状況」** を更新します。

---

## 前提・制限

- **対象は JARTIC が現在公開している月分のみ**（サイトは過去月を残さないため、遡及取得は不可）
- 公開は毎月1日想定だが、作業遅延があり得る（24時間間隔の再チェックで対応）
- 地域 ZIP は **数十 MB〜数 GB** あり得る。Git 管理時は LFS を推奨
- Windows 10/11 向け（トースト・スタートアップ登録）

---

## クイックスタート（開発者）

```powershell
cd F:\Cursor\JATIC-Library
uv venv --python 3.11
uv sync --group dev
uv run playwright install chromium
uv run python -m jatic_library
```

### CLI（#08 時点）

`config.json` に `download.save_root` を設定したうえで:

```powershell
uv run python -m jatic_library scrape              # filename_key を targets.json に保存
uv run python -m jatic_library download -r tokyo   # 1地域 DL
uv run python -m jatic_library download --all      # 51地域
uv run python -m jatic_library check               # 起動時相当の更新確認
```

配布ビルド: `build.bat` → `dist\JATIC-Library\`

---

## 保存先のフォルダ構造（ユーザーデータ）

```
[保存先]/
├── 2026_3/
│   ├── 東京都.zip
│   └── _manifest.json
└── ...

%LOCALAPPDATA%\JATIC-Library\
├── config.json
├── history.db
├── targets.json      # Playwright で学習した filename_key
└── logs/
```

---

## ライセンス

MIT — 詳細は [LICENSE](LICENSE)
