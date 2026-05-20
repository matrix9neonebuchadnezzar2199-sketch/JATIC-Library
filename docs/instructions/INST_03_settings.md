# 指示書 #03: 設定管理

## 前提
- 完了済み指示書: #01, #02
- 参照ドキュメント: docs/DESIGN.md の §5.1

## ゴール
アプリ設定をPydanticモデルで定義し、JSONファイルへの永続化・読込ができる状態にする。
CLIから設定の参照・更新が可能で、設定ファイルが存在しない場合は既定値で初期化される。

## 作成・変更ファイル
- `src/jatic_library/settings/__init__.py`（エクスポート定義）
- `src/jatic_library/settings/config.py`（新規）
- `src/jatic_library/settings/store.py`（新規）
- `tests/test_config.py`（新規）
- `tests/test_store.py`（新規）

## 実装要件

### settings/config.py
- `TargetSelection` — `selected_codes: set[str]`、無効codeは warnings で除去
- `DownloadSettings` — `save_root: Path | None`、concurrency 1〜10 等
- `ScheduleSettings`, `NotificationSettings`, `GitHubSettings`（Literal型）
- `UISettings`, `TraySettings`, `LogSettings`（level, retention）
- `AppConfig` — `default()`, `is_initial_setup_needed()`（save_root None で True）

### settings/store.py
- `ConfigStore.load()` — 無ければ既定値、破損時 `.broken.YYYYMMDDHHMMSS` バックアップ
- `ConfigStore.save()` — アトミック書込（.tmp → rename）
- `model_dump(mode="json")` で Path / set 対応
- `get_default_store()`

### settings/__init__.py
公開 API を `__all__` で列挙。

## テスト要件

### tests/test_config.py（8件以上）
- default / is_initial_setup_needed
- concurrency 境界 ValidationError
- 無効 target code → warnings のみ
- theme / commit_unit の ValidationError

### tests/test_store.py（8件以上）
- load 未存在 → 既定値、ファイル未作成
- save/load 往復（Path, set）
- 破損JSON / バリデーションエラーJSON → 既定値＋バックアップ
- アトミック書込み失敗時に本体が壊れない

## 動作確認手順
1. `pytest tests/test_config.py tests/test_store.py -v`（15件以上）
2. `ruff check src/ tests/`
3. インタラクティブで ConfigStore 往復

## やらないこと（スコープ外）
- 設定タブ UI（#10）
- app.py への組込（#09）

## コミットメッセージ案
```
feat(settings): add Pydantic config models and JSON persistence store
```
