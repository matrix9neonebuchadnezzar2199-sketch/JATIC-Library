# 指示書 #07: スクレイパ（Playwright）

## 前提
- 完了済み指示書: #01〜#06
- 決定事項: Chromium は将来 PyInstaller 同梱（#19）。開発時は `playwright install chromium`

## ゴール
実サイトから typeB ZIP リンクを抽出し、`targets.json` の `filename_key` を更新する。
`python -m jatic_library scrape` で実行可能。

## 作成・変更ファイル
- `src/jatic_library/core/playwright_scraper.py`
- `src/jatic_library/core/scraper.py`（軽量フォールバック・スタブ）
- `tests/test_playwright_scraper.py`（モック）

## 実装要件
- `ScrapedLink(display_name, url, filename_key)`
- `JarticScraper.fetch_typeb_links()` — openDataList レンダリング後 `a[href*='typeB_']`
- `merge_scraped_into_targets()` → `save_overrides` で `TARGETS_CACHE_PATH` へ
- 404 時ダウンローダから再スキャン呼び出し可能（関数エクスポート）

## やらないこと
- PyInstaller 同梱手順（#19）

## コミットメッセージ案
`feat(core): add Playwright scraper for typeB link discovery`
