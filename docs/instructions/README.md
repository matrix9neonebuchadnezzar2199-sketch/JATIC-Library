# 実装指示書一覧

Cursor へ **1 本ずつ** 投入し、完了ごとに `pytest` → `ruff` → `mypy` → コミット。

| # | ファイル | タイトル | 状態 |
|---|----------|----------|------|
| 01 | [INST_01_project_init.md](INST_01_project_init.md) | プロジェクト初期化 | **完了** |
| 02 | [INST_02_targets_url.md](INST_02_targets_url.md) | 定数・地域マスタ・URL生成 | **完了** |
| 03 | [INST_03_settings.md](INST_03_settings.md) | 設定管理 | **完了** |
| 04 | [INST_04_repository.md](INST_04_repository.md) | SQLiteリポジトリ | **完了** |
| 05 | — | ロガー・ノーティファイア | 未作成 |
| 06 | — | ダウンローダ | 未作成 |
| 07 | — | スクレイパ（Playwright） | 未作成 |
| 08 | — | スケジューラ | 未作成 |
| 09〜20 | — | UI / 拡張 / ビルド | 未作成 |

- 差分メモ（照合時）: [ALIGNMENT.md](ALIGNMENT.md)
- 正本設計: [../DESIGN.md](../DESIGN.md)

## 依存関係

```
01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → ...
```
