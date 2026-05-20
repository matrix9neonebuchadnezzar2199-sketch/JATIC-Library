"""Optional Git commit after downloads."""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from jatic_library.settings.config import GitHubSettings


def sync_publication_folder(
    settings: GitHubSettings,
    save_root: Path,
    publish_ym: str,
) -> None:
    """Commit the publication folder when Git sync is enabled."""
    if not settings.enabled or not settings.auto_commit:
        return
    if settings.repo_path is None:
        logger.warning("GitHub sync enabled but repo_path is not set")
        return

    try:
        from git import Repo
    except ImportError as exc:
        logger.error("GitPython is not available: {}", exc)
        return

    repo_path = Path(settings.repo_path)
    if not (repo_path / ".git").is_dir():
        logger.warning("Git repo_path is not a git repository: {}", repo_path)
        return

    folder = save_root / publish_ym
    if not folder.is_dir():
        return

    try:
        repo = Repo(str(repo_path))
        rel = folder.relative_to(repo_path) if folder.is_relative_to(repo_path) else folder
        repo.index.add([str(rel)])
        if repo.is_dirty():
            message = f"chore(data): add JARTIC publication {publish_ym}"
            repo.index.commit(message)
            logger.info("Git commit created for {}", publish_ym)
            if settings.auth_method == "pat":
                logger.info("Push is not automatic; run git push manually or configure remote")
    except Exception as exc:
        logger.error("Git sync failed: {}", exc)
