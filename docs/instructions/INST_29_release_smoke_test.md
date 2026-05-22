# INST_29: リリース前 smoke test と検証

## 目的

INST_28 で生成した `JATIC-Library-0.1.0-beta.1-win64.zip` が、
**配布対象環境（Windows 10 / 11、Python・uv 未導入）で期待どおり動作する**ことを確認し、
v0.1.0-beta.1 を GitHub Releases に公開できる状態にする。

DEV_STATUS の R1（残り）/ R2 動作 / R4 を担当する。
R5〜R7（ドキュメント仕上げ）は別タスク（INST_30 系）に切り出す。

## 対象

- ビルド成果物: `dist/JATIC-Library-0.1.0-beta.1-win64.zip`
- 検証環境:
  - **環境 A**: 開発機（uv / Python / Chromium 導入済み）
  - **環境 B**: クリーン Windows 10/11（Python / uv / Chromium 未導入）

## 成果物

- `docs/BETA_TEST_LOG.md`: 環境ごとの実行結果記録（git 管理）
- GitHub Releases（`v0.1.0-beta.1` タグ + zip）
- 必要なら hotfix コミット

## 進め方

1. `docs/BETA_TEST_LOG.md` に結果を記入しながら Phase 1 → 2 → 3 → 4 を実走
2. blocker があれば hotfix → 該当 Phase のみ再検証
3. 公開可否判断 → GitHub Releases（手順は本指示書末尾）

## 受け入れ基準

- Phase 1: 全項目が pass または既知制限として文書化
- Phase 2: INST_27 ダイアログ（Yes / No）が動作
- Phase 3: クリーン環境で A-04 相当〜 C-10 が完走（beta では Phase 1〜2 後の公開も可 — 意思決定参照）
- Phase 4: サイズ・性能が想定範囲
- blocker は `BETA_TEST_LOG.md` に記録し、公開前に解消

## 意思決定（確定）

- **R4 クリーン環境**: 案 2 / 3 ハイブリッド（別 PC 優先、不可なら公開後フィードバック）
- **Release**: 案 1（Phase 1〜2 後に pre-release、Phase 3 は並行・事後）
- **ログ**: 案 A（`docs/BETA_TEST_LOG.md`）

## 関連

- INST_27: Chromium セットアップ UI
- INST_28: ビルド・zip
- チェックリスト詳細: [../BETA_TEST_LOG.md](../BETA_TEST_LOG.md)

## コミット

`docs: add INST_29 smoke test checklist and BETA_TEST_LOG template`
