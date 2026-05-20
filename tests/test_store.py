"""Tests for JSON configuration store."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from jatic_library.settings.config import AppConfig
from jatic_library.settings.store import ConfigStore


def test_load_missing_returns_default(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    store = ConfigStore(path)
    cfg = store.load()
    assert cfg.is_initial_setup_needed() is True
    assert not path.exists()


def test_save_load_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    store = ConfigStore(path)
    cfg = AppConfig.default()
    cfg.download.save_root = Path("F:/JATIC_data")
    cfg.targets.selected_codes = {"tokyo", "osaka"}
    store.save(cfg)
    loaded = store.load()
    assert loaded.download.save_root == Path("F:/JATIC_data")
    assert loaded.targets.selected_codes == {"tokyo", "osaka"}


def test_broken_json_backup(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text("not json", encoding="utf-8")
    store = ConfigStore(path)
    cfg = store.load()
    assert cfg.is_initial_setup_needed() is True
    backups = list(tmp_path.glob("config.broken.*.json"))
    assert len(backups) == 1


def test_invalid_validation_backup(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"download": {"concurrency": 999}}), encoding="utf-8")
    store = ConfigStore(path)
    cfg = store.load()
    assert cfg.download.concurrency == 3
    assert list(tmp_path.glob("config.broken.*.json"))


def test_atomic_save_on_rename_failure(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text("{}", encoding="utf-8")
    store = ConfigStore(path)
    cfg = AppConfig.default()
    cfg.download.save_root = Path("F:/data")
    with patch.object(Path, "replace", side_effect=OSError("fail")):
        with pytest.raises(OSError):
            store.save(cfg)
    assert path.read_text(encoding="utf-8") == "{}"
