# ロードマップ

実装順は [DESIGN.md](DESIGN.md) §12 に準拠します。

Cursor 向けの細分化指示書は [instructions/README.md](instructions/README.md) を参照。

| Phase | 成果物 | 状態 |
|-------|--------|------|
| **P0** | プロジェクト雛形（pyproject.toml, .gitignore, README, ディレクトリ） | 完了 |
| **P1** | `constants` / `targets` / `url_builder` / `config` / `repository` | 完了 |
| **P2** | `downloader` + `manifest` + `scheduler`（CLI動作確認） | 完了 |
| **P3** | PySide6 `MainWindow` + `SettingsTab` | 完了 |
| **P4** | `LibraryTab` ツリー・詳細・プレビュー | 完了 |
| **P5** | `playwright_scraper` フォールバック統合（DL 404 時） | 一部完了 |
| **P6** | 通知、トレイ常駐、進捗ダイアログ | 未着手 |
| **P7** | カレンダータブ、欠損検出、タグ | 未着手 |
| **P8** | 比較ビュー、可視化、エクスポート | 未着手 |
| **P9** | GitHub連携、ダークモード仕上げ | 一部完了 |
| **P10** | PyInstallerビルド、配布zip、ユーザーマニュアル | 未着手 |

完了した Phase は README の「開発状況」表も更新してください。
