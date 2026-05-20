"""Tests for optional git sync after downloads."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from jatic_library.core.git_sync import sync_publication_folder
from jatic_library.settings.config import GitHubSettings


def test_sync_skips_when_disabled(tmp_path: Path) -> None:
    settings = GitHubSettings(enabled=False)
    with patch("git.Repo") as mock_repo:
        sync_publication_folder(settings, tmp_path, "2026_3")
    mock_repo.assert_not_called()


def test_sync_skips_folder_outside_repo(tmp_path: Path) -> None:
    repo_path = tmp_path / "gitrepo"
    repo_path.mkdir()
    (repo_path / ".git").mkdir()
    save_root = tmp_path / "data"
    pub = save_root / "2026_3"
    pub.mkdir(parents=True)

    settings = GitHubSettings(
        enabled=True,
        auto_commit=True,
        repo_path=repo_path,
    )
    mock_repo = MagicMock()
    mock_repo.is_dirty.return_value = True
    with patch("git.Repo", return_value=mock_repo):
        sync_publication_folder(settings, save_root, "2026_3")
    mock_repo.index.add.assert_not_called()


def test_sync_adds_relative_folder(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    (repo_path / ".git").mkdir()
    pub = repo_path / "2026_3"
    pub.mkdir()

    settings = GitHubSettings(
        enabled=True,
        auto_commit=True,
        repo_path=repo_path,
    )
    mock_repo = MagicMock()
    mock_repo.is_dirty.return_value = True
    with patch("git.Repo", return_value=mock_repo):
        sync_publication_folder(settings, repo_path, "2026_3")
    mock_repo.index.add.assert_called_once()
    added = mock_repo.index.add.call_args[0][0]
    assert added == ["2026_3"]
