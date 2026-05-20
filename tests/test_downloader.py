"""Tests for downloader."""

from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from jatic_library.core.downloader import Downloader
from jatic_library.core.repository import Repository
from jatic_library.core.targets import by_code
from jatic_library.core.url_builder import compute_publish_info
from jatic_library.settings.config import DownloadSettings


class _FakeResponse:
    headers = {"content-length": "7"}

    def raise_for_status(self) -> None:
        return None

    async def aiter_bytes(self, chunk_size: int = 0):
        yield b"zipdata"

    async def aclose(self) -> None:
        return None


class _FakeHttp:
    def __init__(self, timeout_sec: float = 60.0) -> None:
        self._timeout_sec = timeout_sec

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def head(self, url: str) -> None:
        return None

    async def get_stream(self, url: str) -> _FakeResponse:
        return _FakeResponse()


@pytest.mark.asyncio
async def test_download_publication_one_region(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    save_root = tmp_path / "data"
    info = compute_publish_info(date(2026, 5, 15))
    settings = DownloadSettings(save_root=save_root, concurrency=1, retry=0)
    targets = [by_code("tokyo")]

    with Repository(db) as repo:
        downloader = Downloader(settings, repo)
        with patch("jatic_library.core.downloader.JarticHttpClient", _FakeHttp):
            result = await downloader.download_publication(info, targets)
    assert "tokyo" in result.succeeded
    zip_path = save_root / info.folder_name / "東京都.zip"
    assert zip_path.is_file()
    manifest_path = save_root / info.folder_name / "_manifest.json"
    assert manifest_path.is_file()
