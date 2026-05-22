# ロードマップ

実装順は [DESIGN.md](DESIGN.md) §12 に準拠します。

**進捗・残作業の正本は [DEV_STATUS.md](DEV_STATUS.md)**（§5 残作業）。本ファイルは Phase 単位の俯瞰用です。

Cursor 向け実装指示書は [instructions/README.md](instructions/README.md)（#01〜#28 完了、#29 進行中）。

| Phase | 成果物 | 状態 |
|-------|--------|------|
| **P0** | プロジェクト雛形 | 完了 |
| **P1** | コアデータ層 | 完了 |
| **P2** | ダウンロード・スケジューラ・CLI | 完了 |
| **P3** | MainWindow + SettingsTab | 完了 |
| **P4** | LibraryTab | 完了 |
| **P5** | DL 404 時 Playwright 再スクレイプ | 完了 |
| **P6** | 通知・トレイ・進捗ダイアログ | 完了 |
| **P7** | カレンダー・欠損検出・タグ | 完了 |
| **P8** | 比較・可視化・エクスポート | 完了 |
| **P9** | Git 連携・テーマ | 一部（commit のみ、push 未） |
| **P10** | PyInstaller・配布 zip・Release・マニュアル | **進行中**（INST_28 完了 → INST_29 smoke / Release） |

Phase またはマイルストーンが変わったら [DEV_STATUS.md](DEV_STATUS.md) と README を更新してください。
