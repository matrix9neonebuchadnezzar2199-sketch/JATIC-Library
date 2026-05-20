# 指示書 #06: ダウンローダ・マニフェスト・HTTP

## 前提
- 完了済み指示書: #01〜#05
- 決定事項: HTTP/2 試行後、ネゴシエーション失敗時のみ HTTP/1.1（プロセス内1回）

## ゴール
httpx 非同期で ZIP を並列 DL し、SHA256・`_manifest.json`・SQLite まで完走する。
`python -m jatic_library download -r tokyo` で1地域 DL 可能（要ネットワーク）。

## 作成・変更ファイル
- `src/jatic_library/core/http_client.py`
- `src/jatic_library/core/manifest.py`
- `src/jatic_library/core/downloader.py`
- `tests/test_http_client.py`
- `tests/test_manifest.py`
- `tests/test_downloader.py`

## 実装要件
- `JarticHttpClient`: context manager、HEAD/GET stream、HTTP/2→1.1 フォールバック1回
- `Manifest` / `ManifestFileEntry`: JSON 読み書き
- `Downloader.download_publication(info, targets, progress_cb?)` → `DownloadResult`
- 既存ファイルとハッシュ一致ならスキップ
- リトライ指数バックオフ

## やらないこと
- Playwright（#07）
- UI 進捗（#13）

## コミットメッセージ案
`feat(core): add async downloader with manifest and HTTP/2 fallback`
