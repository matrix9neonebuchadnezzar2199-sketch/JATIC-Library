"""Persist ``AppConfig`` to JSON under APP_DATA_DIR."""

import json
import shutil
from datetime import datetime
from pathlib import Path

from loguru import logger
from pydantic import ValidationError

from jatic_library.constants import APP_DATA_DIR, CONFIG_PATH
from jatic_library.paths import normalize_save_root
from jatic_library.settings.config import AppConfig


def _finalize_config(config: AppConfig) -> AppConfig:
    """Ensure ``save_root`` points at the app-adjacent data folder when unset."""
    config.download.save_root = normalize_save_root(config.download.save_root)
    return config


class ConfigStore:
    """Load and save application configuration."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or CONFIG_PATH

    def load(self) -> AppConfig:
        """Load config from disk or return defaults without creating a file."""
        if not self.path.is_file():
            return _finalize_config(AppConfig.default())
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            return _finalize_config(AppConfig.model_validate(raw))
        except json.JSONDecodeError as exc:
            self._backup_broken(exc)
            return _finalize_config(AppConfig.default())
        except ValidationError as exc:
            self._backup_broken(exc)
            return _finalize_config(AppConfig.default())
        except OSError as exc:
            logger.warning("Failed to read config {}: {}", self.path, exc)
            return _finalize_config(AppConfig.default())

    def save(self, config: AppConfig) -> None:
        """Write config atomically via a temporary file."""
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        data = config.model_dump(mode="json")
        try:
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.replace(self.path)
        except OSError as exc:
            logger.error("Failed to save config {}: {}", self.path, exc)
            if tmp.is_file():
                tmp.unlink(missing_ok=True)
            raise

    def exists(self) -> bool:
        """Return True if the config file exists."""
        return self.path.is_file()

    def _backup_broken(self, exc: Exception) -> None:
        """Rename a broken config file for recovery."""
        stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup = self.path.with_suffix(f".broken.{stamp}.json")
        try:
            shutil.move(str(self.path), str(backup))
            logger.warning("Backed up broken config to {} ({})", backup, exc)
        except OSError as move_exc:
            logger.warning("Could not backup broken config {}: {}", self.path, move_exc)


def get_default_store() -> ConfigStore:
    """Return a store using the default config path."""
    return ConfigStore()
