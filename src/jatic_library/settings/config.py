"""Pydantic configuration models."""

import warnings
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from jatic_library.constants import (
    DEFAULT_CHECK_INTERVAL_HOURS,
    DEFAULT_CONCURRENCY,
    DEFAULT_RETRY,
    DEFAULT_TIMEOUT_SEC,
)
from jatic_library.core.targets import all_codes


class TargetSelection(BaseModel):
    """Selected region codes for download."""

    selected_codes: set[str] = Field(default_factory=set)

    @field_validator("selected_codes")
    @classmethod
    def validate_codes(cls, value: set[str]) -> set[str]:
        valid = set(all_codes())
        invalid = value - valid
        if invalid:
            warnings.warn(f"Unknown target codes ignored: {invalid}", stacklevel=2)
        return value & valid


class DownloadSettings(BaseModel):
    """Download behaviour."""

    save_root: Path | None = None
    concurrency: int = Field(default=DEFAULT_CONCURRENCY, ge=1, le=10)
    retry: int = Field(default=DEFAULT_RETRY, ge=0, le=10)
    timeout_sec: int = Field(default=DEFAULT_TIMEOUT_SEC, ge=10, le=600)
    rate_limit_bps: int | None = None


class ScheduleSettings(BaseModel):
    """Startup check scheduling."""

    auto_check_on_startup: bool = True
    recheck_interval_hours: int = Field(default=DEFAULT_CHECK_INTERVAL_HOURS, ge=1, le=720)
    last_check_at: str | None = None


class NotificationSettings(BaseModel):
    """Toast notification toggles."""

    on_new_publish: bool = True
    on_complete: bool = True
    on_error: bool = True


class GitHubSettings(BaseModel):
    """Optional Git sync."""

    enabled: bool = False
    repo_path: Path | None = None
    branch: str = "main"
    auto_commit: bool = False
    commit_unit: Literal["month", "region", "file"] = "month"
    auth_method: Literal["system", "pat"] = "system"
    pat_env_var: str = "GITHUB_PAT"


class UISettings(BaseModel):
    """UI preferences."""

    theme: Literal["light", "dark"] = "light"
    library_default_sort: str = "date_desc"
    show_missing_badge: bool = True


class TraySettings(BaseModel):
    """System tray and startup."""

    enable_tray: bool = False
    minimize_to_tray: bool = False
    start_with_windows: bool = False


class LogSettings(BaseModel):
    """File log preferences."""

    level: Literal["DEBUG", "INFO", "WARN", "ERROR"] = "INFO"
    retention: Literal["30d", "90d", "infinite"] = "90d"


class AppConfig(BaseModel):
    """Root application configuration."""

    targets: TargetSelection = Field(default_factory=TargetSelection)
    download: DownloadSettings = Field(default_factory=DownloadSettings)
    schedule: ScheduleSettings = Field(default_factory=ScheduleSettings)
    notification: NotificationSettings = Field(default_factory=NotificationSettings)
    github: GitHubSettings = Field(default_factory=GitHubSettings)
    ui: UISettings = Field(default_factory=UISettings)
    tray: TraySettings = Field(default_factory=TraySettings)
    log: LogSettings = Field(default_factory=LogSettings)

    @classmethod
    def default(cls) -> "AppConfig":
        """Return a fresh default configuration."""
        return cls()

    def is_initial_setup_needed(self) -> bool:
        """Return True when save_root has not been configured."""
        return self.download.save_root is None
