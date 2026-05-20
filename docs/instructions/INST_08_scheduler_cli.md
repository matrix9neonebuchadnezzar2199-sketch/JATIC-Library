# 指示書 #08: スケジューラ・CLI

## 前提
- 完了済み指示書: #01〜#07
- 参照: docs/DESIGN.md §8

## ゴール
起動時チェック相当のロジックと CLI を実装。
`python -m jatic_library check` で `should_check_now` → 必要なら DL。
選択地域が空なら全51地域対象。

## 作成・変更ファイル
- `src/jatic_library/core/scheduler.py`
- `src/jatic_library/cli.py`
- `src/jatic_library/__main__.py`（CLI エントリ）
- `tests/test_scheduler.py`
- `tests/test_cli.py`

## 実装要件
- `StartupScheduler.should_check_now() -> CheckDecision`
- `StartupScheduler.run_check(force=False) -> CheckOutcome`
- CLI: `check`, `download`, `scrape`, 引数なしはバージョン表示

## コミットメッセージ案
`feat(cli): add scheduler and check/download/scrape commands`
