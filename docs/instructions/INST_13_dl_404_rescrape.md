# 指示書 #13: DL 404 時の自動再スクレイプ

## ゴール
`download_publication` 中に 404 が出たら **1 回だけ** Playwright 再スキャン後リトライ。

## コミット
`feat(core): rescrape targets on 404 during download`
