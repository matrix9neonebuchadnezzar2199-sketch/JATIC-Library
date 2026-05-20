"""_manifest.json read/write."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from jatic_library.constants import APP_VERSION, MANIFEST_FILENAME


@dataclass
class ManifestFileEntry:
    """One file entry in a publication manifest."""

    target_code: str
    display_name: str
    filename: str
    source_url: str
    size: int
    sha256: str
    downloaded_at: str


@dataclass
class Manifest:
    """Publication folder manifest."""

    publish_ym: str
    publish_date: str
    downloaded_at: str
    source_dir_url: str
    app_version: str = APP_VERSION
    files: list[ManifestFileEntry] = field(default_factory=list)

    def path_for_folder(self, folder: Path) -> Path:
        """Return manifest file path under *folder*."""
        return folder / MANIFEST_FILENAME

    def save(self, folder: Path) -> Path:
        """Write manifest JSON to *folder*."""
        folder.mkdir(parents=True, exist_ok=True)
        path = self.path_for_folder(folder)
        path.write_text(
            json.dumps(asdict(self), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    @classmethod
    def load(cls, folder: Path) -> Manifest | None:
        """Load manifest from *folder* if present."""
        path = folder / MANIFEST_FILENAME
        if not path.is_file():
            return None
        raw = json.loads(path.read_text(encoding="utf-8"))
        files = [ManifestFileEntry(**item) for item in raw.get("files", [])]
        return cls(
            publish_ym=raw["publish_ym"],
            publish_date=raw["publish_date"],
            downloaded_at=raw["downloaded_at"],
            source_dir_url=raw["source_dir_url"],
            app_version=raw.get("app_version", APP_VERSION),
            files=files,
        )

    def file_entry(self, target_code: str) -> ManifestFileEntry | None:
        """Find entry by target code."""
        for entry in self.files:
            if entry.target_code == target_code:
                return entry
        return None

    def upsert_file(self, entry: ManifestFileEntry) -> None:
        """Insert or replace a file entry."""
        for index, existing in enumerate(self.files):
            if existing.target_code == entry.target_code:
                self.files[index] = entry
                return
        self.files.append(entry)
