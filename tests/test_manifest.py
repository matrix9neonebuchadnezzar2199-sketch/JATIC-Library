"""Tests for manifest JSON."""

from pathlib import Path

from jatic_library.core.manifest import Manifest, ManifestFileEntry


def test_manifest_roundtrip(tmp_path: Path) -> None:
    folder = tmp_path / "2026_3"
    entry = ManifestFileEntry(
        target_code="tokyo",
        display_name="東京都",
        filename="東京都.zip",
        source_url="https://example.test/typeB_tokyo.zip",
        size=100,
        sha256="abc",
        downloaded_at="2026-05-01T10:00:00+09:00",
    )
    manifest = Manifest(
        publish_ym="2026_3",
        publish_date="2026-05-01",
        downloaded_at="2026-05-01T10:00:00+09:00",
        source_dir_url="https://example.test/",
        files=[entry],
    )
    manifest.save(folder)
    loaded = Manifest.load(folder)
    assert loaded is not None
    assert loaded.publish_ym == "2026_3"
    assert loaded.files[0].target_code == "tokyo"
